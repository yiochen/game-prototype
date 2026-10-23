"""ROOT reconciliation of independent portal-entry preparation before construction."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

run = Path(__file__).resolve().parents[2]
folder = run / 'objects/portal-entry'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


initial_sha = sys.argv[1]
bindings = {
    'reviews/preparation-v1/seal.json': '0b93339deb7350d37d013af28df9d4e737f87b539311ef3d3f0f218ab96dd373',
    'reviews/preparation-v1/hashmanifest.json': 'e062d8565e1250a8de8b761c5e170d816bc858f48c3bc369b1e09c314c6e2022',
    'reviews/criteria.json': '92969b4de70194d82b73d7f6b4c58b52546643bb509d4da73437dca7dd46d8cc',
    'reviews/preparation-v1/root-native-contract.proposed.json': '62734df920423da0cc2bf0f4977791d91415d309aaadebbd05e979566c1ebaae',
    'reviews/preparation-v1/evidence-plan.json': 'c9e3e5721ace12e5e50233ba6c52877c1a570704e29e5acafe96a3b65f139304',
    'source/initial-observations.json': initial_sha,
}
for name, sha in bindings.items():
    assert digest(folder / name) == sha, name
manifest = read(folder / 'reviews/preparation-v1/hashmanifest.json')
assert len(manifest['files']) == 202
for record in manifest['files']:
    assert digest(folder / record['path']) == record['sha256'], record['path']
    assert (folder / record['path']).stat().st_size < 100_000_000
proposal = read(folder / 'reviews/preparation-v1/root-native-contract.proposed.json')
criteria = read(folder / 'reviews/criteria.json')
plan = read(folder / 'reviews/preparation-v1/evidence-plan.json')
contract_path = folder / 'inputs/root-native-contract.json'
recon_path = folder / 'inputs/root-preparation-reconciliation-v1.json'
backup_path = folder / 'inputs/brief-before-native-freeze.json'
assert not any(p.exists() for p in [contract_path, recon_path, backup_path])
hard = [
    'Native portal-entry cyan/blue upright OPEN ring with stable navy support groups and deliberate blue activation accents. Optional restrained small warmgold/neutral construction accents remain subordinate to cyan/aqua dominant and navy support identity. Useful native form/proportion/topology/structure/decoration/partcount/material/bevel/normal/light changes authorized. Old two torus/eight rune/two rock/12mesh counts and exact target outlines/streaks are not locks. No opaque disk/artificial alpha aperture/camera-facing card. All13marked2D effects excluded.',
    'ROOT adopts canonicalS ALLPHASE clearance budget X[-.74,.74],Y[-.30,.30],Z[-.06,1.50],tol1e-5, properly rotated all4. Source sweepX±.7296767/Y[-.182660,.242660]/Z[-.06,1.4696767] is baseline, not perpart equality. Small activation allowance retains original occupied scale/1.48nominalheight and fixed frame; purposeful side depth/reconstruction allowed. Maxima are not desired size/symmetry/fill targets. Preserve transparent frame border/no clipping.',
    'Stable finite nativeZ0 support role remains in every phase; original rocks intentionally straddleZ0 with min-.06, embedding permitted. Coherent finite support-to-ring construction, no floating fixed feet. Original exact two hull shapes/areas/contact coordinates/meshcount are not locks and no fullcell floor opacity/groundpatch/foundation required. Entrycenter rootrelative(0,0,.74) fixed, coherently inside real open aperture; projected allviews(0,-66.3040271)logical. Useful opening/physical side thickness, no invented ship passage/access collision/docking/support/attachment mechanics.',
    'Actual S33_PROP_portal_rim.003/root portal_rim__root.003/scene S33 Native Asset Library Export, worldroot0/properS0 E90 N180 W-90. Own55.0079798degree ORTHO1.5/HORIZONTAL/aspect1.2206555605:1/shiftX0/Y.4096146523952484/world1/cell128/logical192384/root96288/native4x7681536/root3841152/fullcanvasLANCZOSpublished2x384768/root192576/original6x2atlas23041536/rects/order/sourceScale2. Savedstartup charactercamera unrelated. Physical E/W edge views remain coherent, no billboarding/perviewfit/crop/warp/shift/recolor/RGBalpha repair.',
    'Exactly one enter ONE-SHOT clip,12publishedphases12fps/originalphaseorder, consumer clamps terminal frame11. No forcedloop/duplicateclosureframe requirement. Pulse/orbit reads as purposeful activation; support/root/entrycenter stable. Native actionowner/names/counts/amplitudes/angles/easing free within role and clearance. Existing catalog minimumUniqueFrames6 retained, not new arbitrary score. Save actual native actions/required48phase source replays and terminalhold proof honestly, not property-only/manifest-only claims.',
    'Freeze full original independent criteria: substantial continuous rounded cyan rim/layered native structure/convincing support transitions; cyan/navy hierarchy and restrained warm construction detail; organized broad soft highlights/readable lowerfaces/navy support facets without blackdeadspots/blownplates/electricflatbands; coherent front/back and physical E/W depth; clean meaningful detail atlogical/.5phone and allphase activation. No floating/piercing/coplanar seams/shimmering/tangentjoins/clipping/halos/disappearingprofile. Fixedsingleview target guides aesthetics, not literal camera/proportions/paintedglow/unseenviews/old counts. No numeric approval threshold.',
    'One reproducible native material/color/light/capture recipe across all4; broad symmetric horizontal light/no preferredkey/no directional groundshadow. Geometry/normals/shaders/bevels/material/light are methods, oldwatts/contrast/roughness not locks. Preserve own editable source/actualused minimalhelperclosure and original backups. No painted target projection, postexport repaint/warp/RGBalpha cleanup/runtimehelper change.',
    'Required all48native4x/fullcanvas2x/4originalatlases with actual rawauthored/evaluatedgeometry/camera/root/ownership/contact/opening/clipping ledger and fullpixel allview/allphase sheets/path-cell maps, enlarged uncertain details. Same exact current099/570 consumer helpers/root/rects/order/sourceScale, logical192384/.5phone96x192/lightgraydark, bounded0/5/11representatives all4 plus actual full12phase12fps oneshot/settledhold in both actual153headlessmodes/DPR1/executable/options/version/errors. Retain native nearest aftercommoncanvasresize thenwholeCSSfilter, honest mode/native/CSS residuals; APNGdefaultframe/sparse sampling not complete playbackproof. No new48xviewport/backgroundCartesian/redundantstudies.',
    'Portal-rim and portal-entry share legacy nativebuilder and visualfamily only; no established physicalsocket/modularjoin/accessmechanic. Fresh independent editor first interpretation remains uncontaminated. No exact siblinggeometry/material/recipe copy mandate or approval transfer. Shared palette/role coherence matters; no extra family fixture required absent actual functional coupling. Separate submarine presentation establishes scale context only.',
    'Required previewaliases four-view-sheet,phone,motion,enter-N/E/S/W; remove stale nonfunctional repeated-grid preview before construction. NativeValidation must use supported views/captureRecords; optional nativeGeometryMeasurements facing->LISTframes, richer ledgers separatelybound. Never modify gate or fabricate measurements. Every declared media usefulpixel/path/hash coverage by originaljudge; missingevidence not approval. Utilityfixture is not fullReact/Godot/deviceintegration.',
    'Editor owns source/candidates only; judge reviews only; ROOT owns brief/freeze/seal/promote/publish. Allfiles<100MB/minimalactualusedclosure/no runtimeapptrees/frozenpycache. Originalsource/backup/target/preps/initial/criteria/frozeninputs/priorrounds immutable. No extraagents/Git/index/production/deploy/device/liveBlender/sharedhelpers/target regeneration/selfapproval/selfpacket edits by editor orjudge. Unchanged integrity/direction/acceptance checks.'
]
recon = {'asset': 'portal-entry', 'stage': 'ROOT reconciliation before construction', 'preparation': {'path': 'reviews/preparation-v1/hashmanifest.json', 'sha256': bindings['reviews/preparation-v1/hashmanifest.json'], 'rootVerifiedFiles': 202}, 'freshEditorInitial': {'path': 'source/initial-observations.json', 'sha256': initial_sha}, 'canonicalSAllphaseBudget': {'X': [-.74, .74], 'Y': [-.30, .30], 'Z': [-.06, 1.50], 'tolerance': 1e-5}, 'rationale': 'Preserve registered scale and original active sweep, allowing slight activation/side-depth/modeling improvement. Clearance maxima not desired dimensions or exact original bounds. FiniteZ0 supports/intentional-.06embedding/openentry retained, no old hull/area/count/fullfloor law.', 'palette': 'Cyan/aqua dominant, blue/navy structural anchors, restrained subordinate warmgold/neutral craft accents permitted by fixed target.', 'motion': '12phase12fps enter ONE-SHOT plus consumer terminalhold, no forcedclosureloop. Native method/count/easing free; supports/root/entrycenter stable.', 'family': 'Shared original portalbuilder visualfamily only; no exact siblingrecipe/geometry mandate or invented access/attachment/seam fixture.', 'criteria': 'Freeze original independent full criteria, comparative scores only. No candidate approval.'}
write(recon_path, recon)
contract = {'asset': 'portal-entry', 'version': 1, 'status': 'root-frozen-before-construction', 'sourceProposal': {'path': 'reviews/preparation-v1/root-native-contract.proposed.json', 'sha256': bindings['reviews/preparation-v1/root-native-contract.proposed.json']}, 'nativeContract': proposal, 'hardConstraints': hard, 'reconciliation': recon, 'requiredEvidence': plan}
write(contract_path, contract)
shutil.copyfile(folder / 'brief.json', backup_path)
brief = read(folder / 'brief.json')
brief['capture'].update(nativeFrame=[768,1536], nativeCaptureScale=4, publishedFrame=[384,768], publication='Uniform whole native4x canvas to published2x LANCZOS, original6x2atlas; no fitting.', previews=['four-view-sheet','phone','motion','enter-N','enter-E','enter-S','enter-W'])
brief['constraints']['nativeContract'] = str(contract_path.relative_to(folder))
brief['qualityCriteria'] = {'status': 'root-frozen-before-construction', 'definitionOfGood': 'Substantial coherent native cyan/blue open portal, stable dimensional navy supports, restrained subordinate warm craftsmanship and broad soft readable volume light; clean purposeful one-shot activation in all registered views.', 'independentCriteria': criteria, 'hardConstraints': hard, 'criteriaFile': 'reviews/criteria.json', 'criteriaFileSHA256': bindings['reviews/criteria.json'], 'nativeContract': str(contract_path.relative_to(folder)), 'nativeContractSHA256': digest(contract_path), 'preparationManifestSHA256': bindings['reviews/preparation-v1/hashmanifest.json'], 'requiredEvidence': plan}
resources = brief.setdefault('technicalResources', {})
resources.update(rootNativeContract=str(contract_path.relative_to(folder)), preparationReconciliation=str(recon_path.relative_to(folder)), freshEditorInitial='source/initial-observations.json')
for name in bindings:
    resources['bound:' + name] = name
for record in manifest['files']:
    resources['prepared:' + record['path']] = record['path']
write(folder / 'brief.json', brief)
progress = read(run / 'progress.json')
entry = next(x for x in progress['objects'] if x['id'] == 'portal-entry')
entry.pop('preparationJudge', None)
entry.update(status='editing', editor='catalog_portal_entry_editor_v1', judge='catalog_portal_entry_judge_v1', editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate', stage='native-portal-entry-round01', briefSHA256=digest(folder / 'brief.json'))
write(run / 'progress.json', progress)
receipt = {'asset': 'portal-entry', 'scriptSHA256': digest(Path(__file__)), 'editorInitialSHA256': initial_sha, 'rootVerifiedPreparationFiles': 202, 'briefSHA256': digest(folder / 'brief.json'), 'contractSHA256': digest(contract_path), 'reconciliationSHA256': digest(recon_path)}
write(run / 'preparation/portal-entry/freeze-execution-v1.json', receipt)
print(json.dumps(receipt))
