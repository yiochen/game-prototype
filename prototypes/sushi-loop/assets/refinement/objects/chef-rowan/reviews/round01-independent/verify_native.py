import bpy,json,pathlib,hashlib,importlib.util
from mathutils import Vector
b=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-rowan');out=b/'reviews/round01-independent';sc=bpy.context.scene
col=bpy.data.collections['S33_CHARACTER_chef_rowan.001'];root=bpy.data.objects['chef_rowan__ground_root.001'];arm=bpy.data.objects['chef_rowan__armature.001'];plane=bpy.data.objects[root.name+'__held_dish-salmon__image_plane']
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
for l in bpy.context.view_layer.layer_collection.children:l.exclude=l.collection!=col
col.hide_render=col.hide_viewport=False;bpy.context.view_layer.update()
spec=importlib.util.spec_from_file_location('native_judge_verify',b/'source/resources/original-native-actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native);record=json.loads((b/'inputs/source-rig.json').read_text());asset={'root':root,'collection':col,'armature':arm}
def v(x):return [float(y) for y in x]
def mat(x):return [v(y) for y in x]
texture=[]
for m in plane.data.materials:
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE':texture.append({'image':n.image.name,'packedSHA256':hashlib.sha256(bytes(n.image.packed_file.data)).hexdigest(),'size':list(n.image.size)})
actions=[]
for clip,r in record['clips'].items():
 for t in r['actions']:
  action=bpy.data.actions.get(t['action']);curves=[]
  for fc in native._fcurves(action):
   curves.append({'path':fc.data_path,'index':fc.array_index,'keys':[{'co':v(k.co),'left':v(k.handle_left),'right':v(k.handle_right),'interpolation':k.interpolation} for k in fc.keyframe_points]})
  actions.append({'name':action.name,'sha256':hashlib.sha256(json.dumps(curves,sort_keys=True).encode()).hexdigest()})
data={'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'nativeSourceOnly':True,'uv':[v(x.uv) for x in plane.data.uv_layers.active.data],'planeVertices':[v(x.co) for x in plane.data.vertices],'foodTexture':texture,'actions':actions,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':v(o.data.color),'location':v(o.location),'size':getattr(o.data,'size',None)} for o in sc.objects if o.type=='LIGHT'],'world':{'name':sc.world.name},'colorManagement':{'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'renders':[]}
for clip,facing,index in [('idle','S',0),('hold','N',0),('load','S',5)]:
 native.apply_clip(asset,record,clip,index+1,facing,sc);bpy.context.view_layer.update()
 path=out/f'reopened-{clip}-{facing}-{index:02}.png';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True,scene=sc.name);data['renders'].append({'path':str(path),'submitted':f'frames/{clip}-{facing}-{index:02}.png'})
(out/'native_extra.json').write_text(json.dumps(data,indent=2));print('Independent reopening/rendering complete')
