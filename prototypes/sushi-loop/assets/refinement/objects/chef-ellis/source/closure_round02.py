import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;BASE=P.parent;OUT=BASE/'candidates/round-02';F=OUT/'closures';F.mkdir(exist_ok=True);sys.path.insert(0,str(P));import native_actions_round02 as native
rig=json.loads((P/'rig-round02.json').read_text());sc=bpy.data.scenes['Ellis warm soft round02'];bpy.context.window.scene=sc;asset={'root':bpy.data.objects['chef_ellis__ground_root.001'],'collection':bpy.data.collections['S33_CHARACTER_chef_ellis.001']}
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for device in prefs.devices:device.use=device.type=='METAL'
except Exception:pass
rows=[]
for clip in ['idle','work','hold']:
 for d in ['N','E','S','W']:
  native.apply_clip(asset,rig,clip,13,d,sc);path=F/(clip+'-'+d+'-key13.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);rows.append({'clip':clip,'direction':d,'key':13,'path':str(path.relative_to(BASE))})
(OUT/'closure-renders.json').write_text(json.dumps(rows,indent=2))
