import bpy,json,math,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;O=R.parents[1];H=O/'source/resources/approved-human-v3';F=O/'source/round-04.blend';E=O/'inputs/paired-native/dock-entry-round-06.blend'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(F));sc=bpy.context.scene;fr=bpy.data.objects['dock-floor__root'];fr.rotation_euler=(0,0,0)
with bpy.data.libraries.load(str(E),link=False) as (a,b):b.collections=['S33_PROP_dock-entry']
ec=b.collections[0];sc.collection.children.link(ec);ec.hide_render=False;ec.hide_viewport=False;er=bpy.data.objects['dock-entry__root'];er.location=(0,-1.5,0);er.rotation_euler=(0,0,0);bpy.context.view_layer.update()
# Shared boundary extraction is independent of the supplied validation and nominal substitution.
def surface(col):
 dg=bpy.context.evaluated_depsgraph_get();vs=[];ps=[];edges=[];ends=[]
 for o in col.all_objects:
  if o.type!='MESH' or o.hide_render:continue
  e=o.evaluated_get(dg);m=e.to_mesh();v=[e.matrix_world@p.co for p in m.vertices];off=len(vs);vs.extend(v);ps.extend([tuple(off+i for i in p.vertices) for p in m.polygons]);
  for p in m.polygons:
   n=(e.matrix_world.to_3x3().inverted().transposed()@p.normal).normalized();q=[v[i] for i in p.vertices]
   if n.z>.999999:
    for a,b in zip(q,q[1:]+q[:1]):
     if max(abs(a.y+1.5),abs(b.y+1.5))<1e-6 and abs(a.x-b.x)>1e-8:edges.append({'object':o.name,'nativePolygon':p.index,'p':list(a),'q':list(b),'normal':list(n)})
   if abs(n.y)>.999999 and all(abs(x.y+1.5)<1e-6 for x in q) and max(x.z for x in q)>.20 and min(x.z for x in q)<.20:ends.append({'object':o.name,'nativePolygon':p.index,'normal':list(n),'vertices':[list(x) for x in q]})
  e.to_mesh_clear()
 return BVHTree.FromPolygons(vs,ps,epsilon=1e-9),edges,ends
fb,fe,ff=surface(bpy.data.collections['WarmSoft_dock-floor']);eb,ee,ef=surface(ec)
def hits(edges,x):
 out=[]
 for e in edges:
  a,b=e['p'],e['q']
  if min(a[0],b[0])-1e-9<=x<=max(a[0],b[0])+1e-9:
   t=(x-a[0])/(b[0]-a[0]);out.append([a[k]+t*(b[k]-a[k]) for k in range(3)])
 return out
samples=[]
for i in range(157):
 x=-.39+.78*i/156;a=hits(fe,x);b=hits(ee,x);samples.append({'x':x,'floor':a,'entry':b,'maxYMismatch':max(abs(p[1]-q[1]) for p in a for q in b) if a and b else None,'maxZMismatch':max(abs(p[2]-q[2]) for p in a for q in b) if a and b else None})
profile={'floorBoundary':fe,'entryBoundary':ee,'floorEndFaces':ff,'entryEndFaces':ef,'samples':samples,'missing':sum(s['maxZMismatch'] is None for s in samples),'maxYMismatch':max(s['maxYMismatch'] for s in samples if s['maxYMismatch'] is not None),'maxZMismatch':max(s['maxZMismatch'] for s in samples if s['maxZMismatch'] is not None)}
# Actual current approved actor, preserve authored scale before/after native clip application.
rig=json.loads((H/'rig.json').read_text());name=rig['groundRootObject']
with bpy.data.libraries.load(str(H/'customer-rosa-approved.blend'),link=False) as (a,b):b.collections=[n for n in a.collections if n=='S33_PROP_customer-rosa' or n=='WarmSoft_customer-rosa']
if not b.collections:
 with bpy.data.libraries.load(str(H/'customer-rosa-approved.blend'),link=False) as (a,b):b.collections=a.collections
cols=b.collections
# Native actions are fake-user resources, not collection dependencies; append the exact walk cohort explicitly.
with bpy.data.libraries.load(str(H/'customer-rosa-approved.blend'),link=False) as (a,bd):bd.actions=sorted({t['action'] for t in rig['clips']['walk']['actions']})
for c in cols:
 if c and c.name not in [x.name for x in sc.collection.children]:sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
hr=bpy.data.objects[name];hc=next(c for c in cols if c and hr in list(c.all_objects))
spec=importlib.util.spec_from_file_location('review_approved_native_actions',H/'native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
path=[[0,-2.1,0],[0,-1.9,.0733333333],[0,-1.75,.1466666667],[0,-1.55,.22],[0,-1.5,.22],[0,-1.3,.22],[.15,-.65,.22],[0,.12,.22],[.78,-.18,.22]];records=[]
for i,pos in enumerate(path):
 native.apply_clip({'root':hr,'collection':hc},rig,'walk',i+1,'S',sc);hr.location=pos;hr.rotation_euler=(0,0,0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();shoes=[]
 for o in hc.all_objects:
  if o.type!='MESH' or o.hide_render or not any(x in o.name.lower() for x in ['shoe','sole','foot']):continue
  e=o.evaluated_get(dg);m=e.to_mesh();v=[e.matrix_world@p.co for p in m.vertices];bottom=[]
  for p in m.polygons:
   n=(e.matrix_world.to_3x3().inverted().transposed()@p.normal).normalized()
   if n.z<-.5:
    q=[v[j] for j in p.vertices];q.append(sum(q,Vector())/len(q))
    for a in q:
     h=[]
     for tree in [fb,eb]:
      hit,n,idx,dist=tree.ray_cast(Vector((a.x,a.y,2)),Vector((0,0,-1)),4)
      if hit is not None:h.append(hit.z)
     support=max(h) if h else 0
     bottom.append({'world':list(a),'supportZ':support,'soleMinusSupport':a.z-support})
  shoes.append({'name':o.name,'bounds':[[min(a[k] for a in v) for k in range(3)],[max(a[k] for a in v) for k in range(3)]],'bottomSurfaceSamples':bottom,'minBottomMinusSupport':min(a['soleMinusSupport'] for a in bottom) if bottom else None,'minZRelativeToRoot':min(a.z for a in v)-pos[2]});e.to_mesh_clear()
 records.append({'pathIndex':i,'walkFrame':i+1,'rootWorld':pos,'authoredRootScale':list(hr.scale),'shoes':shoes})
report={'candidatePacketSHA256':'205ed0c5916ae2a063423879d771351b4a52999391671f4f6f483c402921378d','method':'Independent actual native source append in background process only; evaluated shared boundary segments and actual current approved walk shoe bottom surface against native support BVHs. Ground outside support footprint is treated asZ0. No source/model saved; no actor fitting/root scale changed.','sourceHashes':{'floor':sha(F),'entry':sha(E),'approvedRosa':sha(H/'customer-rosa-approved.blend'),'rig':sha(H/'rig.json'),'nativeActions':sha(H/'native_actions.py')},'profile':profile,'human':records}
(R/'own-profile-and-human-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('OWN_PROFILE_HUMAN',json.dumps({'missingBoundarySamples':profile['missing'],'maxYZMismatch':[profile['maxYMismatch'],profile['maxZMismatch']],'shoeContacts':[(r['pathIndex'],[s['minBottomMinusSupport'] for s in r['shoes']]) for r in records]}))
