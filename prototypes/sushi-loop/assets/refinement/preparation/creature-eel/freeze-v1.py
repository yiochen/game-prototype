"""Freeze eel body refinement and native action compatibility repair before construction."""
import hashlib
import json
from pathlib import Path
import shutil

run = Path(__file__).resolve().parents[2]
folder = run / 'objects/creature-eel'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


bindings = {
    'reviews/preparation-v1/manifest.json': '7082cece3abe933dd58fde5efd54a172392713ba5fd1c3c92d2e27bd0275ada8',
    'reviews/preparation-v1/seal.json': 'adb32b7238b6529882ccea9de51ad7c9f72d00dc2ea8a1559a3fd4178bcda540',
    'reviews/preparation-v1/root-native-contract.proposed.json': '47c708e51a12a047e39b50a3bfc204dd5f1b3b32673d2f3969584824ec7b0525',
    'reviews/criteria.json': '261342c4418a19dccb561aca940e95c3c4f04f36c7421fa411330d31378913c3',
    'reviews/preparation-v1/evidence-plan.proposed.json': '67583d44203304d59852f10aec98ed428d8bb2ac1d062a66fe926ebbfc33bbf5',
    'source/initial-observations.json': '83310489eea8fe985f9a1d9d338c7bc2b189e80a43ec3b1ec1ff9ed2379c1eed',
}
for name, sha in bindings.items():
    assert digest(folder / name) == sha, name
manifest = read(folder / 'reviews/preparation-v1/manifest.json')
assert len(manifest['files']) == 333
for record in manifest['files']:
    resource = folder / record['path']
    assert digest(resource) == record['sha256'], record['path']
    assert resource.stat().st_size < 100_000_000, record['path']
proposal = read(folder / 'reviews/preparation-v1/root-native-contract.proposed.json')
criteria = read(folder / 'reviews/criteria.json')
plan = read(folder / 'reviews/preparation-v1/evidence-plan.proposed.json')
contract_path = folder / 'inputs/root-native-contract.json'
reconciliation_path = folder / 'inputs/root-preparation-reconciliation-v1.json'
backup_path = folder / 'inputs/brief-before-native-freeze.json'
assert not any(path.exists() for path in [contract_path, reconciliation_path, backup_path])
hard = [
    'Native eel BODY only: recognizable elongated blue body/yellow dorsal-tail-side fins, white/navy expressive eyes and dark mouth, continuous tapered anatomy and coherent dimensional fins. Meaningful anatomy/proportion/topology/part/bone-count improvements are authorized. Original10-sided body/29rings/7bones/12meshes/flat shading and target exact fin/facial detail counts are not locks. Retarget all required actions if hierarchy changes. Do not tune or regenerate any marked2D effect, including warning strip/lightning/discharge/cable/projectile/background fish silhouette.',
    'ROOT allphase design-clearance budget, canonical rootS: X[-1.30,1.30],Y[-.75,1.45],Z[.04,1.00],tol1e-5, transformed by proper S0/E90/N180/W-90 root facings. This is a permitted posed maximum, not desired body size, mandatory symmetry, source AABB equality or a perpart cage. It accommodates the actual intended repaired-motion envelope X[-1.1983,.4760],Y[-.6782,1.3586],Z[.0711,.9184] with remodeling margin and permits either lateral wave. Preserve gross elongated1x2 actor scale/recognizable occupied hit silhouette and attachment clearance. Nominal height.9 and placement footprint are not exact mesh limits; do not fill the budget to create a much larger creature. Floating actor: no feet/ground contact/support mask/fullcell opacity/port introduced. No native or frame clipping.',
    'Native rig compatibility repair is authorized before art construction. Actual raw source seven bones use QUATERNION while all11 actions key rotation_euler, suppressing evaluated spine bending. Use compatible Euler modes, correctly converted quaternion actions, or equivalent native retargeted rig; no literal XYZ method requirement. Broken rest-spine rendering and old numeric amplitudes are not fidelity locks. Preserve meaningful flexible continuous deformation and original clip roles; evaluated bone matrices/vertices must actually move and all facial/fin parts remain attached without tearing/selfintersection.',
    'All11 existing clip IDs,12 published phases at12fps/original order,8loops plus3one-shots remain. Normal calmwave; swim stronger travelingwave; aim forwardpitch; restless fasteragitation/roll; pursuit urgentwave; weave lateralwholebodyturn; dash briskbeat/restrainedyaw; pause restrainedpitchbob; hook briefstruggle/roll; caught largerbentstruggle; escape briefliftedturn. Eight native loopclosing controls13=1; phase12 remains last unique not forced equal1. Hook/caught/escape final12 held through13/24, reaction returning to initial pose under existing semantics. No new actor travel/root translation; internal armature bob/roll allowed. Timeline/cadence/loop roles fixed; useful native easing/amplitudes/rig counts free within clearance.',
    'Actual source S33_CFX_creature-eel.003/root creature-eel__ground_root.003 with constant canonical innerZ180. Preserve effective root rotations S0 E90 N180 W-90 and rootspace metadata hook=cable(0,-.16,.56),nose(0,-.6,.44) with original four-facing projected markers. No native socket empties or simulated tether currently exist: keep the declared accessible attachment region and registered metadata, do not impose everyframe geometry intersection with fixed markers or invent physical tether/foot/submarine parenting law. Four-facing marker fixture uses exact current consumer; separate2D effect art is excluded.',
    'Own character-orthographic35degree camera, ortho3.5/HORIZONTAL, squarepixelaspect1, shiftX0/shiftY.21428516507148743, cell128/world1. Logical448512/root224352, native4x17922048/root8961408, full authored canvas LANCZOS to published2x8961024/root448704 and original6x2atlas53762048/12rects. Saved startup camera and environmental55degree rigs are not this actor contract. Measure actual render-time camera/root/effective matrices allphase or truthful clean hashbound savedsource replay. No perviewfit/crop/warp/offset/recolor/RGBalpha repair or target card. One native reproducible filter/color/material/light recipe all4; symmetric broad horizontal lighting/no preferredkey/directionalgroundcast. Historical140/100W/world0/contrast1.35/rough.85 are observations, not style mandates.',
    'Freeze original independent outcomes: coherent rounded friendly elongated anatomy/expressive face/dimensional fins; blueyellow identity with readable lowerplanes; broad controlled soft native highlights all4; purposeful clean surface/fin/facial articulation; logical448512 and uniform.4phone lightgraydark readability; actual coherent flexible body motion; no blackdeadpatches,whiteclipping,noise,harshrims,detachment,open seams,halos,tearing,selfintersection or registration jumps. Singleview target guides aesthetics, not unseenviews/camera/registration/leftglow. No numeric score threshold or hash-only visual waiver.',
    'Retain all528 required native4x RGBA poses plus exact wholecanvas2x frames/atlases from editable saved source. Measure every clip/facing/phase native raw/evaluated envelope, effective camera/root, finite coherent ownership/attachments/deformation/clipping,8closure13=1 and3terminal12=13=24 controls. Actual evaluated bone matrices required; Eulerproperty changes alone insufficient. Compact useful lossless sheets with path-to-cell coverage may cover all528, enlarge facial/fin/uncertain/extreme regions; no528-scene browser Cartesian matrix. No need12 distinct decoded images if correct coincident poses; exactly12timing slots remain.',
    'Bounded actual consumer evidence uses current099/570 exact helpers/rects/root/sourceScale/order, all44 clip/facing representative states, compact distinct-rule/extrema actual playback, logical/.4phone lightgraydark, both actual supportedChromium153 launchmodes/DPR1/executable/options/version/viewports/errors. Witness realRAF cadence/order/loop12to1/terminalhold and visible flexiblebody; sparse video samples or canvas.drawImage(APNG) defaultframe are not full visual playback proof. Preserve honest pixel/raster/configuration residuals, no blanket visiblepop waiver or new bitexact nativeframe bar. Four-facing root/socket overlays only; no invented full gameplay integration. Every declared hero/preview needs originaljudge actual path/hash/full usefulpixel coverage.',
    'Minimal actual-used private dependency closure/editable Blender, allfiles<100MB/no runtime application trees/frozenpycache. Original source/backups/target/preparation/initial/brief/criteria/prior signed artifacts immutable. Editor owns source/candidates, judge reviews, ROOT seals/promotes/publishes. No editor/judge Git/index/production/deploy/liveBlender/device/sharedhelper/brief/review ownership changes/extraagents. Unchanged integrity/direction/acceptance checks. NativeValidation supported views/captureRecords; optional nativeGeometryMeasurements facing->LIST of frame dictionaries; bind rich other ledgers separately.'
]
reconciliation = {
    'asset': 'creature-eel', 'stage': 'ROOT reconciliation BEFORE construction',
    'preparation': {'path': 'reviews/preparation-v1/manifest.json', 'sha256': bindings['reviews/preparation-v1/manifest.json'], 'rootVerifiedFiles': 333},
    'freshEditorInitial': {'path': 'source/initial-observations.json', 'sha256': bindings['source/initial-observations.json']},
    'canonicalSAllphaseBudget': {'X': [-1.30, 1.30], 'Y': [-.75, 1.45], 'Z': [.04, 1.00], 'tolerance': 1e-5, 'otherFacings': 'proper root rotation; not perview refit'},
    'budgetRationale': 'Margin around actual intended unsaved Euler-compatible evaluated motion; symmetric lateral clearance permits remodeling/other wave handedness. Maxima not desired size/symmetry/sourceequal/perpart limits. Preserve gross elongated actor scale and attachment clearance, not nominalmetadata exact .9 ceiling.',
    'rigRepair': 'Both fresh roles independently found quaternion modes/Euler-key mismatch. Native compatibility correction/converted actions/retarget authorized with actual evaluated continuous deformation, existing11roles/timing/8closure/3terminalholds. No XYZ implementation mandate or oldcount/amplitude lock.',
    'floatingAndAttachments': 'No foot/ground/support law. Exact root metadata and current projected hook/cable/nose markers remain; no invented everyframe marker intersection or physical tether requirement. Separate effects excluded.',
    'capture': 'Actual35degree character camera/pixelaspect1, native4x wholeLANCZOS2x; retain original fixed registered frame/root/rects/atlas. Do not import neighboring55degree convention.',
    'criteria': 'Original independent named outcomes frozen, no numeric score threshold, candidate approval still pending.',
    'evidence': 'All528native poses/measured allphase rig/root/camera/envelope plus closure/holds, useful fullpixel coverage and bounded actual consumer/playback. Source68untouched+26diagnostic renders are preparation only, not exhaustive source rendering or candidate evidence.'
}
contract = {'asset': 'creature-eel', 'version': 1, 'status': 'root-frozen-before-construction', 'sourceProposal': {'path': 'reviews/preparation-v1/root-native-contract.proposed.json', 'sha256': bindings['reviews/preparation-v1/root-native-contract.proposed.json']}, 'preparationManifest': reconciliation['preparation'], 'nativeContract': proposal, 'hardConstraints': hard, 'reconciliation': reconciliation, 'requiredEvidence': plan}
write(reconciliation_path, reconciliation)
write(contract_path, contract)
shutil.copyfile(folder / 'brief.json', backup_path)
brief = read(folder / 'brief.json')
previews = list(dict.fromkeys(['four-view-sheet', 'phone', 'repeated'] + brief['capture']['previews']))
brief['capture'].update(nativeFrame=[1792, 2048], nativeCaptureScale=4, publishedFrame=[896, 1024], publication='Uniform whole native4x canvas to published2x LANCZOS; original6x2 atlas, no fitting.', previews=previews)
brief['constraints']['nativeContract'] = str(contract_path.relative_to(folder))
dimensions = ['shapeVolume', 'color', 'lightingHighlights', 'materialDetail', 'readability', 'motion', 'artifactFree']
brief['qualityCriteria'] = {'status': 'root-frozen-before-construction', 'definitionOfGood': 'One continuous rounded blue/yellow cartoon eel with expressive integrated face, substantial soft fins, controlled broad light/readable lowers and native evaluated flexible action throughout all registered views and states.', 'priorityOutcomes': [{'dimension': key, **criteria[key]} for key in dimensions], 'hardConstraints': hard, 'criteriaFile': 'reviews/criteria.json', 'criteriaFileSHA256': bindings['reviews/criteria.json'], 'nativeContract': str(contract_path.relative_to(folder)), 'nativeContractSHA256': digest(contract_path), 'preparationManifestSHA256': bindings['reviews/preparation-v1/manifest.json'], 'requiredEvidence': plan}
resources = brief.setdefault('technicalResources', {})
resources.update(rootNativeContract=str(contract_path.relative_to(folder)), preparationReconciliation=str(reconciliation_path.relative_to(folder)), nativePreparationManifest='reviews/preparation-v1/manifest.json', freshEditorInitial='source/initial-observations.json')
for record in manifest['files']:
    resources['prepared:' + record['path']] = record['path']
write(folder / 'brief.json', brief)
progress_path = run / 'progress.json'
progress = read(progress_path)
entry = next(row for row in progress['objects'] if row['id'] == 'creature-eel')
entry.pop('preparationJudge', None)
entry.update(status='editing', editor='catalog_creature_eel_editor_v1', judge='catalog_creature_eel_judge_v1', editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate', stage='native-eel-round01', briefSHA256=digest(folder / 'brief.json'))
write(progress_path, progress)
result = {'asset': 'creature-eel', 'scriptSHA256': digest(Path(__file__)), 'editorInitialSHA256': bindings['source/initial-observations.json'], 'rootVerifiedPreparationFiles': 333, 'briefSHA256': digest(folder / 'brief.json'), 'contractSHA256': digest(contract_path), 'reconciliationSHA256': digest(reconciliation_path)}
write(run / 'preparation/creature-eel/freeze-execution-v1.json', result)
print(json.dumps(result))
