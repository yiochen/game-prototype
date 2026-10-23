"""Diagnostic only: exact old own native source at frozen transform, static frozen body; no fitting or candidate edits."""
import bpy,json,pathlib,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parent;R=P/'resources';sc=bpy.context.scene;main=bpy.data.objects['submarine-yellow__root'];main.location=(0,0,0);main.rotation_euler=(0,0,0)
for owner,an in json.loads(main['nativeActions'])['upgraded-dock-ready'].items():
 o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
sc.frame_set(1);bpy.context.view_layer.update()
# Freeze the entire main cohort at its native neutral frame before evaluating own frames.
for o in sc.objects:
 if o.animation_data:o.animation_data_clear()
 if o.name.startswith('PROVISIONAL__harpoon_'):o.hide_render=True;o.hide_viewport=True
for mat in bpy.data.materials:
 if mat.node_tree and mat.node_tree.animation_data:mat.node_tree.animation_data_clear()
with bpy.data.libraries.load(str(R/'own-original-library.blend'),link=False) as (src,dst):
 dst.collections=['S33_PROP_harpoon_mount.001'];dst.actions=[a for a in src.actions if 'sub-harpoon-mount' in a]
c=next(x for x in bpy.data.collections if x.name.startswith('S33_PROP_harpoon_mount'));sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
own=next(o for o in c.all_objects if o.type=='EMPTY');mount=bpy.data.objects['MOUNT__sub-harpoon-mount'];own.parent=mount;own.location=(0,0,0);own.rotation_euler=(0,0,0);own.scale=(1,1,1)
rig=json.loads((R/'inputs/source-rig.json').read_text());outputs=[];phases=[];renderdir=P/'native-mounted-source';renderdir.mkdir(exist_ok=True)
def assign(f):
 for t in rig['clips']['active']['actions']:
  o=bpy.data.objects[t['ownerName']];o.animation_data_create();a=bpy.data.actions[t['action']];o.animation_data.action=a;o.animation_data.action_slot=next(s for s in a.slots if s.identifier==t['slotIdentifier'])
 sc.frame_set(f);bpy.context.view_layer.update()
def mesh(o):
 eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh();vs=[eo.matrix_world@v.co for v in me.vertices];fs=[list(p.vertices) for p in me.polygons];eo.to_mesh_clear();return vs,fs
def tree(o):
 v,f=mesh(o);return BVHTree.FromPolygons(v,f,all_triangles=False,epsilon=0)
def bb(v):return [[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]]
main.rotation_euler.z=0;assign(1)
frozenMainTransforms={o.name:[list(r) for r in o.matrix_local] for o in sc.objects if o.name not in c.all_objects}
mainmeshes=[o for o in sc.objects if o.type=='MESH' and o.name not in c.all_objects and not o.hide_render]
for f in range(1,13):
 assign(f);pairs=[]
 for o in c.all_objects:
  if o.type!='MESH':continue
  a=tree(o)
  for b in mainmeshes:
   hits=a.overlap(tree(b))
   if hits:pairs.append({'own':o.name,'main':b.name,'trianglePairCount':len(hits)})
 vs=[v for o in c.all_objects if o.type=='MESH' for v in mesh(o)[0]]
 phases.append({'frame':f,'bounds':bb(vs),'nativeTriangleOverlaps':pairs,'frozenMainTransformMaxError':max(abs(o.matrix_local[i][j]-frozenMainTransforms[o.name][i][j]) for o in sc.objects if o.name in frozenMainTransforms for i in range(4) for j in range(4))})
for d,ang in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 main.rotation_euler.z=ang
 for f in [1,6,12]:
  assign(f);dst=renderdir/f'old-own-on-frozen-main-{d}-{f:02}.png';sc.render.filepath=str(dst);bpy.ops.render.render(write_still=True)
  vs=[v for o in c.all_objects if o.type=='MESH' for v in mesh(o)[0]];xy=[]
  for v in vs:
   q=world_to_camera_view(sc,sc.camera,v);xy.append([q.x*640,(1-q.y)*768])
  outputs.append({'direction':d,'sourceFrame':f,'path':str(dst.relative_to(P)),'projectedComponentBounds':[[min(p[i] for p in xy) for i in range(2)],[max(p[i] for p in xy) for i in range(2)]]})
main.rotation_euler.z=0;assign(1)
(P/'mounted-source-audit.json').write_text(json.dumps({'qualification':'DIAGNOSTIC exact OLD unrefined own collection only; frozen body upgraded-dock-ready neutral frame1, other components explicitly PROVISIONAL; the own provisional harpoon is hidden and replaced by exact OLD own source. Not a candidate, approval, new fit or final assembled main.','mountMatrix':[list(r) for r in mount.matrix_world],'sourceRootLocalMatrix':[list(r) for r in own.matrix_local],'mainCamera':{'matrix':[list(r) for r in sc.camera.matrix_world],'orthoScale':sc.camera.data.ortho_scale,'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'phases':phases,'renders':outputs,'collisionLimit':'Native surface intersection diagnostic; exact finite-seat support is audited separately. Triangle nonintersection alone is not clearance acceptance.'},indent=2)+'\n')
print('MOUNTED_SOURCE_COMPLETE',len(outputs))
