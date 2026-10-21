import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
repo=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype');b=repo/'prototypes/sushi-loop/assets/refinement/objects/chef-noor';out=b/'reviews'
sys.path.insert(0,str(b/'source'));import native_actions_round01 as actions
rig=json.loads((b/'source/rig-round01.json').read_text());original=json.loads((out/'source-native-inspection.json').read_text());origlook={(r['clip'],r['direction'],r['index']):r for r in original['frames']}
root=bpy.data.objects[rig['groundRootObject']];collection=root.users_collection[0];arm=bpy.data.objects[rig['clips']['idle']['actions'][0]['ownerName']];scene=bpy.context.scene
asset={'root':root,'collection':collection,'armature':arm};report={'projectSHA256':hashlib.sha256((b/'source/round-01.blend').read_bytes()).hexdigest(),'scene':scene.name,'collection':collection.name,'sceneObjects':len(scene.objects),'characterObjects':len(collection.all_objects),'camera':{},'lights':[],'materialGraphs':[],'images':[],'frames':[],'boneEndpointMaxDeltaToOriginal':0,'topologyChanges':[]}
cam=scene.camera;w=scene.render.resolution_x*scene.render.resolution_percentage/100;h=scene.render.resolution_y*scene.render.resolution_percentage/100
def pix(v):
 q=world_to_camera_view(scene,cam,Vector(v));return [q.x*w,(1-q.y)*h]
report['camera']={'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'worldMatrix':[list(r) for r in cam.matrix_world],'resolution':[w,h],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'rootPixel':pix([0,0,0]),'unitXPixel':pix([1,0,0]),'unitDepthPixel':pix([0,-1,0]),'unitHeightPixel':pix([0,0,1])}
report['lights']=[{'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size} for o in scene.objects if o.type=='LIGHT']
for m in bpy.data.materials:
 if not any(o.type=='MESH' and m.name in o.data.materials for o in collection.all_objects):continue
 report['materialGraphs'].append({'name':m.name,'nodeTypes':[n.bl_idname for n in m.node_tree.nodes] if m.use_nodes else [],'principled':[{'roughness':n.inputs['Roughness'].default_value,'metallic':n.inputs['Metallic'].default_value} for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'] if m.use_nodes else []})
for im in bpy.data.images:
 if im.packed_file:report['images'].append({'name':im.name,'path':im.filepath,'packedSHA256':hashlib.sha256(im.packed_file.data).hexdigest()})
report['linkedLibraries']=[x.filepath for x in bpy.data.libraries]
tops={}
for clip in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:
  for i in range(12):
   actions.apply_clip(asset,rig,clip,i+1,d,scene);dg=bpy.context.evaluated_depsgraph_get();aev=arm.evaluated_get(dg);boneends={}
   for bn in ['hand_L','hand_R','foot_L','foot_R']:
    pb=aev.pose.bones.get(bn)
    if pb:boneends[bn]={'head':list(aev.matrix_world@pb.head),'tail':list(aev.matrix_world@pb.tail)}
   ref=origlook[(clip,d,i)]['boneEnds']
   for bn,v in boneends.items():
    for e in ['head','tail']:
     for j,x in enumerate(v[e]):report['boneEndpointMaxDeltaToOriginal']=max(report['boneEndpointMaxDeltaToOriginal'],abs(x-ref[bn][e][j]))
   coords=[]
   for o in collection.all_objects:
    if o.type!='MESH':continue
    ev=o.evaluated_get(dg);tops.setdefault(o.name,set()).add((len(ev.data.vertices),len(ev.data.polygons)))
    if not o.hide_render and '__image_plane' not in o.name:coords.extend(ev.matrix_world@Vector(c) for c in ev.bound_box)
   report['frames'].append({'clip':clip,'direction':d,'index':i,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'boneEnds':boneends,'physicalBounds':{'min':[min(v[j] for v in coords) for j in range(3)],'max':[max(v[j] for v in coords) for j in range(3)]}})
report['topologyChanges']={n:[list(t) for t in v] for n,v in tops.items() if len(v)>1}
report['worldNodes']=[{'type':n.bl_idname,'strength':n.inputs['Strength'].default_value if n.type=='BACKGROUND' else None} for n in scene.world.node_tree.nodes]
(out/'round01-native-independent-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print('CANDIDATE',report['projectSHA256'],'BONES_MAX_DIFF',report['boneEndpointMaxDeltaToOriginal'],'TOPOLOGY_CHANGES',report['topologyChanges'])
print('CAMERA',report['camera'])
print('LIGHTS',report['lights']);print('IMAGES',report['images'])
