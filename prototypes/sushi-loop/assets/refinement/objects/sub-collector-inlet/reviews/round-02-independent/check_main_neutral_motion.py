import bpy,pathlib,json
O=pathlib.Path(__file__).resolve().parent;E=O.parent.parent;bpy.ops.wm.open_mainfile(filepath=str(E/'source/round-02-assembled.blend'));s=bpy.context.scene;root=bpy.data.objects['submarine-yellow__root'];actions=json.loads(root['nativeActions']);own=bpy.data.collections['REFINED__sub-collector-inlet'];skids=[o for o in s.objects if o.name.startswith('body__hover_skid_')]
for suffix in ['guard_rock','mouth_pulse','mouth_sleeve']:
 ob=bpy.data.objects['collector__'+suffix];a=bpy.data.actions[f'INLET_NATIVE__idle__collector__{suffix}'];ob.animation_data_create();ob.animation_data.action=a;ob.animation_data.action_slot=a.slots[0]
records=[]
for clip in actions:
 if not clip.startswith('upgraded-'):continue
 for owner,an in actions[clip].items():
  ob=bpy.data.objects[owner];a=bpy.data.actions[an];ob.animation_data_create();ob.animation_data.action=a;ob.animation_data.action_slot=a.slots[0]
 for frame in range(1,13):
  s.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
  def minz(objects):
   zs=[]
   for ob in objects:
    if ob.type!='MESH':continue
    eo=ob.evaluated_get(dg);me=eo.to_mesh();zs.extend((eo.matrix_world@v.co).z for v in me.vertices);eo.to_mesh_clear()
   return min(zs)
  cz=minz(own.all_objects);sz=minz(skids);records.append({'clip':clip,'frame':frame,'collectorMinimumZ':cz,'skidsMinimumZ':sz,'collectorAboveLowestSkid':cz-sz})
(O/'neutral-through-main-actions.json').write_text(json.dumps({'scope':'Independent geometry check only: exact collector NEUTRAL idle retained through every existing upgraded main native action. No own active action mapped into main, no rendered main576/family approval. Native parent/body resources unchanged; runtime dock deck arrangement remains a later main integration check.','records':records,'sampleCount':len(records),'minimumSkidSeparation':min(r['collectorAboveLowestSkid'] for r in records),'allSkidsRemainLowest':all(r['collectorAboveLowestSkid']>0 for r in records),'dockSkidRange':[[min(r['skidsMinimumZ'] for r in records if r['clip']==c),max(r['skidsMinimumZ'] for r in records if r['clip']==c)] for c in ['upgraded-dock-charging','upgraded-dock-ready']]},indent=2)+'\n');print('MAIN_NEUTRAL_CHECK',len(records),min(r['collectorAboveLowestSkid'] for r in records))
