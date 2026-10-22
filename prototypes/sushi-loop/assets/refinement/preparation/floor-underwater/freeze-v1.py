"""Freeze the independently measured floor boundary repair before native design."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

RUN = Path(__file__).resolve().parents[2]
OBJ = RUN / 'objects/floor-underwater'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def create(path, data):
    assert not path.exists(), str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


manifests = {
    'reviews/preparation-v1/preparation-manifest.json': 'c6e23d07e071107080d491457488e9a7965112c9a52a2b96b54c6d0345af6fa6',
    'reviews/exact-boundary-study-v1/manifest.json': 'ecac18e34d78d14f0ccf4c6c9b54468485d44548f0f69bfbb3a9ee6eb009cac7',
}
records = {}
for relative, expected in manifests.items():
    path = OBJ / relative
    assert sha(path) == expected
    manifest = read(path)
    for record in manifest['files'] + manifest.get('resources', []):
        path = OBJ / record['path']
        assert path.is_file() and sha(path) == record['sha256'], str(path)
        assert path.stat().st_size < 100_000_000
        if record['path'] in records:
            assert records[record['path']]['sha256'] == record['sha256']
        records[record['path']] = record
proposal_path = OBJ / 'reviews/source-contract-proposal.json'
criteria_path = OBJ / 'reviews/proposedcriteria.json'
addendum_path = OBJ / 'reviews/exact-boundary-study-v1/addendum.json'
assert sha(proposal_path) == '995ed15a9600fb229bb441f86a3fcea560b3949baaee69c6ed99a4588112cfb5'
assert sha(criteria_path) == '7ba637f330227f9eabb347064192e2bdab7d658575f6510d2afa11b88261c0ab'
assert sha(addendum_path) == '54b84c698dadb6a2f2ccdf8280608bed559bfdcddc3e925d4c7b7a5b8ae1f099'
proposal, criteria = read(proposal_path), read(criteria_path)
brief_path = OBJ / 'brief.json'
brief = read(brief_path)
assert not brief['qualityCriteria']
backup = OBJ / 'brief-v1-before-native-freeze.json'
assert not backup.exists()
backup.write_bytes(brief_path.read_bytes())
handoff = OBJ / 'inputs/publisher-handoff-v1.txt'
assert not handoff.exists()
shutil.copyfile(RUN / 'preparation/PUBLISHER-HANDOFF.txt', handoff)

capture = ('Actual registered55.0079798014degree orthographic camera/matrices/aspect1.22065556 govern; saved35degree presentation camera is incidental. '
           'Logical128x128/root64,64/cell128; raw4x512x512/root256,256; published2x256x256/root128,128. '
           'Preserve6x2 atlases1536x512, all4 cardinal rotations and exact pitch. '
           'Measured exact-boundary repair freezes one common persisted native filter_size0.5 for every view/frame; retain complete512-to256 LANCZOS. '
           'Common-nativecanvas nearest AFTER resize, ordinary final wholecanvas filtering. No crop/fit/warp/nudge/perview recolor/alpha or RGB repair.')
surface = ('Repair inherited oversized source to exact nominal localX/Y±.5, complete upward finite square baseZ0, area1. '
           'Keep footprint1x1, roots/support/occupied cells and functional ceiling0.004; allowed geometryZ[0,.004]. '
           'The ceiling is a budget, not a raised border requirement. Old±.501 overhang, dark four-edge grout, downward ribbon normals, old partcount/topology are not locks. '
           'No deliberate overlap/expansion or geometric nudge; float representation/rotation tolerance1e-5world is not design growth. '
           'Native opaque coverage must be demonstrated from actual exact finite surface at all48 required frames.')
motion = ('Keep scroll12runtime phases/12fps/one-second loop, real closing13 excluded from atlas, calm perceptible periodic water motion. '
          'Existing weak ribbon/Key owner names/amplitudes are provenance, not mandatory construction. Native material/UV/geometry redesign is allowed. '
          'Prove true evaluated output-state closure or analytical periodic equivalence, meaningful inbetween behavior, and at least the original catalog minimum6 distinct visible frames. '
          'Every repeated tile uses the same global clip time; require complete X/Y edge and shared-corner continuity in all phases/all4 homogeneous facings. '
          'No invented arbitrary mixed-facing/independent-phase gameplay requirement.')
proof = ('All4x12 raw/published frames, four exact atlases and genuine12fps playback; native3x3 and independently captured3x3 on light/gray/dark, '
         'logical128 and realphone filtering with fractional root/pan0,.125,.25,.5,.875 samples from frozen criteria. '
         'Evaluate actual geometry/UV/material edge-and-corner periodicity and visual seam/flicker absence, not just alpha or hashes. '
         'Source-only filter study is feasibility, not candidate/style approval. No deferred2D shafts/bubbles/current or restaurant-floor changes.')
contract = copy.deepcopy(proposal)
contract.update(status='root-frozen-before-fresh-editor', candidateApproval=False,
                proposalSHA256=sha(proposal_path), criteriaSHA256=sha(criteria_path),
                preparationManifests=manifests,
                exactBoundaryAddendum={'path': str(addendum_path.relative_to(OBJ)), 'sha256': sha(addendum_path)},
                rootReconciliation={'capture': capture, 'finiteSurface': surface,
                                    'temporalAndSpatialPeriodicity': motion, 'requiredProof': proof})
contract_path = OBJ / 'inputs/root-native-contract.json'
create(contract_path, contract)
brief['capture'].update(nativeFrame=[512, 512], nativeCaptureScale=4,
                        publishedFrame=[256, 256],
                        publication='Whole512x512 LANCZOS to256x256; common persisted native filter_size0.5')
brief['constraints']['nativeContract'] = 'inputs/root-native-contract.json'
brief['qualityCriteria'] = {
    'status': 'root-frozen-before-editor',
    'definitionOfGood': 'A calm continuous aqua/turquoise water floor with soft connected caustic volume, restrained pale warm highlights, purposeful readable detail and a clean one-second scrolling loop across exact tile borders.',
    'priorityOutcomes': criteria['definitionOfGood'], 'hardConstraints': [capture, surface, motion, proof],
    'criteriaFile': 'reviews/proposedcriteria.json', 'criteriaFileSHA256': sha(criteria_path),
    'nativeContract': 'inputs/root-native-contract.json',
    'requiredEvidence': proposal['sourceEvidence']['futureRequiredEvidence'],
    'reviewMatrix': criteria['reviewMatrix'], 'rootReconciliation': contract['rootReconciliation']}
brief['technicalResources'] = {'root-native-contract': 'inputs/root-native-contract.json',
                               'publisher-handoff': 'inputs/publisher-handoff-v1.txt',
                               'source-proposal': 'reviews/source-contract-proposal.json',
                               'exact-boundary-addendum': str(addendum_path.relative_to(OBJ))}
for relative in manifests:
    brief['technicalResources']['manifest:' + relative] = relative
for relative in ['reviews/preparation-v1/preparation-seal.json', 'reviews/exact-boundary-study-v1/seal.json']:
    brief['technicalResources']['seal:' + relative] = relative
for relative in records:
    brief['technicalResources']['own-prep:' + relative] = relative
brief_path.write_text(json.dumps(brief, indent=2) + '\n')
result = {'asset': 'floor-underwater', 'status': 'outcomes-and-native-boundary-reconciliation-frozen-before-fresh-editor',
          'briefSHA256': sha(brief_path), 'contractSHA256': sha(contract_path),
          'criteriaSHA256': sha(criteria_path), 'proposalSHA256': sha(proposal_path),
          'preparationManifests': manifests, 'verifiedUniquePreparationFiles': len(records),
          'candidateApproval': False}
create(RUN / 'preparation/floor-underwater/root-freeze-v1.json', result)
print(json.dumps(result))
