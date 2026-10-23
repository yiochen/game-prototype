import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent.parent
sc=bpy.context.scene;G=bpy.data.collections['S33_PROP_uniform35-gate'];W=bpy.data.collections['S33_PROP_uniform35-wall-plain']
for o in G.objects:o.hide_render=True
W.hide_render=False;W.hide_viewport=False
for o in W.objects:o.hide_render=False
sc.render.resolution_x=576;sc.render.resolution_y=1344;sc.camera.data.ortho_scale=1.5;sc.camera.data.shift_y=.2696022093296051*4.5/1.5
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.refresh_devices()
 for d in pref.devices:d.use=d.type=='METAL'
 sc.cycles.device='GPU'
except Exception:pass
sc.view_layers[0].update();sc.render.filepath=str(P/'candidates/round-04/wall-context-S.png');bpy.ops.render.render(write_still=True)
print('MATCHING_WALL_CONTEXT_CAPTURED')
