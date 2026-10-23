import bpy,json,pathlib,sys,math,hashlib,importlib.util
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/customer-samir')
MODE=sys.argv[-1] if sys.argv[-1] in ['main','runtime'] else 'main'
R=P/'reviews'/('baseline-'+MODE);R.mkdir(exist_ok=True)
rig=json.loads((P/('inputs/source-rig.json' if MODE=='main' else 'inputs/runtime-variants/export/source/customer-samir/rig.json')).read_text())
root=bpy.data.objects[rig['groundRootObject']]
collection=next(c for c in bpy.data.collections if root in list(c.all_objects) and c.name.startswith('S33_CHARACTER_' if MODE=='main' else 'S10 meal S33_CHARACTER_'))
scene=next(s for s in bpy.data.scenes if root in list(s.objects))
bpy.context.window.scene=scene;bpy.context.window.view_layer=scene.view_layers[0]
for c in scene.collection.children:
 c.hide_render=c!=collection;c.hide_viewport=c!=collection
for layer in scene.view_layers:
 def visit(l):
  l.exclude=False;l.hide_viewport=False
  for q in l.children:visit(q)
 visit(layer.layer_collection)
collection.hide_render=False;collection.hide_viewport=False
native_path=P.parents[2]/'production/source/blender/native_actions.py'
spec=importlib.util.spec_from_file_location('judge_native',native_path);native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
a={'root':root,'collection':collection}
cam=scene.camera
# Restore declared capture camera in the actual asset scene; preserve scene lighting/materials.
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
cam.matrix_world=Matrix(json.loads((P/'inputs/source-camera.json').read_text())['camera']['worldMatrix'])
cam.data.shift_x=0;cam.data.shift_y=0.4583320518334706
scene.render.resolution_x=384;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.fps=12
scene.render.engine='BLENDER_EEVEE';scene.render.image_settings.compression=50
if hasattr(scene,'eevee') and hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=16
body=[o for o in collection.all_objects if o.type=='MESH' and o.get('weighted_character_geometry')]
plane=next(o for o in collection.all_objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi')
foodroot=plane.parent
arm=next(o for o in collection.all_objects if o.type=='ARMATURE')
img=next(n.image for m in plane.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
packed=bytes(img.packed_file.data);(R/'original-packed-food.png').write_bytes(packed)
def plain(v):return [round(float(x),9) for x in v]
def mat(v):return [plain(row) for row in v]
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def px(v):
 t=world_to_camera_view(scene,cam,Vector(v));return [round(t.x*384,7),round((1-t.y)*640,7)]
def bounds(objs):
 dg=bpy.context.evaluated_depsgraph_get();pts=[]
 for o in objs:
  e=o.evaluated_get(dg);me=e.to_mesh();pts.extend([e.matrix_world@v.co for v in me.vertices]);e.to_mesh_clear()
 return [plain([min(v[i] for v in pts) for i in range(3)]),plain([max(v[i] for v in pts) for i in range(3)])]
rest=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':plain(b.head_local),'tail':plain(b.tail_local),'matrix':mat(b.matrix_local),'deform':b.use_deform} for b in arm.data.bones]
actions={t['action']:digest([{'path':f.data_path,'index':f.array_index,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in f.keyframe_points]} for f in native._fcurves(bpy.data.actions[t['action']])]) for clip in rig['clips'].values() for t in clip['actions']}
report={'mode':MODE,'project':bpy.data.filepath,'scene':scene.name,'collection':collection.name,'camera':{'name':cam.name,'matrix':mat(cam.matrix_world),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[384,640],'pixelAspect':[1,1],'projectionMatrix':mat(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=640,scale_x=1,scale_y=1))},'root':{'name':root.name,'location':plain(root.location),'scale':plain(root.scale)},'rootProjection':px((0,0,0)),'rig':{'name':arm.name,'bones':rest,'restSHA256':digest(rest),'actionSHA256':actions},'bodyMeshCount':len(body),'food':{'owner':plane.name,'root':foodroot.name,'image':img.name,'packedSHA256':hashlib.sha256(packed).hexdigest(),'size':list(img.size),'vertices':[plain(v.co) for v in plane.data.vertices],'UV':[plain(v.uv) for v in plane.data.uv_layers.active.data],'localLocation':plain(plane.location),'localRotation':plain(plane.rotation_euler),'drivers':[{'path':d.data_path,'index':d.array_index,'expression':d.driver.expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'id':t.id.name if t.id else None,'dataPath':t.data_path,'transformType':t.transform_type,'space':t.transform_space} for t in v.targets]} for v in d.driver.variables]} for d in plane.animation_data.drivers] if plane.animation_data else [],'custom':{k:str(v) for k,v in plane.items()}},'clips':{}}
for clip in rig['clips']:
 samples=[]
 for direction in ['S','E','N','W']:
  for f in range(1,13):
   native.apply_clip(a,rig,clip,frame=f,direction=direction,scene=scene)
   was_hide_render=plane.hide_render;was_hide_viewport=plane.hide_viewport
   plane.hide_render=False;plane.hide_viewport=False;bpy.context.view_layer.update()
   b=bounds(body);hands={s:plain(arm.matrix_world@arm.pose.bones['hand_'+s].head) for s in ['L','R']};feet={s:plain(arm.matrix_world@arm.pose.bones['foot_'+s].head) for s in ['L','R']}
   def posed_point(bn,point):return arm.matrix_world@arm.pose.bones[bn].matrix@arm.data.bones[bn].matrix_local.inverted()@Vector(point)
   palms={side:posed_point('hand_'+side,arm.data.bones['hand_'+side].head_local+Vector((0,-.002,-.046))) for side in ['L','R']}
   mouth=posed_point('head',(0,-.255,.543))
   seat=arm.matrix_world@(arm.pose.bones['pelvis'].head-Vector((0,0,.08)))
   verts=[plane.matrix_world@v.co for v in plane.data.vertices]
   sample={'direction':direction,'frame':f,'bodyBounds':b,'rootMatrix':mat(root.matrix_world),'evaluatedContactsWorld':{'palms':{k:plain(v) for k,v in palms.items()},'mouth':plain(mouth),'seat':plain(seat),'footBoneHeads':feet},'evaluatedContactsProjected':{'palms':{k:px(v) for k,v in palms.items()},'mouth':px(mouth),'seat':px(seat),'footBoneHeads':{k:px(v) for k,v in feet.items()}},'functionalBoneWorldMatrices':{bn:mat(arm.matrix_world@arm.pose.bones[bn].matrix) for bn in ['ground','pelvis','head','hand_L','hand_R','foot_L','foot_R']},'handBoneHeads':hands,'footBoneHeads':feet,'pelvis':plain(arm.matrix_world@arm.pose.bones['pelvis'].head),'head':plain(arm.matrix_world@arm.pose.bones['head'].head),'foodRootWorld':plain(foodroot.matrix_world.translation),'foodRootPx':px(foodroot.matrix_world.translation),'foodVisible':not was_hide_render,'foodWorldCorners':[plain(v) for v in verts],'foodProjectedCorners':[px(v) for v in verts],'foodPlaneMatrix':mat(plane.matrix_world),'handProjected':{s:px(v) for s,v in hands.items()},'feetProjected':{s:px(v) for s,v in feet.items()}}
   samples.append(sample)
   plane.hide_render=was_hide_render;plane.hide_viewport=was_hide_viewport;bpy.context.view_layer.update()
  # One native representative of every source pose/facing, frame5. Keep all 48/480 numeric samples.
  native.apply_clip(a,rig,clip,frame=5,direction=direction,scene=scene)
  scene.render.filepath=str(R/(clip+'-'+direction+'-f05.png'));bpy.ops.render.render(write_still=True)
 report['clips'][clip]={'loop':rig['clips'][clip]['loop'],'samples':samples,'boundsUnion':[[min(s['bodyBounds'][0][i] for s in samples) for i in range(3)],[max(s['bodyBounds'][1][i] for s in samples) for i in range(3)]],'foodVisibleCount':sum(s['foodVisible'] for s in samples)}
 (R/'audit.json').write_text(json.dumps(report,indent=2))
 print('AUDITED',MODE,clip,report['clips'][clip]['boundsUnion'],report['clips'][clip]['foodVisibleCount'],flush=True)
print('FINISHED',MODE,flush=True)
