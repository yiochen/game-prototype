import sys
sys.dont_write_bytecode=True
import bpy,json,math,pathlib
ROOT=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype');O=ROOT/'prototypes/sushi-loop/assets/refinement/objects/customer-rosa';r=json.loads((O/'inputs/runtime-variants/export/source/customer-rosa/rig.json').read_text());root=bpy.data.objects[r['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];col=next(c for c in root.users_collection if root.name in c.all_objects)
for c in sc.collection.children:c.hide_viewport=c.hide_render=c!=col
for layer in sc.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=col
for ob in col.all_objects:
 if ob.animation_data:
  ob.animation_data.action=None
  for track in ob.animation_data.nla_tracks:track.mute=True
for target in r['clips']['eat-salmon']['actions']:
 ob=bpy.data.objects[target['ownerName']];a=bpy.data.actions[target['action']];ob.animation_data_create();ob.animation_data.action=a;slot=next((s for s in a.slots if s.identifier==target.get('slotIdentifier')),None)
 if slot:ob.animation_data.action_slot=slot
sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100
for d,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=angle;sc.frame_set(1);bpy.context.view_layer.update();sc.render.filepath=str(O/'reviews'/('source-runtime-eat-salmon-'+d+'.png'));bpy.ops.render.render(write_still=True)
