import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
base=Path(__file__).resolve().parents[2];out=base/'evidence/source-filter-study';out.mkdir(exist_ok=True)
record=json.loads((base/'resources/resource-inputs/source-camera.json').read_text());sc=bpy.context.scene;coll=bpy.data.collections['S33_PROP_rock-half-width.001'];root=bpy.data.objects['rock-half-width__root.001']
def layers(l):
 l.exclude=False;l.hide_viewport=False
 for c in l.children:layers(c)
for v in sc.view_layers:layers(v.layer_collection)
for c in sc.collection.children:c.hide_render=c!=coll;c.hide_viewport=c!=coll
coll.hide_render=False;coll.hide_viewport=False
for o in coll.all_objects:o.hide_set(False);o.hide_render=False;o.hide_viewport=False
camdata=bpy.data.cameras.new('Source filter diagnostic camera');cam=bpy.data.objects.new('Source filter diagnostic camera',camdata);sc.collection.objects.link(cam);sc.camera=cam;cam.matrix_world=Matrix(record['camera']['worldMatrix']);camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL';camdata.ortho_scale=192/128
sc.render.resolution_x=768;sc.render.resolution_y=1408;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=record['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.dither_intensity=0
sc.frame_set(1);bpy.context.view_layer.update()
def px(p):
 v=world_to_camera_view(sc,cam,Vector(p));return [v.x*768,(1-v.y)*1408]
b=px((0,0,0));camdata.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-b[1];camdata.shift_y=(248*4-b[1])/dy;bpy.context.view_layer.update()
old=sc.render.filter_size;sc.render.filter_size=.01
records=[]
for d,a in [('S',0),('E',90)]:
 root.rotation_euler.z=math.radians(a);bpy.context.view_layer.update();sc.render.filepath=str(out/f'narrow-filter-native-{d}.png');bpy.ops.render.render(write_still=True)
 records.append({'path':f'narrow-filter-native-{d}.png','direction':d,'filterSize':sc.render.filter_size,'taaRenderSamples':sc.eevee.taa_render_samples,'rootMatrix':[list(r) for r in root.matrix_world],'cameraMatrix':[list(r) for r in cam.matrix_world],'rootPixels':px((0,0,0)),'nativeFrame':[768,1408],'logicalFrame':[192,352],'logicalRoot':[96,248],'captureScale':4})
(out/'native-ledger.json').write_text(json.dumps({'scope':'Minimal source-only capture-filter diagnostic. Original geometry/material/lights/camera/scale preserved; no candidate or permanent source edit.','historicalFilterSize':old,'studyFilterSize':sc.render.filter_size,'records':records},indent=2)+'\n')
