import bpy,sys,json
from pathlib import Path
base=Path.cwd()/'prototypes/sushi-loop/assets';obj=base/'refinement/objects/chef-ellis';sys.path.insert(0,str(base/'production/source/blender'));import native_actions
c=bpy.data.collections['S33_CHARACTER_chef_ellis.001'];c.hide_render=False;c.hide_viewport=False;bpy.context.view_layer.update();a={'collection':c,'root':bpy.data.objects['chef_ellis__ground_root.001'],'armature':bpy.data.objects['chef_ellis__armature.001']};r=json.loads((obj/'inputs/source-rig.json').read_text());native_actions.apply_clip(a,r,'work',4,'W',bpy.context.scene)
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
bpy.context.scene.render.filepath=str(obj/'reviews/round-04-inspection/native-spotcheck-work-W-003.png');bpy.ops.render.render(write_still=True)
