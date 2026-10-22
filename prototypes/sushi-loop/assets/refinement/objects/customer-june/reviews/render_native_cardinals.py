import bpy,json,math,importlib.util
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).parent;OBJ=OUT.parent;REPO=OBJ.parents[5]
spec=importlib.util.spec_from_file_location('native',REPO/'prototypes/sushi-loop/assets/production/source/blender/native_actions.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
r=json.loads((OBJ/'inputs/source-rig.json').read_text());root=bpy.data.objects[r['groundRootObject']];sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];col=next(c for c in sc.collection.children if root in list(c.all_objects))
for layer in sc.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=col
col.hide_render=False;col.hide_viewport=False
cam=sc.camera;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1
cam.matrix_world=Matrix(json.loads((OBJ/'inputs/source-camera.json').read_text())['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_x=cam.data.shift_y=0;bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*384,(1-p.y)*640))
y0=px((0,0,0)).y;cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-y0;cam.data.shift_y=(496-y0)/dy;bpy.context.view_layer.update()
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.render.dither_intensity=0
# Keep source packed materials, compositor and source lighting; no model alteration.
for d in ['S','E','N','W']:
 n.apply_clip({'root':root,'collection':col},r,'stand',1,d,sc);sc.render.filepath=str(OUT/('native-stand-'+d+'.png'));bpy.ops.render.render(write_still=True)
