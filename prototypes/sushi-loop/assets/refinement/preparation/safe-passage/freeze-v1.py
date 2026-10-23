"""ROOT freeze of independently measured small nonblocking passage-flank scenery."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

run = Path(__file__).resolve().parents[2]
folder = run / 'objects/safe-passage'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


bindings = {'reviews/preparation-v1/seal.json': '3c2aa47f7b5bc2d7a638e47572090e363251e4171706379a6e05bef45277924f', 'reviews/preparation-v1/hash-manifest.json': '657f028dfa88507e164e6096ce87a3928b3b0dcbd850b7134ed9aa6e2d507d70', 'reviews/criteria.json': 'fb9c07a40cedb50c4d75ae1887ac8a9dd51f25799c0f99761e3ee3adcdb4137a', 'reviews/preparation-v1/root-native-contract.json': '882db6958ac95c27f1c4785b66d77cc874e98bc0d78d11ba9d18ba7225943ea5', 'reviews/preparation-v1/scoped-evidence-plan.json': '1be22c6595d0339d5d8934df363449fc74c8499b398f359174d33372970aa1af'}
initial_sha = sys.argv[1]
bindings['source/initial-observations.json'] = initial_sha
for name, sha in bindings.items():
    assert digest(folder / name) == sha, name
manifest = read(folder / 'reviews/preparation-v1/hash-manifest.json')
assert len(manifest['files']) == 309
for record in manifest['files']:
    assert digest(folder / record['path']) == record['sha256'], record['path']
    assert (folder / record['path']).stat().st_size < 100_000_000
proposal = read(folder / 'reviews/preparation-v1/root-native-contract.json')
criteria = read(folder / 'reviews/criteria.json')
plan = read(folder / 'reviews/preparation-v1/scoped-evidence-plan.json')
contract_path = folder / 'inputs/root-native-contract.json'
recon_path = folder / 'inputs/root-preparation-reconciliation-v1.json'
backup_path = folder / 'inputs/brief-before-native-freeze.json'
assert not any(p.exists() for p in [contract_path, recon_path, backup_path])
hard = [
    'Safe-passage is native nonblocking underwater passage-flank scenery: two distinguishable blue stone masses, meaningful rooted thick green foliage and three separate shallow cyan guide marks on the lane-facing side. Retain identity/palette/gross small1x1scale, not original14mesh/9kelp-piece topology/count/exact outlines/coordinates. Useful native shape/proportion/structure/decoration/count/bevel/normal/material/light improvements allowed. All13annotated2D effects excluded.',
    'ROOT canonicalS ALLPHASE maximum native design budget X[-.5,.5],Y[-.5,.5],Z[-.05,.53],tol1e-5, properly rotated all4. Use metadata1x1/.53height as functional size budget around measured allphase±.493108/X, .355647/Y and maxZ.47402945, not exact original perpartAABB. Clearance maxima not desired fill/symmetry/target dimensions. No growth outside registered frame, transparent border preserved.',
    'Finite nativeZ0 contact and stable stone support role retained every phase. Intentional original stone embedding-.05/-.03 allowed, not an automatic defect. Exact pentagonal sections/areas/count/native oldhulls notlocks, no opaque fullcell floor/foundation. Foliage coherent rooted or attached to stone through all calm motion; no detached tips/basal pieces or accidental hardintersections. Three readable separate cyan near-ground native marks stay stable and shallow, their exact oldbox vertices/XYZ coordinates not locks. No invented attachmentports.',
    'Actual untouched source scene S33 Native Asset Library Export/collection S33_PROP_safe-passage.001/root safe-passage__root.001. Initial ROOT dispatch mistakenly named nonexistent Sushi33 Native Library; preserve failed probe and versioned clarification, do not use stale hidden matrices. Background executable /opt/homebrew/bin/blender/version5.2.2LTS separately. Actual nativecapture own55.0079798degree ORTHO1.5/HORIZONTAL/aspect1.2206555605:1/exact measured shifts and matrices bound in reviews/preparation-v1/camera-measured.json and proposal. Logical192352/root96248/native4x7681408/root384992/fullcanvasLANCZOSpublished2x384704/root192496/original6x2atlas23041408/rects/order/sourceScale2. ProperrootS0 E90 N180 W-90/world0. No savedstartupcamera inference/perviewfit/crop/warp/nudge/recolor/RGBalpha repair/targetcard.',
    'Exactly ambient12publishedphase slots12fps/one-secondLOOP/originalorder/nativeclosing13=1 excluded from atlas; not stale builder24frames. Calm naturally moving rooted foliage, stable stones/threeguides/root. Original9transformactionowner/count/amplitudes/easing free, equivalent visible role required with actual saved native actions/evaluatedgeometry/attachment/bounds and loopclosing evidence. Existing catalogminimumUniqueFrames6 retained; source12unique is observation, not a new exact image-uniqueness threshold. No forced published12=1.',
    'Freeze all original independent visible criteria: deliberate soft blue rock volumes/two separated meaningful masses, layered thick green foliage, three legible cyan marks; luminous blue/yellowgreen highlight planes/readable lower blues without navyblack holes; controlled broad soft highlights/no favored horizontal key, deliberate mineral/leaf volume detail atlogical/.5phone, coherent all4includingE/W, calm clean attached foliage with no wrap pop. No blackdeadspots/halos/noisymicrotexture/clipping/tangentbrokenjoins/zfight/exposed mechanicalseams. Targetsingleview aestheticguide, not pixeloutline/leftglow/paintedhalos/unseenviews/count rule. No numeric approval threshold.',
    'One reproducible native lighting/material/capture recipe across all4, symmetric broad horizontal/no preferredkey/no directional groundcast. Native geometry/normals/bevel/shader/material/light methods free; old Faceted watts/world0/contrast1.35/ramp/roughness notlocks. Preserve editable source and native usedresourceclosure, never paint/warp/clean RGBalpha postexport or edit shared consumer/checkers.',
    'All48native4x/fullcanvas2x/4originalatlases exactfrom immutable savedsource, separate actual rawauthored/evaluated allphasegeometry/camera/root/light/material/ownership/contact/attachments/clipping and closing13controls. Compact fullframe usefulpixel phase sheets/path-cell maps plus enlarged uncertain regions. Exact current099/570 consumerhelpers/root/rects/order/sourceScale, BOTH actual153headless modes, actual12fps two-loop playback≥2.2s/phaseorder/wrap/errors and representative allviews logical/lightgraydark/DPR1/900420 and phoneuniform.5/lightgraydark/DPR2/390480 as original scoped preparation. Honest native/CSS/mode/dither residuals. No APNGdefaultframe/sparse sampling substitute/new48xviewportCartesian/redundantvideo studies.',
    'compositionContext minimumClearLaneCells3/mirroredFlankRoot[3,0,0] and nonblocking metadata remain unchanged declarative presentation. Catalog actual routefixture places safeS at(0,1), shipNtravel at(3,0); this establishes presentation scale, not an authored physicalcollision/access/attachment mechanic. Do not turn root spacing3 into a contradictory literal3world-unit empty mesh interval, create negative-scale mirrors or invent fullcell floor/seam/ground opacity law. No required siblinggeometry reuse/three-by-threegrid/extra physical familyfixture. Preserve transparent neighboring lane space within actual1x1role.',
    'Before construction remove stale nonfunctional repeated-grid preview; required aliases four-view-sheet,phone,motion,ambient-N/E/S/W. NativeValidation supportedviews/captureRecords, optional nativeGeometryMeasurements facing->LISTframes, richer ledgers separatelybound. Every declared hero/preview originaljudge usefulpixel/path/hash coverage. Missing visual/native evidence notapproval; utilityfixture not fullReact/Godot/device.',
    'Editor owns source/candidates; judge reviews; ROOT brief/freeze/seal/promote/publish. Originalsource/backup/target/preps/initial/criteria/frozeninputs/priorversions immutable. Minimal actualused dependencyclosure/allfiles<100MB/no runtimeapptrees/frozenpycache. No extraagents/Git/index/production/deploy/device/liveBlender/sharedhelper/target regeneration/selfpacket/selfapproval/modeloriginal edits. Unchanged integrity/direction/acceptance checks.'
]
recon = {'asset': 'safe-passage', 'stage': 'ROOT reconciliation before construction', 'preparation': {'path': 'reviews/preparation-v1/hash-manifest.json', 'sha256': bindings['reviews/preparation-v1/hash-manifest.json'], 'rootVerifiedFiles': 309}, 'freshEditorInitial': {'path': 'source/initial-observations.json', 'sha256': initial_sha}, 'canonicalSAllphaseBudget': {'X': [-.5,.5], 'Y': [-.5,.5], 'Z': [-.05,.53], 'tolerance': 1e-5}, 'budgetRationale': 'Functional1x1/.53 metadata budget with real finite supports and deliberate modeling freedom; measuredoldbounds not exact locks, maxima not target fills.', 'support': 'Stable finiteZ0 stones, intentional original negative embedding allowed, coherent foliage and shallow stable cyan marks; no hullarea/count/shape/fullfloor law.', 'motion': 'Actual12phase12fps ambientloop13=1, not stale builder24. Native methods/count/amplitudes free; existingminimumUniqueFrames6 retained, not source12 exactuniqueness mandate.', 'composition': 'Nonblocking presentation metadata3cells/root[3,0,0] retained; catalogbesideship context only, no realcollision/access/attachment/seam contract or invented literal3unit empty meshgap.', 'sourceProvenance': 'Existing baked original actions replayed with actually used adapter, whose hash differs from historical baker. No rebake provenance fiction. Correct raw scene S33 Native Asset Library Export; wrong firstdispatch/failedprobe preserved with clarification.', 'criteria': 'Original full independent criteria frozen before construction. No candidate approval.'}
write(recon_path, recon)
write(contract_path, {'asset': 'safe-passage', 'version': 1, 'status': 'root-frozen-before-construction', 'sourceProposal': {'path': 'reviews/preparation-v1/root-native-contract.json', 'sha256': bindings['reviews/preparation-v1/root-native-contract.json']}, 'nativeContract': proposal, 'hardConstraints': hard, 'reconciliation': recon, 'requiredEvidence': plan})
shutil.copyfile(folder / 'brief.json', backup_path)
brief = read(folder / 'brief.json')
brief['capture'].update(nativeFrame=[768,1408], nativeCaptureScale=4, publishedFrame=[384,704], publication='Uniform whole native4x canvas to published2x LANCZOS; original6x2atlas; no fitting.', previews=['four-view-sheet','phone','motion','ambient-N','ambient-E','ambient-S','ambient-W'])
brief['constraints']['nativeContract'] = str(contract_path.relative_to(folder))
brief['qualityCriteria'] = {'status': 'root-frozen-before-construction', 'definitionOfGood': 'Readable deliberate blue stone masses, thick rooted green foliage and three stable separate cyan marks, broad warm-soft native volume light and clean calm allview motion.', 'independentCriteria': criteria, 'hardConstraints': hard, 'criteriaFile': 'reviews/criteria.json', 'criteriaFileSHA256': bindings['reviews/criteria.json'], 'nativeContract': str(contract_path.relative_to(folder)), 'nativeContractSHA256': digest(contract_path), 'preparationManifestSHA256': bindings['reviews/preparation-v1/hash-manifest.json'], 'requiredEvidence': plan}
resources = brief.setdefault('technicalResources', {})
resources.update(rootNativeContract=str(contract_path.relative_to(folder)), preparationReconciliation=str(recon_path.relative_to(folder)), freshEditorInitial='source/initial-observations.json')
for name in bindings:
    resources['bound:' + name] = name
for record in manifest['files']:
    resources['prepared:' + record['path']] = record['path']
write(folder / 'brief.json', brief)
progress = read(run / 'progress.json')
entry = next(x for x in progress['objects'] if x['id'] == 'safe-passage')
entry.pop('preparationJudge', None)
entry.update(status='editing', editor='catalog_safe_passage_editor_v1', judge='catalog_safe_passage_judge_v1', editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate', stage='native-safe-passage-round01', briefSHA256=digest(folder / 'brief.json'))
write(run / 'progress.json', progress)
receipt = {'asset': 'safe-passage', 'scriptSHA256': digest(Path(__file__)), 'editorInitialSHA256': initial_sha, 'rootVerifiedPreparationFiles': 309, 'briefSHA256': digest(folder / 'brief.json'), 'contractSHA256': digest(contract_path), 'reconciliationSHA256': digest(recon_path)}
write(run / 'preparation/safe-passage/freeze-execution-v1.json', receipt)
print(json.dumps(receipt))
