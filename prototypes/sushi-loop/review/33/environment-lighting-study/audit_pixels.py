"""Read-only capture, silhouette, material-class and animation evidence.

Uses geometry-derived ungraded region masks. Reports clipping without making
an aesthetic choice. Execute with the bundled Python/Pillow/NumPy runtime.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from measure_pair import erode, measure, rgba, sha


def visible_hash(path):
    image = rgba(path)
    image[:, :, :3][image[:, :, 3] == 0] = 0
    return hashlib.sha256(image.tobytes()).hexdigest()


def alpha_pair(left, right):
    a, b = rgba(left), rgba(right)
    if a.shape != b.shape:
        return {'sameCanvas': False, 'byteIdentical': False}
    delta = np.abs(a[:, :, 3].astype(int) - b[:, :, 3].astype(int))
    return {'sameCanvas': True, 'byteIdentical': bool(not delta.any()),
            'differentPixels': int((delta > 0).sum()),
            'maximumByteDifference': int(delta.max())}


def ratio(top, side):
    return top / side if side > 1e-12 else None


def audit(folder, output, production_raw=None):
    manifest = json.loads((folder / 'manifest.json').read_text())
    report = {'sourceSHA256': sha(folder / manifest['source']['blend']),
              'recipeSHA256': sha(folder / manifest['source']['recipe']),
              'approval': 'Measurements only; lighting direction pending user review.',
              'issues': [], 'captureIntegrity': {}, 'subjects': {}}
    expected = {}
    for subject in manifest['subjects']:
        dimensions = [x * subject['captureScale'] for x in subject['frame']]
        for variant in subject['variants']:
            for direction, capture in variant['captures'].items():
                expected[capture['image']] = {'subject': subject['id'], 'variant': variant['id'],
                                             'direction': direction, 'frame': 0,
                                             'dimensions': dimensions, 'camera': variant['camera']}
                for frame, path in enumerate(capture.get('frames', [])):
                    expected[path] = {'subject': subject['id'], 'variant': variant['id'],
                                      'direction': direction, 'frame': frame,
                                      'dimensions': dimensions, 'camera': variant['camera']}
        for direction, path in subject.get('regionMasks', {}).items():
            expected[path] = {'subject': subject['id'], 'variant': 'mask', 'direction': direction,
                              'frame': 0, 'dimensions': dimensions, 'camera': None}
    records = []
    for path in sorted(folder.glob('captures-*.json')):
        value = json.loads(path.read_text())
        if value['sourceSHA256'] != report['sourceSHA256']:
            report['issues'].append(path.name + ': capture source hash differs')
        records += value['records']
    seen = set()
    for record in records:
        path = record['image']
        if path in seen:
            report['issues'].append(path + ': duplicate capture record')
        seen.add(path)
        if path not in expected:
            report['issues'].append(path + ': unexpected capture');continue
        target = folder / path
        info = expected[path]
        if not target.exists():
            report['issues'].append(path + ': capture missing');continue
        image = rgba(target)
        dimensions = [int(image.shape[1]), int(image.shape[0])]
        if dimensions != info['dimensions']:
            report['issues'].append(path + ': canvas differs')
        if sha(target) != record['sha256']:
            report['issues'].append(path + ': recorded hash differs')
        for key in ('subject', 'variant', 'direction', 'frame', 'camera'):
            if record.get(key) != info[key]: report['issues'].append(path + ': incorrect ' + key)
        if abs(record['phase'] + 7 * info['frame'] / 24) > 1e-12:
            report['issues'].append(path + ': recorded phase differs')
        phase_materials = len(record['phaseMaterials'])
        expected_count = 0 if info['variant'] == 'mask' or info['subject'] == 'crate-wood' else 3 if info['subject'] == 'belt-connected' else 1
        if phase_materials != expected_count:
            report['issues'].append(path + ': phase material count differs')
        report['captureIntegrity'][path] = {'sha256': record['sha256'], 'dimensions': dimensions,
                                          'frame': info['frame'], 'phase': record['phase']}
    missing = sorted(set(expected) - seen)
    if missing: report['issues'].append('Missing capture records: ' + ', '.join(missing))
    if len(records) != 148: report['issues'].append('Expected 140 color captures plus eight masks; found ' + str(len(records)))
    for subject in manifest['subjects']:
        baseline = subject['variants'][0]
        subject_report = {'comparisons': {}, 'animations': {}}
        classes = {'top': [255, 0, 0], 'side': [0, 0, 255]}
        if subject['id'] == 'belt-straight': classes['deck'] = [0, 255, 0]
        for variant in subject['variants'][1:]:
            per_direction = {}
            for direction in manifest['directions']:
                original = folder / baseline['captures'][direction]['image']
                candidate = folder / variant['captures'][direction]['image']
                mask = folder / subject['regionMasks'][direction] if subject.get('regionMasks') else None
                if not original.exists() or not candidate.exists() or (mask and not mask.exists()):
                    report['issues'].append(subject['id'] + '/' + variant['id'] + '/' + direction + ': pixel comparison unavailable')
                    continue
                entry = measure(original, candidate, mask, classes)
                for mode in ('reference', 'candidate'):
                    if 'top' in entry['regions']:
                        entry[mode + 'TopToSideRatio'] = ratio(entry['regions']['top'][mode]['meanLinearLuminance'], entry['regions']['side'][mode]['meanLinearLuminance'])
                if not entry['alpha']['byteIdentical']:
                    report['issues'].append(subject['id'] + '/' + variant['id'] + '/' + direction + ': alpha differs')
                per_direction[direction] = entry
            subject_report['comparisons'][variant['id']] = per_direction
        if baseline['captures'].get('S', {}).get('frames'):
            original_frames = baseline['captures']['S']['frames']
            for variant in subject['variants']:
                frames = variant['captures']['S']['frames']
                hashes = [];alpha = []
                for index, path in enumerate(frames):
                    if not (folder / path).exists():
                        report['issues'].append(path + ': animation frame absent');continue
                    hashes.append(visible_hash(folder / path))
                    pair = alpha_pair(folder / original_frames[index], folder / path)
                    alpha.append(pair)
                    if not pair['byteIdentical']:
                        report['issues'].append(path + ': animated alpha differs from baseline')
                item = {'frameCount': len(hashes), 'uniqueVisibleRGBAFrames': len(set(hashes)),
                        'fps': variant['captures']['S']['fps'],
                        'alphaMatchesSamePhaseBaseline': all(a['byteIdentical'] for a in alpha),
                        'visibleFrameSHA256': hashes}
                if item['frameCount'] != 24 or item['uniqueVisibleRGBAFrames'] != 24 or item['fps'] != 12:
                    report['issues'].append(subject['id'] + '/' + variant['id'] + ': incomplete or repeated belt animation')
                subject_report['animations'][variant['id']] = item
        report['subjects'][subject['id']] = subject_report
    if production_raw:
        report['baselineProductionPixelParity'] = {}
        for subject_id, asset_id, clip in (('belt-straight','belt-straight-e','running'),('crate-wood','crate-wood','idle')):
            comparisons = {}
            for direction in manifest['directions']:
                original_path = production_raw / asset_id / (clip+'-'+direction) / '000.png'
                study_path = folder / 'sprites' / subject_id / ('baseline-'+direction+'.png')
                original, study = rgba(original_path), rgba(study_path)
                common = erode((original[:,:,3]>=250)&(study[:,:,3]>=250))
                difference = np.abs(original[:,:,:3].astype(float)-study[:,:,:3].astype(float))[common]
                comparisons[direction] = {'productionCaptureSHA256':sha(original_path),
                    'studyCaptureSHA256':sha(study_path),
                    'alpha':alpha_pair(original_path,study_path),
                    'meanAbsoluteOpaqueRGBByteDifference':float(difference.mean()),
                    'maximumOpaqueRGBByteDifference':float(difference.max())}
            report['baselineProductionPixelParity'][subject_id] = comparisons
        report['baselineProductionPixelParity']['limitation'] = 'Study uses 64 EEVEE samples; existing production captures use 32. RGB/edge alpha need not be byte-identical. Native geometry/UV and shader graphs are checked independently in native-audit.json.'
    if report['sourceSHA256'] != manifest['source']['sha256']:
        report['issues'].append('Final source hash differs from manifest')
    if report['recipeSHA256'] != manifest['source']['recipeSHA256']:
        report['issues'].append('Final recipe hash differs from manifest')
    report['passed'] = not report['issues']
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'captureCount': len(report['captureIntegrity']), 'issues': report['issues']}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--production-raw', type=Path)
    args = parser.parse_args()
    audit(args.study, args.output, args.production_raw)
