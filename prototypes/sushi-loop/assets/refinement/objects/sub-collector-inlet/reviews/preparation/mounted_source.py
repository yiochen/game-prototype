import bpy,json,pathlib,hashlib,math,importlib.util
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
O=pathlib.Path(__file__).resolve().parent;R=O/'resources';E=O.parent.parent;D=O/'mounted-source';D.mkdir(exist_ok=True);s=bpy.context.scene;main=bpy.data.objects['submarine-yellow__root'];main.location=(0,0,0);main.rotation_euler=(0,0,0)
actions=json.loads(main['nativeActions'])
for owner,an in actions['upgraded-dock-ready'].items():
 o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
s.frame_set(1);bpy.context.view_layer.update()
with bpy.data.libraries.load(str(R/'source-replay.blend'),link=False) as (src,dst):
 dst.collections=['S33_PROP_collector_inlet.001']
col=dst.collections[0];s.collection.children.link(col);rig=json.loads(next(R.glob('*-source-rig.json')).read_text());root=bpy.data.objects[rig['groundRootObject']]
# Appending a collection may omit fake-user alternative actions, load them explicitly.
missing=[a['action'] for c in rig['clips'].values() for a in c['actions'] if a['action'] not in bpy.data.actions]
if missing:
 with bpy.data.libraries.load(str(R/'source-replay.blend'),link=False) as (src,dst):dst.actions=missing
spec=importlib.util.spec_from_file_location('saved_native',next(R.glob('*-native_actions.py')));A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
for o in s.objects:
 if o.name.startswith('PROVISIONAL__collector'):o.hide_render=True;o.hide_viewport=True
mount=bpy.data.objects['MOUNT__sub-collector-inlet'];root.parent=mount;root.matrix_parent_inverse=Matrix.Identity(4);root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1)
def en(l):
 l.exclude=False;l.hide_viewport=False
 for c in l.children:en(c)
en(bpy.context.view_layer.layer_collection);col.hide_render=False;col.hide_viewport=False
for o in col.all_objects:o.hide_set(False);o.hide_render=False;o.hide_viewport=False
A.apply_clip({'root':root,'collection':col},rig,'idle',1,'S',s)
def bb(ps):return [[min(p[i] for p in ps) for i in range(len(ps[0]))],[max(p[i] for p in ps) for i in range(len(ps[0]))]]
def px(p):
 q=world_to_camera_view(s,s.camera,Vector(p));return [q.x*s.render.resolution_x,(1-q.y)*s.render.resolution_y]
records=[]
for di,angle in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 main.rotation_euler.z=angle;s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pts=[]
 for o in col.all_objects:
  if o.type!='MESH':continue
  eo=o.evaluated_get(dg);me=eo.to_mesh();pts.extend(eo.matrix_world@v.co for v in me.vertices);eo.to_mesh_clear()
 p=D/f'legacy-collector-on-frozen-body-{di}.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'direction':di,'image':str(p.relative_to(E)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'ownWorldBounds':bb(pts),'ownLogicalBounds':bb([[v/2 for v in px(p)] for p in pts])})
main.rotation_euler.z=0;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();parts=[]
for o in col.all_objects:
 if o.type!='MESH':continue
 eo=o.evaluated_get(dg);me=eo.to_mesh();ps=[eo.matrix_world@v.co for v in me.vertices];faces=[]
 for f in me.polygons:
  n=(eo.matrix_world.to_3x3().inverted().transposed()@f.normal).normalized()
  if n.y>.999:faces.append({'normal':list(n),'bounds':bb([ps[i] for i in f.vertices]),'area':float(f.area)*.16})
 parts.append({'name':o.name,'bounds':bb(ps),'rearFaces':faces});eo.to_mesh_clear()
bpy.data.libraries.write(str(R/'source-mounted-replay.blend'),{s,*[bpy.data.actions[a['action']] for c in rig['clips'].values() for a in c['actions']]},fake_user=True,compress=True)
(O/'mounted-source-audit.json').write_text(json.dumps({'qualification':'Preparation reference only. Original canonical source replaces the provisional collector at the frozen transform; it is not a candidate and fails the reservation. Main body is static upgraded-dock-ready frame1; hull panels and harpoon remain clearly provisional. No active collector mapping into main.','mountMatrix':[list(r) for r in mount.matrix_local],'records':records,'canonicalSMountedParts':parts},indent=2)+'\n');print('MOUNTED SOURCE COMPLETE')
