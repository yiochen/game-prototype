"""Read-only native-capture and material-region measurements.

Uses the bundled Python/Pillow/NumPy runtime. Only audit-pixels.json is written.
The 43 original images/masks are checked against their historical source;
the 35 tuned renders are checked against the final frozen project receipts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'environment-lighting-study'))
from measure_pair import erode, measure, rgba, sha


def alpha_pair(left, right):
    a, b = rgba(left), rgba(right)
    if a.shape != b.shape:
        return {'sameCanvas': False, 'byteIdentical': False}
    delta = np.abs(a[:, :, 3].astype(int)-b[:, :, 3].astype(int))
    return {'sameCanvas': True, 'byteIdentical': bool(not delta.any()),
            'differentPixels': int((delta > 0).sum()), 'maximumByteDifference': int(delta.max())}


def visible_hash(path):
    image = rgba(path)
    image[:, :, :3][image[:, :, 3] == 0] = 0
    return hashlib.sha256(image.tobytes()).hexdigest()


def audit(folder):
    manifest = json.loads((folder/'manifest.json').read_text())
    historical = folder.parent/'environment-lighting-study'
    report = {'sourceSHA256': sha(folder/manifest['source']['blend']),
              'recipeSHA256': sha(folder/manifest['source']['recipe']),
              'approval': 'Faceted lighting selected; material revisions awaiting visual approval.',
              'issues': [], 'captureIntegrity': {}, 'subjects': {}}
    check = lambda condition, message: report['issues'].append(message) if not condition else None
    expected, copied = {}, set()
    for subject in manifest['subjects']:
        dimensions = [value*subject['captureScale'] for value in subject['frame']]
        for variant in subject['variants']:
            for direction, capture in variant['captures'].items():
                paths = [(0, capture['image'])]+list(enumerate(capture.get('frames', [])))[1:]
                for frame, path in paths:
                    expected[path] = {'subject': subject['id'], 'variant': variant['id'],
                                      'direction': direction, 'frame': frame,
                                      'dimensions': dimensions, 'camera': variant['camera'],
                                      'geometrySHA256': variant['geometrySHA256']}
                    if variant['id'] == 'faceted':
                        copied.add(path)
        for direction, path in subject.get('regionMasks', {}).items():
            expected[path] = {'subject': subject['id'], 'variant': 'mask', 'direction': direction,
                              'frame': 0, 'dimensions': dimensions, 'camera': None}
            copied.add(path)
    old_records = {}
    for path in sorted(historical.glob('captures-*.json')):
        for record in json.loads(path.read_text())['records']:
            old_records[record['image']] = record
    for path in sorted(copied):
        original, target = historical/path, folder/path
        check(target.exists(), path+': copied image missing')
        if not target.exists():
            continue
        signature = sha(target)
        check(signature == sha(original) == old_records[path]['sha256'], path+': historical copy/hash differs')
        image = rgba(target)
        dimensions = [int(image.shape[1]), int(image.shape[0])]
        check(dimensions == expected[path]['dimensions'], path+': copied canvas differs')
        report['captureIntegrity'][path] = {'sha256': signature, 'dimensions': dimensions,
                                           'provenance': 'byte-identical historical Faceted/mask capture',
                                           'historicalSourceSHA256': manifest['source']['previousStudySHA256']}
    new_records = []
    for path in sorted(folder.glob('captures-*.json')):
        receipt = json.loads(path.read_text())
        check(receipt['sourceSHA256'] == report['sourceSHA256'], path.name+': final source receipt mismatch')
        new_records += receipt['records']
    seen = set()
    for record in new_records:
        path = record['image']
        check(path not in seen, path+': duplicate receipt')
        seen.add(path)
        if path not in expected or path in copied:
            check(False, path+': unexpected render receipt')
            continue
        info, target = expected[path], folder/path
        check(target.exists(), path+': tuned render missing')
        if not target.exists():
            continue
        image = rgba(target)
        dimensions = [int(image.shape[1]), int(image.shape[0])]
        check(dimensions == info['dimensions'], path+': tuned canvas differs')
        signature = sha(target)
        check(signature == record['sha256'], path+': tuned receipt hash differs')
        for key in ('subject', 'variant', 'direction', 'frame', 'camera', 'geometrySHA256'):
            check(record.get(key) == info[key], path+': receipt '+key+' differs')
        check(abs(record['phase']+7*info['frame']/24) < 1e-12, path+': phase differs')
        phase_count = 0 if info['subject'] == 'crate-wood' else 3 if info['subject'] == 'belt-connected' else 1
        check(len(record['phaseMaterials']) == phase_count, path+': phase material count differs')
        report['captureIntegrity'][path] = {'sha256': signature, 'dimensions': dimensions,
                                           'provenance': 'final saved material-refinement native render',
                                           'frame': info['frame'], 'phase': record['phase']}
    check(len(copied) == 43, 'Expected35 historical colors plus8 masks')
    check(len(new_records) == 35, 'Expected35 final tuned native captures; found '+str(len(new_records)))
    check(set(expected) == set(report['captureIntegrity']), 'Capture inventory incomplete or unexpected')
    actual_pngs = {str(path.relative_to(folder)) for path in folder.rglob('*.png')}
    check(actual_pngs == set(expected), 'Unexpected/missing image files in study')
    for subject in manifest['subjects']:
        before, tuned = subject['variants']
        summary = {'directions': {}, 'animations': {}}
        classes = {'top': [255,0,0], 'side': [0,0,255]}
        if subject['id'] == 'belt-straight':
            classes['deck'] = [0,255,0]
        for direction in manifest['directions']:
            left = folder/before['captures'][direction]['image']
            right = folder/tuned['captures'][direction]['image']
            mask = folder/subject['regionMasks'][direction] if subject.get('regionMasks') else None
            if not left.exists() or not right.exists():
                check(False, subject['id']+'/'+direction+': comparison unavailable')
                continue
            pair = measure(left, right, mask, classes)
            check(pair['alpha']['byteIdentical'], subject['id']+'/'+direction+': silhouette alpha differs')
            if 'top' in pair['regions']:
                for mode in ('reference', 'candidate'):
                    pair[mode+'TopToSideRatio'] = pair['regions']['top'][mode]['meanLinearLuminance']/pair['regions']['side'][mode]['meanLinearLuminance']
            if subject['id'] == 'belt-straight':
                a, b, m = rgba(left), rgba(right), rgba(mask)
                deck = erode((m[:,:,:3] == [0,255,0]).all(2) & (m[:,:,3]>=250) & (a[:,:,3]>=250) & (b[:,:,3]>=250))
                difference = np.abs(a[:,:,:3].astype(int)-b[:,:,:3].astype(int))[deck]
                pair['unmodifiedDeckRGB'] = {'pixels': int(deck.sum()),
                                            'byteIdentical': bool(not difference.any()),
                                            'meanAbsoluteByteDifference': float(difference.mean()),
                                            'maximumByteDifference': int(difference.max())}
            summary['directions'][direction] = pair
        for variant in subject['variants']:
            frames = variant['captures']['S'].get('frames', [])
            if not frames:
                continue
            references = before['captures']['S']['frames']
            if not all((folder/path).exists() for path in frames):
                check(False, subject['id']+'/'+variant['id']+': incomplete animation')
                continue
            hashes = [visible_hash(folder/path) for path in frames]
            alpha = [alpha_pair(folder/references[i], folder/path) for i, path in enumerate(frames)]
            item = {'frames': len(frames), 'uniqueVisibleRGBAFrames': len(set(hashes)),
                    'fps': variant['captures']['S']['fps'], 'samePhaseAlphaUnchanged': all(p['byteIdentical'] for p in alpha),
                    'visibleFrameSHA256': hashes}
            check(item['frames'] == 24 and item['uniqueVisibleRGBAFrames'] == 24 and item['fps'] == 12
                  and item['samePhaseAlphaUnchanged'], subject['id']+'/'+variant['id']+': animation or same-phase alpha differs')
            summary['animations'][variant['id']] = item
        report['subjects'][subject['id']] = summary
    check(report['sourceSHA256'] == manifest['source']['sha256'], 'Final source hash differs')
    check(report['recipeSHA256'] == manifest['source']['recipeSHA256'], 'Final recipe hash differs')
    report['passed'] = not report['issues']
    (HERE/'audit-pixels.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'passed': report['passed'], 'captures': len(report['captureIntegrity']), 'issues': report['issues']}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', type=Path, required=True)
    args = parser.parse_args()
    audit(args.study)
