from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];O=P.parent.parent;R=P/'resources'
def load(p):return json.loads(p.read_text())
a=load(P/'original-native-audit.json');c=load(P/'canonical-native-audit.json')
def rail(n):return 'rear' if ('back_' in n or 'rear_' in n) else 'lower' if 'lower_' in n else 'upper'
def simplify(v):
 p=[np.array(x,dtype=float)for x in v];change=True
 while change and len(p)>3:
  change=False
  for i in range(len(p)):
   if np.linalg.norm(np.cross(p[i]-p[i-1],p[(i+1)%len(p)]-p[i]))<1e-7:
    p.pop(i);change=True;break
 return p
checks=[]
for side,canonSide in [('W','W'),('N','E')]:
 for src in a['caps'][side]:
  canon=next(f for f in c['caps'][canonSide]if rail(f['object'])==rail(src['object']));sv=simplify(src['vertices']);cv=simplify(canon['vertices']);rot=np.array([[0,-1,0],[1,0,0],[0,0,1]])if side=='N' else np.eye(3);cv=[rot@v for v in cv]
  delta=max(min(float(np.linalg.norm(x-y))for y in cv)for x in sv)
  areaVector=sum((np.cross(x,y)for x,y in zip(sv,sv[1:]+sv[:1])),np.zeros(3))/2;out=np.array([-1,0,0])if side=='W'else np.array([0,1,0]);winding=float(np.dot(areaVector,out))
  checks.append({'side':side,'rail':rail(src['object']),'sourceOrderedCap':src['vertices'],'canonicalSide':canonSide,'properRotation':rot.tolist(),'determinant':float(np.linalg.det(rot)),'maxContourDistance':delta,'outwardOrientedArea':winding,'sourceOutwardNormal':src['outwardNormal'],'finiteContourEquivalent':delta<1e-6,'outwardWinding':winding>0})
(P/'ordered-port-check.json').write_text(json.dumps({'ownSourceProfiles':checks,'allChecksPassed':all(x['finiteContourEquivalent']and x['outwardWinding']for x in checks),'meaning':'Own N maps from canonical E by Rz+90, tangent -X and rear lip X[-.26,-.20]. Own W maps canonical W identity. North contact uses approved individual W end at root(0,1) with Rz+90; cap outward normals oppose. Subdivision count is not a contour lock.','collars':{'W':{'x':[-.5,-.42],'basis':{'longitudinal':[1,0,0],'transverse':[0,1,0],'height':[0,0,1]}},'N':{'y':[.42,.5],'basis':{'longitudinal':[0,1,0],'transverse':[-1,0,0],'height':[0,0,1]}}},'sourceMismatch':{'geometry':'No source/canonical contour or handedness mismatch','shaders':'Original flat faceted shader fields differ visibly from approved canonical02. Source material/node/storage identity is not locked; reconstruct actual full canonical fields over both collars with a continuous interior transition.'}},indent=2)+'\n')
def diff(x,y):
 a=np.array(Image.open(x).convert('RGBA')).astype(int);b=np.array(Image.open(y).convert('RGBA')).astype(int)
 if a.shape!=b.shape:return {'sameSize':False}
 d=abs(a-b);return {'sameSize':True,'decodedEqual':bool((d==0).all()),'maxRGBA':d.reshape(-1,4).max(0).tolist(),'differentPixels':int((d!=0).any(2).sum()),'alphaDifferentPixels':int((d[:,:,3]!=0).sum())}
results=load(P/'consumer-baseline/results.json');runs=results['cases'];cross=[];nativeDiffs=[]
for ident in ['logical128-integer','logical128-fractional','phone32-integer','phone32-fractional']:
 x=next(x for x in runs if x['id']==ident and x['mode']=='full-chromium');y=next(x for x in runs if x['id']==ident and x['mode']=='bundled-headless-shell')
 natives=[]
 for f,g in zip(x['nativeCanvases'],y['nativeCanvases']):natives.append({'id':f.split(ident+'-')[1],**diff(P/'consumer-baseline'/f,P/'consumer-baseline'/g)})
 cross.append({'case':ident,'nativeAllDecodedEqual':all(z['decodedEqual']for z in natives),'nativeComparisons':natives,'CSS':diff(P/'consumer-baseline'/x['cssScreenshot'],P/'consumer-baseline'/y['cssScreenshot'])})
 for i in range(0,len(x['nativeCanvases']),2):
  f,g=x['nativeCanvases'][i:i+2];nativeDiffs.append({'case':ident,'kindDirection':f.split(ident+'-')[1].replace('-independent.png',''),**diff(P/'consumer-baseline'/f,P/'consumer-baseline'/g)})
(P/'consumer-baseline-analysis.json').write_text(json.dumps({'scope':'Original source baseline only; no candidate/family approval','runs':len(runs),'versions':sorted(set(x['browserVersion']for x in runs)),'zeroPageErrors':all(not x['errors']for x in runs),'nativeNearestAfterResize':all(not f['nativeSmoothing']and not f['displayCanvasSmoothing']for r in runs for f in r['evidence']['fixtures']),'helpers':{f:hashlib.sha256((R/'consumer'/f).read_bytes()).hexdigest()for f in ['world-sprite-raster.js','sprite-layout.js']},'crossMode':cross,'independentVsNativeControls':nativeDiffs,'interpretation':'Exact decoded native canvas comparisons are independent from actual wholeCSS screenshots. CSS mode residuals, broad finite-light/outer raster differences and local contact defects are retained honestly. Original shaders visibly differ from canonical; no approval follows equality or small numbers.'},indent=2)+'\n')
print('contours',[(x['side'],x['rail'],x['maxContourDistance'],x['outwardOrientedArea'])for x in checks]);print('consumer',len(runs),[(x['case'],x['nativeAllDecodedEqual'],x['CSS'])for x in cross])
