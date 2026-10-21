"""Check measured native facing evidence against the original world publisher."""
import argparse
import hashlib
import json
import math
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
EXPECTED = {'N': math.pi, 'E': math.pi / 2, 'S': 0, 'W': -math.pi / 2}


def angle(matrix):
    return math.atan2(matrix[1][0], matrix[0][0])


def audit(folder, round_name, views=None):
    folder = Path(folder)
    packet = json.loads((folder / 'candidates' / round_name / 'packet.json').read_text())
    views = views or packet['capture']['views']
    validation_path = (folder / 'candidates' / round_name / packet['files']['nativeValidation']['path']).resolve()
    data = json.loads(validation_path.read_text())
    native_reference = data.get('nativeValidation', data.get('sourceAudit'))
    if isinstance(native_reference, str):
        validation_path = (folder / native_reference).resolve()
        bound = {(folder / 'candidates' / round_name / item['path']).resolve(): item['sha256']
                 for item in packet['files'].values()}
        if validation_path not in bound:
            # Evidence-only rounds can retain a hash-bound prior packet rather
            # than duplicate every unchanged native audit as a new resource.
            for prior_path, prior_sha in list(bound.items()):
                if prior_path.name != 'packet.json':
                    continue
                if hashlib.sha256(prior_path.read_bytes()).hexdigest() != prior_sha:
                    raise ValueError(f'{folder.name}: referenced prior packet changed')
                prior = json.loads(prior_path.read_text())
                for item in prior.get('files', {}).values():
                    path = (prior_path.parent / item['path']).resolve()
                    if path == validation_path:
                        bound[path] = item['sha256']
        if validation_path not in bound or hashlib.sha256(validation_path.read_bytes()).hexdigest() != bound[validation_path]:
            raise ValueError(f'{folder.name}: referenced native audit is not exact packet-bound evidence')
        data = json.loads(validation_path.read_text())
    measured = {view: [] for view in views}
    records = next((data[key] for key in ['renders', 'views', 'nativeCaptures',
                    'captureRecords', 'nativeFrames', 'frames', 'audit_directions', 'renderViews'] if data.get(key)), [])
    if isinstance(records, dict) and isinstance(records.get('views'), dict):
        records = records['views']
    manifest_reference = next((data[key] for key in ['renderManifest', 'nativeRecords']
                               if isinstance(data.get(key), str)), None)
    if not records and manifest_reference:
        manifest_path = (validation_path.parent / manifest_reference).resolve()
        if not manifest_path.is_file():
            manifest_path = (folder / manifest_reference).resolve()
        bound = {(folder / 'candidates' / round_name / item['path']).resolve(): item['sha256']
                 for item in packet['files'].values()}
        if manifest_path not in bound:
            raise ValueError(f'{folder.name}: native render manifest is not packet-bound')
        if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != bound[manifest_path]:
            raise ValueError(f'{folder.name}: packet-bound native render manifest changed')
        manifest = json.loads(manifest_path.read_text())
        records = manifest if isinstance(manifest, list) else manifest.get('renders', manifest.get('frames', []))
    entries = records.items() if isinstance(records, dict) else [(record.get('direction'), record) for record in records]
    for facing, record in entries:
        if facing not in measured and isinstance(facing, str) and isinstance(record.get('clip'), str):
            # Static native audits may key captures by their declared clip and
            # facing ("static-N"), rather than by facing alone.
            facing = facing.removeprefix(record['clip'] + '-')
        if facing not in measured:
            continue
        if 'rootRotationZ' in record:
            measured[facing].append(record['rootRotationZ'])
        elif 'rootRotationDegrees' in record:
            measured[facing].append(math.radians(record['rootRotationDegrees']))
        elif 'rootMatrix' in record:
            measured[facing].append(angle(record['rootMatrix']))
    # Some native prop audits record world and local matrices for every part/pose.
    for facing, frames in data.get('nativeGeometryMeasurements', {}).items():
        if facing not in measured:
            continue
        for frame in frames:
            root = frame.get(data.get('rootObject'))
            if root and 'matrixWorld' in root:
                measured[facing].append(angle(root['matrixWorld']))
    if views == ['S'] and not measured['S']:
        roots = [obj for obj in data.get('nativeCurrent', {}).get('objects', [])
                 if obj.get('type') == 'EMPTY' and obj.get('parent') is None]
        if len(roots) == 1:
            measured['S'].append(angle(roots[0]['matrix']))
    for facing, values in measured.items():
        if not values:
            raise ValueError(f'{folder.name}/{facing}: missing measured root rotation evidence')
        for value in values:
            error = math.atan2(math.sin(value - EXPECTED[facing]), math.cos(value - EXPECTED[facing]))
            if abs(error) > 1e-4:
                raise ValueError(f'{folder.name}/{facing}: native rotation {math.degrees(value):.6f}deg differs from publisher {math.degrees(EXPECTED[facing]):.0f}deg')
    return {'asset': folder.name, 'round': round_name, 'status': 'passed',
            'sourceConvention': 'native_actions.apply_clip: S0/E+90/N180/W-90 degrees',
            'sampleCounts': {facing: len(values) for facing, values in measured.items()}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset')
    parser.add_argument('--round', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(RUN / 'objects' / args.asset, args.round)))
