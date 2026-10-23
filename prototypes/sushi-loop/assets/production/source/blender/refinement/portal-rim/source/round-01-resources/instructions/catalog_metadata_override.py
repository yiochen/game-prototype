"""Validate the explicit, independently reviewed dock-cover metadata reconciliation."""
import argparse
import hashlib
import json
import math
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
AUTHORITY_SHA256 = '0e9dcd1481cccef7849a6b2e8bf22dcd2b027b649a930b4f69d00a5aaea4d03e'
BEFORE = {'height': 1.87, 'renderPass': None}
AFTER = {'height': 2.2, 'renderPass': 'overhead'}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_override(folder, original, delivery, bound, project_sha256, review):
    descriptor = delivery.get('catalogMetadataOverride')
    if descriptor is None:
        return None
    require(original['id'] == 'dock-cover', 'Metadata reconciliation is only defined for dock-cover')
    require({key: original.get(key) for key in BEFORE} == BEFORE,
            'Expected the untouched dock-cover height1.87 and ordinary world pass')
    folder = Path(folder).resolve()

    def load_bound(record):
        require(isinstance(record, dict) and {'path', 'sha256'} <= record.keys(),
                'Metadata evidence needs an explicit path and SHA256')
        path = (folder / record['path']).resolve()
        require(path.is_relative_to(folder), 'Metadata evidence must stay inside the object')
        require(bound.get(path) == record['sha256'] and sha(path) == record['sha256'],
                'Metadata evidence is not the exact packet-bound file')
        return read(path)

    receipt = load_bound(descriptor)
    require(receipt.get('asset') == 'dock-cover', 'Wrong metadata receipt object')
    require(receipt.get('before') == BEFORE and receipt.get('after') == AFTER,
            'Only height1.87-to2.20 and the overhead pass are authorized')
    authority = receipt.get('authority', {})
    require(authority.get('sha256') == AUTHORITY_SHA256, 'Wrong frozen height reconciliation')
    law = load_bound(authority)
    require(law.get('asset') == 'dock-cover' and law.get('historicalCatalogHeight') == 1.87
            and law.get('candidateHeightBudget') == 2.2, 'Height authority changed')
    measurements = load_bound(receipt.get('measurements'))
    require(measurements.get('asset') == 'dock-cover'
            and measurements.get('projectSHA256') == project_sha256,
            'Envelope measurements belong to another source')
    samples = measurements.get('samples')
    require(isinstance(samples, list), 'Native envelope samples are missing')
    observed = set()
    for sample in samples:
        clip, direction, frame = sample.get('clip'), sample.get('direction'), sample.get('frame')
        require(clip in ['covered', 'uncover'] and direction in ['N', 'E', 'S', 'W'],
                'Unexpected native envelope clip or facing')
        require(type(frame) in [int, float] and math.isfinite(frame), 'Invalid native phase')
        key = (clip, direction, frame)
        require(key not in observed, 'Duplicate native envelope phase')
        observed.add(key)
        bounds = sample.get('bounds')
        require(isinstance(bounds, list) and len(bounds) == 2
                and all(isinstance(v, list) and len(v) == 3 for v in bounds),
                'Native envelope needs minimum and maximum XYZ bounds')
        require(all(type(v) in [int, float] and math.isfinite(v) for side in bounds for v in side),
                'Nonfinite native envelope coordinate')
        require(all(bounds[0][axis] <= bounds[1][axis] for axis in range(3)), 'Inverted bounds')
        for axis, (low, high) in enumerate([(-1.5, 1.5), (-1.5, 1.5), (-.012, 2.2)]):
            require(bounds[0][axis] >= low - 1e-5 and bounds[1][axis] <= high + 1e-5,
                    'Native cover geometry exceeds the frozen envelope')
    phases = [*range(1, 14), *[v + .5 for v in range(1, 13)]]
    required = {(clip, direction, phase) for clip in ['covered', 'uncover']
                for direction in ['N', 'E', 'S', 'W'] for phase in phases}
    require(required <= observed, 'Missing native key, half-frame, closure or terminal envelope evidence')
    require(review.get('verdict') == 'approve' and review.get('blockers') == []
            and review.get('independentReview') is True, 'Independent approval is missing')
    require(review.get('catalogMetadataOverride') == {
        'receiptSHA256': descriptor['sha256'], 'approved': True, 'fields': AFTER},
        'Judge has not explicitly approved these exact metadata fields and receipt')
    return {'fields': dict(AFTER), 'receipt': descriptor['path'],
            'receiptSHA256': descriptor['sha256'],
            'nativeMeasurementSHA256': receipt['measurements']['sha256'],
            'authoritySHA256': AUTHORITY_SHA256, 'nativeSamples': len(observed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset')
    parser.add_argument('--round', required=True)
    args = parser.parse_args()
    folder = RUN / 'objects' / args.asset
    base = folder / 'candidates' / args.round
    packet = read(base / 'packet.json')
    records = [*packet['files'].values(), *packet['candidateRenders'].values(), *packet['previews'].values()]
    bound = {(base / record['path']).resolve(): record['sha256'] for record in records}
    delivery_record = packet['files'].get('candidateResource:round:delivery.snapshot.json')
    delivery = read(base / delivery_record['path']) if delivery_record else read(folder / 'delivery.json')
    original_path = folder / 'final/original-catalog-object.json'
    if not original_path.exists():
        original_path = folder / 'inputs/catalog-object.json'
        require(bound.get(original_path.resolve()) == sha(original_path),
                'Pre-promotion catalog snapshot must be packet-bound')
    original = read(original_path)
    review = read(folder / 'reviews' / f'{args.round}.json')
    result = validate_override(folder, original, delivery, bound,
                               packet['files']['candidateProject']['sha256'], review)
    require(result is not None, 'No metadata reconciliation was submitted')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
