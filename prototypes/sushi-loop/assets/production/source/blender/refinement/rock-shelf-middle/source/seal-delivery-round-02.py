"""Seal exact round02 editor handoff; official packet and original judge remain root-owned."""
from pathlib import Path
import json,hashlib,math
B=Path(__file__).resolve().parent.parent;E=B/'candidates/round-02';D=B/'delivery/round-02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(B).as_posix()
def record(p):return {'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
assert not (D/'manifest.json').exists(),'Do not overwrite sealed round02'
# Preserve every old stage and original judge evidence; no old manifest/review changes.
old=json.loads((B/'delivery/manifest.json').read_text());supp=json.loads((B/'delivery/publisher-v2/manifest.json').read_text());review=json.loads((B/'reviews/round-01-independent/manifest.json').read_text());packet=json.loads((B/'candidates/round-01/packet.json').read_text())
for mapping in [old['files'],supp['newFiles']]:
 for p,r in mapping.items():assert sha(B/p)==r['sha256'],p
for r in review['files']:assert sha(B/r['path'])==r['sha256'],r['path']
for r in [*packet['files'].values(),*packet['candidateRenders'].values(),*packet['previews'].values()]:assert sha(B/'candidates/round-01'/r['path'])==r['sha256'],r['path']
assert sha(B/'reviews/round-01.json')=='5a90743010161a112d750fbe88dcb553474f74c93c1fd83958e08b98447989c8'
v=json.loads((E/'native-validation.json').read_text());ep=json.loads((E/'endpoint-evidence.json').read_text());poses=json.loads((E/'pose-ledger.json').read_text());replay=json.loads((E/'replay-publication-proof.json').read_text());consumer=json.loads((E/'consumer-results.json').read_text());seams=json.loads((E/'seam-measurements.json').read_text());camera=json.loads((E/'camera-published-2x.json').read_text())
assert v['sourceProjectSHA256']==sha(B/'source/round-02.blend') and v['embeddedRecipeSHA256']==v['externalRecipeSHA256']
assert v['objects'][0]['topology']=={'boundaryEdges':0,'nonManifoldEdges':0}
assert camera['captureScale']==2 and camera['frame']==[192,352] and camera['anchor']==[96,248]
for d,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 assert abs(math.atan2(math.sin(poses['views'][d]['rootRotationZ']-a),math.cos(poses['views'][d]['rootRotationZ']-a)))<1e-4
 assert replay['comparisons'][d]['wholeNativeBOXvsPublished']['sameDecodedRGBA'] and replay['comparisons'][d]['publishedVsAtlas']['sameDecodedRGBA']
heroes={d:f'candidates/round-02/static-{d}.png' for d in 'NESW'}
previews={'four-view-sheet':'candidates/round-02/four-view-sheet.png','repeated':'candidates/round-02/consumer-gray-all4.png','native-four-view':'candidates/round-02/native-all4-4x.png','repeated-light':'candidates/round-02/consumer-light-all4.png','repeated-dark':'candidates/round-02/consumer-dark-all4.png','fractional-NS':'candidates/round-02/consumer-phases-NS.png','fractional-EW':'candidates/round-02/consumer-phases-EW.png'}
newsource=[p for p in (B/'source').iterdir() if p.is_file() and ('round-02' in p.name)]
files={rel(p):{'sha256':sha(p),'bytes':p.stat().st_size} for folder in [E,B/'source/resources'] for p in folder.rglob('*') if p.is_file()}
files.update({rel(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in newsource})
# Read-only prior verdict/packet/header are context resources, not duplicated media/runtime trees.
for p in [B/'reviews/round-01.json',B/'reviews/round-01-independent/manifest.json',B/'candidates/round-01/packet.json',B/'delivery/manifest.json',B/'delivery/seal.json',B/'delivery/publisher-v2/manifest.json',B/'delivery/publisher-v2/seal.json']:
 files[rel(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
resources=sorted(set(files)|{'delivery/round-02/delivery.json','delivery/round-02/manifest.json','delivery/round-02/seal.json'})
delivery={'asset':'rock-shelf-middle','round':'round-02','project':'source/round-02.blend','recipeScript':'source/build-round-02.py','recipe':'source/round-02-settings.json','validation':'candidates/round-02/validation.json','nativeRecords':{'camera':'candidates/round-02/camera-published-2x.json','assetRecord':'candidates/round-02/asset-record.json','rig':'candidates/round-02/rig.json'},'originalNativeCameraRecord':'inputs/source-camera.json','actualNativeCameraRecord':'candidates/round-02/native-camera-4x.json','nativeCaptureScale':4,'publishedSourceScale':2,'heroes':heroes,'previews':previews,'rawFrames':[{'clip':'static','direction':d,'index':0,'path':heroes[d],'size':[384,704],'sourceScale':2,'sha256':sha(B/heroes[d])} for d in 'NESW'],'nativeRawFrames':[{'clip':'static','direction':d,'index':0,'path':f'candidates/round-02/native-{d}-4x.png','size':[768,1408],'sourceScale':4,'sha256':sha(E/f'native-{d}-4x.png')} for d in 'NESW'],'atlases':[{'clip':'static','direction':d,'path':f'candidates/round-02/atlases/{d}/sheet.png','columns':1,'rows':1,'frames':1,'size':[384,704],'rects':[[0,0,384,704]],'sha256':sha(E/f'atlases/{d}/sheet.png')} for d in 'NESW'],'resources':resources,'publication':'Whole native4xRGBA canvas BOX-reduced to published2x. All4 original1x1 layout/static1frame/fps12/nonloop. No pixel repair/perview changes.','measured':{'sourceSHA256':v['sourceProjectSHA256'],'bounds':v['bounds'],'ground':v['finiteGroundSupport'],'coreTopology':v['objects'][0]['topology'],'trueEndpointResidual':ep['trueEndpointResidual'],'neighborRayResidual':ep['maxBandResidual'],'externalBlendDependencies':v['resources']['externalDependencies'],'actualMotion':v['staticActualChecks'],'actualMeasuredDirectionLedger':'candidates/round-02/pose-ledger.json','consumerErrors':consumer['errors'],'nativeOpaqueAlphaUndercoverage':{d:seams['measurements'][d]['metrics']['allNativeOpaque']['assembledAlphaLess255Pixels'] for d in 'NESW'}},'respondsToSignedReview':record(B/'reviews/round-01.json'),'priorBytesUnchanged':{'original132':True,'publisher36':True,'originalJudge130':True,'packet570':True},'replayControl':'candidates/round-02/replay-publication-proof.json','approval':False,'status':'immutable-editor-handoff-awaiting-root-packet-original-judge','limitations':['One ordinary saved-source replay retains exact native/publication/strip residuals; no retries seeking equality or universal GPU identity claim.','Finite-area-light RGB residuals native strips versus independently captured sprites are reported; local visible join review remains independent.','Root creates a new byte-identical object-root delivery alias for unchanged seal_object.py and seals official packet; no sharedtool changes.','Original judge assesses both blockers anew; no family,production,Git,device or live Blender work.']}
(D/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n');files[rel(D/'delivery.json')]={'sha256':sha(D/'delivery.json'),'bytes':(D/'delivery.json').stat().st_size}
for p,r in files.items():assert r['bytes']<100_000_000 and '__pycache__' not in p and not p.endswith('.pyc'),p
manifest={'schemaVersion':1,'asset':'rock-shelf-middle','round':'round-02','purpose':'Exact new art/source/reproduction/nativeconsumer evidence and reused frozen minimal dependency closure. Prior stage context/header hashes retained; no oldbyte edits or approval.','files':files,'frozenInputs':{p:sha(B/p) for p in ['brief.json','inputs/root-native-contract.json','inputs/original.png','inputs/target.png']},'priorBaselineChecks':json.loads((B/'source/round-02-baseline.json').read_text())}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
seal={'asset':'rock-shelf-middle','round':'round-02','status':'sealed-awaiting-root-packet-original-judge','manifestSHA256':sha(D/'manifest.json'),'deliverySHA256':sha(D/'delivery.json'),'sourceSHA256':sha(B/'source/round-02.blend'),'fileCount':len(files),'totalBytes':sum(r['bytes'] for r in files.values()),'prior132Publisher36Judge130Packet570Unchanged':True,'noCandidateApproval':True}
(D/'seal.json').write_text(json.dumps(seal,indent=2)+'\n')
for p,r in files.items():assert sha(B/p)==r['sha256'],p
for p in resources:assert (B/p).is_file(),p
print(json.dumps(seal,indent=2));print('sealSHA256',sha(D/'seal.json'))
