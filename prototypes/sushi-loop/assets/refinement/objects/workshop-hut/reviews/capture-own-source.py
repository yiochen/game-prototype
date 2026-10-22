import bpy, json, pathlib, math, hashlib
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
OUT=pathlib.Path(__file__).parent
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc;sc.frame_set(1)
root=bpy.data.objects['workshop-hut__root.001'];col=bpy.data.collections['S33_PROP_workshop-hut.001']
for c in sc.collection.children:c.hide_render=c!=col
col.hide_render=False;col.hide_viewport=False
def activate_layer(lc):
    lc.exclude=False;lc.hide_viewport=False
    for child in lc.children:activate_layer(child)
for vl in sc.view_layers:activate_layer(vl.layer_collection)
for o in col.all_objects:o.hide_set(False);o.hide_viewport=False;o.hide_render=False
root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1)
bpy.context.view_layer.update()
def bounds(p):return {'min':[min(v[i] for v in p) for i in range(3)],'max':[max(v[i] for v in p) for i in range(3)]}
def mesh_info(o):
    dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);me=ev.to_mesh();p=[root.matrix_world.inverted()@ev.matrix_world@v.co for v in me.vertices]
    d={'name':o.name,'parent':o.parent.name if o.parent else None,'localLocation':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrix':[list(x) for x in o.matrix_world],'boundsRootLocal':bounds(p),'vertexCount':len(me.vertices),'polygonCount':len(me.polygons),'materials':[m.name for m in o.data.materials if m],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'geometrySHA256':hashlib.sha256(json.dumps({'verts':[list(x) for x in p],'faces':[list(f.vertices) for f in me.polygons]},sort_keys=True).encode()).hexdigest()}
    ev.to_mesh_clear();return d,p
allp=[];objects=[]
for o in col.all_objects:
    if o.type=='MESH':d,p=mesh_info(o);objects.append(d);allp+=p
record={'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'collection':col.name,'root':{'name':root.name,'location':list(root.location),'rotation':list(root.rotation_euler),'scale':list(root.scale),'props':{k:str(root[k]) for k in root.keys()}},'boundsRootLocal':bounds(allp),'objects':objects,'rawInventoryCaution':'native-source-inventory[-v2].json recorded pre-update object matrices and is not a placement/bounds authority; use this evaluated record.'}
cam=bpy.data.objects.new('Judge Hut Diagnostic Camera',bpy.data.cameras.new('Judge Hut Diagnostic Camera'));sc.collection.objects.link(cam);sc.camera=cam
metadata=json.loads((OUT.parent/'inputs/source-camera.json').read_text());cam.matrix_world=Matrix(metadata['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
sc.render.resolution_x=384;sc.render.resolution_y=896;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=metadata['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1
def px(v):
    p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*384,(1-p.y)*896))
cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update();base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(704-base.y)/dy;bpy.context.view_layer.update()
o=px((0,0,0));record['camera']={'constructedFromOwnSourceRecord':True,'unrelatedSavedActiveCameraNotUsed':True,'nativeFrame':[384,896],'logicalFrame':[192,448],'logicalRoot':[96,352],'sourceScale':2,'cellSize':128,'matrix':[list(x) for x in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'rootPx':list(o),'unitXPx':list(px((1,0,0))-o),'unitDepthPx':list(px((0,-1,0))-o),'unitHeightPx':list(px((0,0,1))-o),'projectionMatrix':[list(x) for x in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=896,scale_x=sc.render.pixel_aspect_x,scale_y=1)]}
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.fps=12
record['captureTreatment']={'engine':sc.render.engine,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'compositor':sc.use_nodes,'method':'Unchanged source materials/lights/compositor; in-memory visibility isolation and own registered camera only. No blend saved.'}
record['directions']={}
folder=OUT/'source-native';folder.mkdir(exist_ok=True)
for direction,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
    root.rotation_euler.z=angle;bpy.context.view_layer.update();socket=root.matrix_world@Vector((-.12,-.56,0));record['directions'][direction]={'angle':angle,'doorSocket':list(socket),'doorPx':list(px(socket))};sc.render.filepath=str(folder/(direction+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
(OUT/'native-source-evaluated.json').write_text(json.dumps(record,indent=2))
print('JUDGE_NATIVE_RECORD',record['boundsRootLocal'],record['camera'])
