import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;BASE=P.parent;OUT=BASE/'candidates/round-03';sys.path.insert(0,str(P));import native_actions_round03 as native
from audit_common_round03 import geometry
source='--source' in sys.argv;coll=bpy.data.collections['S33_CHARACTER_chef_ellis.001'];root=bpy.data.objects['chef_ellis__ground_root.001'];arm=bpy.data.objects['chef_ellis__armature.001'];rig=json.loads((P/'rig-round03.json').read_text())
if source:
 sc=bpy.data.scenes.new('Ellis original integrity inspection');sc.collection.children.link(coll)
else:sc=bpy.data.scenes['Ellis warm soft round03']
bpy.context.window.scene=sc;coll.hide_render=False;coll.hide_viewport=False
for lc in bpy.context.view_layer.layer_collection.children:lc.exclude=False;lc.hide_viewport=False
for o in coll.all_objects:o.hide_set(False)
asset={'collection':coll,'root':root,'armature':arm};native.apply_clip(asset,rig,'idle',1,'S',sc);arm.data.pose_position='REST';bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();body={o.name:geometry(o,dg) for o in coll.all_objects if o.type=='MESH' and '__image_plane' not in o.name and '__knife_' not in o.name}
bounds=[[min(v['bounds'][i][0] for v in body.values()),max(v['bounds'][i][1] for v in body.values())] for i in range(3)]
actions={}
for clip,info in rig['clips'].items():
 for target in info['actions']:
  action=bpy.data.actions[target['action']];rows=[]
  for fc in native._fcurves(action):rows.append({'path':fc.data_path,'index':fc.array_index,'keys':[[float(k.co[0]),float(k.co[1]),k.interpolation] for k in fc.keyframe_points]})
  data=json.dumps(rows,sort_keys=True,separators=(',',':')).encode();actions[action.name]={'sha256':hashlib.sha256(data).hexdigest(),'channels':len(rows),'keys':sum(len(r['keys']) for r in rows),'owner':target['ownerName'],'slot':target.get('slotIdentifier')}
images=[]
for im in bpy.data.images:
 if im.type!='RENDER_RESULT':images.append({'name':im.name,'packed':bool(im.packed_file),'packedSHA256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None,'size':list(im.size),'path':im.filepath})
report={'source':source,'actions':actions,'rest':{b.name:[list(r) for r in b.matrix_local] for b in arm.data.bones},'restBodyBounds':bounds,'nominalHeight':1.3968749344348907,'heightDeltaFromNominal':bounds[2][1]-1.3968749344348907,'bodyObjectCount':len(body),'objects':len(coll.all_objects),'sceneObjects':[o.name for o in sc.objects],'scenes':[s.name for s in bpy.data.scenes],'collections':[c.name for c in sc.collection.children],'images':images,'libraries':[l.filepath for l in bpy.data.libraries],'salmonPlane':{'representation':bpy.data.objects['chef_ellis__ground_root.001__held_dish-salmon__image_plane'].get('representation'),'uv':[[round(v,9) for v in x.uv] for x in bpy.data.objects['chef_ellis__ground_root.001__held_dish-salmon__image_plane'].data.uv_layers.active.data],'driverExpressions':{o.name:[(fc.data_path,fc.array_index,fc.driver.expression) for fc in o.animation_data.drivers] for o in coll.all_objects if o.animation_data and len(o.animation_data.drivers)}}}
path=OUT/('source-integrity.json' if source else 'reopened-integrity.json');path.write_text(json.dumps(report,indent=2));print('INTEGRITY',str(path),bounds,flush=True)
