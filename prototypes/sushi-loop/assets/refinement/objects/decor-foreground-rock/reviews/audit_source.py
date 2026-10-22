import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parents[1]
S=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=S
root=next(o for o in S.objects if o.get('production_id')=='decor-foreground-rock')
col=next(c for c in root.users_collection if c in S.collection.children[:])
meshes=[o for o in col.all_objects if o.type=='MESH']
bpy.context.view_layer.update()
def bounds(points):return [[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)]
def props(x):return {k:str(x[k]) for k in x.keys()}
def camera(cam):
 return {'name':cam.name,'type':cam.data.type,'worldMatrix':[list(r) for r in cam.matrix_world],'rotationDegrees':[math.degrees(x) for x in cam.rotation_euler],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'resolution':[S.render.resolution_x,S.render.resolution_y],'pixelAspect':[S.render.pixel_aspect_x,S.render.pixel_aspect_y],'elevationDegrees':math.degrees(math.atan2(cam.location.z,math.hypot(cam.location.x,cam.location.y))),'projectionMatrix':[list(r)for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=S.render.resolution_x,y=S.render.resolution_y,scale_x=S.render.pixel_aspect_x,scale_y=S.render.pixel_aspect_y)]}
points=[root.matrix_world.inverted()@o.matrix_world@v.co for o in meshes for v in o.data.vertices]
rec={'source':bpy.data.filepath,'sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blender':bpy.app.version_string,'scene':S.name,'collection':col.name,'root':{'name':root.name,'matrixWorld':[list(r)for r in root.matrix_world],'location':list(root.location),'rotationDegrees':[math.degrees(x)for x in root.rotation_euler],'scale':list(root.scale),'props':props(root)},'initialSavedSceneCamera':camera(S.camera),'rootLocalBounds':bounds(points),'meshCountObservationOnly':len(meshes),'meshes':[],'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'location':list(o.location),'size':getattr(o.data,'size',None)}for o in S.objects if o.type=='LIGHT'],'sceneSettings':{'engine':S.render.engine,'filmTransparent':S.render.film_transparent,'fps':S.render.fps,'viewTransform':S.view_settings.view_transform,'look':S.view_settings.look,'exposure':S.view_settings.exposure,'gamma':S.view_settings.gamma,'world':S.world.name if S.world else None}}
for o in meshes:
 pts=[root.matrix_world.inverted()@o.matrix_world@v.co for v in o.data.vertices]
 rec['meshes'].append({'name':o.name,'parent':o.parent.name if o.parent else None,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'rootLocalBounds':bounds(pts),'materials':[m.name for m in o.data.materials if m],'modifiers':[{'name':m.name,'type':m.type}for m in o.modifiers],'uvLayers':list(o.data.uv_layers.keys()),'shapeKeys':list(o.data.shape_keys.key_blocks.keys())if o.data.shape_keys else [],'animationData':bool(o.animation_data),'props':props(o)})
rec['assetImageDependencies']=[{'material':m.name,'image':n.image.filepath,'packed':bool(n.image.packed_file)}for o in meshes for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
for c in S.collection.children:c.hide_render=(c!=col);c.hide_viewport=(c!=col)
col.hide_render=False;col.hide_viewport=False
def enable_layer(layer):
 layer.exclude=False;layer.hide_viewport=False
 for child in layer.children:enable_layer(child)
for view_layer in S.view_layers:enable_layer(view_layer.layer_collection)
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
# Reconstruct the original asset camera from its actual exported camera record; unrelated startup camera is separately recorded above.
C=json.loads((P/'inputs/source-camera.json').read_text());cam=S.camera
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=C['frame'][0]/C['cellSize'];cam.matrix_world=Matrix(C['camera']['worldMatrix']);cam.data.shift_x=0;cam.data.shift_y=0
S.render.resolution_x=C['frame'][0]*2;S.render.resolution_y=C['frame'][1]*2;S.render.resolution_percentage=100;S.render.pixel_aspect_x=C['camera']['pixelAspect'][0];S.render.pixel_aspect_y=C['camera']['pixelAspect'][1]
bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(S,cam,Vector(v));return Vector((p.x*S.render.resolution_x,(1-p.y)*S.render.resolution_y))
base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y
cam.data.shift_y=(C['anchor'][1]*2-base.y)/dy;cam.data.shift_x=(C['frame'][0]/2-C['anchor'][0])/C['frame'][0]
bpy.context.view_layer.update()
anchor=px((0,0,0));rec['restoredAssetCapture']=camera(cam);rec['restoredAssetCapture']['calibration']={'root':list(anchor),'unitX':list(px((1,0,0))-anchor),'unitDepth':list(px((0,-1,0))-anchor),'unitHeight':list(px((0,0,1))-anchor)}
rec['facings']={}
for facing,deg in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
 rec['facings'][facing]={'rootRotationDegrees':deg,'worldBounds':bounds(pts),'projectedBounds':bounds([Vector((*px(p),0))for p in pts])[:2]}
# Native baseline views for independent inspection; never saved back to project.
S.render.film_transparent=True;S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGBA';S.render.image_settings.color_depth='8';S.render.image_settings.compression=100
for facing,deg in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();S.render.filepath=str(P/'reviews'/('source-native-'+facing+'.png'));bpy.ops.render.render(write_still=True,scene=S.name)
(P/'reviews/source-audit.json').write_text(json.dumps(rec,indent=2)+'\n')
print(json.dumps({'audit':str(P/'reviews/source-audit.json'),'collection':col.name,'bounds':rec['rootLocalBounds'],'initialCamera':rec['initialSavedSceneCamera'],'restoredCapture':rec['restoredAssetCapture']},indent=2))
