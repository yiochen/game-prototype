"""Read-only technical closure and digest refresh for the versioned Omar delivery."""
from pathlib import Path
import json,hashlib,math
from PIL import Image
import numpy as np
P=Path(__file__).resolve().parent;B=P.parent;O=B/'candidates/round-02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
dp=B/'delivery-round-02-held-food-v3.json';d=read(dp);v=read(B/d['validation']);assert v['ok']
assert isinstance(d['resources'],list) and all(isinstance(x,str) and (B/x).is_file() for x in d['resources'])
assert isinstance(d['runtimeVariants']['resources'],list) and all(isinstance(x,str) and (B/x).is_file() for x in d['runtimeVariants']['resources'])
assert set(x['clip'] for x in d['rawFrames'])=={'idle','work','hold','load'}
assert set(x['clip'] for x in d['runtimeVariants']['rawFrames'])=={'hold-cucumber','load-cucumber'}
assert len(d['rawFrames'])==192 and len(d['atlases'])==16
assert len(d['runtimeVariants']['rawFrames'])==96 and len(d['runtimeVariants']['atlases'])==8
facing_counts={};mesh_count=0
for pack in [d,d['runtimeVariants']]:
 records=read(B/pack['renderManifest']);assert len(records)==len(pack['rawFrames'])
 for r in records:
  angle=math.atan2(r['rootMatrix'][1][0],r['rootMatrix'][0][0]);expected={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[r['direction']]
  assert abs(math.atan2(math.sin(angle-expected),math.cos(angle-expected)))<1e-6
  facing_counts[r['direction']]=facing_counts.get(r['direction'],0)+1
  assert r['nativeCaptureScale']==2 and r['publishedScale']==2
  assert all(r[k]==0 for k in ['maxPositionDeltaWorld','maxVertexNormalDelta','maxCornerNormalDelta','maxPoseMatrixDelta','maxPhysicalControlDelta'])
  assert len(r['meshParity'])==69;mesh_count+=len(r['meshParity'])
  assert all(m[k]==0 for m in r['meshParity'].values() for k in ['maxPositionDeltaWorld','maxVertexNormalDelta','maxCornerNormalDelta'])
 for r in pack['rawFrames']:
  p=B/r['path'];assert sha(p)==r['sha256'];im=Image.open(p).convert('RGBA');assert im.size==(384,640)
  box=im.getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<384 and box[3]<640
 for r in pack['atlases']:
  p=B/r['path'];assert sha(p)==r['sha256'];atlas=Image.open(p).convert('RGBA');assert list(atlas.size)==r['size']
  frames=sorted([q for q in pack['rawFrames'] if (q['clip'],q['direction'])==(r['clip'],r['direction'])],key=lambda q:q['index'])
  for q,rect in zip(frames,r['rects']):
   if isinstance(rect,dict):rect=rect['rect']
   x,y,w,h=rect;assert np.array_equal(np.array(atlas.crop((x,y,x+w,y+h))),np.array(Image.open(B/q['path']).convert('RGBA')))
 for path in pack.get('previews',{}).values():assert isinstance(path,str) and (B/path).is_file()
for path in d['heroes'].values():assert isinstance(path,str) and (B/path).is_file()
projects={n:sha(P/n) for n in ['round-02.blend','runtime-round-02.blend']}
assert projects=={'round-02.blend':'abcd13cccd0e278134d094c2adfb145324fc6feaa8a5f5d22703d321338b3b7f','runtime-round-02.blend':'6a26cdc069b95b5e2a4b8e2ddbc14e496b7f7a7c6b4dcd18373e1e1a742927ae'}
prior=read(O/'prior-artifact-integrity.json');assert sha(P/'round-01.blend')==prior['approvedMainSourceSHA256'] and sha(P/'runtime-round-01.blend')==prior['approvedRuntimeSourceSHA256']
assert read(O/v['renderManifest'])==read(B/d['renderManifest'])
for name in ['all-frame-food-transform-validation.json','continuous-law-validation.json','semantic-orientation-validation.json','hidden-mesh-evaluation-validation.json']:
 for folder in [O,O/'runtimeVariants']:assert read(folder/name)['ok']
assert read(O/'fresh-replay-validation.json')['ok']
closure={'ok':True,'rawFrames':288,'catalogRawFrames':192,'runtimeRawFrames':96,'catalogAtlases':16,'runtimeAtlases':8,'nativeCaptureScale':2,'publishedSourceScale':2,'allNativeFramesWithinCanvas':True,'allRawAndAtlasHashesMatch':True,'allAtlasPixelsMatchTheirFullFrameRegions':True,'measuredRootFacingSampleCounts':facing_counts,'perFrameMeshComparisonRecords':mesh_count,'sourceProjects':projects,'versionedDeliverySHA256':sha(dp),'validationSHA256':sha(B/d['validation']),'priorSourcesUnchanged':True,'independentVisualVerdict':'Pending; no self-approval'}
write(O/'final-integrity.json',closure)
h=read(O/'editor-handoff.json');h['delivery']['sha256']=sha(dp);h['validationSHA256']=sha(B/d['validation']);h['finalIntegrity']='candidates/round-02/final-integrity.json';h['nativeCaptureScale']=2;h['publishedSourceScale']=2;h['limitations']='Food-dependent RGB differences observed on32 diagnostic poses: max15/255 channel outside food quad union; causal transport/denoising shares not isolated. Fresh replay max1/255 RGBA across34 shipping samples. Hidden rigid knife meshes explicitly reconstructed under evaluated native parent; actual visible work cross-check max2.98e-8.';write(O/'editor-handoff.json',h)
print(json.dumps(closure,indent=2))
