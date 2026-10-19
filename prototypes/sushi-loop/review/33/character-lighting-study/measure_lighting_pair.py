"""Read-only same-facing lighting comparison using a native hat-class pass.

Mask convention: red=upward hat normal, blue=side normal, other colors excluded.
Use the same pose, facing, camera and complete capture canvas for both images.
This measures pixel evidence; it does not approve a lighting direction or infer
that geometry/camera were unchanged merely because the alpha happens to match.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def erode(mask, iterations=2):
    for _ in range(iterations):
        padded = np.pad(mask, 1, constant_values=False)
        mask = np.logical_and.reduce([padded[y:y + mask.shape[0], x:x + mask.shape[1]] for y in range(3) for x in range(3)])
    return mask


def luminance(rgb):
    value = rgb.astype(np.float64) / 255.
    linear = np.where(value <= .04045, value / 12.92, ((value + .055) / 1.055) ** 2.4)
    return linear @ np.array([.2126, .7152, .0722])


def stats(rgba, region):
    values = luminance(rgba[:, :, :3])[region]
    green = rgba[:, :, 1][region]
    return {'pixels': int(values.size), 'meanLinearLuminance': float(values.mean()),
            'medianLinearLuminance': float(np.median(values)),
            'p05LinearLuminance': float(np.quantile(values, .05)),
            'p95LinearLuminance': float(np.quantile(values, .95)),
            'greenClippedPercent': float((green >= 254).mean() * 100)}


def ratio(numerator, denominator):
    return numerator / denominator if denominator > 1e-12 else None


def measure(reference_path, candidate_path, mask_path):
    reference_path, candidate_path, mask_path = map(Path, (reference_path, candidate_path, mask_path))
    images = []
    for path in (reference_path, candidate_path, mask_path):
        with Image.open(path) as opened: images.append(np.asarray(opened.convert('RGBA')).copy())
    reference, candidate, classification = images
    if reference.shape != candidate.shape or reference.shape != classification.shape:
        raise ValueError('Reference, candidate and mask must retain the same complete authored canvas')
    alpha_delta = np.abs(reference[:, :, 3].astype(int) - candidate[:, :, 3].astype(int))
    report = {'reference': str(reference_path), 'candidate': str(candidate_path), 'mask': str(mask_path),
              'sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in (reference_path, candidate_path, mask_path)},
              'canvas': [int(reference.shape[1]), int(reference.shape[0])],
              'alpha': {'byteIdentical': bool(not alpha_delta.any()), 'differentPixels': int((alpha_delta > 0).sum()),
                        'maximumByteDifference': int(alpha_delta.max())}, 'regions': {}}
    common_opaque = (reference[:, :, 3] >= 250) & (candidate[:, :, 3] >= 250) & (classification[:, :, 3] >= 250)
    regions = {'top': (classification[:, :, 0] >= 180) & (classification[:, :, 1] < 64) & (classification[:, :, 2] < 64),
               'side': (classification[:, :, 2] >= 180) & (classification[:, :, 0] < 64) & (classification[:, :, 1] < 64)}
    for name, region in regions.items():
        region = erode(region & common_opaque)
        if region.sum() < 20: raise ValueError('Insufficient opaque interior hat pixels in ' + name + ' region')
        old, new = stats(reference, region), stats(candidate, region)
        report['regions'][name] = {'reference': old, 'candidate': new,
                                   'candidateToReferenceLuminanceRatio': ratio(new['meanLinearLuminance'], old['meanLinearLuminance'])}
    for mode in ('reference', 'candidate'):
        report[mode + 'TopToSideRatio'] = ratio(report['regions']['top'][mode]['meanLinearLuminance'], report['regions']['side'][mode]['meanLinearLuminance'])
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--mask', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = measure(args.reference, args.candidate, args.mask)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('canvas', 'alpha', 'referenceTopToSideRatio', 'candidateTopToSideRatio')}))
