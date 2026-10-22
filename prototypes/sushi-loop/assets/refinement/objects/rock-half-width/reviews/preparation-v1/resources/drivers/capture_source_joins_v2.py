import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
base=Path(__file__).resolve().parents[2];out=base/'evidence/source-joins-v2';out.mkdir(exist_ok=True)
record=json.loads((base/'resources/resource-inputs/source-camera.json').read_text());sc=bpy.context.scene;coll=bpy.data.collections['S33_PROP_rock-half-width.001'];root=bpy.data.objects['rock-half-width__root.001'];mesh=next(o for o in coll.all_objects if o.type=='MESH')
def layers(l):
 l.exclude=False;l.hide_viewport=False
 for c in l.children:layers(c)
for v in sc.view_layers:layers(v.layer_collection)
for c in sc.collection.children:c.hide_render=c!=coll;c.hide_viewport=c!=coll
coll.hide_render=False;coll.hide_viewport=False
for o in coll.all_objects:o.hide_set(False);o.hide_render=False;o.hide_viewport=False
camdata=bpy.data.cameras.new('Source join diagnostic camera');cam=bpy.data.objects.new('Source join diagnostic camera',camdata);sc.collection.objects.link(cam);sc.camera=cam;cam.matrix_world=Matrix(record['camera']['worldMatrix']);camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL';camdata.ortho_scale=448/128
sc.render.resolution_x=1792;sc.render.resolution_y=2560;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=record['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.dither_intensity=0
sc.frame_set(1);bpy.context.view_layer.update()
def px(p):
 v=world_to_camera_view(sc,cam,Vector(p));return [v.x*1792,(1-v.y)*2560]
b=px((0,0,0));camdata.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-b[1];camdata.shift_y=(384*4-b[1])/dy;bpy.context.view_layer.update()
copies=[]
for dx in [-1,1]:
 o=mesh.copy();o.data=mesh.data;o.parent=None;coll.objects.link(o);copies.append(o)
ledger=[]
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:
 rot=Matrix.Rotation(math.radians(a),4,'Z');root.rotation_euler.z=math.radians(a)
 for o,dx in zip(copies,[-1,1]):o.matrix_world=rot@Matrix.Translation((dx,0,0))
 bpy.context.view_layer.update();sc.render.filepath=str(out/f'join-{d}.png');bpy.ops.render.render(write_still=True)
 ledger.append({'direction':d,'path':f'join-{d}.png','rootMatrices':[[list(r) for r in o.matrix_world] for o in [root]+copies],'nativeFrame':[1792,2560],'logicalFrame':[448,640],'logicalRoot':[224,384],'captureScale':4})
(out/'ledger.json').write_text(json.dumps({'method':'Exact unmodified native source copies at ±1 world cell, common registered camera/projection density. Expanded common canvas to avoid clipping in all four facings. Not a candidate.','renders':ledger,'measuredProjectedRoot':px((0,0,0))},indent=2)+'\n')
