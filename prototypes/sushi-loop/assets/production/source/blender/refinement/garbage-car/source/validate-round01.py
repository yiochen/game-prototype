"""Read-only native evidence validation; run in Blender with saved round01 project."""
import bpy,json,math,sys,pathlib,hashlib
from mathutils import Matrix,Vector
P=pathlib.Path(__file__).resolve().parent.parent;OUT=P/'candidates/round-01';RES=P/'source/resources';sys.dont_write_bytecode=True;sys.path.insert(0,str(RES));import native_actions as A
B=json.loads((P/'brief.json').read_text());frozen=B['constraints']['measuredNativeContract']['nativeContract'];audit=json.loads((OUT/'native-audit.json').read_text());source=json.loads((RES/'evaluated-native-frames.json').read_text());sourceActions=json.loads((RES/'source-actions.json').read_text());rig=json.loads((OUT/'rig.json').read_text());cam=json.loads((OUT/'camera.json').read_text());mapping=json.loads((OUT/'semantic-mapping.json').read_text());errors=[]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def require(c,msg):
 if not c:errors.append(msg)
def maxerr(a,b):
 if isinstance(a,(list,tuple)):return max((maxerr(x,y) for x,y in zip(a,b)),default=0)
 return abs(a-b)
require(sha(P/'brief.json')=='cbbd830658dfb2f28b3dcd1018c95391eb0e1bb7f29747a49e00a074fdc32dd8','frozen brief changed')
for path,key in [(RES/'original-library.blend','projectSHA256'),(P/'../../backups/b1765262bfa897ad-sushi-loop-world-library.blend','backupSHA256')]:require(sha(path)==B['source'][key],'source bytes changed: '+str(path))
require(sha(P/'inputs/target.png')==B['target']['sha256'],'target bytes changed');require(sha(P/'inputs/original.png')==B['target']['references'][0]['sha256'],'original bytes changed')
# Exact action curves; expected source record was independently measured from the frozen b176 library.
curveErrors=[]
for src in sourceActions:
 target=src['owner'];action=bpy.data.actions.get(target['action']);require(action is not None,'missing action '+target['action'])
 if action is None:continue
 actual={(fc.data_path,fc.array_index):fc for fc in A._fcurves(action)}
 require(len(actual)==len(src['curves']),'curve count '+action.name)
 for curve in src['curves']:
  fc=actual.get((curve['path'],curve['arrayIndex']));require(fc is not None,'missing curve '+action.name)
  if fc is None:continue
  keys=list(fc.keyframe_points);require(len(keys)==len(curve['keys']),'key count '+action.name)
  for k,s in zip(keys,curve['keys']):curveErrors.append(max(abs(k.co.x-s['frame']),abs(k.co.y-s['value'])));require(k.interpolation==s['interpolation'],'interpolation changed')
require(max(curveErrors,default=0)<=1e-5,'native key copy drift')
# Evaluated transforms preserve all distinct source role trajectories at every actual direction/phase.
sources={(f['clip'],f['direction'],f['runtimeIndex']):f for f in source['frames']};transformErrors=[];frameSource=[]
for f in audit['frames']:
 s=sources[(f['clip'],f['direction'],f['index'])];objects={o['name']:o for o in s['geometry']['objects']};e=0
 for name,actual in f['carriers'].items():
  expected=objects[name]
  for prop in ['location','rotationEuler','scale']:e=max(e,maxerr(actual[prop],expected[prop]))
 transformErrors.append(e);require(e<=1e-5,'evaluated trajectory drift '+str((f['clip'],f['direction'],f['index'])))
 frameSource.append({'clip':f['clip'],'direction':f['direction'],'index':f['index'],'sourceBounds':s['geometry']['bounds'],'candidateBounds':f['geometry']['bounds'],'sourceCarrierMaxError':e})
require(len(audit['frames'])==100,'100 native frames required')
# Full envelope is checked in source orientation. Orthogonal root rotations never change registered scale.
idle_env=[[-1.51,-1,-.015],[1.5,1,1.32]];trans_source=frozen['animation']['clearance']['transientSourceSBoundsAllPhases'];trans_env=[[v-.02 for v in trans_source[0]],[v+.02 for v in trans_source[1]]]
phaseBounds=[]
def canon_bounds(f):
 lo,hi=f['geometry']['bounds'];rot=f['rootRotationZ'];c,s=math.cos(-rot),math.sin(-rot);ps=[(c*x-s*y,s*x+c*y,z) for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])];return [[min(p[i] for p in ps) for i in range(3)],[max(p[i] for p in ps) for i in range(3)]]
for f in audit['frames']+audit['inbetweens']:
 bd=canon_bounds(f);env=trans_env if f['clip']=='clearance' else idle_env;extra=max([env[0][i]-bd[0][i] for i in range(3)]+[bd[1][i]-env[1][i] for i in range(3)]+[0]);require(extra<=2e-6,'envelope '+str((f['clip'],f['direction'],f.get('index',f.get('frame'))))+': '+str(extra));phaseBounds.append({'clip':f['clip'],'direction':f['direction'],'phase':f.get('index',f.get('frame')),'sourceOrientationBounds':bd,'allowedEnvelope':env,'excess':extra})
# Four wheel supports from actual remodeled tire surfaces, not six declared occupied cells.
sidle=next(f for f in audit['frames'] if f['clip']=='idle' and f['direction']=='S');supports=[]
for x in (-.94,.94):
 for y in (-.75,.75):
  name=f'garbage-car__native__rounded_tire_{x}_{y}';o=next(o for o in sidle['geometry']['objects'] if o['name']==name);lo,hi=o['bounds'];center=[(lo[i]+hi[i])/2 for i in range(3)];drift=math.hypot(center[0]-x,center[1]-y);require(drift<=.05,'wheel support XY drift');require(abs(lo[2])<=.015,'wheel contact Z');supports.append({'wheel':name,'bounds':o['bounds'],'center':center,'expectedXY':[x,y],'xyDrift':drift,'minZ':lo[2]})
closure=[]
for f in audit['closure']:
 first=next(q for q in audit['frames'] if q['clip']=='highlighted' and q['direction']==f['direction'] and q['index']==0);err=max(maxerr(f['carriers'][n][p],first['carriers'][n][p]) for n in f['carriers'] for p in ('location','rotationEuler','scale'));ge=maxerr(f['geometry']['bounds'],first['geometry']['bounds']);require(err<=1e-8 and ge<=1e-7,'key13 closure');closure.append({'direction':f['direction'],'nativeFrame':13,'carrierMaxError':err,'geometryBoundsMaxError':ge,'image':f['path'],'firstImage':first['path']})
# Preserve source-root/facing/camera; camera record is actual renderer data.
c0=frozen['capture']['camera'];camerr=max(maxerr(cam['camera']['worldMatrix'],c0['worldMatrix']),maxerr(cam['camera']['projectionMatrix'],c0['projectionMatrix']),maxerr(cam['camera']['pixelAspect'],c0['pixelAspect']));require(camerr<=1e-6,'camera changed');require(maxerr(cam['calibration']['root'],[576,1088])<=.05,'registered root projection');require(maxerr(cam['calibration']['unitX'],[256,0])<=.05,'cell X pitch');require(maxerr(cam['calibration']['unitDepth'],[0,256])<=.05,'cell depth pitch');require(maxerr(cam['calibration']['unitHeight'],[0,-179.2])<=.05,'height pitch')
for f in audit['frames']:
 expected={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[f['direction']];require(abs(f['rootRotationZ']-expected)<=1e-6,'facing changed');require(maxerr([f['rootMatrix'][i][3] for i in range(3)],[0,0,0])<=1e-6,'root moved')
# Opaque materials; native visible final fragments; no alpha/shader motion/cards/resources.
require(all(m['alpha']==1 for m in audit['materials']),'nonopaque material');externalImages=[im for im in audit['resources']['images'] if im.get('filepath')];require(not audit['resources']['libraries'] and not externalImages,'unclosed external dependency')
for f in audit['frames']:
 if f['clip']=='clearance' and f['index']==11:require(all(maxerr(s['scale'],[.1,.1,.1])<=1e-6 for s in f['carriers'].values()),'terminal shrink scale')
sourceFloor=json.loads((RES/'context/excluded-floor-sha256.json').read_text());worktree=P.parents[5];floorIntegrity=[]
for p,h in sourceFloor.items():
 actual=sha(worktree/p);require(actual==h,'excluded floor changed '+p);floorIntegrity.append({'path':p,'sha256':actual,'unchanged':actual==h})
# Actual saved project mesh/mapping closure, material and animation mechanisms.
meshes=[o for o in bpy.data.objects if o.type=='MESH'];require(len(meshes)==len(mapping['renderableToCarrier']),'native mesh count mapping closure')
mechanism={'carriers':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None} for o in bpy.data.objects if o.name in mapping['carriers']], 'meshes':[{'name':o.name,'parent':o.parent.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'materialSlots':[m.name for m in o.data.materials],'modifiers':[m.type for m in o.modifiers]} for o in meshes], 'noAlphaAnimation':all(not m.node_tree.animation_data for m in bpy.data.materials if m.use_nodes),'noImageTextures':all(n.type!='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes),'noConstraints':not any(o.constraints for o in bpy.data.objects),'sourceActions':len(sourceActions),'actualMatchingActions':len([a for a in bpy.data.actions if a.name.startswith('S33_NATIVE__garbage-car__')])}
require(mechanism['noAlphaAnimation'] and mechanism['noImageTextures'],'shader/image substitute')
mechanism['materials']=[{'name':m.name,'principled':{k:list(v.default_value) if hasattr(v.default_value,'__len__') else v.default_value for k,v in m.node_tree.nodes.get('Principled BSDF').inputs.items() if k in ('Base Color','Metallic','Roughness','Alpha','Specular IOR Level','Coat Weight','Coat Roughness')}} for m in bpy.data.materials if m.use_nodes and m.users>0]
mechanism['lights']=[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'shadow':o.data.use_shadow,'worldMatrix':[list(r) for r in o.matrix_world]} for o in bpy.context.scene.objects if o.type=='LIGHT']
mechanism['render']={'engine':bpy.context.scene.render.engine,'cyclesSamples':bpy.context.scene.cycles.samples,'denoising':bpy.context.scene.cycles.use_denoising,'frame':[bpy.context.scene.render.resolution_x,bpy.context.scene.render.resolution_y],'pixelAspect':[bpy.context.scene.render.pixel_aspect_x,bpy.context.scene.render.pixel_aspect_y],'transparent':bpy.context.scene.render.film_transparent,'viewTransform':bpy.context.scene.view_settings.view_transform,'exposure':bpy.context.scene.view_settings.exposure,'gamma':bpy.context.scene.view_settings.gamma}
result={'schemaVersion':1,'asset':'garbage-car','status':'technical-checks-pass' if not errors else 'technical-checks-fail','errors':errors,'lighting':'One fixed asset-local horizontally symmetric overhead plus four identical cardinal area fills and uniform world. No ground mesh or cast ground shadow. Native repeated context explicitly uses translated receiver-linked copies; see native-context-lighting-audit.json.','nativeValidation':'candidates/round-01/native-audit.json','renders':[{'clip':f['clip'],'direction':f['direction'],'index':f['index'],'rootRotationZ':f['rootRotationZ'],'rootMatrix':f['rootMatrix'],'path':f['path']} for f in audit['frames']],'briefSHA256':sha(P/'brief.json'),'projectSHA256':sha(P/'source/round-01.blend'),'nativeActionKeyMaxError':max(curveErrors,default=0),'evaluatedSourceCarrierMaxError':max(transformErrors,default=0),'cameraMaxError':camerr,'supports':supports,'loopClosure':closure,'frameSourceComparison':frameSource,'phaseEnvelopeChecks':phaseBounds,'mechanism':mechanism,'floorIntegrity':floorIntegrity,'approval':'No visual approval issued by editor. Independent judge required.'}
(OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'errors':errors,'keyError':result['nativeActionKeyMaxError'],'carrierError':result['evaluatedSourceCarrierMaxError'],'cameraError':camerr},indent=2))
if errors:raise RuntimeError('Native validation failed')
