"""Fresh unchanged shipping source replay to NEW evidence outputs. --all replays192.
Never edits or saves source; never overwrites any prior sealed captures.
"""
import bpy,json,sys,hashlib
from pathlib import Path
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-04';sys.path.insert(0,str(P));import native_actions_round03 as native
assert hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()=='0bb3a656a5194329292663166623edc7fbc823d4d5b85ebffcbb0d094fc31dce'
sc=bpy.data.scenes['Lena warm soft round02'];bpy.context.window.scene=sc;asset={'collection':bpy.data.collections['S33_CHARACTER_chef_lena.002'],'root':bpy.data.objects['chef_lena__ground_root.002'],'armature':bpy.data.objects['chef_lena__armature.002']};rig=json.loads((P/'rig-round03.json').read_text());prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
keys=[(c,d,i) for c in ['idle','work','hold','load'] for d in ['N','E','S','W'] for i in range(12)] if '--all' in sys.argv else [('idle','S',0),('work','E',5),('hold','S',0),('hold','E',4),('hold','W',5),('load','N',11)];rows=[]
for c,d,i in keys:
 native.apply_clip(asset,rig,c,i+1,d,sc);p=C/'replay'/(c+'-'+d)/f'{i:03d}.png';p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),'Reproduce into a fresh output copy; never overwrite existing evidence';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);rows.append({'clip':c,'direction':d,'index':i,'path':str(p.relative_to(O)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reference':f'candidates/round-03/frames/{c}-{d}/{i:03d}.png'})
(C/'replay-manifest.json').write_text(json.dumps({'source':'source/round-03.blend','sourceSHA256':hashlib.sha256((P/'round-03.blend').read_bytes()).hexdigest(),'sourceSaved':False,'script':'source/replay_shipping_round04.py','rows':rows},indent=2))
