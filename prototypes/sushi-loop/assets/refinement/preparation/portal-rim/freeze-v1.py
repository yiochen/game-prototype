"""Freeze the upright portal's actual registration, support role and native design freedom."""
import hashlib
import json
from pathlib import Path
import shutil

run = Path(__file__).resolve().parents[2]
folder = run / 'objects/portal-rim'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


bindings = {
    'reviews/preparation-v1/hash-manifest.json': 'acd9f06b0c07c3b49055c5314921be5d35c4b53bf4c9a15b72c2ca4d1b04a105',
    'reviews/preparation-v1/seal.json': '66c3c3c3d94d0016d768f7266da2c9384422914bb59fd4b61ae1a317d0a77562',
    'reviews/preparation-v1/root-native-contract.json': '19b74f01d771661b461b7b19e76eb5a3ea1eb0edcce6aeaa6937f120e6f350d8',
    'reviews/preparation-v1/scoped-evidence-plan.json': '2daa3d284b1353179b3b87267bfc0e685103744376755f240307c1f008c0b623',
    'reviews/criteria.json': 'ab43c5818f27f1b28facfa7dc2177b82e6fe95b6cd4cdb94881f50cc4743f661',
    'source/initial-observations.json': '467ca3bc05b9bb0f15aec378d7f0e03da4ca44f50f135fbd609af561db6e5707',
}
for name, sha in bindings.items():
    assert digest(folder / name) == sha, name
manifest = read(folder / 'reviews/preparation-v1/hash-manifest.json')
assert len(manifest['files']) == 141
for record in manifest['files']:
    resource = folder / record['path']
    assert digest(resource) == record['sha256'], record['path']
    assert resource.stat().st_size < 100_000_000, record['path']
proposal = read(folder / 'reviews/preparation-v1/root-native-contract.json')
criteria = read(folder / 'reviews/criteria.json')
plan = read(folder / 'reviews/preparation-v1/scoped-evidence-plan.json')
catalog = read(folder / 'inputs/catalog-object.json')
assert catalog['requirements']['minimumUniqueFrames'] == 6
contract_path = folder / 'inputs/root-native-contract.json'
reconciliation_path = folder / 'inputs/root-preparation-reconciliation-v1.json'
backup_path = folder / 'inputs/brief-before-native-freeze.json'
assert not any(path.exists() for path in [contract_path, reconciliation_path, backup_path])
hard = [
    'Native portal-rim upright OPEN ring only, cyan/blue dominant with stable navy supports; secondary restrained warmgold/neutral craft accents allowed. Useful native forms/proportions/topology/part/ornament counts/structure/support connections/bevels/normals/material/light changes authorized. Original12meshes/2torus/8rune/2rock counts, exact torus topology/gemcount/target streaks are not locks. Preserve coherent upright open ring identity and stable support groups, not literal support mesh count. No opaque portal disk/targetcard/artificialalpha aperture. All13marked2D effects excluded, portal-entry/extra enter states are separate objects and not required here.',
    'ROOT adopts canonicalS allphase native design budget X[-.73,.73],Y[-.30,.30],Z[-.06,1.48],tol1e-5, properrotated all4. This is permitted maximum, not desired exact dimensions/symmetry/sourceAABB equality/perpart cage. Source raw sweptX±.716194/Zmax1.456194 is reference; evaluated beveltrim not lock. Budget permits useful side depth/model reconstruction while preserving registered scale/height and transparent frame border. Do not grow geometry to fill budget. No native/frame clipping or perviewfitting.',
    'Finite grounded stable native supports remain. Source rocks intentionally crossZ0 with min-.06 and finiteZ0 sections; this embedded geometry is allowed, not an automatic penetration defect. Every resting support group needs coherent finiteZ0 intersection/contact and connection to ring through idle; no floating bases. Exact original two hull shapes/area.0335667/count/negative-depth shape are not locks, no fullcell opaque floor/foundation law. Entry center rootrelative(0,0,.74) stays fixed and coherently inside upright opening, projected allviews(0,-66.3040271)logical. It is a presentation/center reference, no authored ship-passage collision/tether/socket-parenting/modular seam requirement. Keep useful opening; no invented traversal guarantee.',
    'Actual S33_PROP_portal_rim.002/root portal_rim__root.002/worldroot0, proper rootS0 E90 N180 W-90. Own55.0079798degree oblique camera/ortho1.5/aspect1.2206555605:1/shiftX0/Y.4096146523952484/world1/cell128. Logical192384/root96288/native4x7681536/root3841152/full authoredcanvasLANCZOS2x384768/root192576, original6x2atlas23041536/12rects. Saved active35degree character camera is unrelated. Measure actual capturetime root/camera/effectivepose all48 or honest clean hashbound savedsource replay. Physically rotate thin vertical ring: E/W remain intentional coherent edge views, no billboarding/perviewcamera/fit/crop/warp/nudge/recolor/RGBalpha repair/targetcard.',
    'One idle clip only,12publishedphase slots/12fps/originalorder/one-second loop, nativeclosing13=1 excluded from atlas. Preserve visible smooth pulse/circulation and static supports/root/entrycenter. Actual catalog requires at least6 unique rendered phases; this existing requirement is not a new arbitrary score. Source10actionowner/8orbitornament counts/actionnames/numericamplitudes/angularrecipe are free. Rebuild coherent native pulse/orbits/material animation if helpful and adapt to new counts so actual loop closes withoutresetpop. Native shape/material/lighting methods free, one reproducible allviewrecipe/symmetric broad horizontal light/no preferredkey/directionalgroundcast. Old Faceted watts/world0/contrast1.35/roughness/ramp are observations, not style mandates.',
    'Original three independent ranked visible outcomes frozen: substantial intentionally built cyan upright ring with coherent volume/outerstructure/ornamenthousings/supportconnections; cyanblue/navy hierarchy with optional secondary warmgold/neutral craftsmanship and broad soft edge/plane rolloff/readable lowerfaces; distinct aperture/structure/supports inN/S, purposeful thickness inE/W, smooth idle and stable supports at logical/.55phone onlightgraydark. No tangent/brokenjoins,zfight,blackdeadpatches,clippedornaments,halos,noisyunreadabletinydecoration/chalkyglare. Fixedsingleview target aesthetic guide, not outlinepixelmatching/unseenviews/camera/registration/leftglow/count mandates. No numeric approval score threshold/hash-only visual waiver.',
    'Retain all48 exact native4x phase captures/fullcanvas2xframes/original4atlases from editable saved source, with actual allphase raw authored/evaluatedgeometry/root/camera/ownership/finitecontact/supportconnection/entryopening/clipping plus nativeclosing13=1 evidence. Useful allview/allframe fullregistration sheets/path-cell maps/enlarged uncertain regions. Same exact current099/570 helpers/root/rects/sourceScale/order, logical/.55phone/lightgraydark/both actual153launchmodes/DPR1/840780 viewport/executable/options/version/errors, actual12fps playback≥2.2s/phaseorder/11to0wrap. Native nearest AFTER commoncanvasresize then ordinarywholeCSSfilter; honest native/CSS/configuration residuals, APNGdrawImage frozen defaultframe/sparsevideo not completeproof. No redundant48xviewport/background Cartesian. Every declared hero/preview originaljudge complete usefulpixel path/hash coverage.',
    'No functional repeated modular grid/harpoon attachment/ship traversal fixture is required. Original repeated preview is removed from capture.previews before construction; delivery uses four-view-sheet,phone,motion,idle-N/E/S/W aliases with true existingmedia if useful. Context neighbors are presentation scale only, not physical seam/clearance approval. NativeValidation supportedviews/captureRecords, optional nativeGeometryMeasurements facing->LISTframes, richotherledgers separatelybound; nevereditchecker/fabricate. Root fields must be measured, not relabeledmetadata.',
    'Minimal actualused private editable source/helper/module/input/instruction closure/allfiles<100MB/no runtimeapplicationtrees/frozenpycache. Original source/backups/target/initial/prep/brief/criteria/priorversions immutable. Editor owns source/candidates, judge reviews, ROOT seals/promotes/publishes. No editor/judge sourceoriginal/Git/index/production/deploy/liveBlender/device/sharedhelper/brief/review ownership change/extraagents/selfapproval/selfpacket. Unchanged integrity/direction/acceptance checks.'
]
reconciliation = {'asset': 'portal-rim', 'stage': 'ROOT reconciliation BEFORE construction', 'preparation': {'path': 'reviews/preparation-v1/hash-manifest.json', 'sha256': bindings['reviews/preparation-v1/hash-manifest.json'], 'rootVerifiedFiles': 141}, 'freshEditorInitial': {'path': 'source/initial-observations.json', 'sha256': bindings['source/initial-observations.json']}, 'canonicalSAllphaseBudget': {'X': [-.73, .73], 'Y': [-.30, .30], 'Z': [-.06, 1.48], 'tolerance': 1e-5}, 'budgetRationale': 'Adopt useful proposed native allowance around raw swept source, not evaluated trim equality. Fixed192384 framing and transparentborder remain. Purposeful side depth/modeling allowed, maxima not desired geometry.', 'support': 'Preserve finite coherentZ0 contact and support role; intentional original embedded rocks min-.06 allowed. No old hull-area/count/shape/fullfloor lock.', 'openingAndOrientation': 'Upright native open ring, fixed entrycenter(0,0,.74), properall4 with naturally edge-onE/W. No fullportal disk/billboard/shipcollision claim or new attachment law.', 'motion': 'One-second idle12slots12fps/native13=1; source action/ornament counts and amplitudes free with coherent pulse/circulation. Existing catalog minimumUniqueFrames6 retained.', 'capture': 'Actual55degree oblique/aspect1.22065/native4x fullLANCZOS2x. All48originalreplays decodedexact. Savedstartup35camera ignored.', 'previewScope': 'Remove nonfunctional repeated-grid alias before construction; required fourview/phone/motion/four idleview aliases. Actual currentconsumer and aperture/support evidence, not gameplay/Godot/device.', 'criteria': 'Original independent ranked outcomes and dimensions frozen. No candidate or approval yet.'}
write(reconciliation_path, reconciliation)
contract = {'asset': 'portal-rim', 'version': 1, 'status': 'root-frozen-before-construction', 'sourceProposal': {'path': 'reviews/preparation-v1/root-native-contract.json', 'sha256': bindings['reviews/preparation-v1/root-native-contract.json']}, 'preparationManifest': reconciliation['preparation'], 'nativeContract': proposal, 'hardConstraints': hard, 'reconciliation': reconciliation, 'requiredEvidence': plan}
write(contract_path, contract)
shutil.copyfile(folder / 'brief.json', backup_path)
brief = read(folder / 'brief.json')
brief['capture'].update(nativeFrame=[768, 1536], nativeCaptureScale=4, publishedFrame=[384, 768], publication='Uniform whole native4x canvas to published2x LANCZOS; original6x2 atlas, no fitting.', previews=['four-view-sheet', 'phone', 'motion', 'idle-N', 'idle-E', 'idle-S', 'idle-W'])
brief['constraints']['nativeContract'] = str(contract_path.relative_to(folder))
brief['qualityCriteria'] = {'status': 'root-frozen-before-construction', 'definitionOfGood': 'Substantial cyan/blue upright open ring, coherent native structure/ornaments/stable supports, optional restrained warm craft accents, broad soft volume light and clean smooth idle in all registered views including edge-on profiles.', 'priorityOutcomes': criteria['ranking'], 'dimensions': criteria['dimensions'], 'hardConstraints': hard, 'criteriaFile': 'reviews/criteria.json', 'criteriaFileSHA256': bindings['reviews/criteria.json'], 'nativeContract': str(contract_path.relative_to(folder)), 'nativeContractSHA256': digest(contract_path), 'preparationManifestSHA256': bindings['reviews/preparation-v1/hash-manifest.json'], 'requiredEvidence': plan}
resources = brief.setdefault('technicalResources', {})
resources.update(rootNativeContract=str(contract_path.relative_to(folder)), preparationReconciliation=str(reconciliation_path.relative_to(folder)), freshEditorInitial='source/initial-observations.json')
for name in bindings:
    resources['bound:' + name] = name
for record in manifest['files']:
    resources['prepared:' + record['path']] = record['path']
write(folder / 'brief.json', brief)
progress_path = run / 'progress.json'
progress = read(progress_path)
entry = next(row for row in progress['objects'] if row['id'] == 'portal-rim')
entry.pop('preparationJudge', None)
entry.update(status='editing', editor='catalog_portal_rim_editor_v1', judge='catalog_portal_rim_judge_v1', editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate', stage='native-portal-rim-round01', briefSHA256=digest(folder / 'brief.json'))
write(progress_path, progress)
result = {'asset': 'portal-rim', 'scriptSHA256': digest(Path(__file__)), 'editorInitialSHA256': bindings['source/initial-observations.json'], 'rootVerifiedPreparationFiles': 141, 'briefSHA256': digest(folder / 'brief.json'), 'contractSHA256': digest(contract_path), 'reconciliationSHA256': digest(reconciliation_path)}
write(run / 'preparation/portal-rim/freeze-execution-v1.json', result)
print(json.dumps(result))
