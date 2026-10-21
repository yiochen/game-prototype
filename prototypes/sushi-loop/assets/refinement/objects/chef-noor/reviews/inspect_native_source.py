import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector
repo=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
b=repo/'prototypes/sushi-loop/assets/refinement/objects/chef-noor'
brief=json.loads((b/'brief.json').read_text());rig=json.loads((b/'inputs/source-rig.json').read_text())
sys.path.insert(0,str(repo/'prototypes/sushi-loop/assets/production/source/blender'))
import native_actions
root=bpy.data.objects[rig['groundRootObject']]
collection=root.users_collection[0]
scene=bpy.data.scenes.new('JUDGE_SOURCE_NOOR_INSPECTION')
scene.collection.children.link(collection)
bpy.context.window.scene=scene
asset={'root':root,'collection':collection}
arm=bpy.data.objects[rig['clips']['idle']['actions'][0]['ownerName']]
asset['armature']=arm
report={'asset':'chef-noor','sourceProject':brief['source']['project'],'sourceProjectSHA256':hashlib.sha256((b/brief['source']['project']).resolve().read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'collection':collection.name,'groundRoot':root.name,'rootLocalLocation':list(root.location),'rootLocalScale':list(root.scale),'parts':[],'frames':[]}
for o in collection.all_objects:
 report['parts'].append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'rotation':list(o.rotation_euler),'location':list(o.location),'scale':list(o.scale),'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else []})
for clip in ['idle','work','hold','load']:
 for direction in ['N','E','S','W']:
  for i in range(12):
   native_actions.apply_clip(asset,rig,clip,i+1,direction,scene)
   dg=bpy.context.evaluated_depsgraph_get()
   coords=[];top=[];props={}
   for o in collection.all_objects:
    ev=o.evaluated_get(dg)
    if o.type=='MESH':
     top.append([o.name,len(ev.data.vertices),len(ev.data.polygons)])
     if not o.hide_render and '__image_plane' not in o.name:
      coords.extend(ev.matrix_world@Vector(c) for c in ev.bound_box)
    if any(s in o.name for s in ['held_dish','knife','utensil']):
     props[o.name]={'hideRender':o.hide_render,'worldLocation':list(ev.matrix_world.translation),'worldEuler':list(ev.matrix_world.to_euler())}
   boneends={}
   aev=arm.evaluated_get(dg)
   for bn in ['hand_L','hand_R','foot_L','foot_R']:
    pb=aev.pose.bones.get(bn)
    if pb:boneends[bn]={'head':list(aev.matrix_world@pb.head),'tail':list(aev.matrix_world@pb.tail)}
   report['frames'].append({'clip':clip,'direction':direction,'index':i,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'physicalBounds':{'min':[min(v[c] for v in coords) for c in range(3)],'max':[max(v[c] for v in coords) for c in range(3)]},'evaluatedTopology':top,'boneEnds':boneends,'props':props})
report['actionCohorts']={c:{'frames':v['frames'],'loop':v['loop'],'firstFrame':v['firstFrame'],'lastUniqueFrame':v['lastUniqueFrame'],'closingKeyFrame':v['closingKeyFrame'],'actions':v['actions']} for c,v in rig['clips'].items()}
report['images']=[{'name':im.name,'file':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if any(im==n.image for o in collection.all_objects if o.type=='MESH' for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE')]
(b/'reviews/source-native-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print('JUDGE_INSPECTED',len(report['parts']),'parts',len(report['frames']),'native frames')
print('SOURCE_HASH',report['sourceProjectSHA256'])
print('ROOT',report['rootLocalLocation'],report['rootLocalScale'])
for c in ['idle','work','hold','load']:
 fs=[f for f in report['frames'] if f['clip']==c and f['direction']=='S'];print(c,'boundsZ',min(f['physicalBounds']['min'][2] for f in fs),max(f['physicalBounds']['max'][2] for f in fs))
print('IMAGES',report['images'])
