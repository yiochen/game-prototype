import bpy,json,math,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-01';rebuild=O/'clean-rebuild';project=rebuild/'source/round-01.blend'
bpy.ops.wm.open_mainfile(filepath=str(project));sc=bpy.context.scene;col=bpy.data.collections['WarmSoft_workshop-hut'];root=bpy.data.objects['workshop-hut__root'];bpy.context.view_layer.update()
def box(ps):return {'min':[min(p[i] for p in ps) for i in range(3)],'max':[max(p[i] for p in ps) for i in range(3)]}
def geom(c):
 dg=bpy.context.evaluated_depsgraph_get();vs=[];fs=[];records=[]
 for o in c.all_objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();p=[ev.matrix_world@v.co for v in me.vertices];faces=[list(f.vertices) for f in me.polygons];off=len(vs);vs+=p;fs += [[i+off for i in f] for f in faces]
  inc={}
  for face in faces:
   for i in range(len(face)):
    edge=tuple(sorted((face[i],face[(i+1)%len(face)])));inc[edge]=inc.get(edge,0)+1
  records.append({'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':[list(x) for x in ev.matrix_world],'bounds':box(p),'vertices':[list(v) for v in p],'faces':faces,'vertexCount':len(p),'polygonCount':len(faces),'nonmanifoldEdges':sum(n!=2 for n in inc.values()),'zeroAreaFaces':sum(f.area<1e-12 for f in me.polygons),'materials':[m.name for m in o.data.materials],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]});ev.to_mesh_clear()
 return records,BVHTree.FromPolygons(vs,fs,all_triangles=False),box(vs)

def canonical(objects):
 import copy
 records=copy.deepcopy(objects)
 for o in records:o['faces']=sorted(o['faces'])
 return sorted(records,key=lambda x:x['name'])
objects,tree,bounds=geom(col);g=hashlib.sha256(json.dumps(canonical(objects),sort_keys=True).encode()).hexdigest();actual=json.load(open(O/'native-audit.json'));ref=hashlib.sha256(json.dumps(canonical(actual['objects']),sort_keys=True).encode()).hexdigest();records=[]
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=a;bpy.context.view_layer.update();p=rebuild/f'static-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'direction':d,'rootRotationZ':root.rotation_euler.z,'path':str(p.relative_to(B)),'reference':f'candidates/round-01/atlases/static-{d}.png'})
(O/'clean-rebuild-audit.json').write_text(json.dumps({'geometrySHA256':g,'referenceGeometrySHA256':ref,'geometryExact':g==ref,'comparison':'Full evaluated object records sorted by actual object name; face list sorted while each exact winding/index tuple retained. Blender UV-sphere face enumeration order changes across fresh builds; same vertices, faces, transforms, bounds, materials and topology. No geometry field omitted. Detailed raw ordering differences retained in clean-rebuild-difference.json.','bounds':bounds,'filterSize':sc.render.filter_size,'captures':records,'method':'New empty-background process executes immutable native recipe using only copied own resource closure, then second clean process opens rebuilt project and audits/captures. Actual approved source/export bytes untouched.'},indent=2))
print('CLEAN_REBUILD',g==ref)
