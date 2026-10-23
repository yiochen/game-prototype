"""Fresh-reopen compact semantic/numeric parity and native capture for one bundle."""
import bpy,json,math,sys,time,gc
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from food_common_round02 import *
from semantic_food_round02 import *
runtime='--runtime' in sys.argv;c=config(runtime);rec=json.loads((P/('runtime-recipe-round02.json' if runtime else 'recipe-round02.json')).read_text());OUT=(P/c['candidateFolder']).resolve();OUT.mkdir(parents=True,exist_ok=True)
def canonical_quad(sc,plane):
 e=plane.evaluated_get(bpy.context.evaluated_depsgraph_get());w=rec['canonicalLocalWidth'];h=float(np.float32(rec['canonicalLocalHeight']))
 local=[Vector((-w/2,0,0)),Vector((w/2,0,0)),Vector((w/2,h,0)),Vector((-w/2,h,0))];vs=[e.matrix_world@v for v in local];bottom=(vs[0]+vs[1])*.5
 return {'world':np.array(vs,dtype=np.float64),'projected':np.array([px(sc,v) for v in vs]),'bottomWorld':np.array(bottom),'bottomPixel':px(sc,bottom),'visible':not plane.hide_render}
def set_angle(asset,rig,clip,angle,sc):
 native.apply_clip(asset,rig,clip,6,'S',sc);asset['root'].rotation_euler.z=math.radians(angle);asset['root'].update_tag();bpy.context.view_layer.update()
angles=sorted(set([-180,-165,-150,-135,-120,-105,-95,-85,-75,-45,0,45,75,85,95,105,120,135,150,165,180]+[s*(90+d) for s in [-1,1] for d in [-.1,-.02,-.015,-.0146,-.0145,-.014,-.01,-.001,0,.001,.01,.014,.0145,.0146,.015,.02,.1]]))
turn_angles=[-180,-165,-150,-135,-120,-105,-95,-90.1,-90,-89.9,-85,-75,-45,0,45,75,85,89.9,90,90.1,95,105,120,135,150,165,180]
near_values=[-.001,-.0002,-.0001,-.00007,-.00001,0,.00001,.00007,.0001,.0002,.001]
bpy.ops.wm.open_mainfile(filepath=str(P/c['basis']));sc,coll,root,arm,rig,asset,plane=setup(c)
native.apply_clip(asset,rig,next(iter(rig['clips'])),1,'S',sc)
baseline_static=static_scene(sc,coll,plane,rig,native);baseline={};source_intermediate={};rr=np.array(ray(sc),dtype=np.float64)
old_mappings=[{'axis':fc.array_index,'path':fc.data_path,'mapping':fcurve(fc),'expression':fc.driver.expression,'nearZero':[{'input':x,'output':fc.evaluate(x)} for x in near_values]} for fc in plane.animation_data.drivers]
for clip in rig['clips']:
 for direction in ['N','E','S','W']:
  for idx in range(12):
   native.apply_clip(asset,rig,clip,idx+1,direction,sc);gs=frame_geometry(coll,plane);q=canonical_quad(sc,plane);ct=controls(coll,root,arm,plane,gs)
   bias=q['bottomWorld']-ct['parentMatrix'][:3,3];off=float(np.linalg.norm(bias-np.dot(bias,rr)*rr))
   baseline[(clip,direction,idx)]={'geometry':gs,'controls':ct,'quad':q,'oldOffRayWorld':off}
   print('BASELINE',c['variant'],clip,direction,idx,flush=True)
hold='hold-cucumber' if runtime else 'hold'
for a in angles:
 set_angle(asset,rig,hold,a,sc);q=canonical_quad(sc,plane);parent=np.array(plane.parent.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation);bias=q['bottomWorld']-parent
 source_intermediate[a]={'quad':q,'parent':parent,'bias':bias,'oldOffRayWorld':float(np.linalg.norm(bias-np.dot(bias,rr)*rr))}
bpy.ops.wm.open_mainfile(filepath=str(P/c['candidate']));sc,coll,root,arm,rig,asset,plane=setup(c);enable_saved_device(sc)
native.apply_clip(asset,rig,next(iter(rig['clips'])),1,'S',sc)
candidate_static=static_scene(sc,coll,plane,rig,native)
object_parity={n:baseline_static['objects'][n]['semanticSHA256']==candidate_static['objects'].get(n,{}).get('semanticSHA256') for n in baseline_static['objects']}
material_parity={n:v['semanticSHA256']==candidate_static['materials'].get(n,{}).get('semanticSHA256') for n,v in baseline_static['materials'].items()}
static_ok=all(object_parity.values()) and set(baseline_static['objects'])==set(candidate_static['objects']) and all(material_parity.values()) and baseline_static['actions']==candidate_static['actions'] and baseline_static['renderer']['semanticSHA256']==candidate_static['renderer']['semanticSHA256'] and baseline_static['foodShaderSHA256']==candidate_static['foodShaderSHA256']
yaw_old=next(d for d in baseline_static['foodDrivers'] if d['mapping']['path']=='rotation_euler');yaw_new=next(d for d in candidate_static['foodDrivers'] if d['mapping']['path']=='rotation_euler');yaw_same=yaw_old==yaw_new
write(OUT/'static-semantic-parity.json',{'ok':static_ok and yaw_same,'sourceSHA256':sha(P/c['basis']),'candidateSHA256':sha(P/c['candidate']),'objectParity':object_parity,'materialParity':material_parity,'actionParity':baseline_static['actions']==candidate_static['actions'],'rendererParity':baseline_static['renderer']['semanticSHA256']==candidate_static['renderer']['semanticSHA256'],'foodShaderFilteringParity':baseline_static['foodShaderSHA256']==candidate_static['foodShaderSHA256'],'yawDriverAndMappingExactlyPreserved':yaw_same,'source':baseline_static,'candidate':candidate_static})
if not static_ok:print('STATIC MISMATCH',object_parity,material_parity,baseline_static['renderer']['semanticSHA256'],candidate_static['renderer']['semanticSHA256'],flush=True)
rows=[];failures=[];maximum={'position':0.,'vertexNormal':0.,'cornerNormal':0.,'pose':0.,'control':0.,'quadNativePx':0.,'bottomNativePx':0.,'perpendicularWorld':0.,'analyticDepthWorld':0.,'frontSideDepthDeltaWorld':0.,'oldShippingOffRayWorld':0.}
for clip in rig['clips']:
 for direction in ['N','E','S','W']:
  for idx in range(12):
   key=(clip,direction,idx);ref=baseline.pop(key);native.apply_clip(asset,rig,clip,idx+1,direction,sc)
   gs=frame_geometry(coll,plane);mesh_records,(dp,dn,dc)=compact_geometry(gs,ref['geometry']);ct=controls(coll,root,arm,plane,gs);q=quad_state(sc,plane);old=ref['quad'];rr=np.array(ray(sc),dtype=np.float64)
   pose=float(np.max(np.abs(ct['bones']-ref['controls']['bones'])));ctrl=max(float(np.max(np.abs(ct['rootMatrix']-ref['controls']['rootMatrix']))),float(np.max(np.abs(ct['parentMatrix']-ref['controls']['parentMatrix']))),max(float(np.max(np.abs(ct['points'][n]-ref['controls']['points'][n]))) for n in ct['points']),max(float(np.max(np.abs(ct['matrices'][n]-ref['controls']['matrices'][n]))) for n in ct['matrices']))
   delta=q['world']-old['world'];signed=delta@rr;perp=np.linalg.norm(delta-signed[:,None]*rr,axis=1);quad_err=float(np.max(np.abs(q['projected']-old['projected'])));bottom_err=float(np.max(np.abs(q['bottomPixel']-old['bottomPixel'])))
   f=math.cos(root.rotation_euler.z);expected=rec['measuredD0World']-(rec['measuredD0World']-c['dMinWorld'])*max(0,-f)**2;actual=float(np.dot(q['bottomWorld']-ct['parentMatrix'][:3,3],rr));depth_err=abs(actual-expected)
   source_depth=float(np.dot(old['bottomWorld']-ref['controls']['parentMatrix'][:3,3],rr));frontside=abs(actual-source_depth) if direction!='N' else 0
   values=[dp,dn,dc,pose,ctrl,quad_err,bottom_err,float(perp.max()),depth_err,frontside,ref['oldOffRayWorld']]
   for n,v in zip(maximum,values):maximum[n]=max(maximum[n],v)
   if dp or dn or dc or pose or ctrl or quad_err>.001 or bottom_err>.001 or float(perp.max())>1e-6 or depth_err>1e-6 or q['visible']!=old['visible']:failures.append({'clip':clip,'direction':direction,'index':idx,'values':values,'visibilityEqual':q['visible']==old['visible']})
   path=OUT/'frames'/(clip+'-'+direction)/(f'{idx:03d}.png');path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   row={'clip':clip,'direction':direction,'index':idx,'path':path.relative_to(P.parent).as_posix(),'sha256':sha(path),'width':sc.render.resolution_x,'height':sc.render.resolution_y,'nativeCaptureScale':2,'publishedScale':2,'rootRotationRadians':float(root.rotation_euler.z),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':ct['rootMatrix'].tolist(),'rootPixel':px(sc,(0,0,0)).tolist(),'cameraWorldSHA256':packed_hash(np.array(sc.camera.matrix_world)),'meshParity':mesh_records,'maxPositionDeltaWorld':dp,'maxVertexNormalDelta':dn,'maxCornerNormalDelta':dc,'maxPoseMatrixDelta':pose,'maxPhysicalControlDelta':ctrl,'physicalPoints':{n:v.tolist() for n,v in ct['points'].items()},'attachmentMatricesSHA256':{n:packed_hash(v) for n,v in ct['matrices'].items()},'food':{'visible':q['visible'],'canonicalQuadMaxErrorNativePx':quad_err,'canonicalBottomMaxErrorNativePx':bottom_err,'worldDisplacement':(q['bottomWorld']-old['bottomWorld']).tolist(),'signedDepthDeltaWorld':float(signed.mean()),'maxPerpendicularResidualWorld':float(perp.max()),'oldSourceOffRayResidualWorld':ref['oldOffRayWorld'],'semanticForwardDot':f,'expectedBiasWorld':expected,'actualBiasWorld':actual,'biasLawErrorWorld':depth_err,'quadWorld':q['world'].tolist(),'quadNativePixels':q['projected'].tolist(),'bottomWorld':q['bottomWorld'].tolist(),'bottomNativePixel':q['bottomPixel'].tolist(),'baselineBottomNativePixel':old['bottomPixel'].tolist()}}
   rows.append(row);write(OUT/'progress.json',{'complete':len(rows),'total':96 if runtime else 192,'last':[clip,direction,idx]});print('CAPTURE',c['variant'],len(rows),flush=True)
   del gs,ref
gc.collect();write(OUT/'native-frames.json',rows)
intermediate=[];turnframes=[]
for a in angles:
 set_angle(asset,rig,hold,a,sc);q=quad_state(sc,plane);src=source_intermediate[a];parent=np.array(plane.parent.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation);rr=np.array(ray(sc));bias=q['bottomWorld']-parent
 f=math.cos(root.rotation_euler.z);depth=rec['measuredD0World']-(rec['measuredD0World']-c['dMinWorld'])*max(0,-f)**2;actual=float(np.dot(bias,rr));perp=float(np.linalg.norm(bias-actual*rr))
 # Correct analytic v2 ray baseline, separate from the old keyed off-ray mapping.
 analytical_corners=src['quad']['world']-src['bias']+rr*depth
 analytical_projection=np.array([px(sc,p) for p in analytical_corners]);project_err=float(np.max(np.abs(q['projected']-analytical_projection)))
 r={'angleDegrees':a,'measuredRootDegrees':math.degrees(root.rotation_euler.z),'semanticForwardDot':f,'expectedBiasWorld':depth,'actualBiasWorld':actual,'actualMinusAnalyticDepthWorld':actual-depth,'actualPerpendicularResidualWorld':perp,'quadMaxErrorVersusAnalyticNativePx':project_err,'legacySourceOffRayResidualWorld':src['oldOffRayWorld'],'newXYZDriverOutputs':list(plane.evaluated_get(bpy.context.evaluated_depsgraph_get()).location),'bottomWorld':q['bottomWorld'].tolist(),'bottomPixel':q['bottomPixel'].tolist()};intermediate.append(r)
 if a in turn_angles:
  index=turn_angles.index(a);path=OUT/'turn-frames'/f'{index:03d}.png';path.parent.mkdir(exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);turnframes.append({'index':index,'angleDegrees':a,'path':path.relative_to(P.parent).as_posix(),'sha256':sha(path)})
mappings=[{'axis':fc.array_index,'path':fc.data_path,'mapping':fcurve(fc),'expression':fc.driver.expression,'nearZero':[{'input':x,'output':fc.evaluate(x)} for x in near_values]} for fc in plane.animation_data.drivers]
derivatives=[]
lookup={r['angleDegrees']:r for r in intermediate}
for side in [-90,90]:
 for step in [.1,.02,.001]:
  aa=round(side-step,8);bb=round(side+step,8)
  left=next(v for k,v in lookup.items() if abs(k-aa)<1e-7);right=next(v for k,v in lookup.items() if abs(k-bb)<1e-7)
  derivatives.append({'boundaryDegrees':side,'halfStepDegrees':step,'measuredCentralDerivativeWorldPerRadian':(right['actualBiasWorld']-left['actualBiasWorld'])/math.radians(2*step),'analyticCentralDerivativeWorldPerRadian':(right['expectedBiasWorld']-left['expectedBiasWorld'])/math.radians(2*step),'analyticOneSidedLimitBoth':0})
continuity={'ok':max(abs(r['actualMinusAnalyticDepthWorld']) for r in intermediate)<1e-6 and max(r['actualPerpendicularResidualWorld'] for r in intermediate)<1e-6 and max(r['quadMaxErrorVersusAnalyticNativePx'] for r in intermediate)<.001,'law':c['law'],'dMinWorld':c['dMinWorld'],'d0World':rec['measuredD0World'],'semanticForwardSource':'Actual root has no parent, XYZ rotation0/0/yaw and uniform1.25scale; dot(rotated(0,-1,0),camera horizontal(0,-1,0))=cos(rootYaw). No action/head tilt or discrete facing switch.','analyticC1':'For cos(theta)>=0 depth=d0; for cos(theta)<0 depth=d0-A*cos(theta)^2. Depth and first derivative both match at +/-90deg. Only XYZ mappings are exact polynomial0+1*x; original yaw mapping remains.','nativePrecisionToleranceWorld':1e-6,'maxLegacyIntermediateOffRayResidualWorld':max(r['legacySourceOffRayResidualWorld'] for r in intermediate),'maxNewIntermediatePerpendicularResidualWorld':max(r['actualPerpendicularResidualWorld'] for r in intermediate),'maxNewDepthLawErrorWorld':max(abs(r['actualMinusAnalyticDepthWorld']) for r in intermediate),'oldMappings':old_mappings,'newMappings':mappings,'finiteDifferenceDerivatives':derivatives,'samples':intermediate,'turnFrames':sorted(turnframes,key=lambda x:x['index'])}
write(OUT/'continuous-law-validation.json',continuity)
im=image_node(plane).image;image_record={'name':im.name,'size':list(im.size),'packed':bool(im.packed_file),'packedSHA256':sha(P/c['canonical']) if im.packed_file and hashlib.sha256(im.packed_file.data).hexdigest()==sha(P/c['canonical']) else None,'path':im.filepath,'colorspace':im.colorspace_settings.name,'alphaMode':im.alpha_mode,'interpolation':image_node(plane).interpolation,'extension':image_node(plane).extension}
camera={'name':sc.camera.name,'worldMatrix':[list(r) for r in sc.camera.matrix_world],'projectionMatrix':[list(r) for r in sc.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'nativeResolution':[sc.render.resolution_x,sc.render.resolution_y],'nativeCaptureScale':2,'publishedResolution':[384,640],'publishedSourceScale':2,'logicalFrame':[192,320],'logicalRoot':[96,248],'rootNativePixel':px(sc,(0,0,0)).tolist(),'publicationSampling':c['publicationSampling']}
ok=static_ok and yaw_same and not failures and continuity['ok'] and image_record['packedSHA256']==c['canonicalSHA256'] and not bpy.data.libraries
validation={'ok':ok,'asset':'chef-omar','round':'round-02','sourceSHA256':sha(P/c['basis']),'candidateSHA256':sha(P/c['candidate']),'source':c['basis'],'project':c['candidate'],'variant':c['variant'],'nativeFrames':len(rows),'nativeFrameManifest':(OUT/'native-frames.json').relative_to(P.parent).as_posix(),'maximum':maximum,'bodyMeshCount':len(candidate_static['objects']),'allNonFoodStaticSemanticsEqual':static_ok,'yawDriverAndMappingEqual':yaw_same,'staticAudit':(OUT/'static-semantic-parity.json').relative_to(P.parent).as_posix(),'continuousLawAudit':(OUT/'continuous-law-validation.json').relative_to(P.parent).as_posix(),'failures':failures,'nativeFloatPrecisionToleranceWorld':1e-6,'shippingProjectionToleranceNativePx':.001,'camera':camera,'image':image_record,'linkedLibraries':[l.filepath for l in bpy.data.libraries],'notes':['Body position/normal/pose/control maxima are actual numeric source/candidate array comparisons in memory; raw arrays are not serialized.','World food positions change along the approved ray; projected shipping registration is compared to canonical-v2 source mapping.','Intermediate legacy off-ray snapping is quantified separately; candidate follows analytic C1 law, not defective legacy mapping.','Exact saved renderer, camera, lights/materials are checked semantically. RGB differences from food-dependent transport/denoising are assessed separately.']}
write(OUT/'validation.json',validation);print('DONE',c['variant'],json.dumps({'ok':ok,'maxima':maximum,'continuity':continuity['ok']}),flush=True)
