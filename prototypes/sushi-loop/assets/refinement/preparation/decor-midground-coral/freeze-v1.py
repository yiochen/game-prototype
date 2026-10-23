from pathlib import Path
import json, hashlib, copy, shutil
run=Path(__file__).resolve().parents[2]
folder=run/'objects/decor-midground-coral'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
manifest_path=folder/'reviews/preparation-v1/preparation-manifest.json'
assert sha(manifest_path)=='21810c3c452d7c82f7ecd8b82d35998c61b30ad1fd3918bd3f5cca3e0e1bb6e8'
manifest=read(manifest_path);assert len(manifest['files'])==195
for r in manifest['files']:
 p=folder/r['path'];assert p.is_file() and sha(p)==r['sha256'] and p.stat().st_size<100_000_000,r['path']
initial=folder/'source/initial-observations.json'
assert sha(initial)=='fc0a00b9fa97e58dd230c4bf0e289a6f4d11c760493dc1821d424469fd2d4a70'
proposal_path=folder/'reviews/source-contract-proposal.json';criteria_path=folder/'reviews/proposedcriteria.json'
assert sha(proposal_path)=='bbf4171df910b758572d0e971ee242076bfba4f5c231c9846579721f1b5c7434'
assert sha(criteria_path)=='b698945482043da77bf1fd13e773acbe3662377e08461337e97c0b38a0e72ce2'
proposal=read(proposal_path);criteria=read(criteria_path)
recon_path=folder/'inputs/root-preparation-reconciliation-v1.json';contract_path=folder/'inputs/root-native-contract.json';backup=folder/'inputs/brief-before-native-freeze.json'
assert not recon_path.exists() and not contract_path.exists() and not backup.exists()
recon={'asset':'decor-midground-coral','stage':'root reconciliation before any candidate construction',
 'sealedPreparationUnchanged':{'path':manifest_path.relative_to(folder).as_posix(),'sha256':sha(manifest_path),'rootVerifiedFiles':195},
 'freshEditorInitial':{'path':initial.relative_to(folder).as_posix(),'sha256':sha(initial)},
 'occupiedScaleAndSway':{'sourceCanonicalSweptBounds':proposal['functionalEnvelopeProposal']['measuredSourceSweptBoundsRoot'],
  'sourceFinding':'Actual living sway reaches X=.513274908 on a nominal nonblocking1x1 occupied cell. This is already present in native source; occupiedCells is not an opaque square floor or exact animated AABB law.',
  'rootDecision':'Keep static finite reef ground support and neutral colony within horizontal half-cell +/- .5. Permit moving upper coral a source-sized .013275 horizontal excursion beyond the nominal cell on either horizontal axis, invariant under the required proper facing rotations. This reconciles the existing small source excursion before construction and permits equivalent improved rooted sway. Maximum swept XY +/- .513275, numerical tolerance1e-5; no new large overhang, full-floor coverage or gameplay support claim.'},
 'heightEnvelope':{'declaredMaximum':1.45,'originalMeasuredMaximum':1.3385885953903198,'rootDecision':'Declared1.45 is the existing functional upper height/clearance budget, not a requirement to preserve the weak old mesh maximum. Keep every evaluated phase within Z[0,1.45].'},
 'sourceReplay':'Recorded55.00798 object camera supersedes unrelated saved35 camera; exact camera matrices are proven. All7 source actions were explicitly rebound. Historical atlas replay is close, not decoded-identical; preserve that honest evidence. No historical pixel equality requirement.',
 'temporalOwnership':'Keep fixed registered root/static reef, 12 unique frames at12fps/1second loop with native13 closure. Gentle rooted native living motion is the semantic law. Old7 owner names/count/pivot formula/phase/amplitude are not functional locks; any new complete ownership and native implementation must be disclosed and closed.',
 'methods':'Native geometry, normals, shader, materials, symmetric broad lighting and uniform whole-frame compositing can improve target style. Old Faceted140W+4x100/world0/contrast1.35/black height ramp are source observations, not aesthetic locks. No per-facing fitting or recolor/pixel repair.'}
hard=[
 'Registered55.00797980144134 orthographic square-top/front capture and actual recorded world/projection matrices; ortho1.5/pixelaspect1.2206555604934692, one world unit per128 logical cell, fixed root at0/scale1/proper S0 E90 N180 W-90. No reflection or camera/root/perview scale fitting.',
 'Logical192384/root96288; native4x7681536/root3841152; uniform whole-frame LANCZOS reduction to published2x384768/root192576. Keep raw native captures and correctly distinguish native vs published camera scale. One native AA/filter/sample setting recorded and held across every facing/frame; same whole-frame publication method, no selective correction.',
 'Nonblocking midground prop/layer2/occupied1x1/supportCells[]/no sockets or modular ports. Static compact finite reef support grounded Z0 inside XY+/-.5, neutral colony inside nominal cell; moving upper coral swept XY+/-.513275 and Z[0,1.45], tolerance1e-5. Stable root/static reef; actual finite coral bases remain planted in new reef surfaces throughout allphases, no floating gaps/under-ground geometry. Original3octagon support/7tube/mesh counts and cavity layout are not locks. No full opaque square floor law or stand-on support claim.',
 'One idle clip: native1..12 published0..11, 12frames/12fps/loop, atlas6x2 cells384768/size23041536/gutter0, every N/E/S/W. Native13 closure pose equals1; frame13 is evidence only. Complete actual action/driver/shape/shader/material/visibility ownership disclosed, gentle rooted sway on fixed reef/no pop or clipping. New motion implementation/pivots/phase/amplitude free within semantics and envelope.',
 'Fixed selected warm-soft target and pink-dominant/violet/cobalt identity; fuller native hollow coral and clean cavities, soft broad horizontally symmetric colored highlights, controlled midground actor-relative emphasis, no preferred horizontal world key/directional groundcast shadow. Methods free, not literal source graphs/counts/lightpowers. Native model/animation only, no target card or painted export.',
 'Required native fullphase coverage/all4 with all4 actual playbacks/phase sheets plus fourview/intendedsize/phone/repeateddensity/style comparisons. Bounded actual570/099 consumer: fourview,3x3density, actualcatalog submarine/eel interaction at1200/390/DPR1/frame4, both prescribed153 headless modes. Separate nativecanvas nearest-after-resize from ordinary CSS filtering; no broad Cartesian expansion without concrete issue. No modular join test or unrelated actor clearance path law.',
 'No material deadspots/black cavities/intersecting interior walls/overlapping flakes/reversed normals/smeared shading/cut canvas/halos/loop popping. Honest historical sampling and exterior residual evidence stays distinct from visible approval. No fit/crop/warp/perview recolor/RGBalpha repair/overlap/sharedhelper changes. Every declared image/playback must be directly and truthfully covered by original judge before exact approval.'
]
contract={'asset':'decor-midground-coral','version':1,'status':'root-frozen-before-construction',
 'sourceProposal':{'path':proposal_path.relative_to(folder).as_posix(),'sha256':sha(proposal_path)},
 'preparationManifest':{'path':manifest_path.relative_to(folder).as_posix(),'sha256':sha(manifest_path),'rootVerifiedFiles':195},
 'nativeContract':copy.deepcopy(proposal),'reconciliation':recon,'hardConstraints':hard,'requiredEvidence':proposal['boundedEvidencePlan']}
write(recon_path,recon);write(contract_path,contract)
shutil.copyfile(folder/'brief.json',backup);brief=read(folder/'brief.json')
brief['capture'].update(nativeFrame=[768,1536],nativeCaptureScale=4,publishedFrame=[384,768],nativeRoot=[384,1152],publishedRoot=[192,576],publication='Uniform whole-frame LANCZOS4x-to2x; one recorded native filter/sample setting allviews/phases; no local processing.',previews=['four-view-sheet','phone','repeated','idle-N','idle-E','idle-S','idle-W'])
brief['constraints']['nativeContract']='inputs/root-native-contract.json'
brief['qualityCriteria']={'status':'root-frozen-before-construction','definitionOfGood':criteria['qualityCriteria'],'priorityOutcomes':criteria['priority'],'criteriaFile':criteria_path.relative_to(folder).as_posix(),'criteriaFileSHA256':sha(criteria_path),'hardConstraints':hard,'nativeContract':'inputs/root-native-contract.json','nativeContractSHA256':sha(contract_path),'preparationManifestSHA256':sha(manifest_path),'requiredEvidence':proposal['boundedEvidencePlan']}
resources=brief.setdefault('technicalResources',{})
resources.update(rootNativeContract='inputs/root-native-contract.json',preparationReconciliation='inputs/root-preparation-reconciliation-v1.json',nativePreparationManifest=manifest_path.relative_to(folder).as_posix())
for r in manifest['files']:resources['prepared:'+r['path']]=r['path']
write(folder/'brief.json',brief)
p=run/'progress.json';progress=read(p);o=next(x for x in progress['objects'] if x['id']=='decor-midground-coral');o.update(status='editing',editor='catalog_decor_midground_coral_editor_v1',judge='catalog_decor_midground_coral_judge_v1',editorStatus='starting-construction',judgeStatus='prepared-awaiting-candidate',stage='native-midground-coral-round01',briefSHA256=sha(folder/'brief.json'));write(p,progress)
print(json.dumps({'asset':'decor-midground-coral','verifiedPreparationFiles':195,'briefSHA256':sha(folder/'brief.json'),'contractSHA256':sha(contract_path),'reconciliationSHA256':sha(recon_path)}))
