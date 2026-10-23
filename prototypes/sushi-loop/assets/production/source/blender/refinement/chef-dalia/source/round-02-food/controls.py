"""Same-setting source/canonical food-on/off/repeat diagnostic renders. Never save native sources."""
import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));sys.dont_write_bytecode=True
from common import *
poses=[('hold','S',0),('hold','E',0),('hold','N',0),('hold','W',0),('load','S',5),('work','S',5)];rows=[]
for kind,source in [('source',P/'dependencies/approved-body.blend'),('candidate',BASE/'source/round-02.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;record,root,col,arm,foodroot,plane=context();before=baseline()
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 assert sc.cycles.device=='GPU'
 for clip,direction,index in poses:
  for mode in ['food-on-a','food-off']+(['food-on-b'] if (clip,direction,index)==('hold','S',0) else []):
   ph=phase(clip,direction,index);authored=plane.hide_render;visibilityCurves=[]
   if mode=='food-off':
    action=plane.animation_data.action if plane.animation_data else None
    if action:
     for fc in na._fcurves(action):
      if fc.data_path=='hide_render':visibilityCurves.append((fc,fc.mute));fc.mute=True
    plane.hide_render=True;plane.update_tag(refresh={'OBJECT','DATA','TIME'});bpy.context.view_layer.update()
   preRenderVisibility={'hideRender':plane.hide_render,'mutedVisibilityCurves':len(visibilityCurves),'allDiagnosticCurvesMuted':all(fc.mute for fc,mute in visibilityCurves)}
   path=OUT/'controls'/kind/f'{clip}-{direction}-{index:03d}-{mode}.png';path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   rows.append({'kind':kind,'sourceSHA256':sha(source),'clip':clip,'direction':direction,'index':index,'mode':mode,'path':str(path.relative_to(BASE)),'sha256':sha(path),'authoredPlaneHideRender':authored,'diagnosticHideRender':plane.hide_render,'preRenderVisibility':preRenderVisibility,'postRenderHideRender':plane.hide_render,'rootRotationDegrees':ph['rootRotationDegrees'],'rootMatrix':ph['rootMatrix'],'semanticSupportNative':ph['semanticSupportNative'],'foodCornersNative':ph['foodCornersNative'],'diagnosticVisibilityEvaluation':ph['diagnosticVisibilityEvaluation'],'cameraMatrix':ph['cameraMatrix'],'samples':sc.cycles.samples,'seed':sc.cycles.seed,'useAnimatedSeed':sc.cycles.use_animated_seed});
   for fc,mute in visibilityCurves:fc.mute=mute
   plane.hide_render=authored;bpy.context.view_layer.update()
   rows[-1]['visibilityRestoredAfterDiagnostic']=plane.hide_render==authored and all(fc.mute==mute for fc,mute in visibilityCurves)
   if mode=='food-off':assert preRenderVisibility['hideRender'] and rows[-1]['postRenderHideRender'] and len(visibilityCurves)>0
  print('CONTROL',kind,clip,direction,index,flush=True)
 record,root,col,arm,foodroot,plane=context();na.apply_clip({'root':root,'collection':col,'armature':arm},record,'idle',1,'S',sc);after=baseline()
 assert all(before[k]==after[k] for k in ['bodyAndKnifeMeshes','actions','materials','boneRestSHA256'])
write(OUT/'controls-record.json',{'status':'Diagnostic source/candidate food radiance and repeat evidence, not replacement runtime frames','records':rows,'sourceRepeatObservationIsNotUniversalNoiseBudget':True,'foodOffPolicy':'Only in-memory image-plane hide_render=True with its authored hide_render fcurve temporarily muted for the labeled food-off diagnostic. Pre/post-render hidden state recorded. Authored visibility and fcurve mute states restored after render, native source never resaved. First incorrect controls retained under attempt-04-animated-visibility-controls.','nativeSourceFilesUnchanged':True})
print('CONTROLS_COMPLETE',len(rows),flush=True)
