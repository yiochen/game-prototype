"""Freeze independently measured low-shelf outcomes before a fresh editor."""
import copy
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[2]
OBJ = RUN / 'objects/rock-shelf-middle'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def create(path, data):
    assert not path.exists(), str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


prep = OBJ / 'reviews/preparation-v1'
manifest = prep / 'manifest.json'
assert sha(manifest) == '4cd5269c8827f4abe1ed750ee30a84f13b7a970b3848e15ddf444acdfde974fa'
records = read(manifest)['files']
for record in records:
    path = prep / record['path']
    assert path.is_file() and sha(path) == record['sha256'], str(path)
    assert path.stat().st_size < 100_000_000, str(path)
proposal_path = OBJ / 'reviews/source-contract-proposal.json'
criteria_path = OBJ / 'reviews/proposedcriteria.json'
proposal, criteria = read(proposal_path), read(criteria_path)
brief_path = OBJ / 'brief.json'
brief = read(brief_path)
assert not brief['qualityCriteria'], 'Cannot overwrite frozen outcomes'
backup = OBJ / 'brief-v1-before-native-freeze.json'
assert not backup.exists()
backup.write_bytes(brief_path.read_bytes())

capture = ('Registered55.0079798014degree orthographic square-grid capture governs; saved35degree presentation camera is incidental. '
           'Logical192x352/root96,248/cell128; native4x768x1408/root384,992; published2x384x704/root192,496. '
           'Preserve actual matrices/aspect1.22065556 and all4 cardinal root rotations. '
           'Explicit source-study reconciliation: common native filter_size0.5 persisted and whole native4x-to-published2x BOX reduction replace historical filter1.5/LANCZOS. '
           'Native lighting/materials may improve symmetrically for the style and continuity; one recipe for all views and strips. '
           'Actual common canvas nearest AFTER resize, ordinary final wholecanvas filtering, no fitting/cropping/shifting/overlap/alpha or RGB repair/perview recolor.')
profile = ('True W/E ports are localX=-.5/+ .5 at pitch1. Their exact finite ordered(Y,Z) section is '
           '[(-.45,0),(.45,0),(.45,.28),(.39,.43),(-.39,.43),(-.45,.28)]. '
           'Preserve actual finite base x[-.5,.5],y[-.45,.45],z0; intentional nonport ground margins are not gaps. '
           'Native allowed envelope[-.5,-.45,0]..[.5,.45,.45], tolerance1e-5world for float representation, never design extension. '
           'No tall-wall/full1x1 opaque-ground law, endpoint bevel gap, cap rounding, overhang or arbitrary overlap.')
continuity = ('At both true cutplanes, exposed adjacent native profile/albedo/material behavior and rendered normals must match '
              'under authored same-handed W/E connection. First middle may design a better canonical material/normal field, '
              'but both endpoints and their neighboring bands must actually evaluate continuously; labels/AABB alone do not prove this. '
              'Measure evaluated finite sections, ordered normals, albedo/resource signatures and intermediate boundary samples. '
              'No exposed internal endcaps/steps/dark rods/bright fringes. Retain broad finite-area-light native-versus-independent RGB residuals honestly, '
              'separate from actual local boundary defects; approval requires visibly clean all4 native and independent joins at use sizes. '
              'Later edge/corner/end receive fresh independent pairs and reuse the exact approved canonical resources; no family approval inferred.')
contract = copy.deepcopy(proposal)
contract.update(status='root-frozen-before-fresh-editor', candidateApproval=False,
                proposalSHA256=sha(proposal_path), independentCriteriaSHA256=sha(criteria_path),
                preparationManifestSHA256=sha(manifest),
                proposalEvidencePathBase='reviews/preparation-v1/',
                rootReconciliation={'capture': capture, 'finiteProfileAndGround': profile,
                                    'canonicalContinuity': continuity,
                                    'motion': 'Static1frame/nativeframe1/12fps/nonloop; no added animation or gameplay.'})
contract_path = OBJ / 'inputs/root-native-contract.json'
create(contract_path, contract)
brief['capture'].update(nativeFrame=[768, 1408], nativeCaptureScale=4,
                        publishedFrame=[384, 704],
                        publication='Complete native4x frame BOX reduced to2x; native filter_size0.5 persisted')
brief['constraints']['nativeContract'] = 'inputs/root-native-contract.json'
brief['qualityCriteria'] = {
    'status': 'root-frozen-before-editor',
    'definitionOfGood': 'A rounded low blue/cyan stone shelf with purposeful readable slab construction, broad soft non-directional lighting, and clean same-profile repeatable joins in every required facing and actual intended size.',
    'priorityOutcomes': criteria['rankedVisibleOutcomes'],
    'hardConstraints': [capture, profile, continuity, contract['rootReconciliation']['motion']],
    'requiredEvidence': criteria['requiredCandidateEvidence'],
    'criteriaFile': 'reviews/proposedcriteria.json', 'criteriaFileSHA256': sha(criteria_path),
    'nativeContract': 'inputs/root-native-contract.json',
    'proposalSHA256': sha(proposal_path), 'preparationManifestSHA256': sha(manifest)}
brief['technicalResources'] = {'root-native-contract': 'inputs/root-native-contract.json',
                               'independent-preparation-manifest': 'reviews/preparation-v1/manifest.json',
                               'independent-preparation-seal': 'reviews/preparation-v1/seal.json'}
for record in records:
    relative = 'reviews/preparation-v1/' + record['path']
    brief['technicalResources']['own-prep:' + relative] = relative
brief_path.write_text(json.dumps(brief, indent=2) + '\n')
result = {'asset': 'rock-shelf-middle', 'status': 'outcomes-and-technical-contract-frozen-before-fresh-editor',
          'briefSHA256': sha(brief_path), 'contractSHA256': sha(contract_path),
          'criteriaSHA256': sha(criteria_path), 'proposalSHA256': sha(proposal_path),
          'manifestSHA256': sha(manifest), 'verifiedPreparationFiles': len(records), 'candidateApproval': False}
create(RUN / 'preparation/rock-shelf-middle/root-freeze-v1.json', result)
print(json.dumps(result))
