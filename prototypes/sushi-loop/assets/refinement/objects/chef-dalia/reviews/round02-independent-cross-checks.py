from pathlib import Path
import json,hashlib,subprocess,math
import numpy as np
from PIL import Image
b=Path(__file__).resolve().parents[1];r=b/'reviews';p=b/'candidates/round-02'
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def delta(x,y):
 if isinstance(x,dict):return max([delta(x[k],y[k]) for k in x]+[0])
 if isinstance(x,list):return max([delta(a,z) for a,z in zip(x,y)]+[0])
 if isinstance(x,(float,int)) and not isinstance(x,bool):return abs(x-y)
 return 0 if x==y else float('inf')
s=read(r/'v2-held-food-source-audit.json');a=read(r/'round02-independent-food-native-audit.json');m=read(r/'v2-held-food-projected-canonical-map.json');old=read(r/'v2-held-food-native-preservation-baseline.json');new=read(r/'round02-independent-preservation-baseline.json');P=np.array(a['camera']['projectionMatrix']);V=np.linalg.inv(np.array(a['camera']['matrixWorld']))
def project(w):
 q=P@V@np.r_[w,1];return np.array([(q[0]/q[3]+1)*192,(1-q[1]/q[3])*320])
def world(mat,v):return (np.array(mat)@np.r_[v,1])[:3]
def support(path):
 im=Image.open(path).convert('RGBA');aa=np.asarray(im)[:,:,3];yy,xx=np.where(aa>=128);row=int(yy.max());xs=np.where(aa[row]>=128)[0];return {'size':list(im.size),'lowestRow':row,'occupiedX':[int(xs.min()),int(xs.max())],'occupiedCount':len(xs),'pixelCenter':[(float(xs.min())+float(xs.max()))/2+.5,row+.5],'sha256':sha(path)}
sourceSupport=support(r/'v2-held-food-evidence/approved-source-packed-salmon.png');canonicalSupport=support(r/'round02-food-evidence/candidate-packed-canonical-salmon.png');assert sourceSupport['pixelCenter']==[633.5,1050.5] and canonicalSupport['pixelCenter']==[367.5,503.5]
uv=[canonicalSupport['pixelCenter'][0]/731,1-canonicalSupport['pixelCenter'][1]/505];verts=np.array(a['sourceFood']['vertices']);local=verts[0]+uv[0]*(verts[1]-verts[0])+uv[1]*(verts[3]-verts[0]);width=np.linalg.norm(verts[1]-verts[0])*1.25;height=np.linalg.norm(verts[3]-verts[0])*1.25
rows=[];fields=['rootMatrix','foodRootMatrix','planeMatrix','planeLocalLocation','planeRotation','sourceVisibility','palmCentroidsWorld','palmMeanWorld','palmBoundsWorld','nativeHandBones','nativeMouthRestMetadata','evaluatedSmileMeshCentroidWorld','evaluatedBoneMatricesWorld']
for source,actual,expect in zip(s['frames'],a['frames'],m['phaseMapping']):
 key=[actual[k] for k in ['clip','direction','index']];assert key==[source[k] for k in ['clip','direction','index']]==[expect[k] for k in ['clip','direction','index']]
 w=world(actual['planeMatrix'],local);px=project(w);corners=np.array([project(world(actual['planeMatrix'],v)) for v in verts]);fieldDeltas={k:delta(source[k],actual[k]) for k in fields};d=math.sqrt(sum(v*v for v in actual['planeLocalLocation']))*1.25
 rows.append({'clip':key[0],'direction':key[1],'index':key[2],'sourceInvariantMaxDeltas':fieldDeltas,'canonicalCornerMaxNativePixelDelta':float(np.max(np.abs(corners-np.array(expect['canonicalCornersProjectedNative'])))),'semanticSupportNativePixelDelta':float(np.max(np.abs(px-np.array(expect['semanticSupportProjectedNative'])))),'semanticSupportWorldDelta':float(np.max(np.abs(w-np.array(expect['sourceSemanticSupportWorldAtSourceDepth'])))),'supportMinusActualPalmMeanNative':(px-np.array(actual['palmMeanProjected'][:2])).tolist(),'depthWorld':d,'widthWorld':width,'heightWorld':height,'renderHidden':actual['planeHideRender'],'facingDegrees':actual['rootRotationDegrees']})
maxInv={k:max(x['sourceInvariantMaxDeltas'][k] for x in rows) for k in fields};assert max(maxInv.values())<=1e-6
corner=max(x['canonicalCornerMaxNativePixelDelta'] for x in rows);supportPx=max(x['semanticSupportNativePixelDelta'] for x in rows);supportWorld=max(x['semanticSupportWorldDelta'] for x in rows);assert corner<=.001 and supportPx<=.001 and supportWorld<=1e-6
aspectRel=abs(width/height/(731/505)-1);assert aspectRel<=1e-6
exactKeys=[k for k in old if k not in ['sourceSHA256']];preserved={k:old[k]==new[k] for k in exactKeys};assert all(preserved.values());assert s['camera']==a['camera'] and s['render']==a['render'] and s['lightRig']==a['lightRig'] and s['sourceFood']['material']==a['sourceFood']['material'] and s['sourceFood']['planeDrivers']==a['sourceFood']['planeDrivers']
def stats(x,y):
 aa=np.asarray(Image.open(x).convert('RGBA')).astype(int);bb=np.asarray(Image.open(y).convert('RGBA')).astype(int);d=np.abs(aa-bb);return {'differentPixels':int(np.any(d>0,axis=2).sum()),'differentAlphaPixels':int((d[:,:,3]>0).sum()),'maxRGBAByteDifference':d.max(axis=(0,1)).tolist(),'meanAbsoluteRGBAByteDifference':d.mean(axis=(0,1)).tolist()}
controls=read(p/'controls-record.json');records=controls['records'];controlStats=[]
for clip,di,idx in [('hold','S',0),('hold','E',0),('hold','N',0),('hold','W',0),('load','S',5),('work','S',5)]:
 for mode in ['food-on-a','food-off']:
  pair=[next(x for x in records if (x['kind'],x['clip'],x['direction'],x['index'],x['mode'])==(kind,clip,di,idx,mode)) for kind in ['source','candidate']]
  for x in pair:
   assert sha(b/x['path'])==x['sha256'] and x['visibilityRestoredAfterDiagnostic']
   if mode=='food-off':assert x['preRenderVisibility']['hideRender'] and x['postRenderHideRender'] and x['preRenderVisibility']['mutedVisibilityCurves']==1
  controlStats.append({'clip':clip,'direction':di,'index':idx,'mode':mode,'sourceVsCandidate':stats(*[b/x['path'] for x in pair])})
repeats={kind:stats(p/'controls'/kind/'hold-S-000-food-on-a.png',p/'controls'/kind/'hold-S-000-food-on-b.png') for kind in ['source','candidate']}
reopen=read(r/'round02-independent-reopen-control-record.json');fresh=stats(b/reopen['renderFiles'][0]['path'],p/'frames/hold-S/000.png')
allFrames=[]
for clip in ['idle','work','hold','load']:
 for di in ['N','E','S','W']:
  for i in range(12):
   f=p/'frames'/f'{clip}-{di}'/f'{i:03d}.png';im=Image.open(f).convert('RGBA');bbox=im.getchannel('A').getbbox();assert bbox[0]>=64 and bbox[1]>=160 and bbox[2]<=320 and bbox[3]<=536
   allFrames.append({'path':str(f.relative_to(p)),'alphaBBox':list(bbox)})
videos=[]
for f in sorted((p/'playbacks').glob('*.mp4'))+sorted((p/'contexts').glob('*.mp4')):
 info=read(Path('/dev/null')) if False else json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=width,height,r_frame_rate,avg_frame_rate,nb_read_frames,duration','-of','json',str(f)]))['streams'][0]
 assert info['r_frame_rate']=='12/1' and info['avg_frame_rate']=='12/1' and info['nb_read_frames']=='12' and float(info['duration'])==1
 videos.append({'path':str(f.relative_to(p)),'sha256':sha(f),'ffprobe':info})
assert len(videos)==24
ret={'asset':'chef-dalia','candidatePacketSHA256':sha(p/'packet.json'),'sourceSHA256':a['sourceSHA256'],'frozenBriefSHA256':sha(b/'brief-v3-held-food-frozen.json'),'sourceAlpha128':sourceSupport,'canonicalAlpha128':canonicalSupport,'canonicalSupportLocalDerivedFromActualVertices':local.tolist(),'displayWidthWorld':width,'displayHeightWorld':height,'aspectRelativeError':aspectRel,'sourceInvariantMaxDeltas':maxInv,'canonicalCornerMaxNativePixelDelta':corner,'semanticSupportMaxNativePixelDelta':supportPx,'semanticSupportMaxWorldDelta':supportWorld,'depthWorldRange':[min(x['depthWorld'] for x in rows),max(x['depthWorld'] for x in rows)],'strictNativeBaselineMatches':preserved,'cameraRenderLightMaterialAndDriversExact':True,'frames':rows,'controlStats':controlStats,'holdSRepeatStats':repeats,'freshPackedRenderVsBoundHoldS0':fresh,'freshProcessImages':reopen['images'],'rawFrameAlphaBoundsAndAssemblyCropCoverage':allFrames,'actualVideoMetadata':videos,'failedControlsClassification':'Retained attempt-04 food-off samples invalid: hide_render fcurve overwrote the temporary property at render. Excluded as food-off proof. Corrected controls mute exactly one hide_render curve and restore authored visibility/mute state; inspected correct native and control evidence.'}
(r/'round02-independent-cross-checks.json').write_text(json.dumps(ret,indent=2)+'\n');print(json.dumps({k:ret[k] for k in ['candidatePacketSHA256','sourceInvariantMaxDeltas','canonicalCornerMaxNativePixelDelta','semanticSupportMaxNativePixelDelta','semanticSupportMaxWorldDelta','aspectRelativeError','depthWorldRange','freshPackedRenderVsBoundHoldS0','freshProcessImages']},indent=2))
