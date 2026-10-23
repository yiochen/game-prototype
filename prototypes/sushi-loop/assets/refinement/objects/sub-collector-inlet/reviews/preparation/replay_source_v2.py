import bpy,json,pathlib,math,hashlib,importlib.util
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
O=pathlib.Path(__file__).resolve().parent; E=O.parent.parent; R=O/'resources'; D=O/'native-source';D.mkdir(exist_ok=True)
def load(name):return json.loads(next(R.glob('*-'+name)).read_text())
rig=load('source-rig.json');cm=load('source-camera.json');root=bpy.data.objects[rig['groundRootObject']];col=root.users_collection[0];s=bpy.context.scene
spec=importlib.util.spec_from_file_location('saved_native_actions',next(R.glob('*-native_actions.py')));A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
# Only alter the background replay scene. Source files remain immutable.
for child in list(s.collection.children):
 if child!=col:s.collection.children.unlink(child)
if col.name not in s.collection.children:s.collection.children.link(col)
for o in list(s.collection.objects):
 if o.type not in {'CAMERA','LIGHT'}:s.collection.objects.unlink(o)
col.hide_render=False;col.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False
def enable_layer(l):
 l.exclude=False;l.hide_viewport=False;l.collection.hide_render=False;l.collection.hide_viewport=False
 for ch in l.children:enable_layer(ch)
enable_layer(bpy.context.view_layer.layer_collection)
for ob in col.all_objects:ob.hide_set(False)
bpy.context.view_layer.update()
cam=s.camera;cam.matrix_world=Matrix(cm['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_x=0;cam.data.shift_y=0
s.render.resolution_x=384;s.render.resolution_y=704;s.render.resolution_percentage=100;s.render.pixel_aspect_x=cm['camera']['pixelAspect'][0];s.render.pixel_aspect_y=cm['camera']['pixelAspect'][1]
def px(p):
 q=world_to_camera_view(s,cam,Vector(p));return [q.x*s.render.resolution_x,(1-q.y)*s.render.resolution_y]
bpy.context.view_layer.update();base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-base[1];cam.data.shift_y=(496-base[1])/dy;bpy.context.view_layer.update()
s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='8';s.render.fps=12
asset={'root':root,'collection':col}; records=[]
def bounds(ps):return [[min(p[i] for p in ps) for i in range(len(ps[0]))],[max(p[i] for p in ps) for i in range(len(ps[0]))]]
def measure(clip,di,fr):
 A.apply_clip(asset,rig,clip,fr,di,s);dg=bpy.context.evaluated_depsgraph_get();verts=[];parts=[]
 for o in col.all_objects:
  if o.type!='MESH':continue
  eo=o.evaluated_get(dg);me=eo.to_mesh();p=[eo.matrix_world@v.co for v in me.vertices];verts+=p;parts.append({'name':o.name,'bounds':bounds(p),'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrix':[list(r) for r in o.matrix_world]});eo.to_mesh_clear()
 return {'clip':clip,'direction':di,'frame':fr,'worldBounds':bounds(verts),'logicalBounds':bounds([[v/2 for v in px(p)] for p in verts]),'parts':parts,'rootMatrix':[list(r) for r in root.matrix_world]}
for clip in ['idle','active']:
 for di in 'NESW':
  for fr in range(1,2 if clip=='idle' else 14):
   r=measure(clip,di,fr);path=D/f'{clip}-{di}-{fr:02d}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);r['image']=str(path.relative_to(E));r['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();r['closureOnly']=fr==13;records.append(r)
A.apply_clip(asset,rig,'idle',1,'S',s)
# Explicitly retain every clip action in the closed replay source.
for clip in rig['clips'].values():
 for ar in clip['actions']:bpy.data.actions[ar['action']].use_fake_user=True
bpy.data.libraries.write(str(R/'source-replay.blend'),{s,*[bpy.data.actions[ar['action']] for c in rig['clips'].values() for ar in c['actions']]},fake_user=True,compress=True)
settings={'engine':s.render.engine,'frame':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'cameraMatrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'rootPx':px((0,0,0)),'unitX':px((1,0,0)),'unitY':px((0,1,0)),'unitZ':px((0,0,1)),'world':s.world.name,'lights':[{'name':o.name,'power':o.data.energy,'position':list(o.location),'size':o.data.size} for o in s.objects if o.type=='LIGHT'],'view':{'transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'compositor':str(s.compositing_node_group.name) if s.compositing_node_group else None,'resources':{'libraries':[l.filepath for l in bpy.data.libraries],'activeMaterialImages':[]}}
(O/'source-replay-audit.json').write_text(json.dumps({'sourceLibrary':str(R/'source-library.blend'),'cameraSource':str(next(R.glob('*-source-camera.json'))),'rigSource':str(next(R.glob('*-source-rig.json'))),'settings':settings,'records':records,'runtimeFrameCount':52,'closureFrames':4},indent=2)+'\n')
print('REPLAY COMPLETE',len(records))
