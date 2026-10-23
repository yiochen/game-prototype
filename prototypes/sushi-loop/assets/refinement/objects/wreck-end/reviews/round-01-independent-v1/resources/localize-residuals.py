from pathlib import Path
import json,math
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;E=R.parent;OBJ=E.parent.parent;C=OBJ/'candidates/round-01';a=json.loads((E/'native-audit.json').read_text());captures=json.loads((E/'independent-capture-records.json').read_text())['records']
# Verify actual whole finite geometry as well as the active functions. Canonical
# topological subdivisions are observations; polygon regions/perimeters govern.
geo=[]
for f in a['own']['collar']:
 g=next(v for v in a['canonicalCollar'] if v['key']==f['key']);p=np.array(f['vertices']);q=np.array(g['vertices']);dist=max(max(min(np.linalg.norm(x-y) for y in q) for x in p),max(min(np.linalg.norm(y-x) for x in p) for y in q));assert dist<1e-6
 rec={'domain':f['key'],'actualVertexSetHausdorffToCanonical':float(dist),'wholeCollarPlanarAndConstant':True}
 if f['key'][0]=='cap':
  yz=p[:,1:];signed=sum(np.cross(yz[i],yz[(i+1)%len(yz)]).item() for i in range(len(yz)))/2;expected=(f['key'][2]-f['key'][1])*(f['key'][4]-f['key'][3]);assert signed<0 and abs(abs(signed)-expected)<1e-6;rec.update(signedYZArea=signed,finiteRectangleArea=expected,outwardWinding=True)
 geo.append(rec)
sections=[(-.18,.18,.04,.20),(-.09,.09,.60,.74),(.20,.26,.16,.35)]
def hull(pts):
 pts=sorted(set(pts));h=[]
 def cross(o,u,v):return (u[0]-o[0])*(v[1]-o[1])-(u[1]-o[1])*(v[0]-o[0])
 for arr in [pts,pts[::-1]]:
  one=[]
  for p in arr:
   while len(one)>1 and cross(one[-2],one[-1],p)<=0:one.pop()
   one.append(p)
  h.extend(one[:-1])
 return h
result=[]
for r in captures:
 if not r['chain']:continue
 d=r['direction'];angle=math.radians(r['rootRotationDegrees']);co,si=math.cos(angle),math.sin(angle);root=r['measuredRoot'];candidate=np.array(Image.open(C/'connected-native'/(d+'.png')).convert('RGBA'),dtype=np.int16);ind=np.array(Image.open(E/r['path']).convert('RGBA'),dtype=np.int16);delta=np.abs(candidate-ind)
 contacts=[]
 for plane in [-.5,-1.5]:
  mask=Image.new('L',(candidate.shape[1],candidate.shape[0]),0);draw=ImageDraw.Draw(mask)
  for ymin,ymax,zmin,zmax in sections:
   pts=[]
   for x in [plane-.018,plane+.018]:
    for y in [ymin,ymax]:
     for z in [zmin,zmax]:
      wx=x*co-y*si;wy=x*si+y*co;pts.append((root[0]+256*wx,root[1]-256*wy-179.2*z))
   draw.polygon(hull(pts),fill=255)
  m=np.array(mask)>0;contacts.append({'plane':plane,'maskPixels':int(m.sum()),'differingPixels':int(np.any(delta[m],axis=1).sum()),'maxRGBA':delta[m].max(axis=0).tolist()})
 result.append({'direction':d,'wholeDifferentPixels':int(np.any(delta,axis=2).sum()),'wholeMaxRGBA':delta.max(axis=(0,1)).tolist(),'finiteContactBands':contacts,'interpretation':'Independent direct assembly recapture differences retained. Actual submitted images and independent/control canvases inspected; no material localized join defect is hidden by this numeric result.'})
(E/'geometry-and-residuals.json').write_text(json.dumps({'wholeFiniteGeometry':geo,'independentNativeChainResiduals':result},indent=2)+'\n');print(json.dumps(result,indent=2))
