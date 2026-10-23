import bpy, json, math, sys, hashlib, importlib.util, time
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
R=HERE/'resources'; OUT=HERE/'native'; OUT.mkdir(exist_ok=True)
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [plain(x) for x in v]
 except:return str(v)
def props(x):return {k:plain(v) for k,v in x.items()}
def matrix(m):return [list(row) for row in m]
def load(name):
 p=R/'native'/f'{name}.py';spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
scenes=[s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33]
assert len(scenes)==1
sc=scenes[0];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
rig=json.loads((R/'inputs/source-rig.json').read_text());asset=json.loads((R/'inputs/source-assetRecord.json').read_text());root=bpy.data.objects[rig['groundRootObject']]
col=next(c for c in sc.collection.children if root in list(c.all_objects))
asset.update(root=root,collection=col)
saved={'scene':sc.name,'sceneProperties':props(sc),'activeCamera':sc.camera.name if sc.camera else None,'root':{'name':root.name,'matrix':matrix(root.matrix_world),'location':list(root.location),'scale':list(root.scale),'properties':props(root)},'sourceBlendSHA256':sha(R/'native/source.blend'),'blenderVersion':bpy.app.version_string,'renderEngine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]}
# Enable all ownership ancestry and objects before any geometry measurement.
def layers(node):
 yield node
 for child in node.children:yield from layers(child)
for layer in layers(sc.view_layers[0].layer_collection):
 layer.exclude=False
 layer.hide_viewport=False
for c in sc.collection.children:
 c.hide_render=c!=col;c.hide_viewport=c!=col
for c in [col,*list(col.children_recursive)]:c.hide_render=False;c.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False,view_layer=sc.view_layers[0])
sc.view_layers[0].update()
native=load('native_actions');runtime=load('capture_runtime');runtime.scene=lambda:sc;runtime.SCENE_NAME=sc.name
native.apply_clip(asset,rig,'enter',frame=1,direction='S',scene=sc)
def bounds(points):
 if not points:return None
 return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def measure(o):
 raw=[o.matrix_world@v.co for v in o.data.vertices] if o.type=='MESH' else []
 ev=[]
 if o.type=='MESH':
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();ev=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear()
 return {'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':matrix(o.matrix_world),'rawAuthoredWorldBounds':bounds(raw),'evaluatedWorldBounds':bounds(ev),'rawVertexCount':len(raw),'evaluatedVertexCount':len(ev),'visible':not(o.hide_render or o.hide_viewport or o.hide_get()),'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'modifiers':[{'name':m.name,'type':m.type,'showRender':m.show_render,'showViewport':m.show_viewport,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers],'constraints':[{'name':c.name,'type':c.type} for c in o.constraints],'materials':[s.material.name if s.material else None for s in o.material_slots],'shapeKeys':list(o.data.shape_keys.key_blocks.keys()) if o.type=='MESH' and o.data.shape_keys else []}
materials=[]
for m in sorted({s.material for o in col.all_objects for s in o.material_slots if s.material},key=lambda x:x.name):
 materials.append({'name':m.name,'properties':props(m),'diffuseColor':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'properties':props(n)} for n in m.node_tree.nodes] if m.use_nodes else [],'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocket':l.to_socket.name} for l in m.node_tree.links] if m.use_nodes else []})
actions=[]
for t in rig['clips']['enter']['actions']:
 a=bpy.data.actions[t['action']];curves=list(native._fcurves(a));actions.append({**t,'frameRange':list(a.frame_range),'curves':[{'dataPath':f.data_path,'arrayIndex':f.array_index,'keys':[{'co':list(k.co),'interpolation':k.interpolation} for k in f.keyframe_points]} for f in curves]})
pre={'savedPresentation':saved,'collection':col.name,'collectionProperties':props(col),'enabledObjects':[measure(o) for o in col.all_objects],'materials':materials,'actions':actions,'armatures':[o.name for o in col.all_objects if o.type=='ARMATURE'],'externalImages':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file),'users':i.users} for i in bpy.data.images if i.users and any(n.type=='TEX_IMAGE' and n.image==i for m in {s.material for o in col.all_objects for s in o.material_slots if s.material} if m.use_nodes for n in m.node_tree.nodes)],'linkedLibraries':[l.filepath for l in bpy.data.libraries]}
write(HERE/'source-inspection.json',pre)
camera=runtime.configure_camera(asset['projection'],tuple(asset['frame']),tuple(asset['anchor']),int(asset['scale']))
camera['actualOrthoScale']=sc.camera.data.ortho_scale;camera['shift']=[sc.camera.data.shift_x,sc.camera.data.shift_y]
sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.use_persistent_data=True;sc.render.image_settings.compression=15
write(HERE/'native-camera.json',camera)
records=[]
for direction in ['N','E','S','W']:
 folder=OUT/direction;folder.mkdir(exist_ok=True)
 for i in range(12):
  native.apply_clip(asset,rig,'enter',frame=i+1,direction=direction,scene=sc);bpy.context.view_layer.update()
  measurements=[measure(o) for o in col.all_objects]
  path=folder/f'{i:03d}.png';sc.render.filepath=str(path);started=time.monotonic();bpy.ops.render.render(write_still=True,scene=sc.name)
  records.append({'direction':direction,'clip':'enter','index':i,'frame':i+1,'rootRotationZ':root.rotation_euler.z,'rootMatrix':matrix(root.matrix_world),'cameraMatrix':matrix(sc.camera.matrix_world),'objects':measurements,'path':str(path.relative_to(HERE)),'sha256':sha(path),'seconds':time.monotonic()-started})
  write(HERE/'native-measurements.json',{'sourceBlendSHA256':sha(R/'native/source.blend'),'nativeCamera':'native-camera.json','views':records})
  print('PORTAL_PREP_CAPTURE',direction,i,flush=True)
lights=[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None),'matrixWorld':matrix(o.matrix_world),'properties':props(o)} for o in sc.objects if o.type=='LIGHT' and not o.hide_render]
write(HERE/'native-render-settings.json',{'engine':sc.render.engine,'blenderVersion':bpy.app.version_string,'threads':sc.render.threads,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'filmTransparent':sc.render.film_transparent,'dither':sc.render.dither_intensity,'colorManagement':{'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'lights':lights,'worldBackground':[{'color':list(n.inputs['Color'].default_value),'strength':n.inputs['Strength'].default_value} for n in sc.world.node_tree.nodes if n.type=='BACKGROUND'],'compositor':sc.compositing_node_group.name if sc.compositing_node_group else None})
