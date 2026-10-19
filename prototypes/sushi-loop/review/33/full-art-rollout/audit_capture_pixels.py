"""Independent image-level audit of complete native captures, without repacking.

python audit_capture_pixels.py --export EXPORT --raw RAW --output JSON
Optional --ids restricts the audit to completed object batches. Transparent RGB
is zeroed before frame hashing, so invisible color noise cannot fake animation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

from PIL import Image


def audit(export, raw, output, ids=None):
    source = export / 'source'
    asset_ids = ids or sorted(p.parent.name for p in source.glob('*/asset.json'))
    report = {'raw': str(raw), 'assets': {}, 'frames': 0, 'issues': [],
              'definition': 'Unique complete RGBA frames after zeroing fully transparent RGB; no alpha fitting or image mutation.'}
    for aid in asset_ids:
        metadata = json.loads((source / aid / 'asset.json').read_text())
        rig = json.loads((source / aid / 'rig.json').read_text())
        size = tuple(v * metadata['scale'] for v in metadata['frame'])
        measured = {}
        for clip, recipe in rig['clips'].items():
            for direction in metadata.get('directions', ['N', 'E', 'S', 'W']):
                hashes = set(); margins = []; bounds = []; missing = []
                for index in range(recipe['frames']):
                    path = raw / aid / (clip + '-' + direction) / (str(index).zfill(3) + '.png')
                    if not path.exists(): missing.append(index); continue
                    with Image.open(path) as opened:
                        image = opened.convert('RGBA')
                        if image.size != size:
                            report['issues'].append(str(path) + ': dimensions differ from fixed capture metadata')
                        alpha = image.getchannel('A'); box = alpha.getbbox()
                        if not box:
                            # Clearance/effect terminal empty poses are permitted,
                            # but distinct-frame and neighboring frames still count.
                            margins.append(None); bounds.append(None)
                        else:
                            margin = min(box[0], box[1], size[0] - box[2], size[1] - box[3])
                            margins.append(margin); bounds.append(box)
                            if not aid.startswith('floor-') and margin <= 0:
                                report['issues'].append(str(path) + ': visible alpha touches capture edge')
                        transparent = alpha.point(lambda a: 255 if a == 0 else 0)
                        image.paste((0, 0, 0, 0), mask=transparent)
                        hashes.add(hashlib.sha256(image.tobytes()).hexdigest())
                    report['frames'] += 1
                if missing: report['issues'].append(aid + '/' + clip + '/' + direction + ': missing indices ' + str(missing))
                elif recipe['frames'] > 1 and len(hashes) < 6:
                    report['issues'].append(aid + '/' + clip + '/' + direction + ': only ' + str(len(hashes)) + ' distinct visible frames')
                measured[clip + '-' + direction] = {'frames': recipe['frames'] - len(missing), 'uniqueVisibleFrames': len(hashes),
                                                    'minimumAlphaMarginPixels': min((v for v in margins if v is not None), default=None)}
        report['assets'][aid] = measured
        print('AUDIT_CAPTURE ' + aid, flush=True)
    report['passed'] = not report['issues']
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'assets': len(report['assets']), 'frames': report['frames'], 'issues': report['issues']}), flush=True)
    return report


def watch(export, raw, output, ids=None, timeout=14400):
    """Audit each finished object once while workers fill the shared raw root."""
    source = export / 'source'
    expected_ids = ids or sorted(p.parent.name for p in source.glob('*/asset.json'))
    complete = set()
    report = {'state': 'watching', 'expectedAssets': len(expected_ids), 'assets': {}, 'frames': 0,
              'issues': [], 'passed': False, 'raw': str(raw), 'startedAtUnix': time.time(),
              'definition': 'Full-frame dimensions, alpha margins and unique visible RGBA frames; fully transparent RGB is zeroed only for hashing.'}
    deadline = time.monotonic() + timeout
    def save():
        report['completedAssets'] = len(complete)
        report['updatedAtUnix'] = time.time()
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix('.partial.json')
        temporary.write_text(json.dumps(report, indent=2) + '\n')
        temporary.replace(output)
    save()
    while len(complete) < len(expected_ids):
        for aid in expected_ids:
            if aid in complete: continue
            metadata = json.loads((source / aid / 'asset.json').read_text())
            rig = json.loads((source / aid / 'rig.json').read_text())
            directions = metadata.get('directions', ['N', 'E', 'S', 'W'])
            jobs = [(clip, direction, index) for clip, recipe in rig['clips'].items() for direction in directions for index in range(recipe['frames'])]
            if not all((raw / aid / (clip + '-' + direction) / (str(index).zfill(3) + '.capture.json')).exists() for clip, direction, index in jobs): continue
            batch = audit(export, raw, None, [aid])
            report['assets'].update(batch['assets']); report['frames'] += batch['frames']; report['issues'] += batch['issues']; complete.add(aid)
            save()
            if batch['issues']:
                report['state'] = 'failed'; save(); return report
        if time.monotonic() > deadline:
            report['state'] = 'timed-out'; save(); return report
        if len(complete) < len(expected_ids): time.sleep(15)
    report['state'] = 'complete'; report['passed'] = not report['issues']; save()
    print('AUDIT_WATCH_COMPLETE ' + json.dumps({'passed': report['passed'], 'assets': len(complete), 'frames': report['frames']}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ids', nargs='+')
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    (watch if args.watch else audit)(args.export, args.raw, args.output, args.ids)
