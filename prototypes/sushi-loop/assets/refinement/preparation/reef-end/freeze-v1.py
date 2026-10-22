from pathlib import Path
import copy
import hashlib
import json
import shutil

run = Path(__file__).resolve().parents[2]
folder = run / 'objects/reef-end'
prep = folder / 'reviews/preparation-v1'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


manifest_path = prep / 'manifest.json'
assert sha(manifest_path) == '9c96f431489d87d67304c3f5d34469e2880a1692390fe063c26b4c46456d6b2a'
manifest = read(manifest_path)
assert len(manifest['files']) == 94
for record in manifest['files']:
    path = prep / record['path']
    assert sha(path) == record['sha256']
    assert path.stat().st_size < 100_000_000

initial = folder / 'source/initial-observations.json'
assert initial.is_file(), 'Fresh editor must finish its independent initial before construction freeze'
corner = run / 'objects/reef-corner'
corner_packet_path = corner / 'candidates/round-01/packet.json'
corner_review_path = corner / 'reviews/round-01.json'
corner_packet = read(corner_packet_path)
corner_review = read(corner_review_path)
assert sha(corner_packet_path) == '969ab83edd7a8d615fe7284bb7c979a293a5bfde0a6d0b50abe62ac16068f599'
assert sha(corner_review_path) == '1c4bb1d47794344f7b60bae243ed3cae8f3d0058d1e4744c15d7ebc77716fef8'
assert corner_review['verdict'] == 'approve' and corner_review['blockers'] == []
assert corner_review['candidatePacketSHA256'] == sha(corner_packet_path)
seal = read(corner / 'reviews/round-01-independent/postreview-seal.json')
for key in ('review', 'supplementalManifest', 'gate'):
    assert sha(corner / seal[key + 'Path']) == seal[key + 'SHA256']
assert seal['gatePassed'] is True
assert sha(run / 'tools/acceptance_contract.py') == seal['unchangedAcceptanceContractSHA256']

binding_root = folder / 'inputs/approved-reef-corner-v1'
assert not binding_root.exists()
bindings = {}


def retain(alias, source, destination, expected=None):
    assert expected is None or sha(source) == expected
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    assert sha(destination) == sha(source)
    bindings[alias] = {'path': destination.relative_to(folder).as_posix(),
                       'sha256': sha(destination), 'originalPath': source.relative_to(run).as_posix()}


retain('packet', corner_packet_path, binding_root / 'packet.json')
retain('review', corner_review_path, binding_root / 'review.json')
base = corner_packet_path.parent
record = corner_packet['files']['candidateProject']
retain('project', (base / record['path']).resolve(), binding_root / 'round-01.blend', record['sha256'])
for facing, record in corner_packet['candidateRenders'].items():
    retain('hero-' + facing, (base / record['path']).resolve(), binding_root / (facing + '.png'), record['sha256'])
write(binding_root / 'binding.json', {'asset': 'reef-corner', 'round': 'round-01',
      'scope': 'Exact approved source and four heroes for native/independent full-L context; no family approval.',
      'files': bindings})

proposal = read(prep / 'proposed-root-contract.json')
criteria = read(prep / 'criteria.json')
canonical = read(prep / 'evidence/canonical-native.json')
background = next(node for node in canonical['world']['nodes'] if node['type'] == 'BACKGROUND')
strength = background['inputs']['Strength']
assert abs(strength - .32) < 1e-7
reconciliation = {
    'asset': 'reef-end', 'stage': 'root reconciliation before construction',
    'sealedPreparationUnchanged': {'path': 'reviews/preparation-v1/manifest.json', 'sha256': sha(manifest_path)},
    'worldCorrection': {'proposalWorldStrength': proposal['canonicalLightMaterialAdoption']['worldStrength'],
        'actualCanonicalBackgroundStrength': strength, 'actualCanonicalBackgroundWeight': background['inputs'].get('Weight'),
        'evidence': {'path': 'reviews/preparation-v1/evidence/canonical-native.json', 'sha256': sha(prep / 'evidence/canonical-native.json')},
        'rule': 'Clone actual approved canonical world graph, including Color/Strength/links. Strength .32 is distinct from unused Weight0; proposal scalar0 is superseded. No change to target or visible criteria.'},
    'fullFamilyL': {'status': 'Previously pending corner resolved by exact independent approval',
        'binding': {'path': 'inputs/approved-reef-corner-v1/binding.json', 'sha256': sha(binding_root / 'binding.json')}},
    'freshEditorInitial': {'path': 'source/initial-observations.json', 'sha256': sha(initial)},
}
write(folder / 'inputs/root-preparation-reconciliation-v1.json', reconciliation)
hard = [
    'True single W connector at X=-.5, exact ordered asymmetric eight-point width/Z reef section and proper all4 rotations, pitch1; no reflection, port growth, rounded join cuts or inward steps.',
    'Preserve full .08 canonical W collar X[-.5,-.42], actual triangle surface/normalized post-interpolation shader-used normal/albedo/material/light fields. Approved middle02 source51d515119c1a229f57f3b242fdf040b28ef00121692cb3d40d8821dab70ff3c5 is authority. Equivalent native storage/shader methods allowed with actual field equivalence; ring IDs alone insufficient.',
    'Finite ground rectangle X[-.5,.34]/Y[-.38,.38]/Z0, area.6384; geometry within same XY and Z[0,.68], 1e-5 representation tolerance. No extra wholecell floor, overhang or borrowing middle bounds. Exposed closed E end, internal rings/topology/part counts and useful native decoration/forms are free inside this envelope; old cap cross-section is not a lock.',
    'Direct native2x384704/root192496/filter.01/EEVEE64, publish exact PNG with no reduction; registered55.0079798/aspect1.22065556/logical192352/root96248/cell128/static1/frame1/12fps/nonloop/all4. Clone canonical camera/light/world graph: actual Background Strength.32 and Color(.62,.69,.78), centered100W/size5 plus4cardinal45W/size4.5. No source historical lighting reset.',
    'Hard direct approved-middle-to-end and full-family-L fixtures exactly as planned in all4 global rotations, native combined plus independent current570/099 actual consumer128/32/lightgraydark and planned fractional phases/both headless modes. Use exact approved edge01 in preparation and approved corner01 binding here. Original plan pending-corner text is resolved only by this binding. No family-wide approval inferred.',
    'No visible local crack/stripe/band/crown step/fringe/black patch/opaque-interior alpha loss. Preserve broad finite-area-light/source-extent and honest renderer residuals separately, no numerical-only seam waiver. No perviewfit, crop, warp, recolor, target card, alpha/RGB repair, overlap, directional ground shadow or shared helper change. Reuse comparison-only extent diagnosis only for actual discrepancy with zero visible discard and exact integer restoration.'
]
native = copy.deepcopy(proposal)
native['canonicalLightMaterialAdoption']['worldStrength'] = strength
native['canonicalLightMaterialAdoption']['worldGraphEvidence'] = reconciliation['worldCorrection']['evidence']
contract = {'asset': 'reef-end', 'version': 1, 'status': 'root-frozen-before-construction',
    'sourceProposal': {'path': 'reviews/preparation-v1/proposed-root-contract.json', 'sha256': sha(prep / 'proposed-root-contract.json')},
    'preparationManifest': {'path': 'reviews/preparation-v1/manifest.json', 'sha256': sha(manifest_path), 'rootVerifiedFiles': 94},
    'nativeContract': native, 'hardConstraints': hard,
    'requiredEvidence': read(prep / 'assembly-evidence-plan.json'),
    'requiredEvidenceOriginalPathBase': 'reviews/preparation-v1',
    'reconciliation': reconciliation, 'approvedCorner': bindings}
contract_path = folder / 'inputs/root-native-contract.json'
assert not contract_path.exists()
write(contract_path, contract)
backup = folder / 'inputs/brief-before-native-freeze.json'
assert not backup.exists()
shutil.copyfile(folder / 'brief.json', backup)
brief = read(folder / 'brief.json')
brief['capture'].update(nativeFrame=[384, 704], nativeCaptureScale=2, publishedFrame=[384, 704],
                        publication='Exact direct-native2x PNG/filter.01, no reduction.',
                        previews=['four-view-sheet', 'repeated', 'full-family-L'])
brief['constraints']['nativeContract'] = 'inputs/root-native-contract.json'
brief['qualityCriteria'] = {'status': 'root-frozen-before-construction',
    'definitionOfGood': criteria['definitionOfGood'], 'priorityOutcomes': criteria['rankedVisibleOutcomes'],
    'hardConstraints': hard, 'criteriaFile': 'reviews/preparation-v1/criteria.json',
    'criteriaFileSHA256': sha(prep / 'criteria.json'), 'nativeContract': 'inputs/root-native-contract.json',
    'nativeContractSHA256': sha(contract_path), 'preparationManifestSHA256': sha(manifest_path),
    'requiredEvidence': contract['requiredEvidence']}
resources = brief.setdefault('technicalResources', {})
resources.update(rootNativeContract='inputs/root-native-contract.json',
    preparationReconciliation='inputs/root-preparation-reconciliation-v1.json',
    nativeProposal='reviews/preparation-v1/proposed-root-contract.json',
    nativePreparationManifest='reviews/preparation-v1/manifest.json',
    nativeEvidencePlan='reviews/preparation-v1/assembly-evidence-plan.json',
    approvedCornerBinding='inputs/approved-reef-corner-v1/binding.json')
for record in manifest['files']:
    if record['path'].startswith('resources/'):
        resources['preparedResource:' + record['path']] = 'reviews/preparation-v1/' + record['path']
write(folder / 'brief.json', brief)
progress_path = run / 'progress.json'
progress = read(progress_path)
item = next(item for item in progress['objects'] if item['id'] == 'reef-end')
item.update(status='editing', editor='catalog_reef_end_editor_v1', judge='catalog_reef_end_judge_v1',
    editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate',
    stage='canonical-mixed-reef-end-round01', briefSHA256=sha(folder / 'brief.json'))
write(progress_path, progress)
print(json.dumps({'asset': 'reef-end', 'verifiedPreparationFiles': 94,
    'briefSHA256': sha(folder / 'brief.json'), 'contractSHA256': sha(contract_path),
    'reconciliationSHA256': sha(folder / 'inputs/root-preparation-reconciliation-v1.json')}))
