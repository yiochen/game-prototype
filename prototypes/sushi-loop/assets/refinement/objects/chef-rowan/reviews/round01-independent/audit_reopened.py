import bpy,json,pathlib,importlib.util,hashlib,math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
base=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
b=base/'prototypes/sushi-loop/assets/refinement/objects/chef-rowan';out=b/'reviews/round01-independent'
src=base/'prototypes/sushi-loop/assets/production/source/blender'
spec=importlib.util.spec_from_file_location('rowan_judge_native',src/'revisions/d88e53edef8e7c73/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
sc=bpy.context.scene;bpy.context.window.scene=sc
col=bpy.data.collections['S33_CHARACTER_chef_rowan.001'];root=bpy.data.objects['chef_rowan__ground_root.001'];arm=bpy.data.objects['chef_rowan__armature.001'];food=bpy.data.objects[root.name+'__held_dish-salmon'];plane=bpy.data.objects[root.name+'__held_dish-salmon__image_plane'];knife=bpy.data.objects[root.name+'__utensil']
def layers(n):
 yield n
 for c in n.children:yield from layers(c)
for n in layers(bpy.context.view_layer.layer_collection):n.exclude=False
for n in bpy.context.view_layer.layer_collection.children:n.exclude=n.collection!=col
col.hide_viewport=False;col.hide_render=False
for o in col.all_objects:o.hide_set(False)
bpy.context.view_layer.update()
record=json.loads((b/'inputs/source-rig.json').read_text());asset={'root':root,'collection':col,'armature':arm}
objects=list(col.all_objects);body=[o for o in objects if o.type=='MESH' and o!=plane and o.parent!=knife];knife_parts=list(knife.children)
def v(x):return [float(y) for y in x]
def mat(x):return [v(y) for y in x]
def bounds(obs,dg):
 pts=[]
 for o in obs:
  if o.hide_render:continue
  e=o.evaluated_get(dg);me=e.to_mesh();pts.extend([e.matrix_world@v.co for v in me.vertices]);e.to_mesh_clear()
 return {'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]} if pts else None
contacts=[];maxerr=0
rest={'rootLocation':v(root.location),'rootScale':v(root.scale),'rootMatrix':mat(root.matrix_world),'armatureLocalMatrix':mat(arm.matrix_local),'bones':[{'name':x.name,'parent':x.parent.name if x.parent else None,'matrixLocal':mat(x.matrix_local),'useDeform':x.use_deform} for x in arm.data.bones], 'bodyObjects':[o.name for o in body]}
for clip in ['idle','work','hold','load']:
 for facing in ['S','E','N','W']:
  for index in range(12):
   native.apply_clip(asset,record,clip,index+1,facing,sc);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ae=arm.evaluated_get(dg)
   hand={}
   for side,sign in [('L',-1),('R',1)]:
    bone=ae.pose.bones['hand_'+side];p=Vector((sign*.267,-.025,.165));local=bone.matrix@ae.data.bones['hand_'+side].matrix_local.inverted()@p;hand[side]=ae.matrix_world@local
   center=(hand['L']+hand['R'])/2;expected=center+root.matrix_world.to_3x3()@Vector((0,0,.018));actual=food.evaluated_get(dg).matrix_world.translation.copy();err=(actual-expected).length;maxerr=max(maxerr,err)
   contact={'clip':clip,'facing':facing,'index':index,'rootLocation':v(root.location),'rootScale':v(root.scale),'rootYaw':float(root.rotation_euler.z),'bodyBounds':bounds(body,dg),'knifeBounds':bounds(knife_parts,dg),'handsWorld':{k:v(x) for k,x in hand.items()},'foodRootWorld':v(actual),'foodPalmMidpointError':err,'foodPlaneWorldMatrix':mat(plane.evaluated_get(dg).matrix_world),'foodVisible':not plane.hide_render,'knifeVisible':[not o.hide_render for o in knife_parts],'feetBoneWorld':{side:v(ae.matrix_world@ae.pose.bones['foot_'+side].head) for side in ['L','R']},'headBoneWorld':v(ae.matrix_world@ae.pose.bones['head'].head)}
   contacts.append(contact)
images=[];materials=set()
for o in objects:
 if o.type=='MESH':
  for m in o.data.materials:
   if m:materials.add(m)
for m in materials:
 if m.use_nodes:
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE' and n.image:
    im=n.image;images.append({'material':m.name,'image':im.name,'filepath':im.filepath,'packed':bool(im.packed_file),'size':list(im.size),'packedSHA256':hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None})
foreign=[]
for o in objects:
 if o.parent and o.parent not in objects:foreign.append([o.name,'parent',o.parent.name])
 for mod in o.modifiers:
  t=getattr(mod,'object',None)
  if t and t not in objects:foreign.append([o.name,'modifier',t.name])
 for con in o.constraints:
  t=getattr(con,'target',None)
  if t and t not in objects:foreign.append([o.name,'constraint',t.name])
cam=sc.camera
summary={'sourceProjectSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'method':'Original native export scene made active; all layer exclusions first cleared; non-Rowan collections excluded; Rowan globally unhidden in viewport+render; depsgraph updated before all192 native evaluations; no save/model mutation. Native apply_clip assigns original baked cohort, never rebuilds pose.','objectCount':len(objects),'bodyMeshCount':len(body),'rigBones':len(arm.data.bones),'camera':{'matrix':mat(cam.matrix_world),'type':cam.data.type,'orthoScale':float(cam.data.ortho_scale),'shift': [cam.data.shift_x,cam.data.shift_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'rootPixels':v(world_to_camera_view(sc,cam,Vector((0,0,0))))},'images':images,'foreignDependencies':foreign,'driverTargets':[{'object':o.name,'path':d.data_path,'index':d.array_index,'expression':d.driver.expression,'targets':[{'id':t.id.name if t.id else None,'path':t.data_path} for x in d.driver.variables for t in x.targets]} for o in objects if o.animation_data for d in o.animation_data.drivers],'maxFoodPalmMidpointError':maxerr,'bodyBoundsAllFrames':{'min':[min(x['bodyBounds']['min'][i] for x in contacts) for i in range(3)],'max':[max(x['bodyBounds']['max'][i] for x in contacts) for i in range(3)]},'clips':{clip:{'fps':record['clips'][clip]['fps'],'loop':record['clips'][clip]['loop'],'closingKeyFrame':record['clips'][clip]['closingKeyFrame'],'SHeadZ':[x['headBoneWorld'][2] for x in contacts if x['clip']==clip and x['facing']=='S'],'SFoodRoot':[x['foodRootWorld'] for x in contacts if x['clip']==clip and x['facing']=='S']} for clip in ['idle','work','hold','load']}}
(out/'source_native_audit.json').write_text(json.dumps({'summary':summary,'rest':rest,'frames':contacts},indent=2));print(json.dumps({'project':summary['sourceProjectSHA256'],'bounds':summary['bodyBoundsAllFrames'],'images':summary['images'],'foodPalmError':summary['maxFoodPalmMidpointError'],'foreignDependencies':summary['foreignDependencies']}))
