import bpy,json,hashlib,sys,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
repo=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype');b=repo/'prototypes/sushi-loop/assets/refinement/objects/chef-noor';out=b/'reviews';brief=json.loads((b/'brief-v3-held-food-semantic-contact.json').read_text());sys.path.insert(0,str(b/'source'));import native_actions_round01 as actions
rig=json.loads((b/'source/rig-round01.json').read_text());root=bpy.data.objects[rig['groundRootObject']];coll=root.users_collection[0];arm=bpy.data.objects[rig['clips']['idle']['actions'][0]['ownerName']];asset={'root':root,'collection':coll,'armature':arm};scene=bpy.context.scene;cam=scene.camera
plane=next(o for o in coll.all_objects if '__held_dish-salmon__image_plane' in o.name);foodroot=plane.parent;im=next(n.image for m in plane.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
packed=bytes(im.packed_file.data);(out/'round02-inspected-packed.png').write_bytes(packed)
def custom(o):return {k:str(v) for k,v in o.items()}
def drivers(o):
 result=[]
 if not o.animation_data:return result
 for f in o.animation_data.drivers:
  result.append({'dataPath':f.data_path,'arrayIndex':f.array_index,'expression':f.driver.expression,'valid':f.driver.is_valid,'variables':[{'name':v.name,'type':v.type,'targets':[{'idName':t.id.name if t.id else None,'isActualRoot':t.id==root,'dataPath':t.data_path} for t in v.targets]} for v in f.driver.variables]})
 return result
p=lambda v: [float(v.x),float(v.y),float(v.z)]
def px(v):
 v=world_to_camera_view(scene,cam,Vector(v));return [v.x*scene.render.resolution_x,(1-v.y)*scene.render.resolution_y]
r={'asset':'chef-noor','scope':'read-only approved source inspection; dependency-only preparation','sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'canonicalSHA256':hashlib.sha256((b/brief['foodDependency']['artwork']).resolve().read_bytes()).hexdigest(),'sourcePackedImage':{'name':im.name,'size':list(im.size),'alphaMode':im.alpha_mode,'colorspace':im.colorspace_settings.name,'filepath':im.filepath,'packedSHA256':hashlib.sha256(packed).hexdigest()},'sourcePlane':{'name':plane.name,'parent':foodroot.name,'vertices':[list(v.co) for v in plane.data.vertices],'polygons':[list(v.vertices) for v in plane.data.polygons],'uvLoops':[list(v.uv) for v in plane.data.uv_layers.active.data],'location':list(plane.location),'rotationEuler':list(plane.rotation_euler),'scale':list(plane.scale),'customProperties':custom(plane),'drivers':drivers(plane),'visibleCamera':plane.visible_camera,'visibleDiffuse':plane.visible_diffuse,'visibleGlossy':plane.visible_glossy,'visibleShadow':plane.visible_shadow},'foodRoot':{'name':foodroot.name,'parent':foodroot.parent.name,'location':list(foodroot.location),'scale':list(foodroot.scale),'customProperties':custom(foodroot)},'chefRoot':{'name':root.name,'location':list(root.location),'scale':list(root.scale),'customProperties':custom(root)},'material':[],'lights':[{'name':o.name,'location':list(o.location),'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size} for o in scene.objects if o.type=='LIGHT'],'camera':{'name':cam.name,'matrix':[list(row) for row in cam.matrix_world],'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[scene.render.resolution_x,scene.render.resolution_y],'rootPixel':px([0,0,0])},'actions':{},'evaluatedSamples':[]}
for m in plane.data.materials:
 nodes=[]
 for n in m.node_tree.nodes:
  nodes.append({'name':n.name,'type':n.bl_idname,'image':n.image.name if n.type=='TEX_IMAGE' else None,'interpolation':n.interpolation if n.type=='TEX_IMAGE' else None,'extension':n.extension if n.type=='TEX_IMAGE' else None,'inputs':{s.name:s.default_value if isinstance(s.default_value,(int,float,str,bool)) else list(s.default_value) for s in n.inputs if hasattr(s,'default_value')}})
 r['material'].append({'name':m.name,'nodes':nodes,'links':[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in m.node_tree.links]})
for clip in ['idle','work','hold','load']:
 r['actions'][clip]={'loop':rig['clips'][clip]['loop'],'frames':rig['clips'][clip]['frames'],'fps':rig['clips'][clip]['fps'],'owners':rig['clips'][clip]['actions']}
 for d in ['N','E','S','W']:
  for i in range(12):
   actions.apply_clip(asset,rig,clip,i+1,d,scene);dg=bpy.context.evaluated_depsgraph_get();ev=plane.evaluated_get(dg);fr=foodroot.evaluated_get(dg);ar=arm.evaluated_get(dg)
   r['evaluatedSamples'].append({'clip':clip,'direction':d,'index':i,'hideRender':plane.hide_render,'rootYawDegrees':math.degrees(root.rotation_euler.z),'foodRootWorld':list(fr.matrix_world.translation),'planeEvaluatedWorldMatrix':[list(row) for row in ev.matrix_world],'planeLocalLocation':list(plane.location),'planeLocalEuler':list(plane.rotation_euler),'projectedVerticesNative':[px(ev.matrix_world@v.co) for v in plane.data.vertices],'bonePalms':{s:{'head':p(ar.matrix_world@ar.pose.bones['hand_'+s].head),'tail':p(ar.matrix_world@ar.pose.bones['hand_'+s].tail)} for s in ['L','R']}})
(out/'round02-native-independent-inspection.json').write_text(json.dumps(r,indent=2)+'\n')
print('SOURCE',r['sourceSHA256']);print('PACKED',r['sourcePackedImage']);print('PLANE',r['sourcePlane']);print('FOODROOT',r['foodRoot']);print('MATERIAL',r['material'])
