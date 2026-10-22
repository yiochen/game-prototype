"""Freeze this standalone prop's reconciled contract before native construction."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('--editor-initial-sha', required=True)
args = parser.parse_args()
run = Path(__file__).resolve().parents[2]
folder = run / 'objects/decor-background-rock'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


manifest_path = folder / 'reviews/preparation-v1/manifest.json'
assert digest(manifest_path) == 'e126ab79d70c560c39a23680c551c724928ca0216837676005d571a6dc466956'
manifest = read(manifest_path)
assert len(manifest['files']) == 153
for record in manifest['files']:
    resource = folder / record['path']
    assert digest(resource) == record['sha256'], record['path']
    assert resource.stat().st_size < 100_000_000, record['path']
seal_path = folder / 'reviews/preparation-v1/seal.json'
assert digest(seal_path) == '7a473ea6c5a55f599c41b541485021a4565a2e97880997ad92031fa00eb8fd22'
criteria_path = folder / 'reviews/proposedcriteria.json'
proposal_path = folder / 'reviews/source-contract-proposal.json'
assert digest(criteria_path) == '5e49007e5949f7434f5cac16c2ef3845e34f47e52cd68f180ecd9ba60bf3ebf0'
assert digest(proposal_path) == '9af46450ee2fc7f6cfccc83ed7d9032a40032ccc1ebc9722afb1d6538bf23f79'
initial_path = folder / 'source/initial-observations.json'
assert len(args.editor_initial_sha) == 64 and digest(initial_path) == args.editor_initial_sha
criteria, proposal = read(criteria_path), read(proposal_path)
contract_path = folder / 'inputs/root-native-contract.json'
reconciliation_path = folder / 'inputs/root-preparation-reconciliation-v1.json'
backup_path = folder / 'inputs/brief-before-native-freeze.json'
assert not any(path.exists() for path in [contract_path, reconciliation_path, backup_path])

hard = [
    'Standalone Quiet background rock, cobalt scenery on catalog depthLayer1/nonblocking/one-cell placement. Actual original collection S33 production concept cobalt-shelf.001/root S33 production concept cobalt-shelf root.001. Root0/unit scale/world1 cell=1; proper facing S0/E+90/N180/W-90. Improve recognizable organic stone forms, proportions, topology, part count and purposeful details freely inside the functional envelope; old four pieces/128vertices/104faces/old ramp are descriptive only.',
    'Finite one-cell native geometry envelope X/Y[-.5,.5], Z[0,1.075], tolerance1e-6, proper-rotated all4. Actual authored crown1.07500005 establishes the design budget; nominal catalog1.05 is rounded metadata and does not force shrinking. Tiny standalone silhouette drift within that envelope is allowed. No exact old outline or per-part box lock. Keep native grounded stone mass at original ground planeZ0 with finite closed support/bottoms; no floating or detached stones/exposed open bottoms. Original .9494783 base-cap union/shape/area/four-part count are evidence, not exact candidate requirements. No full opaque square/feet/platform/socket/port/modular contact invented.',
    'Preserve actual registered top-down-oblique-square-grid55.0079798 camera/projection/world scale/pixel aspect1.22065556/ortho1.5 and measured matrices, not saved unrelated35 chef startup camera. Logical192352/root96256/cell128; native4x7681408/root3841024; published2x384704/root192512. Uniform full authored native canvas LANCZOS reduction to published frame, original atlas layout; no subject fit/crop/warp/ground-root shift. Retain measured float root/basis tolerance under unchanged normalization. No per-view fitting, posing to target, per-view recoloring or alpha/RGB repair.',
    'Exactly one actual static frame1 in eachN/E/S/W, frame range1..1,12fps/nonloop/frameOrder[0]. Preserve no active temporal channels in own geometry/materials/shaders/world/compositor/capture owners; no invented sway/closure/terminal. Record effective ownership and clean editable-source replay, packed or explicit actual-used dependencies. No target image card/paint-over/linked unrelated scene geometry.',
    'Native geometry, normals, bevel, shader/material and light methods remain editor choices. Use one symmetric broad horizontal lighting recipe across all4, no preferred horizontal key or directional ground cast shadow. Source filter1.5/whole LANCZOS stays the first-candidate capture recipe; historical watts/world0/contrast1.35/faceted normals/old roughness are not aesthetic locks. No other modular family rig/collar/sampling constraints imported. A genuine new sampling conflict must be reported before any contract change.',
    'Five frozen visible outcomes: coherent organic stone volumes; original cobalt palette and quiet background role; controlled broad soft blue plane/edge highlights; purposeful restrained stone detail; grounded artifact-free readability in every required view/use context. Fixed target guides style/forms, not camera/brightness/placement/unseen-view truth. No clipped cyan-white glow/seam lattice/black dead patches/overlap/bad normals/halos/clipping/accidental transparency. Scores/hashes alone never establish visible quality.',
    'Native/published all4; full-frame four-view sheet, repeated3x3 all4 as density/silhouette evidence without a modular seam criterion, light/gray/dark logical and64px-cell use sheet. Frozen six actual consumer cases in both Chromium153 documented headless modes with recorded executables/options/version/DPR1/viewport/helper/input/atlas/rect/root/order hashes; exact sprite-layout099/world-sprite-raster570 composition, native nearest AFTER resize then ordinary whole-canvas CSS filtering. Actor context rockS(0,1), submarineN travel(2,0), eelN swim(4,1), static t0; context actors use exact current published art without family approval. Preserve native/CSS numerical residuals honestly. Fixture is bounded actual-helper composition, not claimed React/Godot/device execution; no Godot catalog entry for this prop.',
    'Every declared packet hero/preview directly covered independently by the original judge at full resolution; lossless full-pixel tiles or explicit identical-hash aliases may establish coverage, reduced sheets/hash ledgers alone cannot. Unchanged candidate integrity/direction/acceptance gates. Exact resource manifests/minimal used private closure, files<100MB/no runtime app trees/pycache. Originals/backups/target/preparation/initial/brief/frozen criteria immutable. Editor owns source/candidates; judge owns reviews. No Git/index/production/deploy/liveBlender/device/shared-helper edits or extra agents.'
]
consumer = read(folder / 'reviews/preparation-v1/consumer/results.json')
plan = {
    'asset': 'decor-background-rock',
    'scope': 'Bounded static standalone prop; no modular seam or motion playback requirement.',
    'requiredFrames': ['static/N/0', 'static/E/0', 'static/S/0', 'static/W/0'],
    'previews': criteria['futureReviewCoverage']['previews'],
    'consumerCasesPerMode': [case['config'] for case in consumer['modes'][0]['cases']],
    'browserModes': proposal['boundedConsumerEvidence']['browserModes'],
    'dpr': 1,
    'scene': proposal['boundedConsumerEvidence']['context'],
    'nativeGate': 'Measure actual saved native root/camera, all4 envelope/grounded closed support/effective ownership/static temporal channels and complete full-canvas LANCZOS publication; no exact old cap union or vertex/count lock.',
    'coverage': 'All declared media directly inspected by original judge, with exact-path/hash bindings and acyclic supplemental evidence; unchanged validators.'
}
reconciliation = {
    'asset': 'decor-background-rock',
    'stage': 'ROOT reconciliation BEFORE native construction',
    'preparation': {'path': str(manifest_path.relative_to(folder)), 'sha256': digest(manifest_path), 'rootVerifiedFiles': 153},
    'freshEditorInitial': {'path': str(initial_path.relative_to(folder)), 'sha256': digest(initial_path)},
    'height': {'decision': 'Adopt actual source crown as1.075 native design budget with1e-6 representation tolerance; do not shrink to rounded nominal1.05.', 'xy': [-.5, .5], 'z': [0, 1.075], 'nominalCatalogHeightRetained': 1.05},
    'support': 'Keep actual ground plane and finite closed grounded stone semantics; permit useful base/outline remodeling within placement budget and tiny standalone silhouette drift. Baseline .9494783 cap union/area/old four parts are not exact geometry locks. No invented fullsquare opacity/feet/platform/ports.',
    'camera': 'Adopt measured own55.0079798 registered camera/native4x with complete-frame LANCZOS published2x; saved35 startup camera is unrelated. Preserve honest tiny root/basis/historical replay residuals.',
    'style': 'Freeze original five independent proposed visible outcomes, including quiet layer1 scenery role beside actual yellow submarine/eel context. Fixed target remains unchanged. Editor chooses native implementation and useful form/detail improvements; no exact target glare/part count mandate.',
    'historicalEvidence': 'All4 reconstructed historical frames have matching alpha extents but mean error<.00016/max5 channel residual; missing historical raw PNGs are not fabricated. Early BOX sheets are labeled diagnostics, not publication contract. Both consumer modes retained: all6 native pairs decoded-exact; CSS filtering residuals honest.',
    'scope': 'No candidate approval. Root later promotes exact approved bytes/publishes PR37; existing34-object Godot integration remains separate.'
}
contract = {
    'asset': 'decor-background-rock', 'version': 1, 'status': 'root-frozen-before-construction',
    'sourceProposal': {'path': str(proposal_path.relative_to(folder)), 'sha256': digest(proposal_path)},
    'preparationManifest': {'path': str(manifest_path.relative_to(folder)), 'sha256': digest(manifest_path), 'rootVerifiedFiles': 153},
    'nativeContract': proposal, 'hardConstraints': hard, 'reconciliation': reconciliation, 'requiredEvidence': plan
}
write(reconciliation_path, reconciliation)
write(contract_path, contract)
shutil.copyfile(folder / 'brief.json', backup_path)
brief = read(folder / 'brief.json')
brief['capture'].update(nativeFrame=[768, 1408], nativeCaptureScale=4, publishedFrame=[384, 704], publication='Uniform complete-frame native4x to published2x LANCZOS; no fitting or crop.', previews=['four-view-sheet', 'phone', 'repeated'])
brief['constraints']['nativeContract'] = 'inputs/root-native-contract.json'
brief['qualityCriteria'] = {
    'status': 'root-frozen-before-construction', 'definitionOfGood': criteria['definitionOfGood'],
    'priorityOutcomes': criteria['criteria'], 'hardConstraints': hard,
    'criteriaFile': str(criteria_path.relative_to(folder)), 'criteriaFileSHA256': digest(criteria_path),
    'nativeContract': str(contract_path.relative_to(folder)), 'nativeContractSHA256': digest(contract_path),
    'preparationManifestSHA256': digest(manifest_path), 'requiredEvidence': plan
}
resources = brief.setdefault('technicalResources', {})
resources.update(rootNativeContract=str(contract_path.relative_to(folder)), preparationReconciliation=str(reconciliation_path.relative_to(folder)), nativePreparationManifest=str(manifest_path.relative_to(folder)), freshEditorInitial=str(initial_path.relative_to(folder)))
for record in manifest['files']:
    resources['prepared:' + record['path']] = record['path']
write(folder / 'brief.json', brief)
progress_path = run / 'progress.json'
progress = read(progress_path)
entry = next(row for row in progress['objects'] if row['id'] == 'decor-background-rock')
entry.update(status='editing', editor='catalog_decor_background_rock_editor_v1', judge='catalog_decor_background_rock_judge_v1', editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate', stage='native-background-rock-round01', briefSHA256=digest(folder / 'brief.json'))
write(progress_path, progress)
result = {'asset': 'decor-background-rock', 'scriptSHA256': digest(Path(__file__)), 'editorInitialSHA256': args.editor_initial_sha, 'rootVerifiedPreparationFiles': 153, 'briefSHA256': digest(folder / 'brief.json'), 'contractSHA256': digest(contract_path), 'reconciliationSHA256': digest(reconciliation_path)}
write(run / 'preparation/decor-background-rock/freeze-execution-v1.json', result)
print(json.dumps(result))
