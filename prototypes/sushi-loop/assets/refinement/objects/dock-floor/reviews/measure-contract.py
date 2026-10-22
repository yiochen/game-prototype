from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image,ImageFilter
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6];ASSETS=OUT.parents[3];PROD=ASSETS/'production';OBJ=OUT.parent
D=json.loads((OUT/'native-inspection.json').read_text());P=json.loads((OUT/'published-raster-evidence.json').read_text());C=json.loads((OUT/'native-capture-evidence.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mesh(aid,only=None):return [o for o in D['assets'][aid]['objects'] if o['type']=='MESH' and not o['hideRender'] and (only is None or only in o['name'])]
def z_at(aid,x,y,offset=(0,0,0),only=None):
 hits=[]
 for o in mesh(aid,only):
  v=np.array(o['vertices'])+offset
  for f in o['polygons']:
   ids=f['vertices'];a=v[ids[0]]
   for i in range(1,len(ids)-1):
    b,c=v[ids[i]],v[ids[i+1]];m=np.array([[b[0]-a[0],c[0]-a[0]],[b[1]-a[1],c[1]-a[1]]]);det=np.linalg.det(m)
    if abs(det)<1e-12:continue
    u,t=np.linalg.solve(m,np.array([x-a[0],y-a[1]]))
    if u>=-1e-7 and t>=-1e-7 and u+t<=1+1e-7:hits.append({'part':o['name'],'z':float(a[2]+u*(b[2]-a[2])+t*(c[2]-a[2]))})
 return sorted(hits,key=lambda h:h['z'],reverse=True)
report={'method':'Independent vertical triangle intersections of evaluated native mesh vertices/polygons from native-inspection.json; source at facingS/root0. Native and published crops compared without subject fitting.','rawEvidenceSHA256':sha(OUT/'native-inspection.json'),'deckSamples':[],'entrySamples':[],'joinRasterComparison':{},'sourceFiles':[]}
for x,y in [(.125,0),(.125,-1.5),(.125,-1.49),(.125,-1.45),(0,0),(0,-1.49),(-1.17,0),(.78,.35),(.66,-.21),(-.93,-.42),(-.47,-.42)]:report['deckSamples'].append({'xy':[x,y],'hits':z_at('dock-floor',x,y)})
for y in [-1.996,-1.995,-1.875,-1.755,-1.75,-1.745,-1.625,-1.505,-1.5,-1.495,-1.375,-1.255,-1.25,-1.245,-1.125,-1.005,-1.0]:
 h=z_at('dock-entry',.125,y,(0,-1.5,0));f=z_at('dock-floor',.125,y);report['entrySamples'].append({'xy':[.125,y],'floorTop':f[0] if f else None,'entryTop':h[0] if h else None,'nativeVisibleTop':max([v for v in [f[0] if f else None,h[0] if h else None] if v],key=lambda h:h['z']) if f or h else None})
for d in ['N','E','S','W']:
 native=np.array(Image.open(OUT/f'native-entry-join-{d}.png').convert('RGBA')).astype(float);pub=np.array(Image.open(OUT/f'published-entry-join-{d}.png').convert('RGBA')).astype(float)
 def over(a):return a[:,:,:3]*a[:,:,3:]/255+167*(1-a[:,:,3:]/255)
 diff=np.max(abs(over(native)-over(pub)),axis=2)
 # projected entry overlap ROI: same registered camera, axial rotation of corner coordinates; includes all entry geometry.
 angle={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d];pts=[]
 for x in [-.51,.51]:
  for y in [-1.995,-1.005]:
   for z in [-.01,.4825]:
    xx=math.cos(angle)*x-math.sin(angle)*y;yy=math.sin(angle)*x+math.cos(angle)*y;pts.append((576+256*xx,704-256*yy-179.2*z))
 x0=max(0,math.floor(min(p[0] for p in pts))-3);x1=min(1152,math.ceil(max(p[0] for p in pts))+3);y0=max(0,math.floor(min(p[1] for p in pts))-3);y1=min(1280,math.ceil(max(p[1] for p in pts))+3);v=diff[y0:y1,x0:x1]
 report['joinRasterComparison'][d]={'roiNativePx':[x0,y0,x1,y1],'maxCompositeGrayChannelDelta':float(v.max()),'pixelsDeltaAbove20':int(np.count_nonzero(v>20)),'meanMaxChannelDelta':float(v.mean()),'interpretation':'This baseline does NOT prove native/raster parity. Different sampling4x->2x versus native2x also contributes at edges; large filled-step region discrepancy is geometric/painter visibility, as directly inspected.'}
# Bound observed references and all actual reader inputs.
files=[OBJ/'brief.json',OBJ/'prompts/judge.txt',ASSETS/'refinement/preparation/dock-floor/judge-dispatch.txt',OBJ/'inputs/original.png',OBJ/'inputs/target.png',ASSETS/'refinement/style/warm-soft-reference.png',ASSETS/'refinement/backups/b1765262bfa897ad-sushi-loop-world-library.blend',PROD/'source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend',PROD/'source/blender/revisions/0d156c24ebd2a314/world_components.py',PROD/'source/blender/native_actions.py',PROD/'source/blender/capture_runtime.py',PROD/'source/blender/publish_captures.py',PROD/'source/blender/validate_connected_fixtures.py',ROOT/'wireframe/sprite-layout.js']
# Correct workspace relative files explicitly.
GAME=ASSETS.parent
files=[p for p in files if p.exists()]+[GAME/f'wireframe/{n}' for n in ['sprite-layout.js','world-sprite-raster.js','object-review.jsx']]+[GAME/'godot/scripts/native_pixel_compositor.gd']
for aid in ['dock-floor','dock-entry','workshop-hut','submarine-yellow','dock-cover','dock-post-rope']:
 for n in ['camera.json','asset.json','rig.json']:files.append(PROD/f'source/records/{aid}/{n}')
 for d in ['N','E','S','W']:
  guide=PROD/f'source/registered/{aid}/static-{d}/guide.json'
  if guide.exists():files.append(guide)
for p in files:report['sourceFiles'].append({'path':str(p),'exists':p.exists(),'sha256':sha(p) if p.exists() else None,'bytes':p.stat().st_size if p.exists() else None})
report['declaredRawCaptureFiles']=[{'path':str(PROD/x['image']),'exists':(PROD/x['image']).exists(),'declaredSHA256':x['sha256']} for x in P['objects']['dock-floor']['source']['rawFrames']]
report['sourceConsistency']={'snapshotMatchesPublishedS':sha(OBJ/'inputs/original.png')==sha(PROD/'sprites/dock-floor/static-S.png'),'sourceMatchesBackup':sha(PROD/'source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend')==sha(ASSETS/'refinement/backups/b1765262bfa897ad-sushi-loop-world-library.blend'),'targetMatchesFrozenSHA':sha(OBJ/'inputs/target.png')=='2a2450d166d5e5d08a6b19936bed5d7c2b400a34d381d93dbd4c5218205dba34'}
# Transparent RGB halos actual composited color fringe, per-facing image records.
report['alphaEdgeColors']={}
for d in ['N','E','S','W']:
 a=np.array(Image.open(PROD/f'sprites/dock-floor/static-{d}.png').convert('RGBA'));partial=(a[:,:,3]>0)&(a[:,:,3]<128);red=(a[:,:,0]>100)&(a[:,:,1]<12)&(a[:,:,2]<12);yellow=(a[:,:,0]>100)&(a[:,:,1]>100)&(a[:,:,2]<12)
 report['alphaEdgeColors'][d]={'partialAlphaBelow128Pixels':int(partial.sum()),'redLowAlphaPixels':int((partial&red).sum()),'yellowLowAlphaPixels':int((partial&yellow).sum()),'warning':'Counts are diagnostic color-edge indicators, not an automatic art defect threshold. Direct light/gray/dark inspection determines visibility.'}
(OUT/'contract-measurements.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'consistency':report['sourceConsistency'],'rawCaptureFiles':report['declaredRawCaptureFiles'],'joinRasterComparison':report['joinRasterComparison'],'alphaEdgeColors':report['alphaEdgeColors']},indent=2))
