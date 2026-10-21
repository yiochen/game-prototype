import bpy,json,sys,hashlib
from pathlib import Path
P=Path(__file__).parent;BASE=P.parent;OUT=BASE/'candidates/round-02';sys.path.insert(0,str(P));import native_actions_round02 as native
sc=bpy.data.scenes['Lena warm soft round02'];bpy.context.window.scene=sc;coll=bpy.data.collections['S33_CHARACTER_chef_lena.002'];root=bpy.data.objects['chef_lena__ground_root.002'];arm=bpy.data.objects['chef_lena__armature.002'];rig=json.loads((P/'rig-round02.json').read_text());asset={'collection':coll,'root':root,'armature':arm}
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
rows=[];folder=OUT/'reproduction';folder.mkdir(exist_ok=True)
for clip,direction,index in [('idle','S',0),('work','E',5),('hold','W',5),('load','N',11)]:
 native.apply_clip(asset,rig,clip,index+1,direction,sc);p=folder/(clip+'-'+direction+'-'+str(index)+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);rows.append({'clip':clip,'direction':direction,'index':index,'path':str(p.relative_to(BASE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reference':'candidates/round-02/frames/'+clip+'-'+direction+'/'+f'{index:03d}.png'})
(OUT/'reproduction-manifest.json').write_text(json.dumps({'source':str(P/'round-02.blend'),'sourceSHA256':hashlib.sha256((P/'round-02.blend').read_bytes()).hexdigest(),'operation':'Fresh reopening ordinary final .blend and exact native renders, no art changes','frames':rows},indent=2))
