"""Complete all-frame food transform proof, including viewport-culled idle/work planes.
No project is saved and no render visibility/controller is changed. Existing PNG bytes stay exact.
"""
import bpy,sys,json,math,shutil
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from food_common_round02 import *
for runtime in [False,True]:
 c=config(runtime);rec=json.loads((P/('runtime-recipe-round02.json' if runtime else 'recipe-round02.json')).read_text());out=(P/c['candidateFolder']).resolve();reference={}
 for mode,project in [('canonical-v2',c['canonicalBaseline']),('candidate',c['candidate'])]:
  bpy.ops.wm.open_mainfile(filepath=str(P/project));sc,coll,root,arm,rig,asset,plane=setup(c);rr=np.array(ray(sc));result=[]
  for clip in rig['clips']:
   for d in ['N','E','S','W']:
    for i in range(12):
     native.apply_clip(asset,rig,clip,i+1,d,sc);flags={'hideRender':plane.hide_render,'hideViewport':plane.hide_viewport,'hideGet':plane.hide_get()};q=evaluated_food_transform(sc,plane);parent=np.array(plane.parent.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation)
     restored=flags=={'hideRender':plane.hide_render,'hideViewport':plane.hide_viewport,'hideGet':plane.hide_get()};assert restored
     if mode=='canonical-v2':reference[(clip,d,i)]={'quad':q,'parent':parent,'flags':flags};continue
     old=reference[(clip,d,i)];f=math.cos(root.rotation_euler.z);expected=rec['measuredD0World']-(rec['measuredD0World']-c['dMinWorld'])*max(0,-f)**2;bias=q['bottomWorld']-parent;actual=float(bias@rr);delta=q['world']-old['quad']['world'];signed=delta@rr;perp=float(np.linalg.norm(delta-signed[:,None]*rr,axis=1).max());oldbias=old['quad']['bottomWorld']-old['parent'];oldperp=float(np.linalg.norm(oldbias-(oldbias@rr)*rr));quaderr=float(np.abs(q['projected']-old['quad']['projected']).max());bottomerr=float(np.abs(q['bottomPixel']-old['quad']['bottomPixel']).max())
     result.append({'clip':clip,'direction':d,'index':i,'nativeVisibility':flags,'originalVisibilityEqual':flags==old['flags'],'viewportOnlyEvaluationNeeded':q['viewportEvaluationForced'],'visibilityRestoredBeforeRendering':restored,'quadNativePxError':quaderr,'bottomNativePxError':bottomerr,'perpendicularWorld':perp,'oldSourceOffRayResidualWorld':oldperp,'expectedDepthWorld':expected,'actualDepthWorld':actual,'depthLawErrorWorld':abs(actual-expected),'frontSideDepthDeltaWorld':abs(actual-float(oldbias@rr)) if d!='N' else 0,'quadWorld':q['world'].tolist(),'quadNativePixels':q['projected'].tolist(),'bottomWorld':q['bottomWorld'].tolist(),'bottomNativePixel':q['bottomPixel'].tolist(),'baselineBottomNativePixel':old['quad']['bottomPixel'].tolist(),'worldDisplacement':(q['bottomWorld']-old['quad']['bottomWorld']).tolist(),'signedDepthDeltaWorld':float(signed.mean()),'parentTrajectoryDeltaWorld':float(np.abs(parent-old['parent']).max())})
  if mode=='candidate':
   fields={'quadNativePx':'quadNativePxError','bottomNativePx':'bottomNativePxError','perpendicularWorld':'perpendicularWorld','analyticDepthWorld':'depthLawErrorWorld','frontSideDepthDeltaWorld':'frontSideDepthDeltaWorld','oldShippingOffRayWorld':'oldSourceOffRayResidualWorld'};maximum={k:max(r[v] for r in result) for k,v in fields.items()};ok=maximum['quadNativePx']<=.001 and maximum['bottomNativePx']<=.001 and maximum['perpendicularWorld']<1e-6 and maximum['analyticDepthWorld']<1e-6 and all(r['originalVisibilityEqual'] and r['visibilityRestoredBeforeRendering'] and r['parentTrajectoryDeltaWorld']==0 for r in result)
   audit={'ok':ok,'candidateSHA256':sha(P/c['candidate']),'canonicalV2BaselineSHA256':sha(P/c['canonicalBaseline']),'method':'Actual native food transforms evaluated after temporary viewport-only unhide for culled food planes; hide_render is never changed. Native visibility restored immediately; no source save, controller/geometry change or re-render. Initial unforced hidden matrix observations are preserved separately.','hiddenEvaluationFrames':sum(r['viewportOnlyEvaluationNeeded'] for r in result),'maximum':maximum,'frames':result};write(out/'all-frame-food-transform-validation.json',audit)
   # Preserve the initial diagnostic observations, then correct only their food-transform fields.
   valpath=out/'validation.json';rowsfile=out/'native-frames.json'
   for p in [valpath,rowsfile]:
    backup=p.with_name(p.stem+'-initial-culled-observations.json')
    if not backup.exists():shutil.copyfile(p,backup)
   val=json.loads(valpath.read_text());rows=json.loads(rowsfile.read_text());rrr={(r['clip'],r['direction'],r['index']):r for r in result}
   for r in rows:
    n=rrr[(r['clip'],r['direction'],r['index'])];r['food'].update({'canonicalQuadMaxErrorNativePx':n['quadNativePxError'],'canonicalBottomMaxErrorNativePx':n['bottomNativePxError'],'maxPerpendicularResidualWorld':n['perpendicularWorld'],'biasLawErrorWorld':n['depthLawErrorWorld'],'actualBiasWorld':n['actualDepthWorld'],'oldSourceOffRayResidualWorld':n['oldSourceOffRayResidualWorld'],'quadWorld':n['quadWorld'],'quadNativePixels':n['quadNativePixels'],'bottomWorld':n['bottomWorld'],'bottomNativePixel':n['bottomNativePixel'],'baselineBottomNativePixel':n['baselineBottomNativePixel'],'worldDisplacement':n['worldDisplacement'],'signedDepthDeltaWorld':n['signedDepthDeltaWorld'],'viewportOnlyDiagnosticEvaluation':n['viewportOnlyEvaluationNeeded']})
   val['maximum'].update(maximum);val['initialDiagnosticIssue']='Viewport-culled idle/work food objects can return stale identity matrices. Original observations are retained in *-initial-culled-observations.json; only derived food-transform evidence is corrected, with source/render/controller bytes unchanged.';val['foodTransformAudit']='all-frame-food-transform-validation.json';val['failures']=[f for f in val['failures'] if any(f['values'][j] for j in range(5)) or f['values'][5]>.001 or f['values'][6]>.001 or f['values'][7]>1e-6 or not f['visibilityEqual']];val['ok']=val['allNonFoodStaticSemanticsEqual'] and not val['failures'] and ok and json.loads((out/'continuous-law-validation.json').read_text())['ok'];write(rowsfile,rows);write(valpath,val);print('CORRECTED',c['variant'],val['ok'],maximum,flush=True)
