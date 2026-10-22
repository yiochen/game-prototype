import bpy, json, math
from pathlib import Path
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

OUT=Path(__file__).parent
BASE=OUT.parent
record=json.loads((BASE/'inputs/source-camera.json').read_text())
original=bpy.context.scene
lights=[o for o in original.objects if o.type=='LIGHT']
scene=original.copy();scene.name='Independent ruin source replay'
scene.compositing_node_group=original.compositing_node_group.copy()
for node in scene.compositing_node_group.nodes:
    if node.type=='R_LAYERS':node.scene=scene
bpy.context.window.scene=scene
for col in list(scene.collection.children):scene.collection.children.unlink(col)
col=bpy.data.collections['S33 production concept reef-face']
scene.collection.children.link(col);col.hide_render=False;col.hide_viewport=False
def enable_layer(lc):
    lc.exclude=False;lc.hide_viewport=False
    for child in lc.children:enable_layer(child)
for layer in scene.view_layers:enable_layer(layer.layer_collection)
for o in list(scene.collection.objects):
    if o.type not in {'LIGHT','CAMERA'}:scene.collection.objects.unlink(o)
for o in lights:
    if o.name not in scene.objects:scene.collection.objects.link(o)
cam=original.camera.copy();cam.data=original.camera.data.copy();scene.collection.objects.link(cam);scene.camera=cam
cam.matrix_world=Matrix(record['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_x=0;cam.data.shift_y=.75
scene.render.resolution_x=384;scene.render.resolution_y=960;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
bpy.context.view_layer.update()
def px(p):
    v=world_to_camera_view(scene,cam,Vector(p));return [v.x*384,(1-v.y)*960]
origin=px((0,0,0))
calibration={'root':origin,'unitX':[a-b for a,b in zip(px((1,0,0)),origin)],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),origin)],'unitHeight':[a-b for a,b in zip(px((0,0,1)),origin)]}
projection=[list(row) for row in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=960,scale_x=1,scale_y=1)]
root=bpy.data.objects['S33 production concept reef-face root']
captures=[]
for direction,degrees in [('N',180),('E',90),('S',0),('W',-90)]:
    root.rotation_euler.z=math.radians(degrees);bpy.context.view_layer.update()
    assert abs(root.matrix_world[0][0]-math.cos(math.radians(degrees)))<.0001, (direction,list(root.rotation_euler),[list(r) for r in root.matrix_world])
    saved=[]
    for obj in col.all_objects:
        if obj.type!='MESH':continue
        old=[v.co.copy() for v in obj.data.vertices];saved.append((obj,old));inv=obj.matrix_world.inverted()
        for v in obj.data.vertices:
            p=obj.matrix_world@v.co;blend=max(0,1-max(0,p.z)/.42)**2;p.y*=1+(1/math.sin(math.radians(35))-1)*blend;v.co=inv@p
        obj.data.update()
    bpy.context.view_layer.update()
    points=[o.matrix_world@v.co for o in col.all_objects if o.type=='MESH' for v in o.data.vertices]
    projected=[px(p) for p in points]
    captures.append({'direction':direction,'rootRotationDegrees':degrees,'rootMatrix':[list(row) for row in root.matrix_world],'captureBounds':{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]},'projectedGeometryBounds':{'min':[min(p[i] for p in projected) for i in range(2)],'max':[max(p[i] for p in projected) for i in range(2)]}})
    scene.render.filepath=str(OUT/f'original-native-replay-{direction}.png')
    bpy.ops.render.render(write_still=True,scene=scene.name)
    for obj,old in saved:
        for v,p in zip(obj.data.vertices,old):v.co=p
        obj.data.update()
    bpy.context.view_layer.update()
report={'sceneCameraMismatch':{'sourceActiveResolution':[original.render.resolution_x,original.render.resolution_y],'sourceActiveCameraShiftY':original.camera.data.shift_y,'rule':'per-object registered camera restores correct frame/root'},'camera':{'matrix':[list(row) for row in cam.matrix_world],'projectionMatrix':projection,'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[1,1],'frame':[384,960],'logicalFrame':[192,480],'sourceScale':2,'elevationDegrees':35},'calibration':calibration,'footingDeformation':{'worldYScale':'1 + (1/sin(35deg) - 1) * max(0,1 - max(0,Z)/0.42)^2','thresholdZ':.42,'appliedAfterFacingRotation':True},'captureSettings':{'engine':scene.render.engine,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma,'useNodes':scene.use_nodes},'lights':[{'name':o.name,'energy':o.data.energy,'type':o.data.type,'location':list(o.location)} for o in lights],'captures':captures}
(OUT/'original-capture-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
