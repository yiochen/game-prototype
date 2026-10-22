from pathlib import Path
import hashlib
import json
import shutil

run = Path(__file__).resolve().parents[2]
folder = run / 'objects/rock-half-width'
prep = folder / 'reviews/preparation-v1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2) + '\n')


mp = prep / 'manifest.json'
assert sha(mp) == '9515440e8d69f3060b35515cc506ce3de4b3d852b0265cb82be48d56e8ca683a'
manifest = read(mp)
assert len(manifest['files']) == 208
for record in manifest['files']:
    p = folder / record['path']
    assert sha(p) == record['sha256']
    assert p.stat().st_size < 100_000_000
seal = read(prep / 'seal.json')
assert sha(folder / seal['verificationPath']) == seal['verificationSHA256']
initial = folder / 'source/initial-observations.json'
assert sha(initial) == '03777f1245ea912dfb06a248ad5e1e6d1776dc84b98061aa125c56a532c7c96d'
proposal = read(folder / 'reviews/source-contract-proposal.json')
criteria = read(folder / 'reviews/proposedcriteria.json')
plan = read(prep / 'evidence-plan.json')
reconciliation = {
    'asset': 'rock-half-width', 'status': 'root decisions before construction',
    'preparationManifestSHA256': sha(mp),
    'sampling': {'nativeScale': 4, 'nativeFrame': [768, 1408], 'nativeRoot': [384, 992],
        'filterSize': .01, 'publication': 'Uniform whole-frame BOX reduction to384x704, exact unchanged full-frame placement; no pixel repair.',
        'publishedScale': 2, 'publishedFrame': [384, 704], 'publishedRoot': [192, 496],
        'sourceOnlyFinding': 'Removes measured S alpha loss. The old opaque E cap/top stripe remains a required native material/normal continuity problem, not a sampling pass or accepted defect.'},
    'physical': {'ground': 'Full finite X[-.5,.5]/Y[-.17,.17]/Z0 strip, area.34',
        'envelope': {'x': [-.5, .5], 'y': [-.17, .17], 'z': [0, .95], 'tolerance': 1e-5},
        'ports': proposal['functionalInterfaces']['finiteSectionYZ'],
        'freedom': 'Useful native forms, internal contour/stone grouping, topology/counts and active normal/material treatment may change inside this budget. Original facets, dark lower ramp and old cut-cap shading are not locks.'},
    'canonicalCollars': {'W': [-.5, -.42], 'E': [.42, .5],
        'fields': 'Establish coherent actual native surface geometry and normalized shader-used normal/albedo/material fields under W/E translation across finite collars, including actual cap/top rendering behavior. Source fields may be redesigned; terrain remains opaque.'},
    'context': {'parallelStrips': 'Preserve one-cell row spacing and the original finite strip, giving .66 geometric clearance.',
        'scope': 'No particular native submarine path is declared in the actual self-join placements. This refinement preserves dimensions/clearance and makes no new actor-transit certification or gameplay change.'},
    'consumerCases': [
        {'id': 'logical128-integer', 'cellCSS': 128, 'viewport': [1120, 720], 'DPR': 1, 'rootPhase': [0, 0], 'pan': [0, 0]},
        {'id': 'logical128-fractional', 'cellCSS': 128, 'viewport': [1120, 720], 'DPR': 1, 'rootPhase': [.25, .75], 'pan': [.213, -.371]},
        {'id': 'phone32-portrait', 'cellCSS': 32, 'viewport': [390, 844], 'DPR': 1, 'rootPhase': [0, 0], 'pan': [0, 0]},
        {'id': 'phone32-landscape-fractional', 'cellCSS': 32, 'viewport': [844, 390], 'DPR': 1, 'rootPhase': [.25, .75], 'pan': [.213, -.371]}],
    'consumerCoverage': 'Execute all four bounded cases in each actual headless mode; each fixture covers all4 facings/light-gray-dark. Keep native canvas and displayed CSS separate; expand only for a concrete concern.',
    'freshEditorInitial': {'path': 'source/initial-observations.json', 'sha256': sha(initial)},
    'scope': 'Fixed target/independent visible criteria retained. Preparation has no candidate, family or production approval.'}
write(folder / 'inputs/root-preparation-reconciliation-v1.json', reconciliation)
hard = [
    'True W/E X±.5, exact measured ordered six-point YZ section: (-.17,0),(.17,0),(.17,.64),(.12,.93),(-.12,.93),(-.17,.64). Same-profile translation and proper all4 rotations; cap geometric winding/outward normals oppose. No source profile transplant from rock-wall/shelf, mirror or growth/rounded join cuts.',
    'Full finite ground strip X[-.5,.5]/Y[-.17,.17]/Z0/area.34; complete geometry sameXY/Z[0,.95], 1e-5 float representation tolerance. Original body facets/partcounts/interior height variation/dark ramp are not locks. No fullsquare widening, overhang, floating base or new holes below opaque blocking terrain.',
    'New coherent native geometry/normalized post-interpolation shader-used normal/albedo/material field on full .08 W/E collars must match under translation and every root rotation; actual cap/top RGB behavior must be clean. Surface opacity remains1. Native implementation free if actual fields/visible joins pass, no ID/point-only proof or literal graph/storage veto. Do not preserve the old opaque cap stripe or erase cut faces as a seam workaround.',
    'Registered55.0079798/aspect1.22065556/ortho1.5/logical192352/root96248/cell128/native4x7681408/root384992/filter.01 -> uniform wholeBOX2x384704/root192496/staticframe1/oneframe/12fps/nonloop/all4. Same fixed camera/light/material recipe across allviews, no perviewfit/shift/grade. Historical filter1.5/LANCZOS and source replay residuals remain observations.',
    'One soft horizontally symmetric native light/material recipe, no preferred horizontal key or directional ground cast shadow. Old140W/4x100W/world0 is historical, not artistic authority. Preserve chosen actual native settings and evaluated field descriptors for exact replay.',
    'True three-module native and independent repeats all4 plus parallel-strip geometric context, actual current570/099 consumer in both fullChromium and headlessShell at four bounded cases defined in root reconciliation (logical128 integer/fractional, phone32 portrait/landscapefractional), all4/lightgraydark. Registered common camera extension/density/root, ordinary painter order and nearest common-canvas display preserved.',
    'Purposeful substantial blue/cyan stone volumes, readable lower blue body and clean allview caps/joins at use size. No local line/stripe/band/crack/alpha puncture/normal break/deadspot/clipping waiver. Preserve broad finite-light/outerprecision residuals honestly; source-only S alpha success is not all-facing approval. No crop/warp/paint/targetcard/RGBalpha repair/overlap/sharedhelper change. Comparison-only extent diagnosis only for actual discrepancy with zero visible discard/exact integer restoration.'
]
contract_path = folder / 'inputs/root-native-contract.json'
assert not contract_path.exists()
write(contract_path, {'asset': 'rock-half-width', 'version': 1, 'status': 'root-frozen-before-construction',
    'sourceProposal': {'path': 'reviews/source-contract-proposal.json', 'sha256': sha(folder / 'reviews/source-contract-proposal.json')},
    'preparationManifest': {'path': 'reviews/preparation-v1/manifest.json', 'sha256': sha(mp), 'rootVerifiedFiles': 208},
    'nativeContract': proposal, 'hardConstraints': hard, 'reconciliation': reconciliation,
    'requiredEvidence': plan})
backup = folder / 'inputs/brief-before-native-freeze.json'
assert not backup.exists()
shutil.copyfile(folder / 'brief.json', backup)
brief = read(folder / 'brief.json')
brief['capture'].update(nativeFrame=[768, 1408], nativeCaptureScale=4, publishedFrame=[384, 704],
    publication='Uniform whole-frame BOX4x->2x/filter.01; no local edits.', previews=['four-view-sheet', 'repeated', 'phone'])
brief['constraints']['nativeContract'] = 'inputs/root-native-contract.json'
brief['qualityCriteria'] = {'status': 'root-frozen-before-construction',
    'definitionOfGood': 'A narrow grounded blue stone barrier with substantial softly lit rounded/faceted native masses, readable lower body and seamless true repeated ports in every facing.',
    'priorityOutcomes': criteria['rankedVisibleOutcomes'], 'hardConstraints': hard,
    'criteriaFile': 'reviews/proposedcriteria.json', 'criteriaFileSHA256': sha(folder / 'reviews/proposedcriteria.json'),
    'nativeContract': 'inputs/root-native-contract.json', 'nativeContractSHA256': sha(contract_path),
    'preparationManifestSHA256': sha(mp), 'requiredEvidence': plan}
resources = brief.setdefault('technicalResources', {})
resources.update(rootNativeContract='inputs/root-native-contract.json',
    rootReconciliation='inputs/root-preparation-reconciliation-v1.json',
    nativeProposal='reviews/source-contract-proposal.json', preparationManifest='reviews/preparation-v1/manifest.json',
    evidencePlan='reviews/preparation-v1/evidence-plan.json')
for record in manifest['files']:
    if record['path'].startswith('reviews/preparation-v1/resources/'):
        resources['preparedResource:' + record['path']] = record['path']
write(folder / 'brief.json', brief)
progress_path = run / 'progress.json'
progress = read(progress_path)
item = next(item for item in progress['objects'] if item['id'] == 'rock-half-width')
item.update(status='editing', editor='catalog_rock_half_width_editor_v1', judge='catalog_rock_half_width_judge_v1',
    editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate',
    stage='native-half-width-round01', briefSHA256=sha(folder / 'brief.json'))
write(progress_path, progress)
print(json.dumps({'asset': 'rock-half-width', 'verifiedPreparationFiles': 208,
    'briefSHA256': sha(folder / 'brief.json'), 'contractSHA256': sha(contract_path),
    'reconciliationSHA256': sha(folder / 'inputs/root-preparation-reconciliation-v1.json')}))
