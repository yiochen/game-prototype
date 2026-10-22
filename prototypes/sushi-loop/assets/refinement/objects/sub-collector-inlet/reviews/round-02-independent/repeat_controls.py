import bpy,pathlib,math,json
O=pathlib.Path(__file__).resolve().parent;s=bpy.context.scene;root=bpy.data.objects['collector__root'];rows=[]
for suffix in ['guard_rock','mouth_pulse','mouth_sleeve']:
 ob=bpy.data.objects['collector__'+suffix];a=bpy.data.actions[f'INLET_NATIVE__active__collector__{suffix}'];ob.animation_data_create();ob.animation_data.action=a;ob.animation_data.action_slot=a.slots[0]
for di in 'EW':
 root.rotation_euler.z={'E':math.pi/2,'W':-math.pi/2}[di]
 for fr in [1,13]:
  s.frame_set(fr);bpy.context.view_layer.update()
  for i in range(8):
   p=O/'native'/f'extra-control-{di}-{fr}-{i}.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True);rows.append({'direction':di,'frame':fr,'repeat':i,'image':str(p.relative_to(O.parent.parent))})
(O/'extra-controls.json').write_text(json.dumps({'method':'Eight repeated same-pose renders each saved frame1 and13 in E/W; source/settings unchanged, no normalization or image repair. Expanded after initial closure differences exceeded initial per-facing samepose pixel counts.','records':rows},indent=2))
