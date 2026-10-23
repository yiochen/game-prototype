"""ROOT native suspended-fragment contract, frozen only after independent initial."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

run = Path(__file__).resolve().parents[2]
folder = run / 'objects/attack-reef-fragments'
read = lambda path: json.loads(path.read_text())
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


bindings = {'reviews/preparation-v1/seal.json': '3ef72d9be7525e7a72b1e83269de915f1fb4337cb5768fe9f33ba8d00dc1bf8d', 'reviews/preparation-v1/hash-manifest.json': 'f5680fbc14641545b87015283d29a6f647302bb873e8723a3352b8d483071209', 'reviews/criteria.json': 'e2c0d98309dac1eb96975170c38559f3ef805e14a62add271c36925ac69b49f5', 'reviews/preparation-v1/proposed-root-native-contract.json': 'ff5de8600673193aac9cc789e0f8f5027dae1706dc332fc6e7896186d6ecd21b', 'reviews/preparation-v1/evidence-plan.json': '6d2b9e0b4d0d118252cc2e9cbb718c536f0404a77310fe042d45660eb29d0c54'}
initial_sha = sys.argv[1]
bindings['source/initial-observations.json'] = initial_sha
for name, sha in bindings.items():
    assert digest(folder / name) == sha, name
manifest = read(folder / 'reviews/preparation-v1/hash-manifest.json')
assert len(manifest['files']) == 294
for record in manifest['files']:
    assert digest(folder / record['path']) == record['sha256'], record['path']
    assert (folder / record['path']).stat().st_size < 100_000_000
proposal = read(folder / 'reviews/preparation-v1/proposed-root-native-contract.json')
criteria = read(folder / 'reviews/criteria.json')
plan = read(folder / 'reviews/preparation-v1/evidence-plan.json')
cp = folder / 'inputs/root-native-contract.json'
rp = folder / 'inputs/root-preparation-reconciliation-v1.json'
bp = folder / 'inputs/brief-before-native-freeze.json'
assert not any(p.exists() for p in [cp, rp, bp])
hard = [
    'Native3D attack-reef-fragments suspended debris only, recognizable open scatter of distinct irregular chunky blue/cyan and violet/purple solids. Useful native forms/proportions/piece construction/structure/topology/count/decor/bevel/normal/material/light improvements authorized. Originalnine12vertex20faceicospherepieces/27objectactions/exacttargetshapes/tinychips/paintedstreaks not locks. All13annotated2D effects excluded, including other attack swirl/current/electrical effects.',
    'ROOT ALLPHASE canonicalS native clearance budget X[-1.20,1.20],Y[-1.20,1.20],Z[.04,.90],tol1e-5, properall4. Real original allview/evaluated sweepXY±1.144987464/Z[.080000006,.879327536] is baseline; nominal1x1footprint is registration metadata, not a literalXY±.5cage. New budget preserves burst scale/nominal.9height with room for useful shape/bevel changes. Maxima not desiredfills/symmetry/perpartAABB/oldexacttrajectories. Actual everyphase projectedgeometry must remain inside fixed registeredcanvas with transparentborder; axisbudget alone is not framecontainment proof.',
    'Effectorigin fixed world(0,0,0), no actorroottravel. Native debris stays suspended aboveZ0; no feet/supportcells/floor/contact/opacity/port/socket/attachment/modularjoin law or groundcast receiver. No invented physical submarine/eelconnection or repeatedtile fixture. Context neighbors establish presentation only. Useful transparent space between fragments, no accidental solidsurface/foundation.',
    'Actual raw scene S33 Native Asset Library Export/collection S33_CFX_attack-reef-fragments.001/root attack-reef-fragments__ground_root.001, properrootS0 E90 N180 W-90/world1/cell128. Own55.0079798degree ORTHO2.5/HORIZONTAL/aspect1.2206555605:1/shiftX0/Y.24576884508132935/logical320448/root160320/native4x12801792/root6401280/fullcanvasLANCZOSpublished2x640896/root320640/original6x2atlas38401792/rects/order/sourceScale2. Exact actual measured matrices/calibration bound in prep. Savedstartupcamera irrelevant. No crop/fit/warp/nudge/perviewcamera/color/RGBalpha repair/targetcard/runtimehelper edits.',
    'Exactly windup,active,recovery THREE ONE-SHOT IDs, each12publishedphases12fps/originalorder/consumerterminalframe11held, no loopclosing/duplicateframe mandate. Preserve functional progression: windup expansion/lift settling, active outward spreading/rotation, recovery farther spread with coherent strongshrink and quietheldterminal. Old exact perpieceamplitudes/trajectories/actionowner/count/10percentnumericendings/easing are descriptive, not new locks. Native methods may improve within role/origin/budget/cadence. No abruptscalejump/resetpop in required playback, no new motiontranslationofeffectorigin. Existing minimumUniqueFrames fromcatalog unchanged.',
    'Freeze full original independent criteria: distinct chunky irregular debris/mainfacet hierarchy/softeredges/coherent turningvolume allfacings/states; bluecyan/violetidentity with restrained optional warmcream/gold edgecrowns, readable colored lowers without blackwedges/flatuniformbrightness/bleachedareas/noisyspecularflicker; purposeful mineral/crystalline detail atlogical/.5phone/openreadablescatter/cleanrealtransparency. No clipping/halos/coplanarflicker/suddenpop/billboards. Fixedsingleview target guides aesthetics, not outlines/camera/distortedproportions/unseenviews/literalglow/count. No numeric scorethreshold/hash-only visualwaiver.',
    'One reproducible native material/light/color/capture recipe acrossall4, broad symmetric horizontal/no preferredkey/no directionalgroundshadow. Geometry/normals/bevel/shaders/material/light methods free, old Faceted watts/world0/roughness/ramp/sRGBcontrast1.35 not stylemandates. Allfinalpixels come from editable native scene, no postexportpaint/warp/alphaRGBcleanup/targetprojection/sharedchecker/helperchange.',
    'Required144actualnative4x/fullcanvas2xframes/12originalatlases from immutable savedsource with actual rawauthored/evaluated allphasegeometry/camera/root/actions/ownership/suspension/containment and native terminalhold evidence, correct all3savedclips. Compact complete usefulpixel allphase sheets/path-cell maps/enlarged uncertain facets/extrema/terminals. Same exact099/570 currentconsumerhelpers/root/rects/order/sourceScale, both actual153headless modes/DPR1/1280900/logical320448/phone160224/lightgraydark scopedframe5representatives and actual complete12fps allclip/allfacingplayback through terminalclamp. Honest native/CSS/mode/resampling/dither residuals, no APNGdefaultframe/sparse sampling substitute/new144xviewportCartesian/redundantvideo study. Existing original replay144decodedexactafterreduction, historical4xrawsource-captures absent; retainhonest rawparityunavailable, do not claim historicalnativeexactness.',
    'Remove stale generic repeated-grid requiredpreview beforeconstruction; required four-view-sheet,phone,motion plus windup-N/E/S/W,active-N/E/S/W,recovery-N/E/S/W aliases. Each declared preview must receive originaljudge complete usefulpixel/path/hash coverage; exactsharedpath aliases permitted only explicit mapping. NativeValidation supportedviews/captureRecords; optionalgeometryfacing->LISTframes, richledgers separatelybound. No fabricatedfields/modifiedgates. Utilityconsumer fixture not fullReact/Godot/deviceintegration.',
    'Originalsource/backup/target/preps/initial/criteria/brief/frozeninputs/priorversions immutable; minimal actualused editablehelper/module/input/instruction closure/allfiles<100MB/no runtimeapptrees/frozenpycache. Editor source/candidates only, judge reviews only, ROOT freeze/seal/promote/publish. No extraagents/Git/index/production/device/liveBlender/targetregen/briefreviewownership/sharedhelperedits/selfpacket/selfapproval. Unchanged integrity/direction/acceptance gates.'
]
recon = {'asset': 'attack-reef-fragments', 'stage': 'ROOT reconciliation before construction', 'preparation': {'path': 'reviews/preparation-v1/hash-manifest.json', 'sha256': bindings['reviews/preparation-v1/hash-manifest.json'], 'rootVerifiedFiles': 294}, 'freshEditorInitial': {'path': 'source/initial-observations.json', 'sha256': initial_sha}, 'canonicalSAllphaseBudget': {'X': [-1.20,1.20], 'Y': [-1.20,1.20], 'Z': [.04,.90], 'tolerance': 1e-5}, 'rationale': 'Real suspendedburst sweep exceeds nominal1x1; retain gross burst scale and.9height with useful native geometry allowance and independent actualcanvascontainment. No oldpieceAABB/trajectory/count lock or grow-to-fill target.', 'support': 'Floatingeffectorigin, no nativecontacts/support/floor/ports/sockets/attachments/modularfamily fixture.', 'motion': '12phase12fps windup/active/recovery nonloops with quiet terminalclamp; functional progression retained, native amplitudes/counts/easing/endshrink may improve within envelope, no numeric10percentmandate.', 'provenance': 'One original144native replay yields all current atlaspixels decodedexact afterfullLANCZOS4xto2x. Historical referenced4xsourcecaptures absent, parity unavailable; guides/source/actualusedreplaydrivers retained honestly.', 'criteria': 'Full original independent criteria frozen before candidate, no approval.'}
write(rp, recon)
write(cp, {'asset': 'attack-reef-fragments', 'version': 1, 'status': 'root-frozen-before-construction', 'sourceProposal': {'path': 'reviews/preparation-v1/proposed-root-native-contract.json', 'sha256': bindings['reviews/preparation-v1/proposed-root-native-contract.json']}, 'nativeContract': proposal, 'hardConstraints': hard, 'reconciliation': recon, 'requiredEvidence': plan})
shutil.copyfile(folder / 'brief.json', bp)
brief = read(folder / 'brief.json')
previews = ['four-view-sheet','phone','motion'] + [clip+'-'+direction for clip in ['windup','active','recovery'] for direction in 'NESW']
brief['capture'].update(nativeFrame=[1280,1792], nativeCaptureScale=4, publishedFrame=[640,896], publication='Uniform full native4x canvas to published2x LANCZOS, original6x2atlas; no fitting.', previews=previews)
brief['constraints']['nativeContract'] = str(cp.relative_to(folder))
brief['qualityCriteria'] = {'status': 'root-frozen-before-construction', 'definitionOfGood': 'Distinct irregular chunky bluecyan/violet floating debris, broad soft native facets/edgevolume/readablecoloredlowers, open readable windup/burst/recoveryshrink in all registered views.', 'independentCriteria': criteria, 'hardConstraints': hard, 'criteriaFile': 'reviews/criteria.json', 'criteriaFileSHA256': bindings['reviews/criteria.json'], 'nativeContract': str(cp.relative_to(folder)), 'nativeContractSHA256': digest(cp), 'preparationManifestSHA256': bindings['reviews/preparation-v1/hash-manifest.json'], 'requiredEvidence': plan}
resources = brief.setdefault('technicalResources', {})
resources.update(rootNativeContract=str(cp.relative_to(folder)), preparationReconciliation=str(rp.relative_to(folder)), freshEditorInitial='source/initial-observations.json')
for name in bindings:
    resources['bound:' + name] = name
for record in manifest['files']:
    resources['prepared:' + record['path']] = record['path']
write(folder / 'brief.json', brief)
progress = read(run / 'progress.json')
entry = next(x for x in progress['objects'] if x['id'] == 'attack-reef-fragments')
entry.pop('preparationJudge', None)
entry.update(status='editing', editor='catalog_attack_reef_fragments_editor_v1', judge='catalog_attack_reef_fragments_judge_v1', editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate', stage='native-reef-fragments-round01', briefSHA256=digest(folder / 'brief.json'))
write(run / 'progress.json', progress)
receipt = {'asset': 'attack-reef-fragments', 'scriptSHA256': digest(Path(__file__)), 'editorInitialSHA256': initial_sha, 'rootVerifiedPreparationFiles': 294, 'briefSHA256': digest(folder / 'brief.json'), 'contractSHA256': digest(cp), 'reconciliationSHA256': digest(rp)}
write(run / 'preparation/attack-reef-fragments/freeze-execution-v1.json', receipt)
print(json.dumps(receipt))
