import bpy,math,json
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
p=Path(__file__).resolve().parents[1]
a=json.loads((p/'evidence/original-native-audit.json').read_text())
col=bpy.data.collections[a['collection']];root=bpy.data.objects[a['root']]
sc=next(sc for sc in bpy.data.scenes if root.name in sc.objects);bpy.context.window.scene=sc
for c in bpy.data.collections:c.hide_viewport=False;c.hide_render=False
def enable(lc):
    lc.exclude=False;lc.hide_viewport=False
    for c in lc.children:enable(c)
for vl in sc.view_layers:enable(vl.layer_collection)
owned=set(col.all_objects);lights={x['name'] for x in a['lights']}
for o in sc.objects:
    o.hide_render=not(o in owned or o.name in lights or o==sc.camera)
    if o in owned:o.hide_set(False)
sc.frame_set(1)
sc.render.resolution_x=768;sc.render.resolution_y=1408;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=1.2206555604934692;sc.render.pixel_aspect_y=1
sc.render.filter_size=1.5;sc.render.film_transparent=True
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
cam=sc.camera;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
record=json.loads((p/'resources/object/source-camera.json').read_text())
cam.matrix_world=Matrix(record['camera']['worldMatrix']);cam.data.shift_x=0;cam.data.shift_y=0
bpy.context.view_layer.update()
def px(v):
    q=world_to_camera_view(sc,cam,Vector(v));return Vector((q.x*768,(1-q.y)*1408))
base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y
cam.data.shift_y=(992-base.y)/dy;bpy.context.view_layer.update()
cal={'root':list(px((0,0,0))),'x':list(px((1,0,0))-px((0,0,0))),'depth':list(px((0,-1,0))-px((0,0,0))),'height':list(px((0,0,1))-px((0,0,0)))}
meta={'scope':'bounded historical source replay, not approval','source':'resources/source/original.blend','resolution':[768,1408],'publication':[384,704],'scale':4,'filter':1.5,'reduction':'whole-frame Pillow LANCZOS exactly 1/2','cameraMatrix':[list(r) for r in cam.matrix_world],'ortho':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'calibration':cal,'color':{'view_transform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'world':{'name':sc.world.name,'nodes':[(n.name,n.type) for n in sc.world.node_tree.nodes]},'lights':a['lights'],'engine':sc.render.engine,'blender':bpy.app.version_string,'frame':1,'facings':{}}
(p/'evidence/original-replay').mkdir(exist_ok=True)
for facing,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
    root.rotation_euler.z=angle;bpy.context.view_layer.update()
    sc.render.filepath=str(p/'evidence/original-replay'/('native4x-'+facing+'.png'))
    meta['facings'][facing]={'radians':angle,'rootMatrix':[list(r) for r in root.matrix_world]}
    bpy.ops.render.render(write_still=True)
(p/'evidence/original-replay-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
