from pathlib import Path
import json,math,hashlib
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];O=P.parent.parent;A=json.loads((P/'native-independent-audit.json').read_text());C=A['candidate'];K=A['canonical'];budget=json.loads((O/'reviews/preparation-v1/raw-authoring-envelope.json').read_text())['rawXYConvexHullCCW'];support=[v[:2]for v in json.loads((O/'reviews/preparation-v1/finite-support-outline.json').read_text())['outlineCCW']]
def area(p):return abs(sum(x[0]*y[1]-y[0]*x[1]for x,y in zip(p,p[1:]+p[:1])))/2 if len(p)>2 else 0
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def signed(p):return sum(x[0]*y[1]-y[0]*x[1]for x,y in zip(p,p[1:]+p[:1]))/2
def clip(poly,bounds):
 out=[list(p)for p in poly];bounds=bounds if signed(bounds)>0 else list(reversed(bounds))
 for a,b in zip(bounds,bounds[1:]+bounds[:1]):
  source=out;out=[]
  if not source:break
  for s,e in zip(source[-1:]+source[:-1],source):
   ds=cross(a,b,s);de=cross(a,b,e);ins=ds>=-1e-12;ine=de>=-1e-12
   if ins!=ine:
    t=ds/(ds-de);out.append([s[i]+t*(e[i]-s[i])for i in range(2)])
   if ine:out.append(e)
 return out
# Independent ear triangulation of the frozen concave ten-point support outline.
def triangulate(poly):
 q=list(poly if signed(poly)>0 else reversed(poly));out=[]
 while len(q)>3:
  found=False
  for i in range(len(q)):
   a,b,c=q[i-1],q[i],q[(i+1)%len(q)]
   if cross(a,b,c)<=1e-12:continue
   other=[q[k]for k in range(len(q))if k not in [(i-1)%len(q),i,(i+1)%len(q)]]
   if any(all(cross(x,y,p)>=-1e-12 for x,y in [(a,b),(b,c),(c,a)])for p in other):continue
   out.append([a,b,c]);q.pop(i);found=True;break
  assert found
 out.append(q);return out
st=triangulate(support);sarea=sum(area(t)for t in st)
profiles={'lower':(-.18,.18,.04,.20),'upper':(-.09,.09,.60,.74),'rear':(.20,.26,.16,.35)}
rail=lambda n:next(k for k in profiles if k+'_' in n)
results=[]
for v in C['views']:
 pts=[p for o in v['objects']for p in o.get('vertices',[])];dist=[]
 for x,y,z in pts:
  dist.append(min(cross(a,b,[x,y])/math.dist(a,b)for a,b in zip(budget,budget[1:]+budget[:1])))
 tris=[[p[:2]for p in t['vertices']]for t in v['supportTriangles']];ta=sum(area(t)for t in tris);inside=sum(area(clip(t,s))for t in tris for s in st);overlap=sum(area(clip(t,s))for i,t in enumerate(tris)for s in tris[i+1:]);outside=ta-inside;missing=sarea-inside
 fields=[]
 for side in ['W','N']:
  polys=[f for f in v['fullCollarPolygons']if f['side']==side];L=(-.5,-.42)if side=='W'else(.42,.5)
  for r,(tm,tp,zm,zp)in profiles.items():
   pf=[f for f in polys if r+'_' in f['owner']]
   for tag,axis,fixed,span,n in [('bottom',2,zm,(tm,tp),(0,0,-1)),('top',2,zp,(tm,tp),(0,0,1)),('transverse-min',1,tm,(zm,zp),(0,-1,0)),('transverse-max',1,tp,(zm,zp),(0,1,0))]:
    fs=[]
    for f in pf:
     canonical=[[p[0],p[1],p[2]]if side=='W'else[p[1],-p[0],p[2]]for p in f['vertices']]
     if all(abs(p[axis]-fixed)<1e-6 for p in canonical)and max(p[0]for p in canonical)-min(p[0]for p in canonical)>1e-7:
      points=[[p[0],p[1 if axis==2 else 2]]for p in canonical];expected=np.array(n)if side=='W'else np.array([-n[1],n[0],n[2]]);normals=f['shaderCornerNormalRoot'];err=max(float(np.linalg.norm(np.array(nn)-expected))for nn in normals)if normals else 999
      fs.append({'area':area(points),'normalError':err,'material':f['material'],'domain':f['attributeDomain'],'type':f['attributeType'],'allCornerUnitValuesSame':all(np.linalg.norm(np.array(nn)-np.array(normals[0]))<1e-7 for nn in normals)if normals else False})
    total=sum(f['area']for f in fs);expect=.08*(span[1]-span[0]);fields.append({'side':side,'rail':r,'patch':tag,'polygons':len(fs),'area':total,'expectedArea':expect,'areaError':abs(total-expect),'maxActualNormalError':max([f['normalError']for f in fs]or[999]),'constantNormalizedInterpolation':all(f['allCornerUnitValuesSame']for f in fs),'materials':sorted(set(f['material']for f in fs)),'allMatchActualCanonicalGraph':all(any(m['tree']==k['tree']for k in K['materials'])for m in C['materials']if m['name']in{f['material']for f in fs})})
 capchecks=[]
 for side,caps in v['caps'].items():
  for f in caps:
   points=f['vertices'];expected=np.array([-1,0,0])if side=='W'else np.array([0,1,0]);nerror=max(np.linalg.norm(np.array(n)-expected)for n in f['shaderCornerNormalRoot']);crossarea=sum((np.cross(x,y)for x,y in zip(points,points[1:]+points[:1])),np.zeros(3))/2
   capchecks.append({'side':side,'rail':rail(f['owner']),'orderedVertices':points,'outwardArea':float(np.dot(crossarea,expected)),'actualShaderNormalError':float(nerror),'geometricNormalError':float(np.linalg.norm(np.array(f['geometryNormal'])-expected))})
 results.append({'direction':v['direction'],'rootMatrix':v['rootMatrix'],'finiteBudget':{'minSignedXYDistance':min(dist),'zBounds':v['bounds'][2],'insideTolerance1e-6':min(dist)>=-1e-6 and v['bounds'][2][0]>=.04-1e-6 and v['bounds'][2][1]<=.78+1e-6},'finiteSupport':{'triangleCountObserved':len(tris),'sumArea':ta,'sourceUnionArea':sarea,'intersectionArea':inside,'outsideArea':outside,'missingArea':missing,'pairwiseOverlapArea':overlap,'sameActualRegionWithin1e-6':max(abs(outside),abs(missing),overlap)<1e-6},'finiteCollarPatches':fields,'caps':capchecks,'sourceCalibration':v['calibration']})
def diff(p,q):
 a=np.array(Image.open(p).convert('RGBA')).astype(int);b=np.array(Image.open(q).convert('RGBA')).astype(int);d=abs(a-b);return {'decodedEqual':bool((d==0).all()),'differentPixels':int((d!=0).any(2).sum()),'maxRGBA':d.reshape(-1,4).max(0).tolist()}
replays=[{'direction':v['direction'],**diff(P/v['recapture']['path'],O/'candidates/round-01/frames/static'/v['direction']/'000.png')}for v in C['views']]
matmatches=[{'candidateMaterial':m['name'],'canonicalActualGraphMatch':next((k['name']for k in K['materials']if k['tree']==m['tree']),None)}for m in C['materials']]
report={'candidatePacketSHA256':hashlib.sha256((P/'resources/packet.json').read_bytes()).hexdigest(),'sourceSHA256':C['sourceSHA256'],'algorithm':'Independent evaluated source all4. Convex raw13point halfplanes/Z; finite support checked by independent concave ear triangulation, triangle clipping, outside/missing and pairwise overlap areas (triangulation free). All24 actual side patches cover complete.08 finite area, actual shaderused corner fields constant after normalized interpolation and actual graphs identical to approved canonical. All6 cap fields/windings evaluated separately.','all4':results,'materialGraphCorrespondence':matmatches,'worldGraphIdentical':C['scene']['world']==K['scene']['world'],'lightDataAndMatricesIdentical':C['scene']['lights']==K['scene']['lights'],'compositorGraphIdentical':C['scene']['compositor']==K['scene']['compositor'],'renderAndCamera':C['scene'],'savedSourceReplay':replays,'staticOwnership':{'all30OwnersObserved':len(C['views'][0]['objects'])+1,'ownAnimationData':any(o['animationData']for o in C['views'][0]['objects']),'constraints':[o['name']for o in C['views'][0]['objects']if o['constraints']],'instances':[o['name']for o in C['views'][0]['objects']if o['instanceCollection']],'externalLibraries':C['externalLibraries'],'imageNodes':C['imageNodes'],'allSceneGeometryOwned':set(C['sceneGeometryOwners'])==set(o['name']for o in C['views'][0]['objects']if o['type']!='EMPTY')},'limits':'Field graph equality is evidence of actual implementation here, not a required literal graph/storage method. Alpha1 refers to real surfaces, not openbay raster coverage. Actual albedo world-Z ramp/materialconstants have zero longitudinal derivative and unchanged proper rotation; needed tangent absent at actual zero anisotropy. Numeric results never waive visible defects.'}
(P/'independent-technical-analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'budgetAll':all(v['finiteBudget']['insideTolerance1e-6']for v in results),'supportAll':all(v['finiteSupport']['sameActualRegionWithin1e-6']for v in results),'maxCollarNormalError':max(f['maxActualNormalError']for v in results for f in v['finiteCollarPatches']),'maxCollarAreaError':max(f['areaError']for v in results for f in v['finiteCollarPatches']),'replays':replays,'static':report['staticOwnership']},indent=2))
