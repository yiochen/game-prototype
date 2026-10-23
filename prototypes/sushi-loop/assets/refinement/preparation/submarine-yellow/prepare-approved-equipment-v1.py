"""Snapshot the two accepted equipment inputs without adopting them into the body."""
import hashlib
import json
import shutil
from pathlib import Path

RUN = Path(__file__).resolve().parents[2]
DEST = RUN / 'objects/submarine-yellow/inputs/approved-equipment-preparation-v1'
assert not DEST.exists(), 'Immutable preparation already exists'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


components = []
records = []
specs = [
    ('sub-hull-panels', 'round-01', 'delivery-round-01.json',
     'f811ac32a84bc59ea572a773963a5df54015b5d2a45cc5297cfd8408f8120473',
     'a2d09d1dbc230bb9417d1e425346f42ad48c5689dc6fe5b2b288fecdc63d4803',
     ['source/round-01-neutral.blend', 'candidates/round-01/neutral-resource-identity.json',
      'candidates/round-01/mounted/inverse-mount-identity.json']),
    ('sub-harpoon-mount', 'round-02', 'delivery-round-02-v3.json',
     '305a67d960aaaddaedbf68d5bd2786f62041a6937324a902cdbaee3760eb5b8d',
     'd7310ba7abc83f1a1fa02bb1160309af8f32c5904648e8d65d26c04adcfd615e',
     ['source/round-02/project.blend', 'candidates/round-02/canonical-neutral-persistent-resources.json',
      'candidates/round-02/canonical-neutral-resources.json',
      'candidates/round-02/canonical-neutral-identity.json']),
]
for asset, round_name, delivery_name, packet_hash, review_hash, selected in specs:
    obj = RUN / 'objects' / asset
    packet_path = obj / 'candidates' / round_name / 'packet.json'
    review_path = obj / 'reviews' / f'{round_name}.json'
    assert sha(packet_path) == packet_hash and sha(review_path) == review_hash
    packet, review, delivery = read(packet_path), read(review_path), read(obj / delivery_name)
    assert review['verdict'] == 'approve' and review['blockers'] == []
    assert review['candidatePacketSHA256'] == packet_hash
    bound = {}
    for group in ['files', 'candidateRenders', 'previews']:
        for record in packet[group].values():
            bound[(packet_path.parent / record['path']).resolve()] = record['sha256']
    assert sha(obj / delivery_name) in bound.values(), 'Adoption metadata is not in the accepted packet'
    for facing in 'NESW':
        record = next(x for x in delivery['atlases'] if x['clip'] == 'idle' and x['direction'] == facing)
        selected.append(record['path'])
    copies = selected + [f'candidates/{round_name}/packet.json', f'reviews/{round_name}.json', delivery_name]
    for relative in copies:
        src = obj / relative
        if relative not in [f'candidates/{round_name}/packet.json', f'reviews/{round_name}.json', delivery_name]:
            assert bound.get(src.resolve()) == sha(src), str(src)
        target = DEST / asset / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        assert sha(target) == sha(src)
        records.append({'path': str(target.relative_to(DEST)), 'sha256': sha(target),
                        'bytes': target.stat().st_size, 'upstreamObjectPath': relative})
    components.append({'asset': asset, 'acceptedRound': round_name, 'packetSHA256': packet_hash,
                       'originalJudgeReviewSHA256': review_hash,
                       'mainAdoption': delivery.get('mainAdoption', delivery.get('extraction')),
                       'upstreamExperiment': str(obj.relative_to(RUN)),
                       'scope': 'Exact accepted native neutral resource input only. Copied packet/review provide approval provenance; their full upstream evidence closure remains in the original committed experiment, not duplicated here.'})
manifest = {'schemaVersion': 1, 'asset': 'submarine-yellow',
            'stage': 'immutable-approved-equipment-input-preparation-only',
            'collectorPending': True, 'mainAdoptionPerformed': False, 'mainApproval': False,
            'components': components, 'files': records,
            'instruction': 'Do not resume/adopt until root supplies the third original-judge-approved collector and final three-component dispatch. Preserve frozen body/camera/lights/actions/mounts; append exact canonical IDLE neutral resources only, no remodeling or active-main mapping.'}
(DEST / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'manifestSHA256': sha(DEST / 'manifest.json'), 'files': len(records),
                  'bytes': sum(x['bytes'] for x in records), 'mainAdoptionPerformed': False}))
