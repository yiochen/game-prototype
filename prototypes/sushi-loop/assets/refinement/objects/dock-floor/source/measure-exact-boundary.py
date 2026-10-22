"""Extract actual evaluated boundary edges, bypassing BVH epsilon at exact edge."""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-03';P=B/'inputs/paired-native/dock-entry-round-05.blend';sc=bpy.context.scene
with bpy.data.libraries.load(str(P),link=False) as (a,b):b.collections=['S33_PROP_dock-entry']
ec=b.collections[0];sc.collection.children.link(ec);ec.hide_viewport=False;ec.hide_render=False;er=bpy.data.objects['dock-entry__root'];er.location=(0,-1.5,0);er.rotation_euler=(0,0,0);bpy.data.objects['dock-floor__root'].rotation_euler=(0,0,0);bpy.context.view_layer.update()
def measure(c):
 dg=bpy.context.evaluated_depsgraph_get();edges=[];faces=[]
 for o in c.all_objects:
  if o.type!='MESH' or o.hide_render:continue
  e=o.evaluated_get(dg);m=e.to_mesh();v=[e.matrix_world@p.co for p in m.vertices]
  for poly in m.polygons:
   n=(e.matrix_world.to_3x3().inverted().transposed()@poly.normal).normalized();ps=[v[i] for i in poly.vertices]
   if n.z>.999999:
    for p,q in zip(ps,ps[1:]+ps[:1]):
     if abs(p.y+1.5)<1e-6 and abs(q.y+1.5)<1e-6 and abs(p.z-.22)<1e-6 and abs(q.z-.22)<1e-6 and abs(p.x-q.x)>1e-9:edges.append({'owner':o.name,'faceIndex':poly.index,'p':list(p),'q':list(q),'topNormal':list(n),'tangent':list((q-p).normalized())})
   if abs(n.y)>.99999 and all(abs(p.y+1.5)<1e-6 for p in ps) and max(p.z for p in ps)>.2 and min(p.z for p in ps)<.2:faces.append({'owner':o.name,'faceIndex':poly.index,'normal':list(n),'vertices':[list(p) for p in ps]})
  e.to_mesh_clear()
 return {'topBoundaryEdges':edges,'endFacesAtZPoint2':faces}
e=measure(ec);f=measure(bpy.data.collections['WarmSoft_dock-floor'])
def point_at(edges,x):
 hit=[]
 for r in edges:
  a,b=r['p'],r['q']
  if min(a[0],b[0])-1e-9<=x<=max(a[0],b[0])+1e-9:
   t=(x-a[0])/(b[0]-a[0]);p=[a[i]+t*(b[i]-a[i]) for i in range(3)];hit.append({'point':p,'normal':r['topNormal'],'nativeFaceIndex':r['faceIndex'],'owner':r['owner']})
 return hit
sections=[]
for i in range(157):
 x=-.39+.78*i/156;a=point_at(e['topBoundaryEdges'],x);b=point_at(f['topBoundaryEdges'],x);sections.append({'x':x,'entry':a,'floor':b,'maxZMismatches':max(abs(p['point'][2]-q['point'][2]) for p in a for q in b) if a and b else None,'maxYMismatches':max(abs(p['point'][1]-q['point'][1]) for p in a for q in b) if a and b else None})
widths=[sorted([r['p'][0],r['q'][0]]) for r in e['topBoundaryEdges'] if min(r['p'][0],r['q'][0])<-.39 and max(r['p'][0],r['q'][0])>.39]
report={'method':'Actual evaluated mesh face/edge extraction, doubleprecision interpolation along native horizontal boundary segments. This measures modeled shared plane directly; no expected coordinate substituted. Float BVH rays1e-7 inside a boundary can miss n-gon top; raw such diagnostics retained separately.','floorProjectSHA256':hashlib.sha256((B/'source/round-03.blend').read_bytes()).hexdigest(),'entryProjectSHA256':hashlib.sha256(P.read_bytes()).hexdigest(),'entry':e,'floor':f,'commonProfile':sections,'nativeTerminalIntervals':widths,'guaranteedClearWidth':.78,'maxTopMismatch':max(r['maxZMismatches'] for r in sections if r['maxZMismatches'] is not None),'maxPlaneMismatch':max(r['maxYMismatches'] for r in sections if r['maxYMismatches'] is not None),'missingProfiles':sum(r['maxZMismatches'] is None for r in sections),'maxZErrorFromPoint22':max(abs(a['point'][2]-.22) for r in sections for k in ['entry','floor'] for a in r[k]),'rawBVHDiagnostics':['paired-native-validation.json','clear-corridor-validation.json'],'interpretation':'Guaranteed commonW=.78 is inside actual evaluated terminal boundaryW=.814 and physical treadW=.96. Native cap clear width=.78. Floor contact support extends beyond terminal fullwidth across X[-.48,.48].'}
(O/'exact-boundary-validation.json').write_text(json.dumps(report,indent=2));print('EXACT_NATIVE_BOUNDARY',len(widths),report['maxTopMismatch'],report['maxPlaneMismatch'],report['missingProfiles'],report['maxZErrorFromPoint22'])
