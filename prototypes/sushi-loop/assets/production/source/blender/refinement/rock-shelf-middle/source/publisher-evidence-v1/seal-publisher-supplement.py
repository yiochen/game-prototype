"""One-shot compatible delivery and exact supplemental closure; no prior file edits."""
import json,math,hashlib
from pathlib import Path
B=Path(__file__).resolve().parents[2];S=B/'source/publisher-evidence-v1';E=B/'candidates/round-01/publisher-evidence-v1';D=B/'delivery/publisher-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(B).as_posix()
def record(p):return {'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
assert not (D/'manifest.json').exists(),'Do not replace sealed supplement'
original=json.loads((B/'delivery/manifest.json').read_text());old=json.loads((B/'delivery/delivery.json').read_text());ledger=json.loads((E/'pose-ledger.json').read_text());proof=json.loads((E/'rgba-replay-and-publication-proof.json').read_text())
assert len(original['files'])==132
assert sha(B/'delivery/manifest.json')=='81a1a65f05d6651ca1557203165cb3bfdb36859775fc01ca8edef4867143d2ee'
assert sha(B/'delivery/seal.json')=='c9d3d4f9b6ec2722ac1c60674b8f23a3a82257a665ec8921d0d069ec2f3e8834'
assert sha(B/'source/round-01.blend')=='da1b8a61f51d4dad60132e9627650ba1b2563e8f6887a6e27b0bb155926669af'
for p,rec in original['files'].items():assert sha(B/p)==rec['sha256'],p
# Structural checks use actual ledger data and the unchanged auditor's documented convention.
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};anglesMeasured={}
for d,a in angles.items():
 r=ledger['views'][d];m=r['rootMatrix'];matrixAngle=math.atan2(m[1][0],m[0][0]);err=math.atan2(math.sin(r['rootRotationZ']-a),math.cos(r['rootRotationZ']-a));assert abs(err)<1e-4
 anglesMeasured[d]={'rootRotationZ':r['rootRotationZ'],'matrixRotationZ':matrixAngle,'publisherExpected':a,'angularError':err,'rawFrame':r['path'],'rawSHA256':r['sha256']}
cam=json.loads((E/'camera-published-2x.json').read_text());native=json.loads((E/'native-camera-4x.json').read_text());assert cam['captureScale']==2 and cam['frame']==[192,352] and cam['anchor']==[96,248]
assert native['captureScale']==4 and native['nativeRasterFrame']==[768,1408] and cam['camera']==native['camera']
for key in native['calibration']:assert all(abs(v*.5-w)<1e-9 for v,w in zip(native['calibration'][key],cam['calibration'][key]))
validation={'purpose':'Pre-seal technical schema/measurement checks, not official packet audit or approval','publisherFieldChecks':{'projectExists':True,'recipeIsOriginal':True,'rawFrames2xOriginalAll4':True,'nativeRawFrames4xOriginalAll4':True,'unchangedPreviewCount':len(old['previews']),'cameraCaptureScale':cam['captureScale'],'cameraFrame':cam['frame'],'cameraAnchor':cam['anchor'],'nativeRawScale':native['captureScale'],'cameraMatricesUnchangedByNormalization':True},'actualDirectionMeasurements':anglesMeasured,'strictAuditPending':'Root seals official packet, then runs unchanged audit_directions.py; this supplement supplies exact packet-bound validation.nativeValidation -> primary measured views/rootRotationZ ledger.','inspectedTechnicalSchemaFiles':{str(p):sha(p) for p in [B.parents[1]/'tools/seal_object.py',B.parents[1]/'tools/audit_directions.py',B.parents[1]/'tools/promote_object.py']}}
# Tool paths: B=.../refinement/objects/asset; B.parents[1]=.../refinement.
(E/'publisher-schema-checks.json').write_text(json.dumps(validation,indent=2)+'\n')
raw=[];nativeRaw=[];atlases=[]
for d in 'NESW':
 raw.append({'clip':'static','direction':d,'index':0,'path':old['candidateRenders'][d],'size':[384,704],'sourceScale':2,'sha256':sha(B/old['candidateRenders'][d])})
 nativeRaw.append({'clip':'static','direction':d,'index':0,'path':old['nativeCaptures'][d],'size':[768,1408],'sourceScale':4,'sha256':sha(B/old['nativeCaptures'][d])})
 atlases.append({'clip':'static','direction':d,'path':old['originalLayoutAtlases'][d],'columns':1,'rows':1,'frames':1,'size':[384,704],'rects':[[0,0,384,704]],'sha256':sha(B/old['originalLayoutAtlases'][d])})
resources=set(original['files'])|{'delivery/manifest.json','delivery/seal.json'}
resources|={rel(p) for folder in [S,E] for p in folder.rglob('*') if p.is_file()}
resources|={rel(D/'delivery.json'),rel(D/'manifest.json'),rel(D/'seal.json')}
delivery={'asset':'rock-shelf-middle','round':'round-01','supplement':'publisher-v2','metadataOnly':True,'metadataOnlyMeaning':'Metadata/reproduction supplement to exact original unapproved art; not an art revision or approval.','project':'source/round-01.blend','recipeScript':'source/build-round-01.py','validation':rel(E/'validation.json'),'nativeRecords':{'camera':rel(E/'camera-published-2x.json'),'assetRecord':rel(E/'asset-record-published-2x.json'),'rig':rel(E/'rig.json')},'originalNativeCameraRecord':'inputs/source-camera.json','actualNativeCameraRecord':rel(E/'native-camera-4x.json'),'nativeCaptureScale':4,'publishedSourceScale':2,'heroes':old['candidateRenders'],'previews':old['previews'],'rawFrames':raw,'nativeRawFrames':nativeRaw,'atlases':atlases,'resources':sorted(resources),'publication':'Exact original full native4x frames uniformly wholeRGBA BOX-reduced to published2x384x704; no new native2x render or image repair. All4 atlas1x1/static1frame/fps12/nonloop.','primaryNativePoseLedger':record(E/'pose-ledger.json'),'unchangedControlPoseLedger':record(E/'replay-control-02/pose-ledger.json'),'replayProof':record(E/'rgba-replay-and-publication-proof.json'),'originalHandoff':{'delivery':record(B/'delivery/delivery.json'),'manifest':record(B/'delivery/manifest.json'),'seal':record(B/'delivery/seal.json'),'original132Unchanged':True,'sourceProjectSHA256':sha(B/'source/round-01.blend')},'approval':False,'status':'immutable-metadata-supplement-awaiting-root-packet-and-original-judge','limitations':['First W clean replay onegreen-byte residual by1 at one nativepixel is retained; ordinary unchanged second all4 control matches original decodedRGBA/native and wholeBOX/published exactly. No further renders or universalGPU bitidentity claim.','Root must materialize a new byte-identical object-root alias for seal_object.py --delivery because unchanged tool restricts deliveryJSON to object root.','Official packet, strict direction audit, original judge verdict and any promotion remain pending root-owned work.']}
(D/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
newfiles={rel(p):{'sha256':sha(p),'bytes':p.stat().st_size} for folder in [S,E,D] for p in sorted(folder.rglob('*')) if p.is_file() and p.name not in ['manifest.json','seal.json']}
for p,rec in newfiles.items():assert rec['bytes']<100_000_000 and '__pycache__' not in p and not p.endswith('.pyc')
manifest={'schemaVersion':1,'asset':'rock-shelf-middle','supplement':'publisher-v2','purpose':'Exact original132 plus old manifest/seal and minimal new metadata/reproduction evidence. Art/source/7previews unchanged; no approval.','priorArtFiles':original['files'],'priorHandoffFiles':{'delivery/manifest.json':record(B/'delivery/manifest.json'),'delivery/seal.json':record(B/'delivery/seal.json')},'newFiles':newfiles,'frozenInputs':original['frozenInputs'],'sourceProjectSHA256':sha(B/'source/round-01.blend')}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
seal={'asset':'rock-shelf-middle','round':'round-01','supplement':'publisher-v2','status':'immutable-awaiting-root-packet-and-original-judge','manifestSHA256':sha(D/'manifest.json'),'deliverySHA256':sha(D/'delivery.json'),'sourceSHA256':sha(B/'source/round-01.blend'),'original132Unchanged':True,'originalManifestSHA256':sha(B/'delivery/manifest.json'),'newFileCount':len(newfiles),'newBytes':sum(x['bytes'] for x in newfiles.values()),'noArtOrApprovalChange':True}
(D/'seal.json').write_text(json.dumps(seal,indent=2)+'\n')
for p,rec in original['files'].items():assert sha(B/p)==rec['sha256']
for p,rec in newfiles.items():assert sha(B/p)==rec['sha256']
for path in delivery['resources']:assert (B/path).is_file(),path
print(json.dumps(seal,indent=2));print('sealSHA256',sha(D/'seal.json'))
