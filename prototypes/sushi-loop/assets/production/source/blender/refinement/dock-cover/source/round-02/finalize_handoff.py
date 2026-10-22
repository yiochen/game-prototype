"""Freeze an editor handoff only. Does not seal, approve, publish or change production."""
import sys,json,hashlib,math,datetime,subprocess,importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
from PIL import Image
import PIL,numpy
H=Path(__file__).resolve().parent;O=H.parent.parent;D=O/'candidates/round-02';L=O/'delivery/round-02'
assert not L.exists(),'Immutable handoff already exists'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def desc(p):return {'path':str(p.relative_to(O)),'sha256':sha(p)}
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
expected={'brief-v4-resource-paths.json':'7fd27d24700df7262e5aad0ed912621b1f5446d7332891923a1fb1fd1a60b269','brief-v3-final-context.json':'95e23f52c1a18cf4f38d5b425ad33341fb78797a29cc001642446efc00106d26','inputs/root-native-contract-v3-final-context.json':'5ccee6349b2e14fa225a4fad61af6be6286caff7fe107f67cc81a783b1608219','delivery/preliminary-v2/handoff.json':'9385f20c9d3b684190a90af0f45ddaf57dd6a1a3c8c09d6679a42fa5604726c3','source/initial-observations.json':'41e501f6123d34faf35d3c115fed2f19d2db50c1ed330c9f3000b5ff6fe1c72a'}
for p,s in expected.items():assert sha(O/p)==s,p
project=H/'cover.blend';projectSHA=sha(project);assert projectSHA=='aea9e932ba845ede5c32ed4074eb5ff69acfef0f2c169398d147a7e6be0ad3a3'
phase=read(D/'native-phase-audit.json');family=read(D/'final-family-audit.json');con=read(D/'consumer/consumer-evidence.json');dom=read(D/'consumer-dom/actual-SpriteScene-parity.json');present=read(D/'native-present-reference/evidence.json');play=read(D/'playback-verified-v3/evidence.json');dep=read(D/'depth-identity/depth-order-audit.json');sd=read(D/'support-depth/depth-order-audit.json');hum=read(D/'human-depth-proof.json');replay=read(D/'saved-source-reopen-decoded-audit.json')
assert phase['sourceSHA256']==family['coverSourceSHA256']==dep['sourceProjectSHA256']==projectSHA
assert len(phase['renders'])==96 and len(phase['inbetweens'])==112
assert len(family['clearance'])==208 and len(family['human'])==468 and len(family['actualAllFacingFiniteSurfaceCovariance'])==832
assert len(family['support'])==3 and all(r['contactArea']>.0069 and r['minimumGapWorld']>=-1e-5 for r in family['support'])
assert all(not r['actualBVHTriangleIntersectionPairs']for r in family['human'])
for r in family['clearance']:
 for v in r['companions'].values():assert v['actualBVHTriangleIntersectionPairs']==0 and (v['minimumGapWorld']is None or v['minimumGapWorld']>=.02)
assert all(r['minimumGapWorld']is None or r['minimumGapWorld']>=.02 for r in family['human'])
assert dep['maximumConflictPixels']==sd['maximumConflictPixels']==0
assert hum['minimumClothFrontDepthSeparationOnAnyProjectedOverlap']>0
assert con['caseCount']==1536 and con['presentationCount']==18432 and not con['errors']
assert len(dom['records'])==432 and all(r['exactDecodedNativeCanvasParity']for r in dom['records'])and not dom['errors']
assert present['presentationCases']==2304 and present['backgroundCases']==6912
assert play['allPass']and not play['errors']and len(play['records'])==8
assert all(r['exactDecodedRGBA']for r in replay['cleanProcessReplay'])
allposes=phase['renders']+phase['inbetweens'];pose={(r['clip'],r['direction'],r['frame']):r for r in allposes}
for d in 'NESW':
 for clip,indices in [('covered',[1,13]),('uncover',[12,12.5,13,16])]:
  signatures=[[(o['name'],o['evaluatedWorldVertexSHA256'])for o in pose[clip,d,i]['objects']]for i in indices];assert all(s==signatures[0]for s in signatures)
raw=read(D/'raw-frame-records.json');atlases=read(D/'atlas-records.json');assert len(raw)==96 and len(atlases)==8
for r in raw:
 p=O/r['path'];assert sha(p)==r['sha256'];im=Image.open(p).convert('RGBA');assert im.size==(1472,1408);box=im.getchannel('A').getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<1472 and box[3]<1408
for r in atlases:
 p=O/r['path'];assert sha(p)==r['sha256'];im=Image.open(p).convert('RGBA');assert im.size==(7360,4224)and r['columns']==5 and r['rows']==3 and r['fps']==12 and r['loop']==(r['clip']=='covered')and r['frameOrder']==list(range(12))
 for i,rect in enumerate(r['rects']):
  ref=Image.open(D/'frames'/f'{r["clip"]}-{r["direction"]}'/f'{i:03d}.png').convert('RGBA');x,y,w,h=rect;assert im.crop((x,y,x+w,y+h)).tobytes()==ref.tobytes()
 assert not im.crop((2944,2816,7360,4224)).getbbox()
# Exact source-function and companion-byte provenance, independent of stale catalogHashExact hints.
full=(H/'resources/consumer/actual-object-review.jsx').read_text();snippet=full[full.index('function SpriteScene('):];snippet=snippet[:snippet.index('\n}\n')+3].strip();ours=(H/'browser/SpriteScene.jsx').read_text();ours=ours[ours.index('export function SpriteScene('):].replace('export function','function',1).strip();assert snippet==ours
spriteRows=read(H/'resources/consumer/sprite-inputs.json');provenance=[]
for r in spriteRows:
 p=O/r['path'];assert sha(p)==r['sha256'];aid=r['object'];proof=O/('inputs/approved-final-main-v1/manifest.json'if aid=='submarine-yellow'else 'inputs/shared-world-pose-v1/resources/source/resources/approved-human-v3/customer-rosa-approved-catalog-object.json'if aid=='customer-rosa'else f'inputs/approved-dock-family-v1/{aid}/packet.json');assert r['sha256']in proof.read_text();provenance.append({'object':aid,'clip':r['clip'],'direction':r['direction'],**desc(p),'approvedEvidence':desc(proof)})
assert len(provenance)==36
runtime=[]
for name in ['native_pixel_compositor.gd','native_world_layer.gd','native_reduce2.gdshader','native_present.gdshader']:
 p=H/'resources/consumer'/name;original=O.parents[4]/'godot/scripts'/name
 # These current-repository snapshots are hash-bound reference inputs, not a claim of GPU execution.
 runtime.append({**desc(p),'referenceRole':'Exact current runtime source snapshot used by CPU arithmetic reference'})
smoke=read(D/'reproduction-smoke/reproduction-manifest.json')
for r in smoke['records']:
 a=Image.open(D/'reproduction-smoke'/r['path']).convert('RGBA');b=Image.open(D/'frames'/f'{r["clip"]}-{r["direction"]}'/f'{r["index"]:03d}.png').convert('RGBA');assert a.size==b.size and a.tobytes()==b.tobytes()
binding={'candidateProject':desc(project),'finalPacketBrief':desc(O/'brief-v4-resource-paths.json'),'unchangedPriorBrief':desc(O/'brief-v3-final-context.json'),'resourceReconciliation':desc(O/'inputs/root-resource-path-reconciliation-v1.json'),'finalMainRelease':desc(O/'inputs/final-main-release-v1.json'),'nativeContract':desc(O/'inputs/root-native-contract-v3-final-context.json'),'actualSpriteSceneFunctionMatchesOriginalExceptExport':True,'spriteProvenance':provenance,'nativePixelRuntimeSnapshots':runtime,'noCrossProjectionWholeSceneRGBIdentityClaim':True}
write(D/'exact-context-binding.json',binding)
# Reach the unchanged metadata helper's final approval gate, without inventing a review.
tool=H/'resources/delivery-tools/catalog_metadata_override.py';spec=importlib.util.spec_from_file_location('cover_metadata',tool);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);receipt=D/'catalog-metadata-override.json';measurement=D/'native-envelope-measurements.json';authority=O/'inputs/root-height-reconciliation-v1.json';bound={p.resolve():sha(p)for p in [receipt,measurement,authority]}
try:mod.validate_override(O,read(O/'inputs/catalog-object.json'),{'catalogMetadataOverride':desc(receipt)},bound,projectSHA,{})
except ValueError as e:assert str(e)=='Independent approval is missing';metadataGate=str(e)
else:raise AssertionError('Independent metadata approval must still be required')
environment={'python':sys.version,'pillow':PIL.__version__,'numpy':numpy.__version__,'node':subprocess.check_output(['node','--version'],text=True).strip(),'ffmpeg':subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-version'],text=True).splitlines()[0],'blender':replay.get('blender','5.2.2 LTS, exact background executable /opt/homebrew/bin/blender'),'noRuntimeApplicationTreesCopied':True}
write(D/'environment.json',environment)
L.mkdir(parents=True)
validation={'asset':'dock-cover','stage':'Final exact-context editor evidence complete; original independent judge and coordinator sealing pending','selfApproval':False,'finalFamilyApproved':False,'source':desc(project),'nativeValidation':str((D/'native-phase-audit.json').relative_to(O)),'binding':desc(D/'exact-context-binding.json'),'nativeFamily':desc(D/'final-family-audit.json'),'nativeDepth':desc(D/'depth-identity/depth-order-audit.json'),'humanDepth':desc(D/'human-depth-proof.json'),'actualConsumer':desc(D/'consumer/consumer-evidence.json'),'actualSpriteScene':desc(D/'consumer-dom/actual-SpriteScene-parity.json'),'nativePixelReference':desc(D/'native-present-reference/evidence.json'),'actualPlayback':desc(D/'playback-verified-v3/evidence.json'),'cleanReopen':desc(D/'saved-source-reopen-decoded-audit.json'),'recipeSmoke':desc(D/'reproduction-smoke/reproduction-manifest.json'),'nativeEvaluatedEnvelope':phase['maximumEvaluatedEnvelope'],'nativeSampleTuples':208,'rawFrames':96,'originalLayoutAtlases':8,'finiteSupports':[{'name':r['support'],'contactArea':r['contactArea'],'finiteContactFraction':r['finiteContactFraction'],'minimumSignedGapWorld':r['minimumGapWorld'],'beveledEdgeMaximumPositiveGap':r['maximumGapWorld']}for r in family['support']],'minimumFiniteClearanceWorld':{aid:min(r['companions'][aid]['minimumGapWorld']for r in family['clearance']if r['companions'][aid]['minimumGapWorld']is not None)for aid in ['hut','sub']},'minimumHumanFiniteClearanceWorld':min(r['minimumGapWorld']for r in family['human']if r['minimumGapWorld']is not None),'allFacingInverseRigidMaximumVertexError':max(r['inverseRigidMaximumVertexError']for r in family['actualAllFacingFiniteSurfaceCovariance']),'opaqueNativeCoverDepthConflicts':0,'actualConsumerCases':1536,'actualConsumerPresentations':18432,'actualComponentExactNativeCanvasComparisons':432,'nativePresenterArithmeticCases':2304,'nativePresenterBackgroundCases':6912,'catalogMetadataOverride':desc(receipt),'metadataTechnicalGateReached':True,'metadataGateStillRequires':metadataGate,'disclosures':['Common55 native physical proof and actual independent Main65/human35/environment55 assembly are separate. The registered human silhouette shifts with its authored projection; visible cloth/poles can occlude it in the actual consumer. Judge the bound nine-stance/all-facing actual images; whole-scene cross-projection RGB identity is neither expected nor claimed.','Native whole-overhead representability is measured at opaque alpha>=254 against actual front-cohort ID, tolerance4. No mask, opacity/visibility trick, per-view nudge, geometry warp or source-pixel repair was used.','CPU native-pixel reference is explicit premultiplied shader arithmetic, not actual Godot GPU execution. Actual current570 browser consumer and exact original SpriteScene are separately exercised.','Each sole has82.051% actual finite deck contact; its remaining outer portion bridges the real bevel with positive gap, maximum.004529world. Three noncollinear native contacts remain in the frozen near-corner bands.','Source inherited preliminary_only/provisional stage annotations are retained. published-assetRecord.json is the candidate-bound truthful height/pass adapter. Metadata receipt is technically valid but still requires explicit original judge approval.'],'retainedDiagnostics':{'round01NativeFailure':'candidates/round-01/failure-summary.json','firstAtomicReadRace':'candidates/round-02/consumer-dom/diagnostic-before-atomic-canvas-read.json','concurrentPlaybackUnderAuditLoad':'candidates/round-02/consumer/consumer-evidence.json actualPlayback','isolatedShortWindowMeanDiagnostics':['candidates/round-02/playback-verified/evidence.json','candidates/round-02/playback-verified-v2/evidence.json'],'resolution':'Actual consumer unchanged; atomic canvas snapshot fixed28 stale/default reads. Playback draws only on source-frame changes and validates exact12fps clock indices/no skips with measured refresh latency; endpoint means are still reported, with all raw traces retained.'},'pending':['Coordinator seals exact v4 brief and this exact immutable delivery.','Original independent judge visually inspects every required named view/preview and explicitly approves or rejects the exact height/pass receipt.'],'productionWrites':False,'editorSealedPacket':False}
write(L/'validation.json',validation)
previews={'four-view-sheet':'candidates/round-02/covered-01-four-view.png','repeated':'candidates/round-02/previews/repeated-sheet.png',**{f'{c}-{d}':f'candidates/round-02/playback/{c}-{d}.mp4'for c in ['covered','uncover']for d in 'NESW'},'native-family':'candidates/round-02/previews/native-family-sheet.png','consumer-family':'candidates/round-02/previews/consumer-family-sheet.png','support-contact':'candidates/round-02/previews/support-contact-sheet.png','human-approach':'candidates/round-02/previews/human-uncover-12.png','covered-playback':'candidates/round-02/previews/actual-consumer-covered-all4modes.mp4','uncover-playback':'candidates/round-02/previews/actual-consumer-uncover-all4modes.mp4','terminal-reveal':'candidates/round-02/previews/human-uncover-12.png','human-covered':'candidates/round-02/previews/human-covered-01.png','human-transition':'candidates/round-02/previews/human-uncover-06.png','native-presenter':'candidates/round-02/native-present-reference/presenter-sheet.png','actual-phone':'candidates/round-02/previews/actual-component-phone.png','actual-desktop':'candidates/round-02/previews/actual-component-desktop.png'}
brief=read(O/'brief-v4-resource-paths.json');assert set(brief['capture']['previews'])<=set(previews)
for p in previews.values():assert (O/p).is_file()
files={p.resolve()for root in [H,D,O/'inputs']for p in root.rglob('*')if p.is_file()and '__pycache__'not in p.parts}
files|={O/p for p in brief.get('technicalResources',{}).values()};files|={O/p for p in expected};files|={L/'validation.json'};files|={O/r['path']for r in spriteRows};files|={O/'prompts/editor.txt',O/'prompts/judge.txt'}
for key in ['project','backup']:assert sha((O/brief['source'][key]).resolve())==brief['source'][key+'SHA256']
files.add((O/brief['source']['snapshot']).resolve())
files.add((O/brief['target']['image']).resolve())
if brief['target'].get('prompt'):files.add((O/brief['target']['prompt']).resolve())
# Keep concrete failed-source witnesses, without treating its obsolete all-phase ledger as new proof.
for p in ['source/round-01/cover.blend','source/round-01/native-redesign.json','candidates/round-01/failure-summary.json','candidates/round-01/depth-identity/joint/dock-ready-covered-E-00.png']:
 if (O/p).is_file():files.add(O/p)
for p in files:assert p.is_file()and p.resolve().is_relative_to(O.resolve())and p.stat().st_size<100_000_000,p
resources=[{**desc(p),'bytes':p.stat().st_size}for p in sorted(files)]
delivery={'asset':'dock-cover','round':'round-02','stage':'Immutable final exact-context editor handoff; coordinator sealing and original independent review pending','createdUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'brief':desc(O/'brief-v4-resource-paths.json'),'project':str(project.relative_to(O)),'projectSHA256':projectSHA,'recipeScript':str((H/'reproduce.py').relative_to(O)),'constructionScript':str((H/'build_cover.py').relative_to(O)),'validation':str((L/'validation.json').relative_to(O)),'nativeRecords':{'camera':str((H/'camera.json').relative_to(O)),'assetRecord':str((H/'published-assetRecord.json').relative_to(O)),'rig':str((H/'rig.json').relative_to(O))},'heroes':{d:f'candidates/round-02/frames/covered-{d}/000.png'for d in 'NESW'},'previews':previews,'rawFrames':raw,'nativeRawFrames':raw,'atlases':atlases,'catalogMetadataOverride':desc(receipt),'resources':resources,'selfApproval':False,'finalFamilyApproval':False,'finalCandidateSealed':False,'preservedPreliminaryHandoff':desc(O/'delivery/preliminary-v2/handoff.json'),'finalMainRelease':desc(O/'inputs/final-main-release-v1.json'),'representationDisclosure':validation['disclosures']}
write(L/'delivery.json',delivery)
manifest={'asset':'dock-cover','round':'round-02','stage':'Immutable editor artifact closure; manifest excludes itself and enclosing handoff to avoid hash cycles','files':resources+[{'path':str((L/'delivery.json').relative_to(O)),'sha256':sha(L/'delivery.json'),'bytes':(L/'delivery.json').stat().st_size}]};write(L/'artifact-manifest.json',manifest)
for r in manifest['files']:assert sha(O/r['path'])==r['sha256']
handoff={'asset':'dock-cover','round':'round-02','stage':'IMMUTABLE FINAL EXACT-CONTEXT EDITOR HANDOFF; STOP for coordinator/original judge','project':desc(project),'delivery':desc(L/'delivery.json'),'validation':desc(L/'validation.json'),'artifactManifest':desc(L/'artifact-manifest.json'),'catalogMetadataOverride':desc(receipt),'brief':desc(O/'brief-v4-resource-paths.json'),'finalMainRelease':desc(O/'inputs/final-main-release-v1.json'),'fileCount':len(manifest['files']),'totalBytes':sum(r['bytes']for r in manifest['files']),'largestFileBytes':max(r['bytes']for r in manifest['files']),'resourceRehashMismatches':0,'selfApproval':False,'finalCandidateSealed':False,'productionWrites':False,'coordinatorNextStep':'Create byte-identical object-root delivery alias as required by unchanged sealer, then seal round-02 against exact brief-v4-resource-paths.json. Original same judge reviews all declared paths and explicitly decides metadata receipt. No source/capture/consumer byte changes after this handoff.'};write(L/'handoff.json',handoff)
print(json.dumps(handoff,indent=2))
