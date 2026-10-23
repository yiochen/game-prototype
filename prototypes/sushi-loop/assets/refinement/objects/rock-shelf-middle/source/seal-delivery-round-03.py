"""Seal exact round03 editor handoff; official packet and original judge remain root-owned."""
from pathlib import Path
import json,hashlib,math
B=Path(__file__).resolve().parent.parent;E=B/'candidates/round-03';D=B/'delivery/round-03'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(B).as_posix()
def record(p):return {'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
assert not (D/'manifest.json').exists(),'Do not overwrite sealed round03'
# Preserve every earlier packet and independentjudge member, plus immutable editor handoffs.
for prior in ['round-01','round-02']:
 packet=json.loads((B/f'candidates/{prior}/packet.json').read_text())
 for r in [*packet['files'].values(),*packet['candidateRenders'].values(),*packet['previews'].values()]:assert sha(B/f'candidates/{prior}'/r['path'])==r['sha256'],r['path']
 review=json.loads((B/f'reviews/{prior}-independent/manifest.json').read_text())
 for r in review['files']:assert sha(B/r['path'])==r['sha256'],r['path']
for path,key in [('delivery/manifest.json','files'),('delivery/publisher-v2/manifest.json','newFiles'),('delivery/round-02/manifest.json','files')]:
 for p,r in json.loads((B/path).read_text())[key].items():assert sha(B/p)==r['sha256'],p
assert sha(B/'reviews/round-02.json')=='f8ae79b19353df926fc72d0a77c0b8b4c0787bfb0534348063e13cee9f9d470f'
v=json.loads((E/'native-validation.json').read_text());ep=json.loads((E/'endpoint-evidence.json').read_text());poses=json.loads((E/'pose-ledger.json').read_text());replay=json.loads((E/'replay-publication-proof.json').read_text());consumer=json.loads((E/'consumer-results.json').read_text());seams=json.loads((E/'seam-measurements.json').read_text());camera=json.loads((E/'camera-published-2x.json').read_text())
assert v['sourceProjectSHA256']==sha(B/'source/round-03.blend') and v['embeddedRecipeSHA256']==v['externalRecipeSHA256']
assert v['objects'][0]['topology']=={'boundaryEdges':0,'nonManifoldEdges':0}
assert camera['captureScale']==2 and camera['frame']==[192,352] and camera['anchor']==[96,248]
for d,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 assert abs(math.atan2(math.sin(poses['views'][d]['rootRotationZ']-a),math.cos(poses['views'][d]['rootRotationZ']-a)))<1e-4
 assert replay['comparisons'][d]['wholeNativeBOXvsPublished']['sameDecodedRGBA'] and replay['comparisons'][d]['publishedVsAtlas']['sameDecodedRGBA']
heroes={d:f'candidates/round-03/static-{d}.png' for d in 'NESW'}
previews={'four-view-sheet':'candidates/round-03/four-view-sheet.png','repeated':'candidates/round-03/consumer-gray-all4.png','native-four-view':'candidates/round-03/native-all4-4x.png','repeated-light':'candidates/round-03/consumer-light-all4.png','repeated-dark':'candidates/round-03/consumer-dark-all4.png','fractional-NS':'candidates/round-03/consumer-phases-NS.png','fractional-EW':'candidates/round-03/consumer-phases-EW.png'}
newsource=[p for p in (B/'source').iterdir() if p.is_file() and ('round-03' in p.name)]
files={rel(p):{'sha256':sha(p),'bytes':p.stat().st_size} for folder in [E,B/'source/round-03-resources'] for p in folder.rglob('*') if p.is_file()}
files.update({rel(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in newsource})
# Read-only prior verdict/packet/header are context resources, not duplicated media/runtime trees.
for p in [B/'reviews/round-02.json',B/'reviews/round-02-independent/manifest.json',B/'candidates/round-02/packet.json',B/'delivery/round-02/manifest.json',B/'delivery/round-02/seal.json',B/'source/round-02.blend']:
 files[rel(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
resources=sorted(set(files)|{'delivery/round-03/delivery.json','delivery/round-03/manifest.json','delivery/round-03/seal.json'})
delivery={'asset':'rock-shelf-middle','round':'round-03','project':'source/round-03.blend','recipeScript':'source/build-round-03.py','recipe':'source/round-03-settings.json','validation':'candidates/round-03/validation.json','nativeRecords':{'camera':'candidates/round-03/camera-published-2x.json','assetRecord':'candidates/round-03/asset-record.json','rig':'candidates/round-03/rig.json'},'originalNativeCameraRecord':'inputs/source-camera.json','actualNativeCameraRecord':'candidates/round-03/native-camera-4x.json','nativeCaptureScale':4,'publishedSourceScale':2,'heroes':heroes,'previews':previews,'rawFrames':[{'clip':'static','direction':d,'index':0,'path':heroes[d],'size':[384,704],'sourceScale':2,'sha256':sha(B/heroes[d])} for d in 'NESW'],'nativeRawFrames':[{'clip':'static','direction':d,'index':0,'path':f'candidates/round-03/native-{d}-4x.png','size':[768,1408],'sourceScale':4,'sha256':sha(E/f'native-{d}-4x.png')} for d in 'NESW'],'atlases':[{'clip':'static','direction':d,'path':f'candidates/round-03/atlases/{d}/sheet.png','columns':1,'rows':1,'frames':1,'size':[384,704],'rects':[[0,0,384,704]],'sha256':sha(E/f'atlases/{d}/sheet.png')} for d in 'NESW'],'resources':resources,'publication':'Whole native4xRGBA canvas BOX-reduced to published2x. All4 original1x1 layout/static1frame/fps12/nonloop. No pixel repair/perview changes.','measured':{'sourceSHA256':v['sourceProjectSHA256'],'bounds':v['bounds'],'ground':v['finiteGroundSupport'],'coreTopology':v['objects'][0]['topology'],'trueEndpointResidual':ep['trueEndpointResidual'],'neighborRayResidual':ep['maxBandResidual'],'externalBlendDependencies':v['resources']['externalDependencies'],'actualMotion':v['staticActualChecks'],'actualMeasuredDirectionLedger':'candidates/round-03/pose-ledger.json','consumerErrors':consumer['errors'],'nativeOpaqueAlphaUndercoverage':{d:seams['measurements'][d]['metrics']['allNativeOpaque']['assembledAlphaLess255Pixels'] for d in 'NESW'}},'usedCurrentConsumerSHA256':sha(B/'source/round-03-resources/consumer/world-sprite-raster.js'),'preservedAcceptedProgress':'candidates/round-03/accepted-progress-preservation.json','respondsToSignedReview':record(B/'reviews/round-02.json'),'priorBytesUnchanged':json.loads((B/'source/round-03-baseline.json').read_text()),'replayControl':'candidates/round-03/replay-publication-proof.json','approval':False,'status':'immutable-editor-handoff-awaiting-root-packet-original-judge','limitations':['One ordinary saved-source replay retains exact native/publication/strip residuals; no retries seeking equality or universal GPU identity claim.','Finite-area-light RGB residuals native strips versus independently captured sprites are reported; local visible join review remains independent.','Root creates a new byte-identical object-root delivery alias for unchanged seal_object.py and seals official packet; no sharedtool changes.','Original judge assesses both blockers anew; no family,production,Git,device or live Blender work.']}
(D/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n');files[rel(D/'delivery.json')]={'sha256':sha(D/'delivery.json'),'bytes':(D/'delivery.json').stat().st_size}
for p,r in files.items():r['path']=p
for p,r in files.items():assert r['bytes']<100_000_000 and '__pycache__' not in p and not p.endswith('.pyc'),p
manifest={'schemaVersion':1,'pathBase':'object root (rock-shelf-middle)', 'objectRoot':str(B),'asset':'rock-shelf-middle','round':'round-03','purpose':'Exact new art/source/reproduction/nativeconsumer evidence and reused frozen minimal dependency closure. Prior stage context/header hashes retained; no oldbyte edits or approval.','files':files,'frozenInputs':{p:sha(B/p) for p in ['brief.json','inputs/root-native-contract.json','inputs/original.png','inputs/target.png']},'priorBaselineChecks':json.loads((B/'source/round-03-baseline.json').read_text())}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
seal={'asset':'rock-shelf-middle','round':'round-03','status':'sealed-awaiting-root-packet-original-judge','manifestSHA256':sha(D/'manifest.json'),'deliverySHA256':sha(D/'delivery.json'),'sourceSHA256':sha(B/'source/round-03.blend'),'fileCount':len(files),'totalBytes':sum(r['bytes'] for r in files.values()),'allPriorPacketsHandoffsJudgeMembersUnchanged':True,'noCandidateApproval':True}
(D/'seal.json').write_text(json.dumps(seal,indent=2)+'\n')
for p,r in files.items():assert sha(B/p)==r['sha256'],p
for p in resources:assert (B/p).is_file(),p
print(json.dumps(seal,indent=2));print('sealSHA256',sha(D/'seal.json'))
