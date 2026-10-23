from pathlib import Path
import argparse, hashlib, json, shutil

parser=argparse.ArgumentParser()
parser.add_argument('--editor-initial-sha',required=True)
args=parser.parse_args()
run=Path(__file__).resolve().parents[2];folder=run/'objects/wreck-end'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2)+'\n')
mp=folder/'reviews/preparation-v1/manifest.json'
assert sha(mp)=='c4df843ec24c036478282827c036be521610935be4b92e5c40f77959c55ae93d'
m=read(mp);assert len(m['files'])==362
for f in m['files']:
    p=folder/f['path'];assert sha(p)==f['sha256'] and p.stat().st_size<100_000_000,f['path']
initial=folder/'source/initial-observations.json'
assert len(args.editor_initial_sha)==64 and sha(initial)==args.editor_initial_sha
pp=folder/'reviews/source-contract-proposal.json';cp=folder/'reviews/proposedcriteria.json';ep=folder/'reviews/preparation-v1/evidence-plan.json'
assert sha(pp)=='f5a451bbc1a9d387bc09ffc6e99f6ddf003278ae6fb82163268130d6ef63f0f6'
assert sha(cp)=='cae1568c32f258a336543a135fbdc6b83f59d4a33653f0517c7b13712f0035fc'
assert sha(ep)=='d212567cda0a611c6422934da1dc08931f7a829cb803a9ba3b73d24a5ccd1faf'
proposal,criteria,plan=read(pp),read(cp),read(ep)
assert len(proposal['authoringBudgetProposal']['rawXYOutlineCCW'])==8
assert len(proposal['finiteSupport']['unionXYApprox'])==8
contract_path=folder/'inputs/root-native-contract.json';recon_path=folder/'inputs/root-preparation-reconciliation-v1.json'
binding_path=folder/'inputs/approved-wreck-authorities-v1.json';backup=folder/'inputs/brief-before-native-freeze.json'
assert not any(p.exists() for p in [contract_path,recon_path,binding_path,backup])
expected={
    'wreck-middle':('d44748684c4e13a25bfd7e28fe5862232ccb8b0d11d530cd9702ea66f525d46c','f371a2509c600cce6b4f53223aa6c0ed546a9db00b79ffcc78dc8fb710b68005','6f06d28d217abe29bff3ceaa672814a1233553b87a856f54afb4d28a1a33ac76'),
    'wreck-edge':('a7f8357632d42d3f5113f7ee3b423634bdd834e0d3cbfb9a058ea513767a1498','7fe4e36723fe87bea1a94d12f9b85e62b4cafffcc0e34b814b3298e8866aaae1','aea556e4669f9a9d57bd92d02de484d00a225934d5705a5124683a444c993f58')}
authorities={}
for asset,(source_sha,packet_sha,review_sha) in expected.items():
    base=folder/'reviews/preparation-v1/resources/canonical'/asset
    source=base/'native.blend';packet=base/'packet.json';review=base/'review.json'
    assert sha(source)==source_sha and sha(packet)==packet_sha and sha(review)==review_sha
    pkt,receipt=read(packet),read(review)
    assert receipt['verdict']=='approve' and not receipt['blockers'] and receipt['candidatePacketSHA256']==packet_sha
    assert pkt['files']['candidateProject']['sha256']==source_sha
    records={'source':source,'packet':packet,'review':review}
    for facing,descriptor in pkt['candidateRenders'].items():
        matches=[folder/f['path'] for f in m['files'] if f['path'].startswith(str(base.relative_to(folder))+'/') and f['path'].endswith('.png') and f['sha256']==descriptor['sha256']]
        assert matches,(asset,facing)
        records['hero-'+facing]=sorted(matches)[0]
    authorities[asset]={key:{'path':str(p.relative_to(folder)),'sha256':sha(p)} for key,p in records.items()}
write(binding_path,{'asset':'wreck-end','authorities':authorities,'scope':'Exact approved native technical fields/rig/capture and individual art only. Corner remains unapproved at freeze; no corner/full-familyL dependency or family approval.'})
recon={
    'asset':'wreck-end','stage':'root reconciliation BEFORE construction',
    'preparation':{'path':str(mp.relative_to(folder)),'sha256':sha(mp),'rootVerifiedFiles':362},
    'freshEditorInitial':{'path':str(initial.relative_to(folder)),'sha256':sha(initial)},
    'authoringEnvelope':{'decision':'Adopt own RAW eight-point XY authoring hull extrudedZ[.04,.78]/tol1e-6, proper-rotated all4. Actual enabled transformed raw vertices govern; evaluated bevel trim and actual top.76 are observations, not tighter locks. No middle/corner AABB/perpart boxes/3Dhull/count/old blankness constraints.','xy':proposal['authoringBudgetProposal']['rawXYOutlineCCW'],'z':[.04,.78],'tolerance':1e-6},
    'finiteSupport':{'decision':'Preserve actual evaluated lowest support UNION of lower rail X[-.5,.34]/Y+/-.18 plus terminal bottom X[.312,.368]/Y+/-.203 atZ.04, with1e-6 representation tolerance. Union area.315056, eight-point finite boundary. This is not sum of overlapping face areas, AABB or raw unbeveled terminal X[.3,.38]/Y+/-.215. Topology/triangulation free, no exact part-count lock. Terminal may be redesigned above unchanged support inside own raw budget. No geometricZ0/fullsquarefloor/base lift/drop/outside support.','unionXY':proposal['finiteSupport']['unionXYApprox'],'unionArea':proposal['finiteSupport']['unionAreaApprox'],'z':.04,'tolerance':1e-6,'actualEvaluatedFaces':proposal['finiteSupport']['evaluatedLowestSupportFaces']},
    'canonical':{'binding':{'path':str(binding_path.relative_to(folder)),'sha256':sha(binding_path)},'decision':'Adopt exact approved middle02 full finite.08 W contact geometry and actual shader-used normalized postinterpolation side/cap normal/albedo/material/alpha/needed tangent/longitudinal fields, rig/world/capture underall4. Equivalent native storage/graphs allowed. SoleW port only; no new N/E interface. Edge02 is exact bounded chain neighbor, no end/family approval.'},
    'targetFreedom':'Opaque blue layered target boards are aesthetic exploration, not a mandate for literal count/opacity or a ban on purposeful new infill. Preserve coherent substantial terminal/rail/iron hierarchy and useful intentional negative space without locking exact old bay emptiness. Native forms/topology/count/material methods free outside interfaces inside budget; no invented actor traversal law.',
    'history':'Correct explicit-visible baseline-v2 and failed visibility/measurement diagnostics retained. Historical4x source replay has same alpha bbox but maxalpha5 residual and is NOT decoded/byte-identical. New canonical direct2x must not reset historical Faceted/world0/contrast135.',
    'evidenceScope':'Actual true chain ownend0/middle02(-1,0)/edge02(-2,0), proper-rotate all4; native and current570/099 same roots/order/rects. Same bounded4case×2mode plan. No approvedcorner exists at freeze; conditional familyL is not required or authorized by an unapproved reference. Exact localW evidence and technical authorities remain strict.',
    'unchanged':'Fixed target, six proposed visible outcomes, source identity/function/root/static timing/registration/atlas/capture and unchanged validators; no candidate approval.'}
hard=[
    'Actual S33_PROP_wreck-end.001/rootwreck-end__root.001/root0/unit scale/properS0 E90 N180 W-90/pitch1/1x1/staticframe1/range1..1/12fps/nonloop/all4. Own RAW8point XY hull extrudedZ[.04,.78]/tol1e-6, proper rotated. Source measured top.76/evaluated bevel trim/middle bounds/perpart/3Dhull/count/old construction are not smaller design locks.',
    'Actual finite lowest support UNION atZ.04/tol1e-6: lower rectangleX[-.5,.34]/Y+/-.18 plus evaluated terminal bottomX[.312,.368]/Y+/-.203, eight-point union/.315056 area. Preserve actual finite region, topology free; overlapping face-area sum or AABB alone insufficient. Raw unbeveled terminal bottom is not the actual support. No Z0/fullsquarefloor/lift/drop/outside support; terminal form above may improve inside own budget.',
    'Sole trueW port[-.5,0,0]/normal-X with exact ordered three disconnected source/canonical rectangle sections/outwardcapwindings atX-.5, properall4/unitpitch. Full.08 W[-.5,-.42] actual shader-used normalized postinterpolation side/cap normals/albedo/material/alpha/needed tangent/longitudinal derivatives match approvedmiddle02; side versus cap fields distinct. Equivalent native storage/nodes allowed, no literal Principled/customnormal veto, ringIDs or isolated samples alone insufficient. No new N/E ports, mirrors, cutgrowth/rounding/deletion/overlap/step/fake alpha.',
    'Registered55.0079798/aspect1.22065556/heroortho1.5/logical192352/root96248/cell128, DIRECTnative2x384704/root192496/filter.01/full PNGidentity/no reduction/original1x1atlas/all4/static1/12fps/nonloop. Exact canonical EEVEE/Standard/None/exposure0/gamma1/dither0/worldStrength.28/color(.72,.80,1), overhead195Wsize8Z5+4equal114Wsize8radius6Z4 DISKshadowfalse/fullgraphs/matrices. No historicalFaceted/world0/contrast135 reset, preferredhorizontal key/directionalgroundcast/perview adjustment.',
    'All4 true native chain end0/middle02Rz(a)*(-1,0,0)/edge02Rz(a)*(-2,0,0), allrotationa. Real W-to-E connections/fullgeometry/pitch1, exact individual frames through actual570/099 atsame roots/order/atlasrects. Expanded proof camera/canvas derived from actual integer geometry preserving128 logical units/cell and sourcebasis/root correspondence; no perview artfit. No unapproved corner/fullfamilyL or inferred family approval.',
    'Frozen4case×2 prescribed Chromium153 modes/all4/lightgraydark/128+32/integer-fractionalroot+pan/wholeCSSscale, nativecanvas nearest AFTER resize then ordinary wholeCSS filtering. Actual versions/executables/launch/DPR/viewport/fixtures/helper/atlas/control/placementorder hashes and raw differences retained. Expand concrete risk only. No raster/crop/warp/nudge/overlap/perviewrecolor/alphaRGB repair/targetcard/paint/sharedhelper changes.',
    'Same six visible outcomes: substantial purposeful soft blue hull/iron/palefasteners/finished terminal, controlled colored broad highlights/plane turns/readable recesses/native crafted detail/coherentall4/openbay hierarchy/12832readability. Optional target board fill/count and old weakgeometry are not mandates. No localized crack/slit/stripe/step/doubledcap/fringe/halo/blackpatch/normal seam/clipping/deadspot waiver. Legitimate continuous openframe accepted; broad finite-light/outer-raster residuals separately honest, source or numerical equality not a visible defect waiver.',
    'Private portable editable native actual-used resource closure/staticownership and actual source/camera/root/finite support/fullfields/replay required. Every declared hero/preview directly covered by originaljudge with exactpath/hash provenance; missing evidence is not approval. Unchanged integrity/direction/acceptance gates. Originals/preparation/initial/target/criteria/prior signed bytes immutable. No editor/judge production/Git/deploy/device/liveBlender/extraagent/sharedhelper/brief/review ownership violations.'
]
contract={'asset':'wreck-end','version':1,'status':'root-frozen-before-construction','sourceProposal':{'path':str(pp.relative_to(folder)),'sha256':sha(pp)},'preparationManifest':{'path':str(mp.relative_to(folder)),'sha256':sha(mp),'rootVerifiedFiles':362},'nativeContract':proposal,'hardConstraints':hard,'reconciliation':recon,'requiredEvidence':plan,'approvedCanonical':authorities}
write(recon_path,recon);write(contract_path,contract);shutil.copyfile(folder/'brief.json',backup)
brief=read(folder/'brief.json');brief['capture'].update(nativeFrame=[384,704],nativeCaptureScale=2,publishedFrame=[384,704],publication='Exact direct native2x PNG identity/filter.01; no reduction.',previews=['four-view-sheet','phone','repeated'])
brief['constraints']['nativeContract']='inputs/root-native-contract.json'
brief['qualityCriteria']={'status':'root-frozen-before-construction','definitionOfGood':'A substantial softly finished blue wreck terminal with distinct iron and pale fasteners, controlled colored plane highlights, coherent useful negative space and clean trueW connection in every facing/use size.','priorityOutcomes':criteria['outcomes'],'hardConstraints':hard,'criteriaFile':str(cp.relative_to(folder)),'criteriaFileSHA256':sha(cp),'nativeContract':'inputs/root-native-contract.json','nativeContractSHA256':sha(contract_path),'preparationManifestSHA256':sha(mp),'requiredEvidence':plan}
resources=brief.setdefault('technicalResources',{});resources.update(rootNativeContract='inputs/root-native-contract.json',preparationReconciliation='inputs/root-preparation-reconciliation-v1.json',approvedCanonicalBinding=str(binding_path.relative_to(folder)),nativePreparationManifest=str(mp.relative_to(folder)),freshEditorInitial=str(initial.relative_to(folder)))
for f in m['files']:resources['prepared:'+f['path']]=f['path']
write(folder/'brief.json',brief)
p=run/'progress.json';d=read(p);entry=next(x for x in d['objects'] if x['id']=='wreck-end');entry.update(status='editing',editor='catalog_wreck_end_editor_v1',judge='catalog_wreck_end_judge_v1',editorStatus='starting-construction',judgeStatus='prepared-awaiting-candidate',stage='native-wreck-end-round01',briefSHA256=sha(folder/'brief.json'));write(p,d)
result={'asset':'wreck-end','scriptSHA256':sha(Path(__file__)),'editorInitialSHA256':args.editor_initial_sha,'rootVerifiedPreparationFiles':362,'briefSHA256':sha(folder/'brief.json'),'contractSHA256':sha(contract_path),'reconciliationSHA256':sha(recon_path)}
write(run/'preparation/wreck-end/freeze-execution-v1.json',result);print(json.dumps(result))
