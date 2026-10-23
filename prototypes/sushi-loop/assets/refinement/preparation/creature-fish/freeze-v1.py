"""Freeze fish body outcomes, native repair and clearance before construction."""
import hashlib
import json
from pathlib import Path
import shutil

run = Path(__file__).resolve().parents[2]
folder = run / 'objects/creature-fish'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


bindings = {
    'reviews/preparation-v1/hashmanifest.json': 'dcb36f488aa3fd8af2322b020ac9b90b1b4771b6055fe551e71640a6818b6afe',
    'reviews/preparation-v1/preparation-seal.json': '5ed04d37577c9167216169e9c230d1aa75ef4c2d960dd9eefa6a1e6f7c3e10fe',
    'reviews/preparation-v1/proposed-root-native-contract.json': '708ab5a023df701dd6b41b777643bcfb265f7a8cb8e7a7b80a5b99c58dc835a3',
    'reviews/preparation-v1/proposed-scoped-evidence-plan.json': '2da7ffacb22c5a4b0fe127cdebe6551c6e1d4f7a81b099d8408c7fe82b079935',
    'reviews/preparation-v1-rig-supplement-v1/hashmanifest.json': '26edbb34cb9e52e449baaa8c26f457cf81c986a6a5646d0730079c7321653c72',
    'reviews/preparation-v1-rig-supplement-v1/supplement-seal.json': 'f833e88dffedc3fa2389e6fb73f5746607d56d72e7ebc4ffb6ed6b012b9f91f3',
    'reviews/criteria.json': 'dc420c15832f29f626b4d7de96bbb479450f4af0fd0ec140d44e0e80db3f15bc',
    'source/initial-observations.json': '7237baa4ebaf0c077351abe26ce3ba1d72205e27fb8feba62c302d80a36d89df',
}
for name, sha in bindings.items():
    assert digest(folder / name) == sha, name
manifests = []
resources = {}
for name, expected in [('reviews/preparation-v1/hashmanifest.json', 245), ('reviews/preparation-v1-rig-supplement-v1/hashmanifest.json', 9)]:
    manifest = read(folder / name)
    assert len(manifest['files']) == expected
    for record in manifest['files'] + manifest.get('dependencyReferences', []):
        resource = folder / record['path']
        assert digest(resource) == record['sha256'], record['path']
        assert resource.stat().st_size < 100_000_000, record['path']
        resources['prepared:' + record['path']] = record['path']
    manifests.append({'path': name, 'sha256': digest(folder / name), 'rootVerifiedFiles': expected})
proposal = read(folder / 'reviews/preparation-v1/proposed-root-native-contract.json')
criteria = read(folder / 'reviews/criteria.json')
plan = read(folder / 'reviews/preparation-v1/proposed-scoped-evidence-plan.json')
contract_path = folder / 'inputs/root-native-contract.json'
reconciliation_path = folder / 'inputs/root-preparation-reconciliation-v1.json'
backup_path = folder / 'inputs/brief-before-native-freeze.json'
assert not any(path.exists() for path in [contract_path, reconciliation_path, backup_path])
hard = [
    'Native creature-fish BODY only, generic friendly rounded cobalt/cyan blue fish/pale underside/whitecream eyes/navy pupils, coherent body-tail taper and dimensional fins/dorsal ridge. Useful native anatomy/proportion/topology/part/bone-count/form/detail/normal/material/light reconstruction authorized. Original12meshes/5bones/flat facets/thin fins and target exactdetail counts/gloss are not locks. Retarget allrequired actions if rig changes. Separate background fish silhouette and all13marked2D effects are excluded; do not generate/tune cable/projectile/eel effects.',
    'ROOT allphase native posed clearance budget: X/Y[-1.02,1.02],Z[.02,1.18],tol1e-5, proper all4 root rotations. This maximum accommodates actual compatible source motion XY±.944127/Z.039348..1.107549 with useful remodeling margin. It is not desired size/symmetry/amplitude/sourceAABB equality/perpart cage; preserve gross recognizable1x1 gameplay actor/hitcatch scale rather than filling the budget with a much larger fish. Metadata height.84 and occupied-cell mask are not literal mesh envelopes. Intentionally suspended, no feet/ground contact/support/fullcellopacity/modular port invented. No native/frame clipping.',
    'Both fresh roles independently found boneQUATERNION modes while all11actions key rotation_euler. Sealed supplemental actual source shows zero relativebone response, visible oldmotion is armatureobject only. Native compatibility repair is authorized: compatible Euler modes, correct quaternion action conversion or equivalent retarget, no mandatory XYZ implementation. Broken rigid-spine result/source numericamplitudes are not fidelity locks. All required native body actions must genuinely evaluate with attached eye/mouth/fins, no tearing/selfintersection; inspect evaluated matrices/vertices notEulerprops alone. Supplement corrects ambiguous original preparation deforming wording without rewriting sealed history.',
    'Keep all11clipIDs,12exportedphase slots/12fps/originalorder/eightloops plus hook/caught/escape one-shots. Preserve established calmnormal/strongerswim/aimpitch/restlessagitation/pursuiturgency/weaveturn/dashbeat/pausebob/hookstruggle/caughtlargerreaction/escapelift meanings. Saved native rig/catalog12frames take precedence over stale builder24text. Loops native13=1, exported12 is lastunique notforcedequal1; one-shots native12 held13/24, final returns initial after brief reaction under source semantics. Native easing/amplitudes/rigcounts free withinclearance; registered root no new actortranslation/travel, internalarmature bob/rotation allowed.',
    'Actual S33_CFX_creature-fish.001/root creature-fish__ground_root.001/constantinnerZ180; effective rootS0 E90 N180 W-90 and exact rootrelative metadata hook=cable(0,-.16,.56),nose(0,-.51,.44). No socketempties/physicaltether in source; retain useful accessible attachment region and projected four-facing markers, no moving sockets to fit target/no invented everyframe surface-marker intersection or submarine parenting/ground law. Four-facing normal/contact-extreme marker overlay uses existingmetadata/currentconsumer, not a solved cable interaction or separate effect work.',
    'Own CHARACTER35degree ORTHO3.5/HORIZONTAL/aspect1/shiftX0/Y.21428516507148743, cell128/world1. Logical448512/root224352/native4x17922048/root8961408/full authoredcanvasLANCZOS to2x8961024/root448704/original6x2atlas53762048/12rects. Measure real capturetime root/camera/effectivepose matrices allphase or truthful hashbound savedsource replay. Saved active1.5camera/7681280/environmental55not authority. No perviewfit/crop/warp/nudge/recolor/RGBalpha repair/targetcard. One reproducible nativefilter/color/material/lightrecipe all4, symmetric broad horizontal light/no preferredkey/directionalgroundcast. Old140/100W/world0/contrast1.35/rough.85/ramp are observations, not aesthetic targets.',
    'Freeze original independent three ranked visible outcomes and technical/motion outcomes: friendly coherent rounded fish/fins/dorsal all4; cobalt/cyan/pale eyes/underside and controlled soft plane light without chalkyglare/inertnavypatches/facetstripe; anchored separated expressive eyes/readablemouth/purposeful detail at logical/.4phone. Native continuous motion/attachments, no clipping/seams/blackdeadspots/halos/noisybanding. Fixedsingleview target aesthetic guide only, not unseenview/camera/registration/occupancy/leftglow. No numeric approval threshold or hash-only visual waiver.',
    'Retain all528 exact native4x required phase captures plus fullcanvas2xframes/atlases from exact editable savedsource. Measured everyphase raw/evaluated bounds, actual root/camera/ownership/rigrelativedeformation/face-finattachments/clipping,8loop13=1 and3terminal12=13=24 controls. Useful lossless allphase sheets/path-cell coverage, enlarge uncertain/extreme face/fin regions. Compact state/all4 actual12fps>=2.2s playback, root/socket overlays atnormal/contactextremes. Same current099/570 helpers/root/sourceScale/rects/order, logical/.4phone/lightgraydark/fullphone393852DPR1+wide logical/both actual supported153launchmodes/executables/options/version/errors. Honest native/CSS/configuration differences. RealRAF wrap/heldterminal and actualcompositor samples, not APNGdrawImage frozenframe/sparse video as fullproof. No528xbackgroundxviewport Cartesian, no arbitrary12decodedunique demand; everydeclared hero/preview gets originaljudge complete usefulpixel path/hash coverage.',
    'Minimal actualused private source/helper/module/input/instruction closure/editable Blender, files<100MB/no runtimeapplication trees/frozenpycache. Preserve untouchedoriginal/backup/target/initial/prep+rigsupplement/brief/criteria/priorversions. Editor owns source/candidates, judge reviews, ROOT seals/promotes/publishes. No editor/judge Git/index/production/deploy/liveBlender/device/sharedhelper/brief/review ownership change/extraagents/selfapproval/selfpacket. Unchanged integrity/direction/acceptance checks. NativeValidation supportedviews/captureRecords, optional nativeGeometryMeasurements facing->LISTframes; richotherledgers separatelybound, nevereditchecker/fabricate.'
]
reconciliation = {'asset': 'creature-fish', 'stage': 'ROOT reconciliation BEFORE construction', 'preparationManifests': manifests, 'freshEditorInitial': {'path': 'source/initial-observations.json', 'sha256': bindings['source/initial-observations.json']}, 'allphaseBudget': {'XY': [-1.02, 1.02], 'Z': [.02, 1.18], 'tolerance': 1e-5}, 'budgetRationale': 'Small margin beyond intended native compatibility-only motion; maxima not desired size/symmetry/amplitudes/perpart sourcebox. Preserve gross actor/hit scale. Actual original already exceeds nominal .84.', 'nativeRepair': 'Mode/channel mismatch independently observed by fresh roles and quantified with relativebone/vertex response. Allow correct native interpretation/retarget, no literalXYZ mandate or brokenrigid-spine fidelity. Original native/both preparation packets stay immutable.', 'suspensionAndAttachments': 'Floating actor/no support law. Exact rootspace metadata/socket markers retained; no everyframe geometryintersection/tether/effect requirement.', 'capture': 'Actual35degree squarepixel registered actor camera, native4x fullLANCZOS2x.44originalsampled replay cells exact, not528rerendered. Both consumer originalall528 coverage retained.', 'criteria': 'Original independent ranked outcomes and technical/motion outcomes frozen. No candidate/approval yet.'}
write(reconciliation_path, reconciliation)
contract = {'asset': 'creature-fish', 'version': 1, 'status': 'root-frozen-before-construction', 'sourceProposal': {'path': 'reviews/preparation-v1/proposed-root-native-contract.json', 'sha256': bindings['reviews/preparation-v1/proposed-root-native-contract.json']}, 'preparationManifests': manifests, 'nativeContract': proposal, 'hardConstraints': hard, 'reconciliation': reconciliation, 'requiredEvidence': plan}
write(contract_path, contract)
shutil.copyfile(folder / 'brief.json', backup_path)
brief = read(folder / 'brief.json')
previews = list(dict.fromkeys(['four-view-sheet', 'phone', 'repeated'] + brief['capture']['previews']))
brief['capture'].update(nativeFrame=[1792, 2048], nativeCaptureScale=4, publishedFrame=[896, 1024], publication='Uniform whole native4x canvas to published2x LANCZOS; original6x2 atlas, no fitting.', previews=previews)
brief['constraints']['nativeContract'] = str(contract_path.relative_to(folder))
brief['qualityCriteria'] = {'status': 'root-frozen-before-construction', 'definitionOfGood': 'Coherent friendly rounded blue fish, expressive integrated face/dimensional fins, controlled soft native light/readable lowers and genuinely evaluated attached body motion in every registered state/facing.', 'priorityOutcomes': criteria['priorityOutcomes'], 'technicalAndMotion': criteria['technicalAndMotion'], 'hardConstraints': hard, 'criteriaFile': 'reviews/criteria.json', 'criteriaFileSHA256': bindings['reviews/criteria.json'], 'nativeContract': str(contract_path.relative_to(folder)), 'nativeContractSHA256': digest(contract_path), 'preparationManifests': manifests, 'requiredEvidence': plan}
resources.update({name: name for name in bindings})
resources.update(rootNativeContract=str(contract_path.relative_to(folder)), preparationReconciliation=str(reconciliation_path.relative_to(folder)), freshEditorInitial='source/initial-observations.json')
brief.setdefault('technicalResources', {}).update(resources)
write(folder / 'brief.json', brief)
progress_path = run / 'progress.json'
progress = read(progress_path)
entry = next(row for row in progress['objects'] if row['id'] == 'creature-fish')
entry.pop('preparationJudge', None)
entry.update(status='editing', editor='catalog_creature_fish_editor_v1', judge='catalog_creature_fish_judge_v1', editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate', stage='native-fish-round01', briefSHA256=digest(folder / 'brief.json'))
write(progress_path, progress)
result = {'asset': 'creature-fish', 'scriptSHA256': digest(Path(__file__)), 'editorInitialSHA256': bindings['source/initial-observations.json'], 'rootVerifiedPreparationFiles': 245, 'rootVerifiedRigSupplementFiles': 9, 'briefSHA256': digest(folder / 'brief.json'), 'contractSHA256': digest(contract_path), 'reconciliationSHA256': digest(reconciliation_path)}
write(run / 'preparation/creature-fish/freeze-execution-v1.json', result)
print(json.dumps(result))
