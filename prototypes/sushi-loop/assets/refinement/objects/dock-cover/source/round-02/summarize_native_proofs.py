"""Read-only source-bound numerical proofs and candidate metadata receipt."""
import sys,json,hashlib,math
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;O=H.parent.parent;D=O/'candidates/round-02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,r):p.write_text(json.dumps(r,indent=2)+'\n')
raw=json.loads((D/'native-phase-audit.json').read_text());projectSHA=sha(H/'cover.blend');assert raw['sourceSHA256']==projectSHA
samples=[{k:r[k]for k in ('clip','direction','frame','bounds')}for r in raw['renders']+raw['inbetweens']]
assert len(samples)==len({(r['clip'],r['direction'],r['frame'])for r in samples})==208
required={(c,d,1+i*.5)for c in ('covered','uncover')for d in 'NESW'for i in range(25)}
assert required<={(r['clip'],r['direction'],r['frame'])for r in samples}
for r in samples:
 lo,hi=r['bounds'];assert all(math.isfinite(v)for v in lo+hi)
 assert lo[0]>=-1.5 and lo[1]>=-1.5 and lo[2]>=-.012 and hi[0]<=1.5 and hi[1]<=1.5 and hi[2]<=2.2
measure={'asset':'dock-cover','projectSHA256':projectSHA,'measurementSource':{'path':str((D/'native-phase-audit.json').relative_to(O)),'sha256':sha(D/'native-phase-audit.json')},'sampleSpace':'Actual evaluated world vertices at standalone zero-location root, each required facing; bounds are local envelope after rigid facing; +.23 root belongs to paired context only.','samples':samples,'maximumEvaluatedEnvelope':raw['maximumEvaluatedEnvelope']}
mp=D/'native-envelope-measurements.json';write(mp,measure)
schema=json.loads((O/'inputs/final-catalog-metadata-schema-v1.json').read_text());receipt={k:schema[k]for k in ('asset','before','after','authority')};receipt['measurements']={'path':str(mp.relative_to(O)),'sha256':sha(mp)};write(D/'catalog-metadata-override.json',receipt)
ids=json.loads((D/'depth-identity/records.json').read_text());assert ids['projectSHA256']==projectSHA
alone={};records=[]
for r in ids['records']:
 key=(r['clip'],r['direction'],r['index'])
 if r['kind']=='isolated-cover-ID':alone[key]=np.array(Image.open(O/r['path']).convert('RGBA'))
 else:
  a=alone[key];b=np.array(Image.open(O/r['path']).convert('RGBA'));opaque=a[:,:,3]>=254
  front=(b[:,:,0]>=251)&(b[:,:,1]<=4)&(b[:,:,2]>=251)&(b[:,:,3]>=254)
  conflict=opaque&~front;yy,xx=np.where(conflict)
  records.append({k:r[k]for k in ('clip','direction','index','mode','path')}|{'opaqueIsolatedCoverPixels':int(opaque.sum()),'opaqueCoverPixelsHiddenByOtherNativeCohort':int(conflict.sum()),'witnessBounds':[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]if len(xx)else None})
audit={'sourceProjectSHA256':projectSHA,'method':ids['method'],'threshold':'Isolated alpha>=254 and joint magenta(255,0,255) tolerance4 with joint alpha>=254. Includes the opaque boundary, not only eroded interiors.','records':records,'maximumConflictPixels':max(r['opaqueCoverPixelsHiddenByOtherNativeCohort']for r in records)}
write(D/'depth-identity/depth-order-audit.json',audit)
sd=json.loads((D/'support-depth/records.json').read_text());assert sd['coverSourceSHA256']==projectSHA
humanMax=max(r['actualActorMaximumWorldZ']for r in sd['records']if 'actualActorMaximumWorldZ'in r)
clothMin=min(o['bounds'][0][2]+.23 for r in raw['renders']+raw['inbetweens']for o in r['objects']if 'attached_canvas'in o['name'])
camera=json.loads((H/'camera.json').read_text());el=math.radians(camera['camera']['elevationDegrees']);slope=abs(camera['calibration']['unitHeight'][1])/camera['calibration']['unitDepth'][1];factor=slope*math.cos(el)+math.sin(el)
proof={'sourceProjectSHA256':projectSHA,'cameraSHA256':sha(H/'camera.json'),'stationaryCohortAudit':{'path':'candidates/round-02/support-depth/depth-order-audit.json','sha256':sha(D/'support-depth/depth-order-audit.json')},'actualHumanCohortRecords':{'path':'candidates/round-02/support-depth/records.json','sha256':sha(D/'support-depth/records.json')},'actualNativeClothRecords':{'path':'candidates/round-02/native-phase-audit.json','sha256':sha(D/'native-phase-audit.json')},'measuredMovingClothMinimumWorldZ':clothMin,'allNineExactHumanPosesMaximumWorldZ':humanMax,'positiveWorldHeightDifference':clothMin-humanMax,'cameraScreenYHeightToDepthRatio':slope,'cameraDepthDeltaPerDeltaZAtSameProjectedXY':factor,'minimumClothFrontDepthSeparationOnAnyProjectedOverlap':factor*(clothMin-humanMax),'derivation':'Actual common55 orthographic screenY=-Y-.7Z. Equal screen coordinates imply deltaY=-.7deltaZ; camera-near depth=-cos(elevation)Y+sin(elevation)Z. Therefore equal projected XY depth difference=(.7cos(elevation)+sin(elevation))*deltaZ. All evaluated attached cloth/hems/stitches are above every vertex of all nine unchanged humans, so any common55 projected overlap places moving cloth in front for every sampled phase and direction. Stationary native frame/support/braces are separately tested with cloth hidden for all nine poses and four directions. Published human35/Main65 remain independent: no whole-scene mixed-projection RGB identity is claimed.','sampledPhaseCount':208,'scope':'Native physical depth proof for all nine exact source stances and all sampled phases; actual atlas consumer remains independently inspected.'}
assert clothMin>humanMax;write(D/'human-depth-proof.json',proof)
replay=json.loads((D/'saved-source-reopen-audit.json').read_text())
for r in replay['cleanProcessReplay']:
 a=Image.open(O/r['path']).convert('RGBA');b=Image.open(O/r['reference']).convert('RGBA');r['exactDecodedRGBA']=a.size==b.size and a.tobytes()==b.tobytes();r['decodedRGBASHA256']=hashlib.sha256(a.tobytes()).hexdigest();assert r['exactDecodedRGBA']
write(D/'saved-source-reopen-decoded-audit.json',replay)
print(json.dumps({'source':projectSHA,'samples':len(samples),'maximumNativeDepthConflictPixels':audit['maximumConflictPixels'],'clothMinimumWorldZ':clothMin,'humanMaximumWorldZ':humanMax,'nativeClothDepthMargin':proof['minimumClothFrontDepthSeparationOnAnyProjectedOverlap'],'cleanReopenDecodedRGBA':[r['exactDecodedRGBA']for r in replay['cleanProcessReplay']]},indent=2))
