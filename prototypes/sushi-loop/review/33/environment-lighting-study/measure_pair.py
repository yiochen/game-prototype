"""Read-only pixel evidence for the isolated environment-lighting study.

Masks are unlit, ungraded geometry/material classifications. All comparisons
retain the complete authored canvas and use common opaque pixels eroded by
two source pixels. A clipped channel is evidence to report, not art approval.
"""
import hashlib
from pathlib import Path

import numpy as np
from PIL import Image


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rgba(path):
    with Image.open(path) as image:
        return np.asarray(image.convert('RGBA')).copy()


def erode(mask, iterations=2):
    for _ in range(iterations):
        padded = np.pad(mask, 1, constant_values=False)
        mask = np.logical_and.reduce([
            padded[y:y + mask.shape[0], x:x + mask.shape[1]]
            for y in range(3) for x in range(3)
        ])
    return mask


def luminance(rgb):
    srgb = rgb.astype(np.float64) / 255.
    linear = np.where(srgb <= .04045, srgb / 12.92,
                      ((srgb + .055) / 1.055) ** 2.4)
    return linear @ np.array([.2126, .7152, .0722])


def statistics(pixels):
    if not pixels.size:
        return {'pixels': 0}
    light = luminance(pixels)
    clipped = pixels >= 254
    return {
        'pixels': int(pixels.shape[0]),
        'meanRGB': pixels.mean(axis=0).tolist(),
        'meanLinearLuminance': float(light.mean()),
        'medianLinearLuminance': float(np.median(light)),
        'p05LinearLuminance': float(np.quantile(light, .05)),
        'p95LinearLuminance': float(np.quantile(light, .95)),
        'channelClippedPercent': dict(zip(('red', 'green', 'blue'),
                                         (clipped.mean(axis=0) * 100).tolist())),
        'anyChannelClippedPercent': float(clipped.any(axis=1).mean() * 100),
        'allChannelsClippedPercent': float(clipped.all(axis=1).mean() * 100),
    }


def measure(reference_path, candidate_path, mask_path=None, classes=None):
    reference, candidate = rgba(reference_path), rgba(candidate_path)
    if reference.shape != candidate.shape:
        raise ValueError('Complete authored canvases differ')
    delta = np.abs(reference[:, :, 3].astype(int) - candidate[:, :, 3].astype(int))
    report = {
        'referenceSHA256': sha(reference_path),
        'candidateSHA256': sha(candidate_path),
        'canvas': [int(reference.shape[1]), int(reference.shape[0])],
        'alpha': {
            'byteIdentical': bool(not delta.any()),
            'differentPixels': int((delta > 0).sum()),
            'maximumByteDifference': int(delta.max()),
        },
        'regions': {},
    }
    common = (reference[:, :, 3] >= 250) & (candidate[:, :, 3] >= 250)
    regions = {'all-opaque': erode(common)}
    if mask_path:
        classification = rgba(mask_path)
        if classification.shape != reference.shape:
            raise ValueError('Classification canvas differs')
        common &= classification[:, :, 3] >= 250
        report['maskSHA256'] = sha(mask_path)
        for name, color in (classes or {}).items():
            target = np.array(color[:3], dtype=int)
            # Exact class interiors, allowing one byte of color-space rounding.
            region = np.max(np.abs(classification[:, :, :3].astype(int) - target), axis=2) <= 1
            regions[name] = erode(region & common)
    for name, region in regions.items():
        old = statistics(reference[:, :, :3][region])
        new = statistics(candidate[:, :, :3][region])
        item = {'reference': old, 'candidate': new}
        if old['pixels']:
            item['candidateToReferenceLuminanceRatio'] = (
                new['meanLinearLuminance'] / old['meanLinearLuminance']
                if old['meanLinearLuminance'] > 1e-12 else None)
            item['newAnyChannelClippingPercentagePoints'] = (
                new['anyChannelClippedPercent'] - old['anyChannelClippedPercent'])
        report['regions'][name] = item
    return report
