import bpy, sys, json, math, hashlib, importlib.util
sys.dont_write_bytecode=True
from pathlib import Path
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
P=ROOT/'prototypes/sushi-loop/assets/refinement/objects/garbage-car'
OUT=P/'reviews/source-inspection'
OUT.mkdir(parents=True,exist_ok=True)
BASE=ROOT/'prototypes/sushi-loop/assets/production/source/blender'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jwrite(name,d):(OUT/name).write_text(json.dumps(d,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('car_judge_native_actions',BASE/'native_actions.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
rig=json.loads((P/'inputs/source-rig.json').read_text())
camera_record=json.loads((P/'inputs/source-camera.json').read_text())
root=bpy.data.objects[rig['groundRootObject']]
scenes=[s for s in bpy.data.scenes if root.name in s.objects]
scene=next(s for s in scenes if s.get('source')=='native_actions.py')
bpy.context.window.scene=scene
bpy.context.window.view_layer=scene.view_layers[0]
collection=next(c for c in scene.collection.children if root in list(c.all_objects))
asset={'root':root,'collection':collection}
objects=list(collection.all_objects)
def layer_walk(x):
 yield x
 for child in x.children:yield from layer_walk(child)
for layer in layer_walk(scene.view_layers[0].layer_collection):layer.exclude=False
for layer in scene.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=collection
for c in scene.collection.children:c.hide_render=c!=collection;c.hide_viewport=c!=collection

saved_camera={'name':scene.camera.name,'matrix':[list(r) for r in scene.camera.matrix_world],'data':{'type':scene.camera.data.type,'orthoScale':scene.camera.data.ortho_scale,'shift':[scene.camera.data.shift_x,scene.camera.data.shift_y]},'frame':[scene.render.resolution_x,scene.render.resolution_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y]}
# Reconstruct this object's registered capture in memory, never save the library.
scene.render.resolution_x=1152;scene.render.resolution_y=1664;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=camera_record['camera']['pixelAspect'][0];scene.render.pixel_aspect_y=1
cam=bpy.data.objects.new('garbage-car judge registered camera',bpy.data.cameras.new('garbage-car judge registered camera'))
scene.collection.objects.link(cam);scene.camera=cam
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=4.5
cam.matrix_world=Matrix(camera_record['camera']['worldMatrix']);cam.data.shift_x=0;cam.data.shift_y=0
def px(p):
 v=world_to_camera_view(scene,cam,Vector(p));return [v.x*scene.render.resolution_x,(1-v.y)*scene.render.resolution_y]
scene.view_layers[0].update();initial=px((0,0,0));cam.data.shift_y=1;scene.view_layers[0].update();dy=px((0,0,0))[1]-initial[1]
cam.data.shift_y=(1088-initial[1])/dy;scene.view_layers[0].update()
zero=px((0,0,0));cal={'root':zero,'unitX':[a-b for a,b in zip(px((1,0,0)),zero)],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),zero)],'unitHeight':[a-b for a,b in zip(px((0,0,1)),zero)]}
nativecam={'worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1152,y=1664,scale_x=scene.render.pixel_aspect_x,scale_y=1)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[scene.render.pixel_aspect_x,1],'frame':[1152,1664],'calibration':cal}

def object_state(o):
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':[list(r) for r in o.matrix_world],'hideRender':o.hide_render,'hideViewport':o.hide_viewport}
 if o.type=='MESH':d.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),uvLayers=[x.name for x in o.data.uv_layers],shapeKeys=[x.name for x in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],materials=[m.name if m else None for m in o.data.materials],modifiers=[{'name':m.name,'type':m.type} for m in o.modifiers])
 return d
def geometry():
 deps=bpy.context.evaluated_depsgraph_get();rows=[];allpts=[]
 for o in objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(deps);mesh=ev.to_mesh();pts=[ev.matrix_world@v.co for v in mesh.vertices];ev.to_mesh_clear()
  if not pts:continue
  lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
  pix=[px(p) for p in pts]
  row={'name':o.name,'bounds':[lo,hi],'projectedBounds':[[min(p[i] for p in pix) for i in range(2)],[max(p[i] for p in pix) for i in range(2)]],'minZVertices':[list(p) for p in pts if p.z<=lo[2]+.002],'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale)}
  rows.append(row)
  if not o.hide_render:allpts.extend(pts)
 return {'bounds':[[min(p[i] for p in allpts) for i in range(3)],[max(p[i] for p in allpts) for i in range(3)]] if allpts else None,'objects':rows}

actions=[]
for clip,record in rig['clips'].items():
 for target in record['actions']:
  a=bpy.data.actions[target['action']]
  actions.append({'clip':clip,'owner':target,'frameRange':list(a.frame_range),'curves':[{'path':fc.data_path,'arrayIndex':fc.array_index,'keys':[{'frame':p.co.x,'value':p.co.y,'interpolation':p.interpolation} for p in fc.keyframe_points]} for fc in A._fcurves(a)]})
jwrite('source-actions.json',actions)
materials=[]
for m in sorted({m for o in objects if o.type=='MESH' for m in o.data.materials if m},key=lambda m:m.name):
 materials.append({'name':m.name,'diffuseColor':list(m.diffuse_color),'surfaceRenderMethod':getattr(m,'surface_render_method',None),'useNodes':m.use_nodes,'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'inputs':{s.name:(list(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value) for s in n.inputs if hasattr(s,'default_value')},'image':n.image.name if getattr(n,'image',None) else None} for n in m.node_tree.nodes] if m.use_nodes else [],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links] if m.use_nodes else []})

frames=[]
for clip,record in rig['clips'].items():
 for direction in ['N','E','S','W']:
  for frame in range(1,record['frames']+1):
   A.apply_clip(asset,rig,clip,frame,direction,scene);frames.append({'clip':clip,'direction':direction,'sourceFrame':frame,'runtimeIndex':frame-1,'root':object_state(root),'geometry':geometry()})
closure=[]
for direction in ['N','E','S','W']:
 A.apply_clip(asset,rig,'highlighted',13,direction,scene);closure.append({'direction':direction,'sourceFrame':13,'geometry':geometry()})
jwrite('evaluated-native-frames.json',{'frames':frames,'loopClosure':closure})
A.apply_clip(asset,rig,'idle',1,'S',scene)
integrity={'project':bpy.data.filepath,'projectSHA256':sha(bpy.data.filepath),'targetSHA256':sha(P/'inputs/target.png'),'originalSHA256':sha(P/'inputs/original.png'),'sourceUnmodifiedByAudit':True,'noBlendSaveCalled':True,'blenderVersion':bpy.app.version_string,'scene':scene.name,'collection':collection.name,'savedActiveCamera':saved_camera,'registeredCamera':nativecam,'root':object_state(root),'objects':[object_state(o) for o in objects],'materials':materials,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'location':list(o.location),'rotation':list(o.rotation_euler),'size':getattr(o.data,'size',None)} for o in scene.objects if o.type=='LIGHT'],'world':{'name':scene.world.name if scene.world else None,'nodes':[{'type':n.type,'name':n.name,'values':{s.name:(list(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value) for s in n.inputs if hasattr(s,'default_value')}} for n in scene.world.node_tree.nodes] if scene.world and scene.world.use_nodes else []},'render':{'engine':scene.render.engine,'filmTransparent':scene.render.film_transparent,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma},'resources':{'libraries':[{'name':x.name,'filepath':x.filepath} for x in bpy.data.libraries],'images':[{'name':x.name,'filepath':x.filepath,'packed':bool(x.packed_file),'source':x.source} for x in bpy.data.images],'foreignParents':[o.name for o in objects if o.parent and o.parent not in objects],'constraints':[{'owner':o.name,'name':c.name,'type':c.type,'target':getattr(getattr(c,'target',None),'name',None)} for o in objects for c in o.constraints],'drivers':[{'owner':o.name,'path':fc.data_path} for o in objects if o.animation_data for fc in o.animation_data.drivers]}}
jwrite('native-source-audit.json',integrity)
print('AUDIT_COMPLETE',len(objects),len(frames),len(actions),nativecam)
if '--render' in sys.argv:
 scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.film_transparent=True
 for direction in ['N','E','S','W']:
  A.apply_clip(asset,rig,'idle',1,direction,scene);scene.render.filepath=str(OUT/f'native-source-idle-{direction}.png');bpy.ops.render.render(write_still=True)
 print('RENDER_COMPLETE')
