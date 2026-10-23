import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;BASE=P.parent;OUT=BASE/'candidates/round-05';sys.path.insert(0,str(P));import native_actions_round05 as native
assert json.loads((OUT/'semantic-parity.json').read_text())['ok']
sc=bpy.data.scenes['Ellis warm soft round04'];bpy.context.window.scene=sc;asset={'root':bpy.data.objects['chef_ellis__ground_root.001'],'collection':bpy.data.collections['S33_CHARACTER_chef_ellis.001']};rig=json.loads((P/'rig-round05.json').read_text())
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for device in prefs.devices:device.use=device.type=='METAL'
except Exception:pass
rows=[]
for c,f in [('hold',6),('load',6),('load',12)]:
 for d in ['N','E','S','W']:
  native.apply_clip(asset,rig,c,f,d,sc);path=OUT/'representatives'/(c+'-'+d+'-'+str(f)+'.png');path.parent.mkdir(exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);rows.append({'clip':c,'direction':d,'sourceFrame':f,'path':str(path.relative_to(BASE))})
(OUT/'food-representatives.json').write_text(json.dumps(rows,indent=2))
