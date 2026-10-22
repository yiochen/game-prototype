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

objects,tree,bounds=geom(col);g=hashlib.sha256(json.dumps(sorted(objects,key=lambda x:x['name']),sort_keys=True).encode()).hexdigest();actual=json.load(open(O/'native-audit.json'));ref=hashlib.sha256(json.dumps(sorted(actual['objects'],key=lambda x:x['name']),sort_keys=True).encode()).hexdigest();records=[]

old={o['name']:o for o in actual['objects']};new={o['name']:o for o in objects};diffs=[]
for name in old.keys()|new.keys():
 if name not in old or name not in new:diffs.append({'name':name,'missing':True});continue
 for k in old[name]:
  if old[name][k]!=new[name][k]:
   a,b=old[name][k],new[name][k]
   if k in ['vertices','matrixWorld','location','rotation','scale']:
    import itertools
    def flat(v):
     for x in v:
      if isinstance(x,list):yield from flat(x)
      else:yield x
    aa=list(flat(a));bb=list(flat(b));delta=max(abs(x-y) for x,y in zip(aa,bb)) if len(aa)==len(bb) else None
    diffs.append({'name':name,'field':k,'maxDifference':delta,'firstOld':aa[:6],'firstNew':bb[:6]})
   else:diffs.append({'name':name,'field':k,'old':a if k not in ['faces'] else str(a)[:200],'new':b if k not in ['faces'] else str(b)[:200]})
(O/'clean-rebuild-difference.json').write_text(json.dumps({'differences':diffs},indent=2));print(json.dumps(diffs)[:8000])
