import bpy,pathlib,math,json
O=pathlib.Path(__file__).resolve().parent;s=bpy.context.scene;root=bpy.data.objects['collector__root'];root.rotation_euler.z=-math.pi/2
for suffix in ['guard_rock','mouth_pulse','mouth_sleeve']:
 ob=bpy.data.objects['collector__'+suffix];a=bpy.data.actions[f'INLET_NATIVE__active__collector__{suffix}'];ob.animation_data_create();ob.animation_data.action=a;ob.animation_data.action_slot=a.slots[0]
records=[]
for fr in [1,13]:
 s.frame_set(fr);bpy.context.view_layer.update()
 for i in range(8):
  p=O/'native'/f'extra-control-W-{fr}-{i}.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'frame':fr,'repeat':i,'image':str(p.relative_to(O.parent.parent))})
(O/'extra-w-controls.json').write_text(json.dumps({'sourceUnchanged':True,'settingsUnchanged':True,'method':'Eight repeated captures per unchanged source pose1 and13 inW, no builder, no setting or pixel changes; expands empirical sample after initial Wclosure had9one-level pixels while initial Wsame-pose pairs had1.','records':records},indent=2)+'\n')
