import bpy,json,sys,hashlib
from pathlib import Path
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-01';D=C/'reproduction';D.mkdir(exist_ok=True);sys.path.insert(0,str(P));import native_actions_round01 as native
sc=bpy.data.scenes['Noor warm soft round01'];bpy.context.window.scene=sc;coll=bpy.data.collections['S33_CHARACTER_chef_noor.001'];root=bpy.data.objects['chef_noor__ground_root.001'];arm=bpy.data.objects['chef_noor__armature.001'];rig=json.loads((P/'rig-round01.json').read_text());asset={'collection':coll,'root':root,'armature':arm}
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for dev in prefs.devices:dev.use=dev.type=='METAL'
rows=[]
for c,d,i in [('work','S',5),('hold','E',5),('idle','W',0),('load','N',11)]:
 native.apply_clip(asset,rig,c,i+1,d,sc);dest=D/(c+'-'+d+'-'+str(i)+'.png');sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True);rows.append({'clip':c,'direction':d,'index':i,'path':str(dest.relative_to(O)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(C/'reproduction-manifest.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256((P/'round-01.blend').read_bytes()).hexdigest(),'frames':rows},indent=2))
