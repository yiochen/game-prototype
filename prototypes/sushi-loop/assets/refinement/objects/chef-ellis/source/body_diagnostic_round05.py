"""Labeled diagnostic only: same approved body rendered with its2D food hidden, never saved."""
import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;OUT=P.parent/'candidates/round-05';sys.path.insert(0,str(P));import native_actions_round05 as native
baseline='--baseline' in sys.argv;sc=bpy.data.scenes['Ellis warm soft round04'];bpy.context.window.scene=sc;asset={'root':bpy.data.objects['chef_ellis__ground_root.001'],'collection':bpy.data.collections['S33_CHARACTER_chef_ellis.001']};rig=json.loads((P/'rig-round05.json').read_text());plane=bpy.data.objects['chef_ellis__ground_root.001__held_dish-salmon__image_plane']
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for device in prefs.devices:device.use=device.type=='METAL'
except Exception:pass
for d in ['N','E','S','W']:
 native.apply_clip(asset,rig,'hold',6,d,sc);saved=plane.hide_render;plane.hide_render=True;bpy.context.view_layer.update();path=OUT/'body-diagnostics'/('approved04' if baseline else 'candidate05')/(d+'.png');path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);plane.hide_render=saved;bpy.context.view_layer.update()
print('BODY_DIAGNOSTIC_COMPLETE',baseline,flush=True)
