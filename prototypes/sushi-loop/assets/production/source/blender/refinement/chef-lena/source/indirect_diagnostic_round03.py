"""Diagnostic-only source replay: hide food or camera-only food transiently.
Never saves or edits either bound .blend. Not a shipping render or placement change.
"""
import bpy,json,sys,hashlib
from pathlib import Path
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-03';out=C/'indirect-diagnostic';out.mkdir(exist_ok=True);sys.path.insert(0,str(P));import native_actions_round03 as native
rig=json.loads((P/'rig-round03.json').read_text());rows=[]
for rd in ['02','03']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'round-{rd}.blend'));sc=bpy.data.scenes['Lena warm soft round02'];bpy.context.window.scene=sc;coll=bpy.data.collections['S33_CHARACTER_chef_lena.002'];root=bpy.data.objects['chef_lena__ground_root.002'];arm=bpy.data.objects['chef_lena__armature.002'];asset={'collection':coll,'root':root,'armature':arm};prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 for direction in ['S','E','W','N']:
  for mode in ['food-hidden','camera-only-food','camera-only-no-denoise']:
   native.apply_clip(asset,rig,'hold',1,direction,sc);plane=bpy.data.objects['chef_lena__ground_root.002__held_dish-salmon__image_plane'];visibility={k:getattr(plane,k) for k in ['hide_render','visible_camera','visible_diffuse','visible_glossy','visible_transmission','visible_volume_scatter','visible_shadow']}
   muted=[];denoise=sc.cycles.use_denoising
   if mode=='food-hidden':
    for f in native._fcurves(plane.animation_data.action):
     if f.data_path=='hide_render':muted.append((f,f.mute));f.mute=True
    plane.hide_render=True
   else:
    for k in ['visible_diffuse','visible_glossy','visible_transmission','visible_volume_scatter','visible_shadow']:setattr(plane,k,False)
   if mode=='camera-only-no-denoise':sc.cycles.use_denoising=False
   sc.render.filepath=str(out/f'round{rd}-hold-{direction}-{mode}.png');bpy.ops.render.render(write_still=True);rows.append({'round':int(rd),'clip':'hold','direction':direction,'index':0,'mode':mode,'path':str(Path(sc.render.filepath).relative_to(O)),'sha256':hashlib.sha256(Path(sc.render.filepath).read_bytes()).hexdigest(),'originalVisibility':visibility})
   for k,v in visibility.items():setattr(plane,k,v)
   for f,m in muted:f.mute=m
   sc.cycles.use_denoising=denoise
(out/'manifest.json').write_text(json.dumps({'policy':'Temporary diagnostic renders only. Bound sources never saved; shipping frames unchanged. Hidden mode isolates identical physical body; camera-only mode suppresses noncamera food rays to separate food-induced indirect light/denoiser changes.','frames':rows},indent=2))
