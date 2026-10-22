"""Freeze the isolated distant wreck contract after both independent initials."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('--editor-initial-sha', required=True)
args = parser.parse_args()
run = Path(__file__).resolve().parents[2]
folder = run / 'objects/decor-background-wreck'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


manifest_path = folder / 'reviews/preparation-v1/manifest.json'
assert digest(manifest_path) == 'c1271bbd42143fcd571c29493551c0da0966f30b1c6474fe601d3bc59b497181'
manifest = read(manifest_path)
assert len(manifest['files']) == 135
for record in manifest['files']:
    resource = folder / record['path']
    assert digest(resource) == record['sha256'], record['path']
    assert resource.stat().st_size < 100_000_000, record['path']
seal_path = folder / 'reviews/preparation-v1/preparation-seal.json'
assert digest(seal_path) == '6797eacda7655f7667180a466f2e9fc623742735e9d03d96bb8b94c3de43702e'
criteria_path = folder / 'reviews/proposedcriteria.json'
proposal_path = folder / 'reviews/source-contract-proposal.json'
assert digest(criteria_path) == 'b2da1303a13c000f5d95e08295e6530d8973e7214283bf8d2f802b688c827698'
assert digest(proposal_path) == 'ef20d418224c98546ea45c03d5448235132835dfbe081ad8189efb6e555b9225'
initial_path = folder / 'source/initial-observations.json'
assert len(args.editor_initial_sha) == 64 and digest(initial_path) == args.editor_initial_sha
proposal, criteria = read(proposal_path), read(criteria_path)
contract_path = folder / 'inputs/root-native-contract.json'
reconciliation_path = folder / 'inputs/root-preparation-reconciliation-v1.json'
backup_path = folder / 'inputs/brief-before-native-freeze.json'
assert not any(path.exists() for path in [contract_path, reconciliation_path, backup_path])
hard = [
    'Quiet background wreck: standalone nonblocking layer1 elongated blue hull/mast/crossbar/cabin silhouette. Actual S33_PROP_decor-background-wreck.001/root decor-background-wreck__root.001/root0/unit scale/proper S0 E+90 N180 W-90. Preserve identity, palette, one-cell placement and coherent owned assembly. Native forms/proportions/construction/details/counts/topology/UV/normal/material methods may improve freely within clarified budget; exact source4meshes/slabs/intersection depths are not locks.',
    'Adopt proposed REST native remodeling envelope X[-.5,.5],Y[-.1,.1],Z[.04,.75], tolerance1e-6 and proper rotations/all4. This is a new preconstruction design budget allowing depth.20 versus old.12, not a claim about source truth. Keep recognizable elongated hull; coherent E/W end volume may improve without mimicking frontal target in allviews. Raw/evaluated bounds and bevel trim are baseline evidence, not tighter hull/perpart locks. Ground root is registration only: actual source lowestZ.07 and no mesh intersectsZ0. Do not invent ground plane/feet/foundation/fullsquare opacity/support sockets/ports/modular continuity/collision expansion. Lower.04 budget permits integrated native wear, not forced support.',
    'Own registered55.0079798 ORTHO/ortho1.5/pixelAspect1.22065556 camera and measured actual matrices/root/world scale, not unrelated saved35 startup camera. Logical192352/root96248/cell128/native4x7681408/root384992/published2x384704/root192496. Uniform whole authored native canvas LANCZOS reduction, original one-frame atlas rect[0,0,384,704]; no crop/subject fit/warp/perview nudge/recolor/alphaRGB repair. Native and published capture scales are distinct. Record one consistent actual filter/color/render recipe across all4; no other family filter/rig recipe imported.',
    'Exactly one actual static frame1/NESW/12fps/nonloop/frameOrder[0]. Effective own object/data/material/shader/world/compositor/capture ownership has no active temporal channels. Preserve true static hold0,1/12,11/12,2seconds with bounded source channel/frame probes; no invented sway/action/closure workload. No target image card/paint-over, linked unrelated visible scene assets, or source-original edits. Keep every used native dependency packed or exact portable private closure.',
    'Freeze original three ranked visible outcomes and all additional outcomes: coherent soft worn elongated wreck, blue quiet actor hierarchy, broad soft symmetric native highlights, purposeful coarse readable detail, all4/use-size artifact-free owned joins/static holds. Muted warm wood/moss accent is optional; no mandatory golden target glare/whitebarnacle counts/foliage or exact target silhouette. One broad symmetric horizontal light recipe acrossall4/no preferred key or directional groundcast. Native geometry/normals/bevel/shader/light choices remain editor-owned. No clipped edge bands/black dead spots/float detached mast/cabin/zfight/accidental cracks/halos/clipping.',
    'All4 native/published exactframes, full-frame fourview sheet, all4 neutral light/gray/dark128/32/fractional47.3 use, repeated3x3 density study with no modular seam claim. Adopt exact15 prepared consumer configs x2 documented Chromium153 modes, preserving root(.37,.61)/pan(.23,.47), current099/570 helper and frozen companion image/atlas/rect/root/order/version/executable/DPR/error provenance. Add only two bounded final actual viewport contexts320720 and1280720 per mode; no redundant whole Cartesian matrix at each viewport. Native commoncanvas nearest AFTER resize then ordinary wholecanvasCSS filtering; preserve actual source/native/CSS residuals honestly. Fixture reproduces exact SpriteScene methods, not full productionUI/Godot/device execution.',
    'Every declared hero/preview independently inspected by original judge at complete resolution, with lossless tiles or explicit identical-hash aliases where needed; reduced sheets/hashes/source equality alone never certify quality. Required brief preview names four-view-sheet/phone/repeated should be exact aliases to declared actual media, not new art. Unchanged integrity/direction/acceptance gates. Minimal actual-used private closure/allfiles<100MB/no runtime application trees/frozen pycache. Originals/backup/target/preparation/initial/frozen criteria/brief immutable. Editor source/candidates only; judge reviews only. No sharedhelper/Git/index/production/deploy/liveBlender/device changes or extraagents.'
]
ledger = read(folder / 'reviews/preparation-v1/consumer-ledger.json')
keys = ['kind', 'cell', 'background', 'phase', 'seconds', 'pan']
configs = [{key: case[key] for key in keys if key in case} for case in ledger['runs'][0]['cases']]
assert len(configs) == 15
plan = {'asset': 'decor-background-wreck', 'scope': 'Static isolated atmospheric wreck, no native ground/modular or animation law invented.', 'requiredFrames': ['static/N/0', 'static/E/0', 'static/S/0', 'static/W/0'], 'preparedConsumerCasesPerMode': configs, 'preparedHostViewport': [1400, 1000], 'dpr': 1, 'browserModes': [{'headless': True, 'channel': 'chromium'}, {'headless': True}], 'finalContextViewports': [[320, 720], [1280, 720]], 'staticHoldSeconds': [0, 1 / 12, 11 / 12, 2], 'requiredEvidence': proposal['boundedConsumerPlan']['futureCandidate'], 'coverage': 'Direct exact media coverage with original judge and acyclic manifests. Include supported actual nativeValidation views/captureRecords; rich geometry ledger separately bound if incompatible. nativeGeometryMeasurements is facing -> list of frame dictionaries when used.'}
reconciliation = {'asset': 'decor-background-wreck', 'stage': 'ROOT reconciliation BEFORE construction', 'preparation': {'path': str(manifest_path.relative_to(folder)), 'sha256': digest(manifest_path), 'rootVerifiedFiles': 135}, 'freshEditorInitial': {'path': str(initial_path.relative_to(folder)), 'sha256': digest(initial_path)}, 'designBudget': {'decision': 'Adopt original judge proposed .20 native depth and .04..75 height budget for useful remodeling, while retaining elongated quiet role and one-cell registration. Old .12 extrusion and evaluated trim are not tighter locks.', 'X': [-.5, .5], 'Y': [-.1, .1], 'Z': [.04, .75], 'tolerance': 1e-6}, 'support': 'No source Z0 intersection/ground contact. Preserve coherent internal mast/crossbar/cabin-to-hull assembly without exact old intersection-depth/part-count locks; no ground plate or foreground wreck ports.', 'capture': 'Adopt own verified55.00798 native4x registered camera and full-canvas LANCZOS2x. Saved35 startup camera is unrelated; raw historical path is absent and replay residual evidence remains honest.', 'style': 'Original three ranked proposed visible outcomes plus all additional outcomes frozen unchanged. Native improved form/detail methods and small silhouette changes allowed; exact target glare/ground stones/counts/brightness not requirements.', 'evidence': 'Same15 two-mode bounded configs plus only two true final viewport contexts per mode; record static holds/channel evidence without animated Cartesian workload. No React/Godot/device or family approval claimed.', 'scope': 'Preparation reconciliation only; candidate approval and ROOT promotion/publication remain pending.'}
contract = {'asset': 'decor-background-wreck', 'version': 1, 'status': 'root-frozen-before-construction', 'sourceProposal': {'path': str(proposal_path.relative_to(folder)), 'sha256': digest(proposal_path)}, 'preparationManifest': {'path': str(manifest_path.relative_to(folder)), 'sha256': digest(manifest_path), 'rootVerifiedFiles': 135}, 'nativeContract': proposal, 'hardConstraints': hard, 'reconciliation': reconciliation, 'requiredEvidence': plan}
write(reconciliation_path, reconciliation)
write(contract_path, contract)
shutil.copyfile(folder / 'brief.json', backup_path)
brief = read(folder / 'brief.json')
brief['capture'].update(nativeFrame=[768, 1408], nativeCaptureScale=4, publishedFrame=[384, 704], publication='Uniform complete native4x canvas to published2x LANCZOS; no crop or fitting.', previews=['four-view-sheet', 'phone', 'repeated'])
brief['constraints']['nativeContract'] = str(contract_path.relative_to(folder))
outcomes = criteria['priorityOutcomes'] + [{'dimension': key, 'desired': value} for key, value in criteria['additionalOutcomes'].items()]
brief['qualityCriteria'] = {'status': 'root-frozen-before-construction', 'definitionOfGood': 'A coherent softly finished elongated blue distant wreck, with useful native volume/detail and quiet readable actor hierarchy in all4 views.', 'priorityOutcomes': outcomes, 'hardConstraints': hard, 'criteriaFile': str(criteria_path.relative_to(folder)), 'criteriaFileSHA256': digest(criteria_path), 'nativeContract': str(contract_path.relative_to(folder)), 'nativeContractSHA256': digest(contract_path), 'preparationManifestSHA256': digest(manifest_path), 'requiredEvidence': plan}
resources = brief.setdefault('technicalResources', {})
resources.update(rootNativeContract=str(contract_path.relative_to(folder)), preparationReconciliation=str(reconciliation_path.relative_to(folder)), nativePreparationManifest=str(manifest_path.relative_to(folder)), freshEditorInitial=str(initial_path.relative_to(folder)))
for record in manifest['files']:
    resources['prepared:' + record['path']] = record['path']
write(folder / 'brief.json', brief)
progress_path = run / 'progress.json'
progress = read(progress_path)
entry = next(row for row in progress['objects'] if row['id'] == 'decor-background-wreck')
entry.update(status='editing', editor='catalog_decor_background_wreck_editor_v1', judge='catalog_decor_background_wreck_judge_v1', editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate', stage='native-background-wreck-round01', briefSHA256=digest(folder / 'brief.json'))
write(progress_path, progress)
result = {'asset': 'decor-background-wreck', 'scriptSHA256': digest(Path(__file__)), 'editorInitialSHA256': args.editor_initial_sha, 'rootVerifiedPreparationFiles': 135, 'briefSHA256': digest(folder / 'brief.json'), 'contractSHA256': digest(contract_path), 'reconciliationSHA256': digest(reconciliation_path)}
write(run / 'preparation/decor-background-wreck/freeze-execution-v1.json', result)
print(json.dumps(result))
