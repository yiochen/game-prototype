"""Bind exact three accepted neutral components for the final main export."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

RUN = Path(__file__).resolve().parents[2]
OBJ = RUN / 'objects/submarine-yellow'
DEST = OBJ / 'inputs/approved-canonical-equipment-v1'
assert not DEST.exists()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def create(path, data):
    assert not path.exists(), str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


prior = OBJ / 'inputs/approved-equipment-preparation-v1/manifest.json'
assert sha(prior) == 'a07ed34edf310ba401f554f3c4fbd95e5712d0c15a69a8363b388ffdd402cc64'
data = read(prior)
records = []
for record in data['files']:
    path = prior.parent / record['path']
    assert sha(path) == record['sha256']
    records.append({'path': str(path.relative_to(OBJ)), 'sha256': sha(path), 'bytes': path.stat().st_size})
records.append({'path': str(prior.relative_to(OBJ)), 'sha256': sha(prior), 'bytes': prior.stat().st_size})
components = copy.deepcopy(data['components'])
for component in components:
    component['inputPrefix'] = 'inputs/approved-equipment-preparation-v1/' + component['asset']

upstream = RUN / 'objects/sub-collector-inlet'
packet_path = upstream / 'candidates/round-02/packet.json'
review_path = upstream / 'reviews/round-02.json'
delivery_path = upstream / 'delivery-round-02.json'
assert sha(packet_path) == 'e1dc55a4c0320d694b82372cc4e2ed28cfb3082f501c42310cab25d10ed0bea2'
assert sha(review_path) == '2f8647c1a6ba507e365c3e601328f361545e88cff9d3e392484f91d2924d36e2'
packet, review, delivery = read(packet_path), read(review_path), read(delivery_path)
assert review['verdict'] == 'approve' and review['blockers'] == []
assert review['candidatePacketSHA256'] == sha(packet_path)
bound = {}
for group in ['files', 'candidateRenders', 'previews']:
    for record in packet[group].values():
        bound[(packet_path.parent / record['path']).resolve()] = record['sha256']
assert sha(delivery_path) in bound.values()
selected = [delivery['project'], delivery['canonicalNeutralResources']]
for direction in 'NESW':
    selected.append(next(x for x in delivery['atlases'] if x['clip'] == 'idle' and x['direction'] == direction)['path'])
for relative in selected:
    source = upstream / relative
    assert bound.get(source.resolve()) == sha(source), str(source)
for relative in selected + ['candidates/round-02/packet.json', 'reviews/round-02.json', 'delivery-round-02.json']:
    source = upstream / relative
    target = DEST / 'sub-collector-inlet' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert sha(target) == sha(source)
    assert target.stat().st_size < 100_000_000
    records.append({'path': str(target.relative_to(OBJ)), 'sha256': sha(target), 'bytes': target.stat().st_size})
neutral = read(upstream / delivery['canonicalNeutralResources'])
components.append({'asset': 'sub-collector-inlet', 'acceptedRound': 'round-02',
                   'packetSHA256': sha(packet_path), 'originalJudgeReviewSHA256': sha(review_path),
                   'inputPrefix': 'inputs/approved-canonical-equipment-v1/sub-collector-inlet',
                   'upstreamExperiment': 'objects/sub-collector-inlet',
                   'mainAdoption': {'project': delivery['project'],
                                    'neutralResources': delivery['canonicalNeutralResources'],
                                    'canonicalNeutralResourceFingerprint': neutral['sha256'],
                                    **delivery['neutralMount']},
                   'scope': 'Exact accepted native IDLE neutral geometry/normals/UV/material/transform resources. Full upstream proof remains in committed original experiment; copied packet/review are approval provenance.'})
body_freeze = OBJ / 'inputs/frozen-body-and-interfaces-v1.json'
assert sha(body_freeze) == 'a46d8c7b808edcefef2e2f88a27679246e0f1b385c08d9f6141b1375f35c579d'
body = read(body_freeze)
for binding in [body['body'], body['mountLaw']]:
    assert sha(OBJ / binding['path']) == binding['sha256']
manifest = {'schemaVersion': 1, 'asset': 'submarine-yellow',
            'stage': 'root-frozen-three-accepted-canonical-neutral-components-before-final-export',
            'body': body['body'], 'bodyFreeze': {'path': str(body_freeze.relative_to(OBJ)), 'sha256': sha(body_freeze)},
            'mountLaw': body['mountLaw'], 'components': components, 'files': records,
            'mainAdoptionPerformed': False, 'mainApproval': False,
            'policy': 'Replace only explicitly provisional equipment cohorts with these exact accepted IDLE neutral resources at frozen positive uniform mounts. Preserve body/rig/actions/camera/lights and existing base/upgraded visibility semantics. Neutral state extraction/animation clearing may realize the already-approved canonical neutral; no active-component main mapping, remodeling, rebevel, recolor, nonuniform/perview fit or invented modes. Compare exact resource identities after inverse mount.'}
manifest_path = DEST / 'manifest.json'
create(manifest_path, manifest)
brief_path = OBJ / 'brief.json'
assert sha(brief_path) == 'a00e23446a46bee3e05d080ef406a105a05c8bc948d90ae6b978a7a0cb7b608d'
brief = read(brief_path)
brief['supersedes'] = {'path': 'brief.json', 'sha256': sha(brief_path),
                       'scope': 'Exact final accepted component input binding only; visible outcomes and hard native capture/body/rig/mount/hover/action constraints unchanged.'}
brief['finalCanonicalEquipment'] = {'manifest': str(manifest_path.relative_to(OBJ)), 'sha256': sha(manifest_path),
                                   'bodyFreezeSHA256': sha(body_freeze), 'candidateApproval': False}
brief.setdefault('technicalResources', {}).update({
    'accepted-canonical-equipment': str(manifest_path.relative_to(OBJ)),
    'frozen-body-interfaces': str(body_freeze.relative_to(OBJ)),
    'frozen-body-source': body['body']['path'],
    'frozen-mount-law': body['mountLaw']['path']})
new_brief = OBJ / 'brief-v2-canonical-equipment.json'
create(new_brief, brief)
receipt = {'asset': 'submarine-yellow', 'stage': 'final-inputs-frozen-before-original-editor-resume',
           'manifestSHA256': sha(manifest_path), 'briefSHA256': sha(new_brief),
           'bodySHA256': body['body']['sha256'], 'verifiedInputFiles': len(records),
           'mainAdoptionPerformed': False, 'mainApproval': False}
create(RUN / 'preparation/submarine-yellow/final-input-freeze-v1.json', receipt)
print(json.dumps(receipt))
