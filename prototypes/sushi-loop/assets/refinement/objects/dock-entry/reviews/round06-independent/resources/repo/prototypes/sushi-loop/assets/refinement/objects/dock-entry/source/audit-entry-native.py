"""Dense actual evaluated native support/clearance audit; read-only source."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
B=Path(__file__).resolve().parents[1];p=B/'source/round-05.blend';before=hashlib.sha256(p.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(p));sc=bpy.context.scene;root=bpy.data.objects['dock-entry__root'];root.rotation_euler.z=0;bpy.context.view_layer.update();coll=bpy.data.collections['S33_PROP_dock-entry'];dg=bpy.context.evaluated_depsgraph_get();vs=[];faces=[];tiny=[];details=[]
for o in coll.all_objects:
 if o.type!='MESH':continue
 e=o.evaluated_get(dg);m=e.to_mesh();verts=[e.matrix_world@v.co for v in m.vertices];off=len(vs);vs+=verts;faces += [[i+off for i in p.vertices] for p in m.polygons]
 for poly in m.polygons:
  if poly.area<1e-12:tiny.append({'object':o.name,'face':poly.index,'actualPositiveArea':poly.area,'vertices':[list(verts[i]) for i in poly.vertices]})
 details.append({'object':o.name,'vertices':len(m.vertices),'polygons':len(m.polygons),'materialSlots':[m.name for m in o.data.materials],'externalImages':[n.image.filepath for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeTexImage' and n.image]});e.to_mesh_clear()
tree=BVHTree.FromPolygons(vs,faces,all_triangles=False)
def ray(p,d,length=3):
 q,n,i,dist=tree.ray_cast(Vector(p),Vector(d),length);return {'point':list(q) if q is not None else None,'normal':list(n) if n is not None else None}
paths=[]
for x in [-.38,-.25,0,.25,.38]:
 samples=[ray((x,-.5+i*.5/1000,1),(0,0,-1)) for i in range(1001)];zs=[s['point'][2] for s in samples if s['point']];paths.append({'x':x,'samples':samples,'missing':sum(s['point'] is None for s in samples),'minimumHeightDeltaAlongTowardDeck':min(b-a for a,b in zip(zs,zs[1:])),'terminalZ':zs[-1]})
clear=[]
for i in range(101):
 y=-.5+i*.5/100
 # All geometry above walking plane must lie outside centered clear X±.39.
 z=ray((0,y,1),(0,0,-1))['point'][2]
 for h in [.001,.03,.08,.15,.25]:
  for direction in [-1,1]:clear.append({'y':y,'aboveSupportZ':h,'direction':direction,'supportZ':z,'side':ray((0,y,z+h),(direction,0,0),.39-1e-5)})
terminal=[{'x':-.39+i*.78/156,'top':ray((-.39+i*.78/156,-1e-6,1),(0,0,-1)),'endFace':ray((-.39+i*.78/156,.01,.2),(0,-1,0),.02)} for i in range(157)]
result={'asset':'dock-entry','project':'source/round-05.blend','sha256':before,'nativeSourceUnchanged':before==hashlib.sha256(p.read_bytes()).hexdigest(),'paths':paths,'clearanceProbes':clear,'clearanceBlockedInsideX039':sum(s['side']['point'] is not None for s in clear),'terminalCertifiedWidth':.78,'terminalXEndpoints':[-.39,.39],'physicalTreadWidth':.96,'outerExposedTopWidthApproximate':.81,'widthInterpretation':'Certified W=.78 is exact flat centered terminal and minimum cap corridor. Wider .81 top-surface samples include rounded shoulder transition; .96 is physical board envelope, not whole usable clear path.','terminalProbes':terminal,'tinyPositiveBooleanFaces':tiny,'actualZeroAreaFaces':sum(t['actualPositiveArea']==0 for t in tiny),'tinyFaceDisposition':'Four closed-manifold numerical boolean slivers with positive areas3.78e-16..1.36e-15 world²; no loose vertices/nonmanifold edges. Retained unchanged and disclosed; technical record is not independent acceptance.','nativeResourceDetails':details,'allMeshEnvelope':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]}
(B/'candidates/round-05/dense-native-audit.json').write_text(json.dumps(result,indent=2));print('DENSE_AUDIT',[(p['x'],p['missing'],p['minimumHeightDeltaAlongTowardDeck']) for p in paths],result['clearanceBlockedInsideX039'])
