import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
base=Path.cwd()/'prototypes/sushi-loop/assets';obj=base/'refinement/objects/chef-ellis';out=obj/'reviews/round-04-inspection';mode=sys.argv[sys.argv.index('--')+1];sys.path.insert(0,str(base/'production/source/blender'));import native_actions
record=json.loads((obj/'inputs/source-rig.json').read_text());collection=bpy.data.collections['S33_CHARACTER_chef_ellis.001'];root=bpy.data.objects['chef_ellis__ground_root.001'];arm=bpy.data.objects['chef_ellis__armature.001']
def vec(v):return [float(z) for z in v]
def mat(m):return [vec(r) for r in m]
def action_data(a):
 result=[]
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     result.append({'path':fc.data_path,'index':fc.array_index,'extrapolation':fc.extrapolation,'keys':[(vec(k.co),k.interpolation,vec(k.handle_left),vec(k.handle_right),k.handle_left_type,k.handle_right_type) for k in fc.keyframe_points]})
 return sorted(result,key=lambda r:(r['path'],r['index']))
initialScene=bpy.context.scene
report={'mode':mode,'project':bpy.data.filepath,'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'initialScene':initialScene.name,'initialCamera':initialScene.camera.name if initialScene.camera else None,'collectionWasHidden':[collection.hide_viewport,collection.hide_render],'lights':[{'name':o.name,'location':vec(o.location),'rotation':vec(o.rotation_euler),'type':o.data.type,'energy':o.data.energy,'color':vec(o.data.color),'size':getattr(o.data,'size',None)} for o in initialScene.objects if o.type=='LIGHT'],'world':initialScene.world.name if initialScene.world else None,'render':{'engine':initialScene.render.engine,'frame':[initialScene.render.resolution_x,initialScene.render.resolution_y],'filmTransparent':initialScene.render.film_transparent,'device':initialScene.cycles.device,'samples':initialScene.cycles.samples,'denoise':initialScene.cycles.use_denoising,'viewTransform':initialScene.view_settings.view_transform,'look':initialScene.view_settings.look,'exposure':initialScene.view_settings.exposure},'linkedLibraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'size':list(i.size),'packed':i.packed_file is not None,'packedSHA256':hashlib.sha256(bytes(i.packed_file.data)).hexdigest() if i.packed_file else None,'path':i.filepath} for i in bpy.data.images], 'restBones':{b.name:mat(b.matrix_local) for b in arm.data.bones},'actions':{},'samples':[]}
if initialScene.camera:
 c=initialScene.camera;report['camera']={'matrix':mat(c.matrix_world),'projectionMatrix':mat(c.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=640,scale_x=1,scale_y=1)),'type':c.data.type,'orthoScale':c.data.ortho_scale,'shift':[c.data.shift_x,c.data.shift_y],'sensorFit':c.data.sensor_fit}
for clip in record['clips'].values():
 for target in clip['actions']:
  name=target['action'];report['actions'][name]=hashlib.sha256(json.dumps(action_data(bpy.data.actions[name]),sort_keys=True).encode()).hexdigest()
report['propsNative']={}
for o in collection.all_objects:
 if any(t in o.name for t in ['knife_','__image_plane']):
  report['propsNative'][o.name]={'type':o.type,'vertices':[vec(v.co) for v in o.data.vertices] if o.type=='MESH' else None,'uv':[vec(v.uv) for v in o.data.uv_layers.active.data] if o.type=='MESH' and o.data.uv_layers.active else None,'drivers':[{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression} for f in o.animation_data.drivers] if o.animation_data else [],'materials':[]}
  for m in o.data.materials:
   md={'name':m.name,'diffuse':vec(m.diffuse_color),'nodes':[]}
   if m.use_nodes:
    for n in m.node_tree.nodes:
     nd={'type':n.type,'name':n.name}
     if n.type=='BSDF_PRINCIPLED':nd['inputs']={k:vec(n.inputs[k].default_value) if k=='Base Color' else n.inputs[k].default_value for k in ['Base Color','Metallic','Roughness','Specular IOR Level']}
     if n.type=='TEX_IMAGE':nd['image']=n.image.name if n.image else None
     md['nodes'].append(nd)
   report['propsNative'][o.name]['materials'].append(md)
collection.hide_viewport=False;collection.hide_render=False;scene=bpy.data.scenes.new('IndependentEllisJudgeAudit');scene.collection.children.link(collection);bpy.context.window.scene=scene;bpy.context.view_layer.update();asset={'collection':collection,'root':root,'armature':arm};objects=list(collection.all_objects)
for clip in ['idle','work','hold','load']:
 for direction in ['N','E','S','W']:
  for i in range(12):
   native_actions.apply_clip(asset,record,clip,i+1,direction,scene);dg=bpy.context.evaluated_depsgraph_get();ea=arm.evaluated_get(dg);bounds=[];meshes={};centroids={};feet={}
   for o in objects:
    if o.type!='MESH':continue
    eo=o.evaluated_get(dg);mesh=eo.to_mesh();meshes[o.name]=[len(mesh.vertices),len(mesh.edges),len(mesh.polygons)]
    if not o.hide_render and '__image_plane' not in o.name:
     verts=[eo.matrix_world@v.co for v in mesh.vertices]
     lo=[min(v[j] for v in verts) for j in range(3)];hi=[max(v[j] for v in verts) for j in range(3)]
     if '__knife_' not in o.name:bounds.append((lo,hi))
     if '__palm_' in o.name:centroids[o.name]=[sum(v[j] for v in verts)/len(verts) for j in range(3)]
     if '__minimal_foot_' in o.name:feet[o.name]=[lo,hi]
    eo.to_mesh_clear()
   props={o.name:{'matrix':mat(o.matrix_world),'visible':not o.hide_render} for o in objects if any(t in o.name for t in ['__held_dish-salmon','__utensil','__knife_'])}
   report['samples'].append({'clip':clip,'direction':direction,'index':i,'rotation':math.degrees(root.rotation_euler.z),'rootMatrix':mat(root.matrix_world),'boneMatrices':{b.name:mat(ea.matrix_world@b.matrix) for b in ea.pose.bones},'palms':centroids,'feet':feet,'props':props,'bodyBounds':[[min(b[0][j] for b in bounds),max(b[1][j] for b in bounds)] for j in range(3)],'topology':meshes})
report['closures']={}
for clip in ['idle','work','hold']:
 for direction in ['N','E','S','W']:
  native_actions.apply_clip(asset,record,clip,13,direction,scene);dg=bpy.context.evaluated_depsgraph_get();ea=arm.evaluated_get(dg);report['closures'][clip+'-'+direction]={'boneMatrices':{b.name:mat(ea.matrix_world@b.matrix) for b in ea.pose.bones},'props':{o.name:{'matrix':mat(o.matrix_world),'visible':not o.hide_render} for o in objects if any(t in o.name for t in ['__held_dish-salmon','__utensil','__knife_'])}}
(out/(mode+'-native-audit.json')).write_text(json.dumps(report,indent=2)+'\n');print(mode,len(report['samples']),'samples',len(objects),'objects',len(report['actions']),'actions')
