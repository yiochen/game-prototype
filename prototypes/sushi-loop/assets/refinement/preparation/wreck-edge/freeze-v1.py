from pathlib import Path
import json,hashlib,shutil,copy
run=Path(__file__).resolve().parents[2];folder=run/'objects/wreck-edge';canonical=run/'objects/wreck-middle'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
mp=folder/'reviews/preparation-v1/manifest.json'
assert sha(mp)=='697de8bb7a7a0ab59a3d87cb6e2f99198b22312f9affd5d71ee40c7b566987bb'
m=read(mp);assert len(m['files'])==184
for r in m['files']:
 q=folder/r['path'];assert sha(q)==r['sha256'] and q.stat().st_size<100_000_000,r['path']
initial=folder/'source/initial-observations.json';assert sha(initial)=='b642a7765637c98b4330241dc7117ac98c6b0007f9e50fbbbfabc1796c7c0562'
pp=folder/'reviews/source-contract-proposal.json';cp=folder/'reviews/proposedcriteria.json';ep=folder/'reviews/preparation-v1/evidence-plan.json'
assert sha(pp)=='93f50b2eca541a691dc980998bb67cc05174dd62479e37e576f0856a8af09d87'
assert sha(cp)=='31975a9b49669256f2d59867aa1c8707cc4be2f80bbfe0ab41c2d3cedf3d9efe'
assert sha(ep)=='b8f5f8c5bc710309300c88b48678cc60b6d1276f2698d859df62166bcdec913f'
proposal=read(pp);criteria=read(cp)
pktp=canonical/'candidates/round-02/packet.json';reviewp=canonical/'reviews/round-02.json'
assert sha(pktp)=='f371a2509c600cce6b4f53223aa6c0ed546a9db00b79ffcc78dc8fb710b68005'
assert sha(reviewp)=='6f06d28d217abe29bff3ceaa672814a1233553b87a856f54afb4d28a1a33ac76'
r=read(reviewp);assert r['verdict']=='approve' and r['blockers']==[] and r['candidatePacketSHA256']==sha(pktp)
binding_root=folder/'inputs/approved-wreck-middle-v1';recon_path=folder/'inputs/root-preparation-reconciliation-v1.json';contract_path=folder/'inputs/root-native-contract.json';backup=folder/'inputs/brief-before-native-freeze.json'
assert not any(p.exists() for p in [binding_root,recon_path,contract_path,backup])
pkt=read(pktp);bindings={}
def retain(alias,src,dst,expected=None):
 assert expected is None or sha(src)==expected
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst)
 bindings[alias]={'path':dst.relative_to(folder).as_posix(),'sha256':sha(dst),'originalPath':src.relative_to(run).as_posix()}
retain('packet',pktp,binding_root/'packet.json');retain('review',reviewp,binding_root/'review.json')
p=pkt['files']['candidateProject'];retain('project',(pktp.parent/p['path']).resolve(),binding_root/'round-02.blend',p['sha256'])
for facing,p in pkt['candidateRenders'].items():retain('hero-'+facing,(pktp.parent/p['path']).resolve(),binding_root/(facing+'.png'),p['sha256'])
retain('endpointFields',canonical/'candidates/round-02/canonical-endpoint-fields.json' if (canonical/'candidates/round-02/canonical-endpoint-fields.json').exists() else canonical/'candidates/round-01/canonical-endpoint-fields.json',binding_root/'canonical-endpoint-fields.json')
write(binding_root/'binding.json',{'asset':'wreck-middle','round':'round-02','files':bindings,'scope':'Exact independently approved source/heroes/receipt and endpoint descriptor for mixed native/individual assembly. Approval does not extend to this derivative/family.'})
recon={'asset':'wreck-edge','stage':'root reconciliation BEFORE construction',
 'preparation':{'path':mp.relative_to(folder).as_posix(),'sha256':sha(mp),'rootVerifiedFiles':184},
 'freshEditorInitial':{'path':initial.relative_to(folder).as_posix(),'sha256':sha(initial)},
 'authoringEnvelope':{'decision':'Adopt the proposed derivative-specific original raw seven-point XY convex hull extruded Z[.04,.78], tolerance1e-6. This is the native authoring-size budget including tilted broken sheet, not the smaller evaluated bevel envelope, whole-middle limits, sloping3D hull or per-part boxes. Source hull/evaluated bounds are retained measurements. Shape/construction/count/interior/upper/decor improvements remain free inside actual budget and fixed interfaces.', 'xy':proposal['authoringEnvelopeProposal']['xyPolygonCCW'],'z':[.04,.78]},
 'support':{'decision':'Keep the actual finite lowest lower-rail rectangle X+/-.5/Y+/-.18 atZ.04/area.36; source measured area.3600000183 is floating representation, not new size. No geometry atZ0/fullsquareground; supportCells is occupancy, not arbitrary opaque floor.', 'proposal':proposal['finiteSupport']},
 'canonical':{'binding':{'path':'inputs/approved-wreck-middle-v1/binding.json','sha256':sha(binding_root/'binding.json')},'decision':'Adopt exact actual canonical middle02 complete finite .08 W/E geometry/shader-used normalized normal/albedo/material/tangent/longitudinal fields, world and rig/capture. Same actual fields under required proper rotations are normative; equivalent native storage/nodes allowed. Canonical exact cap fields distinct from side fields. No art/family approval inferred.'},
 'methods':'Native shape/topology/count/normals/material/light methods are free outside fixed interfaces and must preserve exact contact fields/camera/rig. Fixed target/visible criteria unchanged. Legitimate coherent open rail/bay construction allowed; source/native equality is not a visual seam waiver.'}
hard=[
 'Actual ordered three W/E source rectangles atX+/-.5 with same handed YZ profiles as approved middle02, properS0/E90/N180/W-90/root0/scale1/pitch1 and outward opposing geometriccapwindings. No mirrored profile, cutrounding/growth/step, deletion/overlap or fake cut alpha.',
 'Full .08 W[-.5,-.42]/E[.42,.5] canonical side/cap fields: actual active shader-used normalized postinterpolation normal/albedo/material/alpha/tangent/longitudinal derivatives agree undertranslation/all4. Clone actual approved middle02 fields/rig/world; equivalent native storage/nodes allowed if full actual field equivalence proven. Ring IDs or unlinked data alone insufficient.',
 'Own measured seven-point RAW XY convexhull extrudedZ[.04,.78], tolerance1e-6, as explicit root reconciliation. No per-part/3D-hull/evaluated-bevel/count/oldsheettilt locks. Finite lowestsupport X+/-.5/Y+/-.18/Z.04/area.36 preserved, noZ0/fullfloor/dropbase/newoverhang or borrowing otherfamily geometry.',
 'Exact registered55.0079798/aspect1.22065556/ortho1.5/logical192352/root96248/cell128, DIRECTnative2x384704/root192496/filter.01/PNGidentity/no reduction. Static1/frame1/12fps/nonloop/all4/1x1atlasrectunchanged. Native camera/light/world/render settings cloned from actual canonical02, no sourcehistoricalgrade reset/perview fit or recolor.',
 'Actual canonical EEVEE/Standard/None/exposure0/gamma1/dither0, worldBackground Strength.28/Color(.72,.80,1), centered195Wsize8Z5+4equal114Wsize8radius6Z4 DISKno-shadow lights; actual full graphs/matrices in sealed preparation authority over rounded scalar summaries. Same one recipe/all4/no preferred horizontal key or directionalgroundcast.',
 'All4 true mixed3module native references edge atroot0 and approvedmiddle02 at properRz directions times(+/-1,0,0), bothW/E contacts. Exact approved individualframes and actual570/099 independentconsumer atsame roots/order. Frozen bounded4cases×2prescribed headless153modes/all4/lightgraydark/128and32/fractionalroot+pan, nativecanvas separateCSS; expandonlyconcreterisk.',
 'Fixed selected warmsoft target/definition/priority, substantial bluewreck construction/darkiron/palefasteners/purposeful exposededge/softcoloredhighlights/use-size readability. Legitimate open bays must read intentionally continuous; no localized seam slit/stripe/step/fringe/blackpatch/extraopaque cap or source-equality/numerical-only waiver. Preserve honest broadfinite-light/exterior renderer residuals separately. No targetcard/paint/fit/crop/warp/nudge/overlap/RGBalpha repair/perview adjustments/sharedhelper changes.',
 'Portable native source/recipe/private actual-used resource closure/staticownership and measured camera/support/fullfields required. Every declared hero/preview must be directly inspected by originaljudge before exact candidate approval. No derivative/family approval from canonical approval.'
]
contract={'asset':'wreck-edge','version':1,'status':'root-frozen-before-construction','sourceProposal':{'path':pp.relative_to(folder).as_posix(),'sha256':sha(pp)},'preparationManifest':{'path':mp.relative_to(folder).as_posix(),'sha256':sha(mp),'rootVerifiedFiles':184},'nativeContract':copy.deepcopy(proposal),'hardConstraints':hard,'reconciliation':recon,'requiredEvidence':read(ep),'approvedCanonical':bindings}
write(recon_path,recon);write(contract_path,contract);shutil.copyfile(folder/'brief.json',backup)
brief=read(folder/'brief.json');brief['capture'].update(nativeFrame=[384,704],nativeCaptureScale=2,publishedFrame=[384,704],publication='Exact direct native2x PNG identity/filter.01; no reduction.',previews=['four-view-sheet','phone','repeated'])
brief['constraints']['nativeContract']='inputs/root-native-contract.json';brief['qualityCriteria']={'status':'root-frozen-before-construction','definitionOfGood':criteria['definitionOfGood'],'priorityOutcomes':criteria['priorityOutcomes'],'hardConstraints':hard,'criteriaFile':cp.relative_to(folder).as_posix(),'criteriaFileSHA256':sha(cp),'nativeContract':'inputs/root-native-contract.json','nativeContractSHA256':sha(contract_path),'preparationManifestSHA256':sha(mp),'requiredEvidence':read(ep)}
resources=brief.setdefault('technicalResources',{});resources.update(rootNativeContract='inputs/root-native-contract.json',preparationReconciliation='inputs/root-preparation-reconciliation-v1.json',approvedCanonicalBinding='inputs/approved-wreck-middle-v1/binding.json',nativePreparationManifest=mp.relative_to(folder).as_posix())
for r in m['files']:resources['prepared:'+r['path']]=r['path']
write(folder/'brief.json',brief)
p=run/'progress.json';d=read(p);o=next(x for x in d['objects'] if x['id']=='wreck-edge');o.update(status='editing',editor='catalog_wreck_edge_editor_v1',judge='catalog_wreck_edge_judge_v1',editorStatus='starting-construction',judgeStatus='prepared-awaiting-candidate',stage='native-wreck-edge-round01',briefSHA256=sha(folder/'brief.json'));write(p,d)
print(json.dumps({'asset':'wreck-edge','rootVerifiedPreparationFiles':184,'briefSHA256':sha(folder/'brief.json'),'contractSHA256':sha(contract_path),'reconciliationSHA256':sha(recon_path)}))
