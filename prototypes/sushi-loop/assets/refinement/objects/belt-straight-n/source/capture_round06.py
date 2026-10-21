import bpy,math,json,pathlib,hashlib,time,shutil
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parents[1];OUT=P/'candidates/round-06';OUT.mkdir(parents=True,exist_ok=True);(OUT/'frames').mkdir(exist_ok=True);(OUT/'native-runs').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-05.blend'));s=bpy.context.scene;s.render.dither_intensity=0;s.cycles.samples=1;s.cycles.sampling_pattern='TABULATED_SOBOL';s.cycles.scrambling_distance=0;s.cycles.pixel_filter_type='BOX';s.cycles.filter_width=1;s.cycles.use_denoising=False
c=bpy.data.collections['S33_FB_belt-straight-n.001'];root=next(o for o in c.objects if '__root.' in o.name);orient=next(o for o in c.objects if '__orientation.' in o.name);deck=next(o for o in c.objects if 'connected_straight_deck' in o.name);phase=deck.data.materials[0].node_tree.nodes['Value'];root.rotation_euler.z=math.pi;s.frame_set(1);bpy.context.view_layer.update()
project=P/'source/round-06.blend';bpy.ops.wm.save_as_mainfile(filepath=str(project))
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
recipe=json.load(open(P/'source/round-05-recipe.json'));recipe.update(round=6,project=str(project),projectSHA256=sha(project));recipe['render']['ditherIntensity']=0;recipe['render']['device']=s.cycles.device;(P/'source/round-06-recipe.json').write_text(json.dumps(recipe,indent=2))
rotations={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def calibration():
 vals={}
 for k,pt in {'root':(0,0,0),'unitX':(1,0,0),'unitDepth':(0,-1,0),'unitHeight':(0,0,1)}.items():
  v=world_to_camera_view(s,s.camera,Vector(pt));vals[k]=[v.x*s.render.resolution_x,(1-v.y)*s.render.resolution_y]
 r=vals['root'];return {'root':r,**{k:[v[0]-r[0],v[1]-r[1]] for k,v in vals.items() if k!='root'}}
def cameraRecord():return {'worldMatrix':[list(r) for r in s.camera.matrix_world],'projectionMatrix':[list(r) for r in s.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)],'orthoScale':s.camera.data.ortho_scale,'shift':[s.camera.data.shift_x,s.camera.data.shift_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'frame':[s.render.resolution_x,s.render.resolution_y],'calibration':calibration()}
def meshstats():
 dep=bpy.context.evaluated_depsgraph_get();rows=[]
 for o in c.objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(dep);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices]
  rows.append({'name':o.name,'vertices':len(vs),'polygons':len(me.polygons),'bounds':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]],'matrixWorld':[list(r) for r in o.matrix_world],'materials':[m.name for m in o.data.materials],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]});ev.to_mesh_clear()
 return rows
root.rotation_euler.z=0;s.frame_set(1);bpy.context.view_layer.update();baseline=meshstats();bounds=[[min(o['bounds'][0][i] for o in baseline) for i in range(3)],[max(o['bounds'][1][i] for o in baseline) for i in range(3)]]
profiles=[];dep=bpy.context.evaluated_depsgraph_get()
for o in c.objects:
 if 'stationary_rail' not in o.name and o!=deck:continue
 ev=o.evaluated_get(dep);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];pr={'name':o.name,'ends':{}}
 for sign in [-1,1]:pr['ends'][str(sign*.5)]=[list(v) for v in vs if abs(v.y-sign*.5)<1e-6]
 profiles.append(pr);ev.to_mesh_clear()
# Original action survives on the original deck material owner.
act=deck.data.materials[0].node_tree.animation_data.action
curves=[]
for layer in act.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for f in bag.fcurves:curves.append({'dataPath':f.data_path,'arrayIndex':f.array_index,'keys':[{'frame':float(k.co.x),'value':float(k.co.y),'interpolation':k.interpolation} for k in f.keyframe_points]})
validation={'schemaVersion':1,'asset':'belt-straight-n','project':str(project),'projectSHA256':sha(project),'blenderVersion':bpy.app.version_string,'sourceProjectSHA256':json.load(open(P/'brief.json'))['source']['projectSHA256'],'sourceInspection':'source/source-inspection.json','camera':cameraRecord(),'publisherRootRotationsDegrees':{k:v*180/math.pi for k,v in rotations.items()},'authoredChildOrientationRadians':float(orient.rotation_euler.z),'geometry':{'collection':c.name,'baselinePublisherS':baseline,'bounds':bounds,'exactOpenProfiles':profiles,'deckSocket':[0,0,.64],'deckClearance':{'deckTopZ':.64,'railInnerX':[-.35,.35],'nonRailMaximumZ':max(o['bounds'][1][2] for o in baseline if 'stationary_rail' not in o['name'] and 'connected_straight_deck' not in o['name']),'groundContactZ':bounds[0][2]},'railCutFaces':'Open longitudinal side strips retain exact rectangular boundary cross-sections. No decorative cap, overhang or end-profile rounding.','frameGeometryStatic':True},'motion':{'clip':'running','fps':12,'uniqueFrames':24,'closureFrame':25,'phaseFunction':'-7*i/24','periodsPerCell':7,'originalUV':[list(x.uv) for x in deck.data.uv_layers.active.data],'materialOwner':deck.data.materials[0].name,'phaseNode':phase.name,'nativeAction':act.name,'curves':curves,'geometryOwnerCount':len(baseline)},'render':{'engine':s.render.engine,'device':s.cycles.device,'devices':[{'name':d.name,'type':d.type,'use':d.use} for d in bpy.context.preferences.addons['cycles'].preferences.devices],'samples':s.cycles.samples,'samplingPattern':s.cycles.sampling_pattern,'scramblingDistance':s.cycles.scrambling_distance,'filter':s.cycles.pixel_filter_type,'filterWidth':s.cycles.filter_width,'ditherIntensity':s.render.dither_intensity,'denoising':s.cycles.use_denoising,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'alphaMethod':'Native opaque surface coverage from deterministic common single sample; no raster correction. Source-scale2 binary coverage is downsampled only in review previews.','cameraSurfaceMethod':'Native procedural camera-ray radiance, BSDF retained for noncamera transport. No view-specific materials, recoloring or fitting.'},'dependencyClosure':{'libraries':[{'name':x.name,'filepath':x.filepath} for x in bpy.data.libraries],'images':[{'name':x.name,'source':x.source,'filepath':x.filepath,'packed':bool(x.packed_file)} for x in bpy.data.images],'externalResources':[],'sceneObjects':[o.name for o in s.objects]},'frames':[],'nativeRuns':[]}
raw=[]
for d,rot in rotations.items():
 root.rotation_euler.z=rot
 for i in range(25):
  s.frame_set(i+1);bpy.context.view_layer.update();actual=float(phase.outputs[0].default_value);assert abs(actual+7*i/24)<1e-5,(d,i,actual)
  path=OUT/'frames'/('running-%s-%02d.png'%(d,i));s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  r={'clip':'running','direction':d,'index':i,'blenderFrame':i+1,'path':str(path),'rootRotationZ':float(root.rotation_euler.z),'rootRotationDegrees':float(root.rotation_euler.z*180/math.pi),'rootMatrix':[list(r) for r in root.matrix_world],'authoredChildRotationZ':float(orient.rotation_euler.z),'phase':actual,'sha256':sha(path),'geometryBounds':meshstats() if i in [0,24] else None};validation['frames'].append(r)
  if i<24:raw.append({'clip':'running','direction':d,'index':i,'path':str(path)})
  print('CAPTURE_SINGLE',d,i,actual,flush=True)
 (OUT/('hero-'+d+'.png')).write_bytes((OUT/'frames'/('running-%s-00.png'%d)).read_bytes())
(OUT/'raw-frame-records.json').write_text(json.dumps(raw,indent=2));(OUT/'validation.json').write_text(json.dumps(validation,indent=2))
# Native3 modules share the actual same material/action and exact1-cell physical spacing. Expand canvas mathematically; preserve all pixel/world calibration.
original=list(c.objects);clones=[]
for i in [-1,1]:
 mapping={}
 for o in original:q=o.copy();c.objects.link(q);mapping[o]=q
 for o,q in mapping.items():q.parent=mapping.get(o.parent,o.parent)
 clones.append((i,mapping[root]))
s.render.resolution_x=896;s.render.resolution_y=1216;s.camera.data.ortho_scale*=1216/704;s.camera.data.shift_y*=704/1216
validation['nativeRunCamera']=cameraRecord();validation['nativeAssemblyContract']={'frame':[896,1216],'root':[448,752],'singleFrame':[384,704],'singleRoot':[192,496],'cellPitchPixels':256,'moduleRootOffsets':{'N':[[0,-1,0],[0,0,0],[0,1,0]],'S':[[0,-1,0],[0,0,0],[0,1,0]],'E':[[-1,0,0],[0,0,0],[1,0,0]],'W':[[-1,0,0],[0,0,0],[1,0,0]]},'independentPixelOffsets':{'N':[[256,0],[256,256],[256,512]],'S':[[256,0],[256,256],[256,512]],'E':[[0,256],[256,256],[512,256]],'W':[[0,256],[256,256],[512,256]]},'compositingOrder':'Unmodified RGBA source frames, alpha_composite in listed order: back-to-front screenY; equal-depth horizontal tiles left-to-right.'}
for d,rot in rotations.items():
 root.rotation_euler.z=rot
 for j,q in clones:q.rotation_euler.z=rot;q.location=(0,j,0) if d in ['N','S'] else (j,0,0)
 for i in range(25):
  s.frame_set(i+1);bpy.context.view_layer.update();path=OUT/'native-runs'/('native-%s-%02d.png'%(d,i));s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  validation['nativeRuns'].append({'direction':d,'index':i,'path':str(path),'phase':float(phase.outputs[0].default_value),'rootRotationZ':float(root.rotation_euler.z),'moduleRootMatrices':[[list(row) for row in q.matrix_world] for q in [root]+[x[1] for x in clones]],'sha256':sha(path)});print('CAPTURE_NATIVE3',d,i,flush=True)
 (OUT/'validation.json').write_text(json.dumps(validation,indent=2))
# Native record exports use the actual restored camera/capture scale; retain original source record separately.
cam=json.load(open(P/'inputs/source-camera.json'));cam['captureScale']=2;cam['calibration']={'root':[192.,496.00003],'unitX':[256.,0.],'unitDepth':[0.,255.99997],'unitHeight':[0.,-179.20007]};cam['artStyle']={'revision':'warm-soft-native-toon-round06','lighting':'Uniform world + centered85W overhead + four equal30W fills; native camera-ray materials provide symmetric soft stylized radiance','denoising':False,'samples':1,'samplingPattern':'TABULATED_SOBOL','scramblingDistance':0,'pixelFilter':'BOX1','dither':0};(OUT/'camera.json').write_text(json.dumps(cam,indent=2))
asset=json.load(open(P/'inputs/source-assetRecord.json'));asset['scale']=2;asset['artStyle']={'revision':'warm-soft-native-toon-round06','railColorFamily':'coral/salmon','deckColorFamily':'blue-charcoal','supportColorFamily':'honey wood','materialMethod':'Native procedural camera-ray radiance + BSDF transport; no external raster textures'};(OUT/'assetRecord.json').write_text(json.dumps(asset,indent=2))
rig=json.load(open(P/'inputs/source-rig.json'));rig['status']='native-actions-preserved-round06';rig['projectSHA256']=sha(project);rig['actualPhaseCurves']=curves;(OUT/'rig.json').write_text(json.dumps(rig,indent=2))
print('COMPLETE',str(OUT),flush=True)
