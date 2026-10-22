from pathlib import Path
import json,gzip,hashlib,math
import numpy as np
R=Path(__file__).resolve().parent;B=R.parents[1]
with gzip.open(R/'own-native-geometry.json.gz','rt')as f:g=json.load(f)
plan=json.loads((R/'resources/plan.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest();refs={r['direction']:r for r in g['records']if r['case']['id']=='approach'};records=[]
def edges(obs,d):
 a={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d];c,s=math.cos(-a),math.sin(-a);segs=[]
 for ob in obs:
  v=np.array(ob['vertices']);v[:,:2]=v[:,:2]@np.array([[c,s],[-s,c]])
  for ids in ob['triangles']:
   q=v[ids,:];normal=np.cross(q[1]-q[0],q[2]-q[0]);length=np.linalg.norm(normal)
   if length<1e-12 or normal[2]/length<.99999:continue
   for p,z in zip(q,np.roll(q,-1,axis=0)):
    if max(abs(p[1]+1.5),abs(z[1]+1.5))<1e-5 and abs(p[0]-z[0])>1e-8 and min(p[2],z[2])>.21:segs.append({'owner':ob['name'],'p':p.tolist(),'q':z.tolist()})
 return segs
for d,r in refs.items():
 fe=edges(r['floor'],d);ee=edges(r['entry'],d);samples=[]
 for x in np.linspace(-.39,.39,157):
  def hits(es):
   out=[]
   for e in es:
    a,b=e['p'],e['q']
    if min(a[0],b[0])-1e-7<=x<=max(a[0],b[0])+1e-7:
     t=(x-a[0])/(b[0]-a[0]);out.append([a[i]+t*(b[i]-a[i])for i in range(3)])
   return out
  f,e=hits(fe),hits(ee);samples.append({'x':float(x),'floor':f,'entry':e,'maxYZDifference':max(max(abs(p[i]-q[i])for i in[1,2])for p in f for q in e)if f and e else None})
 records.append({'direction':d,'floorEdges':fe,'entryEdges':ee,'samples':samples,'missing':sum(s['maxYZDifference']is None for s in samples),'maxYZDifference':max(s['maxYZDifference']for s in samples if s['maxYZDifference']is not None)})
# Independently compare original companion evaluations to declared frozen source snapshot vertex hashes/matrices.
parity=[]
for row in plan['snapshotNativeVertexParity']:
 aid={'workshop-hut':'hut','submarine-yellow':'sub','dock-cover':'cover','approved-workshop-hut':'approvedHut'}[row['id']];by={o['name']:o for o in g['companionSourceFacingS'][aid]}
 for ob in row['objects']:
  own=by[ob['sourceObject']];digest=sha(json.dumps(own['vertices'],separators=(',',':')).encode());parity.append({'id':aid,'sourceObject':ob['sourceObject'],'ownWorldVertexSHA256':digest,'declaredSHA256':ob['worldVertexSHA256'],'exactVertexHashMatch':digest==ob['worldVertexSHA256'],'maxMatrixDelta':float(np.max(abs(np.array(own['matrix'])-np.array(ob['sourceMatrix']))))})
# Actual matrices/root/source pose rotate in common world, never separately solve per facing.
rot=[];base={r['case']['id']:r for r in g['records']if r['direction']=='S'}
for r in g['records']:
 a={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[r['direction']];c,s=math.cos(a),math.sin(a);M=np.array([[c,-s,0],[s,c,0],[0,0,1]]);maxerr=0
 for own,ref in zip(r['actor'],base[r['case']['id']]['actor']):maxerr=max(maxerr,float(np.max(np.linalg.norm(np.array(own['vertices'])-np.array(ref['vertices'])@M.T,axis=1))))
 rot.append({'direction':r['direction'],'case':r['case']['id'],'maxActorVertexDeltaFromRigidSRotation':maxerr,'maxRootDelta':float(np.max(abs(np.array(r['root'])-M@np.array([*r['case']['sourceFacingXY'],r['case']['solvedRootZ']])))),'authoredScale':r['authoredScale']})
summary={'sharedBoundary':records,'companionParity':parity,'allCompanionDeclaredVertexHashesExact':all(r['exactVertexHashMatch']for r in parity),'maxCompanionMatrixDelta':max(r['maxMatrixDelta']for r in parity),'commonWorldRotation':rot,'maxActorVertexRotationResidual':max(r['maxActorVertexDeltaFromRigidSRotation']for r in rot),'sourceCamera':g['camera'],'boundsS':{k:[np.min(np.concatenate([np.array(o['vertices'])for o in refs['S'][k]]),axis=0).tolist(),np.max(np.concatenate([np.array(o['vertices'])for o in refs['S'][k]]),axis=0).tolist()]for k in['floor','entry']}}
(R/'own-geometry-measurements.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'interface':[{k:v for k,v in r.items()if k in ['direction','missing','maxYZDifference']}for r in records],'companionHashesExact':summary['allCompanionDeclaredVertexHashesExact'],'companionMatrixDelta':summary['maxCompanionMatrixDelta'],'rotationResidual':summary['maxActorVertexRotationResidual']},indent=2))
