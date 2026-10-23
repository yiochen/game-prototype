"""Freeze native salvage form/motion freedom before construction."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('--editor-initial-sha', required=True)
args = parser.parse_args()
run = Path(__file__).resolve().parents[2]
folder = run / 'objects/salvage-metal'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


manifest_path = folder / 'reviews/preparation-v1/hashmanifest.json'
assert digest(manifest_path) == 'a46c829db966f6cfe458d4372ccbed48db4a976fa51e1b7508f2f5ce951fddf2'
manifest = read(manifest_path)
assert len(manifest['files']) == 225
for record in manifest['files']:
    resource = folder / record['path']
    assert digest(resource) == record['sha256'], record['path']
    assert resource.stat().st_size < 100_000_000, record['path']
seal_path = folder / 'reviews/preparation-v1/seal.json'
assert digest(seal_path) == '113258a46c709d3472eb53fa94349dd54583a948ae1912d130853479dfdaa7a9'
proposal_path = folder / 'reviews/preparation-v1/root-native-contract.proposed.json'
criteria_path = folder / 'reviews/criteria.json'
plan_path = folder / 'reviews/preparation-v1/evidence-plan.json'
assert digest(proposal_path) == 'd18253769be1a43e374660d2106038c6937409fb2febb602fe891f19b92c7d7c'
assert digest(criteria_path) == 'ae879574b315b14b343ff7119f4b22b66230d269cdb972b25b104e0b0cd7a8fb'
assert digest(plan_path) == '87d85a7e4e3aae9ee3fd562c9d243d07332c1881965a031b7d0cf55411aae2ca'
initial_path = folder / 'source/initial-observations.json'
assert len(args.editor_initial_sha) == 64 and digest(initial_path) == args.editor_initial_sha
proposal, criteria, plan = read(proposal_path), read(criteria_path), read(plan_path)
contract_path = folder / 'inputs/root-native-contract.json'
reconciliation_path = folder / 'inputs/root-preparation-reconciliation-v1.json'
backup_path = folder / 'inputs/brief-before-native-freeze.json'
assert not any(path.exists() for path in [contract_path, reconciliation_path, backup_path])
hard = [
    'Actual three metal-salvage variants plate/bent/mixed, nine clips shimmer/attract/collect and b-/c- equivalents, four proper facings,432 original unique phase slots. Preserve recognizable variant identities, cool blue-gray metal/slate and mixed wood role, centered one-cell occupancy/root/world scale. Useful native geometry/form/count/topology/normal/bevel/material/detail reconstruction is allowed; old4/3/3 mesh counts, blank panels, weak bent shapes and exact target fastener/rust counts are not locks.',
    'ROOT native design budgets before construction: rest/shimmer/attract XY[-.45,.45],Z[0,.70]; collect XY[-.45,.45],Z[0,1.30]; tolerance1e-5, proper-rotated all4 and measured every phase. These are permitted maxima, not desired surfaces/heights/amplitudes. Source rest max.67861 and dynamic max1.25727 establish scale; nominal metadata.62 is not a universal ceiling. Preserve coherent finite support atZ0 in resting loops, correcting original plate penetration. No exact old support polygon/area/count, opaque full-cell floor, feet, submarine socket or modular port invented. No mesh may penetrate below ground or clip authored frame. Choose native shapes inside useful budget without perpart source-box locks.',
    'Same9clip identifiers/variant gating/12unique phase slots per facing/12fps/originalframeOrder/6x2atlas23041408/publishedframe384704. Six loops have native duplicate closing key13 matching1; published last unique phase12 is not forced equal1. Three collect one-shots rise and shrink coherently and hold terminal native12 through13/24, no loop restart. Root remains registered; no actor travel/submarine attachment. Shimmer/attract may diverge through restrained coherent pose/material treatment or remain related; original identical atlas alias is not a quality requirement. Keep grounded full variant in these loops. Collect may improve easing/lift/shrink and scale relative part origins as a coherent assembly around a stable native pivot; original independent-part spread/old.75lift/.07scale are descriptive, not locks. Terminal remains deliberately tiny, nonzero and held; no rest-size readability requirement or raster fading/repair.',
    'Source allthree roots belong to S33_PROP_salvage_a.001, B/C parented beneathA. Distinguish active variant ownership from parent descendants: A4/B3/C3 are baseline counts only. Exactly intended variant geometry visible in every pose, stable fastener/wood/metal attachments. Validate actual effective world facing/root for active B/C and avoid double parent rotation. Rebuilt private hierarchy allowed if same proper S0 E+90 N180 W-90 and registered semantic roots/variant gating preserved. Preserve actual absence of external textures/linked libraries/armatures unless a native implementation adds explicitly bound resources, never a target card.',
    'Own registered55.0079798 camera/ortho1.5/aspect1.22065556/worldcell1, logical192352/root96248/cell128/native4x7681408/root384992/published2x384704/root192496. Uniform whole authored native4x canvas LANCZOS to2x/originalatlases, no fit/crop/warp/offset/perview recolor/alphaRGB repair. Measure actual render-time root/camera/matrices across required phases or truthful saved-source recapture. Saved startup camera is not authority. One reproducible native filter/color/material/light recipe acrossall4; symmetric broad horizontal lighting/no preferredkey/directionalgroundcast. Historical Faceted watts/world0/contrast1.35/roughness/ramp are implementation history, not aesthetic locks.',
    'Same six independent visible outcomes: crafted chunky soft metal variant volumes; cool blue-gray/slate and mixed wood material separation; controlled broad rounded edge/plane light with readable lowers; purposeful restrained tactile detail; clean attachments/silhouettes/alpha/allphase use-size reading; coherent loop/collect motion with correct cadence/closure/hold. Fixed singleview target guides quality, not camera/registration/unseen surfaces/left glow. Native matte or soft sheen allowed. No mirror glints/blank white tops/black dead patches/speckle/float decoration/zfight/halos/clipping. Latecollect intentionally tiny; no numeric/source-equality waiver for real visible defects.',
    'Render all432 required native4x raw poses and fullcanvas2x publication/atlas cells from exact editable saved source. Measured allphase effective ownership/camera/root/envelope/variant attachments/grounded loop support, closure and heldterminal evidence. Compact synchronized variant/clip family playback in all4 plus deterministic allphase sheets at useful scale, enlarge representative/uncertain regions. Actual browser/compositor playback must witness cadence/phase order/wrap/terminal holds; source fullChromium sparse15samples and canvas.drawImage(APNG) default-frame capture do not prove complete candidate playback. Extract all declared APNG frames and use actual compositor if animated APNG supplied. No requirement for12 decoded-unique images if semantically correct motion has coincident phases; timing slots remain12.',
    'Same bounded compact allstate/facing fixture with light/gray/dark distributed backgrounds, logical andphone.45 scale, representative rest/mid/late/closure/heldcaptures in both actual Chromium153 modes/800900+360900/DPR1, exact current099/570 helpers/root/order/rects/atlas/executables/options/version/errors/realRAF evidence. Native nearest AFTER resize then ordinarywholecanvasCSS filtering; keep actual differences honest. No432xbackgroundxviewport browser Cartesian matrix or invented submarine attach scene. Every declared hero/preview independently inspected by originaljudge with exact path/hash/full useful coverage; missing evidence not approval. NativeValidation measured facing/root records supported views/captureRecords; optional nativeGeometryMeasurements facing->LIST of frame dictionaries, rich other ledgers separately bound.',
    'Exact minimal actual-used private source/helper/module/instruction/input closure and editable Blender, allfiles<100MB/no runtime app trees/frozen pycache. Original source/backup/target/preparation/initial/brief/criteria/prior signed artifacts immutable. Editor owns source/candidates, judge reviews; ROOT seals/promotes/publishes. No editor/judge Git/index/production/deploy/liveBlender/device/sharedhelper/brief/review ownership changes or extraagents. Unchanged integrity/direction/acceptance checks.'
]
reconciliation = {
    'asset': 'salvage-metal', 'stage': 'ROOT reconciliation BEFORE construction',
    'preparation': {'path': str(manifest_path.relative_to(folder)), 'sha256': digest(manifest_path), 'rootVerifiedFiles': 225},
    'freshEditorInitial': {'path': str(initial_path.relative_to(folder)), 'sha256': digest(initial_path)},
    'restBudget': {'XY': [-.45, .45], 'Z': [0, .70], 'tolerance': 1e-5},
    'collectBudget': {'XY': [-.45, .45], 'Z': [0, 1.30], 'tolerance': 1e-5},
    'budgetRationale': 'Useful small centered one-cell forms with modest room beyond observed .372XY/.679rest/1.258collect maxima; permit native meaningful remodeling and plate penetration repair, no source-mesh/evaluated-trim lock. Nominal .62 retained as historical metadata, not maximum native geometry.',
    'ground': 'Finite coherent grounded closed native salvage in resting loops. Correct plate belowZ0 penetration; old contact polygons/counts/areas free. No invented fullsquare opacity/support foot/port/submarine attachment.',
    'motion': 'Preserve9states/3variants/12phase12fps/cadence/6closure13=1/3terminal12=13=24. Allow restrained coherent loop differentiation and meaningful coherent whole-assembly collect lift/shrink/easing. Old independentpart origins/amplitudes/alias atlases not locks; no lateral actor travel. Tiny nonzero terminal remains held.',
    'hierarchy': 'Fresh editor independently confirmed B/C roots underA in samecollection. Private hierarchy may improve, but actual effective activevariant world facing/root/ownership must be measured, no doubled rotations or sibling leakage.',
    'capture': 'Own55/aspect1.22065 native4x fullcanvasLANCZOS2x registration preserved. Source72 sampled frame comparisons decoded exact; all432 source poses measured, not falsely claimed all rendered. Actual consumer sparse RAF/crossmode residual limits remain retained.',
    'criteria': 'Original six proposed visible outcomes frozen unchanged; original model counts/target count/brightness/plant colors are not mandates. No candidate approval.'
}
contract = {'asset': 'salvage-metal', 'version': 1, 'status': 'root-frozen-before-construction', 'sourceProposal': {'path': str(proposal_path.relative_to(folder)), 'sha256': digest(proposal_path)}, 'preparationManifest': {'path': str(manifest_path.relative_to(folder)), 'sha256': digest(manifest_path), 'rootVerifiedFiles': 225}, 'nativeContract': proposal, 'hardConstraints': hard, 'reconciliation': reconciliation, 'requiredEvidence': plan}
write(reconciliation_path, reconciliation)
write(contract_path, contract)
shutil.copyfile(folder / 'brief.json', backup_path)
brief = read(folder / 'brief.json')
brief['capture'].update(nativeFrame=[768, 1408], nativeCaptureScale=4, publishedFrame=[384, 704], publication='Uniform whole native4x canvas to published2x LANCZOS; original6x2 atlas, no fitting.', previews=['four-view-sheet', 'phone', 'repeated'])
brief['constraints']['nativeContract'] = str(contract_path.relative_to(folder))
brief['qualityCriteria'] = {'status': 'root-frozen-before-construction', 'definitionOfGood': 'Three distinct crafted softly rounded salvage variants with readable blue-gray metal/wood, controlled broad highlights, stable attachments and coherent grounded loops/upward collect shrink.', 'priorityOutcomes': criteria['priorities'], 'hardConstraints': hard, 'criteriaFile': str(criteria_path.relative_to(folder)), 'criteriaFileSHA256': digest(criteria_path), 'nativeContract': str(contract_path.relative_to(folder)), 'nativeContractSHA256': digest(contract_path), 'preparationManifestSHA256': digest(manifest_path), 'requiredEvidence': plan}
resources = brief.setdefault('technicalResources', {})
resources.update(rootNativeContract=str(contract_path.relative_to(folder)), preparationReconciliation=str(reconciliation_path.relative_to(folder)), nativePreparationManifest=str(manifest_path.relative_to(folder)), freshEditorInitial=str(initial_path.relative_to(folder)))
for record in manifest['files']:
    resources['prepared:' + record['path']] = record['path']
write(folder / 'brief.json', brief)
progress_path = run / 'progress.json'
progress = read(progress_path)
entry = next(row for row in progress['objects'] if row['id'] == 'salvage-metal')
entry.pop('preparationJudge', None)
entry.update(status='editing', editor='catalog_salvage_metal_editor_v1', judge='catalog_salvage_metal_judge_v1', editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate', stage='native-salvage-round01', briefSHA256=digest(folder / 'brief.json'))
write(progress_path, progress)
result = {'asset': 'salvage-metal', 'scriptSHA256': digest(Path(__file__)), 'editorInitialSHA256': args.editor_initial_sha, 'rootVerifiedPreparationFiles': 225, 'briefSHA256': digest(folder / 'brief.json'), 'contractSHA256': digest(contract_path), 'reconciliationSHA256': digest(reconciliation_path)}
write(run / 'preparation/salvage-metal/freeze-execution-v1.json', result)
print(json.dumps(result))
