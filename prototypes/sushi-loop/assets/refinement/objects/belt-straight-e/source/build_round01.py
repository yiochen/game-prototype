import bpy,math,json,pathlib,hashlib,copy
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parents[1];OUT=P/'candidates/round-01';(OUT/'frames').mkdir(parents=True,exist_ok=True);(OUT/'native-runs').mkdir(exist_ok=True)
H=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
f=json.loads((P/'inputs/family-settings.json').read_text());assert H(P/'inputs/family-settings.json')=='599d7a731dcf8f22305f3d7b8a67a1fa45743535ed34937620dd9a834377ba15'
source=pathlib.Path(f['sourceOfTruth']['path']);assert H(source)==f['sourceOfTruth']['sha256'];assert H(f['project']['path'])==f['project']['sha256']
# Load the exact approved native family configuration, then import the actual E source collection.
bpy.ops.wm.open_mainfile(filepath=f['project']['path']);s=bpy.context.scene
nc=bpy.data.collections[f['project']['collection']];nobjs=list(nc.objects);nroot=next(o for o in nobjs if '__root.' in o.name);norient=next(o for o in nobjs if '__orientation.' in o.name);ndeck=next(o for o in nobjs if 'connected_straight_deck' in o.name)
with bpy.data.libraries.load(str(source),link=False) as (available,loaded):loaded.collections=['S33_FB_belt-straight-e.001']
c=loaded.collections[0];s.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
for o in c.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False);o.update_tag()
root=next(o for o in c.objects if '__root.' in o.name);orient=next(o for o in c.objects if '__orientation.' in o.name);deck=next(o for o in c.objects if 'connected_straight_deck' in o.name)
s.frame_set(1);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
assert abs(orient.rotation_euler.z-math.pi/2)<1e-6
originalEAction=deck.data.materials[0].node_tree.animation_data.action
originalUV=[list(x.uv) for x in deck.data.uv_layers.active.data]
# Preserve E's real deck mesh/UV/action. Copy exact approved family shader graph, retaining E action owner semantics.
m=ndeck.data.materials[0].copy();m.name='S33_belt-straight-e_moving_deck_native';deck.data.materials.clear();deck.data.materials.append(m)
a=m.node_tree.animation_data_create();a.action=originalEAction;a.action_slot=originalEAction.slots[0]
for track in a.nla_tracks:track.mute=True
phase=m.node_tree.nodes['Value']
# Replace weak native source rails by exact approved open section mesh; local transforms and E orientation stay intact.
for o in list(c.objects):
 if 'stationary_rail' in o.name:
  ref=next(n for n in nobjs if 'stationary_rail' in n.name and (n.location-o.location).length<1e-6)
  o.data=ref.data.copy();o.data.name='E_exact_family_open_rail'
 elif 'wood_leg' in o.name or 'lower_wood_frame' in o.name:bpy.data.objects.remove(o,do_unlink=True)
# Approved crafted load-bearing interiors: bevelled honey legs/shoes, ladder frame and attached brass joinery. They remain inside E source envelope.
for o in nobjs:
 if o.type=='MESH' and 'stationary_rail' not in o.name and o!=ndeck:
  q=o.copy();q.data=o.data.copy();c.objects.link(q);q.parent=orient;q.name='E_'+o.name;q.hide_render=False;q.hide_viewport=False;q.hide_set(False);q.update_tag()
# The family node vocabulary must be independent of any removed orientation object.
for o in c.objects:
 if o.type=='MESH':
  for mat in o.data.materials:
   if mat and mat.use_nodes:
    for n in mat.node_tree.nodes:
     if n.type=='TEX_COORD':assert n.object is None,(mat.name,n.object)
# Strip N from the editable E deliverable; it is reloaded read-only only for the render bench.
for o in nobjs:bpy.data.objects.remove(o,do_unlink=True)
if nc.users: s.collection.children.unlink(nc)
for sc in list(bpy.data.scenes):
 if sc!=s:bpy.data.scenes.remove(sc)
# Registered source camera, exact family exposure/render controls; never presentation camera or bounds fitting.
s.camera.matrix_world=Matrix(f['capture']['worldMatrix']);s.camera.data.type='ORTHO';s.camera.data.ortho_scale=f['capture']['orthoScale'];s.camera.data.shift_x=f['capture']['shift'][0];s.camera.data.shift_y=f['capture']['shift'][1]
s.render.resolution_x=384;s.render.resolution_y=704;s.render.resolution_percentage=100;s.render.pixel_aspect_x=f['capture']['pixelAspect'][0];s.render.pixel_aspect_y=f['capture']['pixelAspect'][1]
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=1;s.cycles.use_adaptive_sampling=False;s.cycles.sampling_pattern='TABULATED_SOBOL';s.cycles.scrambling_distance=0;s.cycles.pixel_filter_type='BOX';s.cycles.filter_width=1;s.cycles.use_denoising=False;s.render.dither_intensity=0
s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='8';s.render.fps=12;s.frame_start=1;s.frame_end=24
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
s.name='BeltEastRegisteredCapture';s['asset_id']='belt-straight-e';s['authored_child_orientation_radians']=float(orient.rotation_euler.z);s['source_project_sha256']=H(source);s['family_settings_sha256']=H(P/'inputs/family-settings.json');s['native_phase_function']='-7*(frame-1)/24'
for o in list(bpy.data.objects):
 if o.name not in s.objects:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
def update():bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
def stats(coll):
 dg=bpy.context.evaluated_depsgraph_get();rows=[]
 for o in coll.objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();ps=[ev.matrix_world@v.co for v in me.vertices]
  rows.append({'name':o.name,'vertices':len(me.vertices),'edges':len(me.edges),'polygons':len(me.polygons),'bounds':[[min(p[i] for p in ps) for i in range(3)],[max(p[i] for p in ps) for i in range(3)]],'matrixWorld':[list(r) for r in ev.matrix_world],'materials':[m.name for m in o.data.materials],'topologySHA256':hashlib.sha256(str(([list(v.co) for v in me.vertices],[list(x.vertices) for x in me.polygons])).encode()).hexdigest()});ev.to_mesh_clear()
 return rows
def bounds(rows):return [[min(r['bounds'][0][i] for r in rows) for i in range(3)],[max(r['bounds'][1][i] for r in rows) for i in range(3)]]
def camera():
 points={}
 for k,p in {'root':(0,0,0),'unitX':(1,0,0),'unitDepth':(0,-1,0),'unitHeight':(0,0,1)}.items():
  v=world_to_camera_view(s,s.camera,Vector(p));points[k]=[v.x*s.render.resolution_x,(1-v.y)*s.render.resolution_y]
 r=points['root'];return {'worldMatrix':[list(r) for r in s.camera.matrix_world],'projectionMatrix':[list(r) for r in s.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)],'orthoScale':s.camera.data.ortho_scale,'shift':[s.camera.data.shift_x,s.camera.data.shift_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'frame':[s.render.resolution_x,s.render.resolution_y],'calibration':{'root':r,**{k:[v[0]-r[0],v[1]-r[1]] for k,v in points.items() if k!='root'}}}
root.rotation_euler.z=0;s.frame_set(1);update();base=stats(c)
profiles=[]
for o in c.objects:
 if o.type!='MESH' or ('stationary_rail' not in o.name and o!=deck):continue
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices]
 profiles.append({'name':o.name,'ends':{str(sign*.5):[list(v) for v in vs if abs(v.x-sign*.5)<1e-6] for sign in [-1,1]}});ev.to_mesh_clear()
act=m.node_tree.animation_data.action;curves=[]
for layer in act.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:curves.append({'dataPath':fc.data_path,'arrayIndex':fc.array_index,'keys':[{'frame':float(k.co.x),'value':float(k.co.y),'interpolation':k.interpolation} for k in fc.keyframe_points]})
assert originalUV==[list(x.uv) for x in deck.data.uv_layers.active.data]
for lib in list(bpy.data.libraries):
 if lib.users==0:bpy.data.libraries.remove(lib)
# Pack and save normal main.blend with a sensible S frame, no bench geometry.
root.rotation_euler.z=0;s.frame_set(1);update();bpy.ops.file.pack_all();project=P/'source/round-01.blend';bpy.ops.wm.save_as_mainfile(filepath=str(project))
validation={'schemaVersion':1,'asset':'belt-straight-e','project':str(project),'projectSHA256':H(project),'blenderVersion':bpy.app.version_string,'sourceProjectSHA256':H(source),'sourceInspection':'source/independent-source-inspection.json','familySettingsSHA256':H(P/'inputs/family-settings.json'),'familyApprovalSHA256':H(P/'inputs/family-approval.json'),'approvedNativeProjectSHA256':f['project']['sha256'],'camera':camera(),'publisherRootRotationsDegrees':{'N':180,'E':90,'S':0,'W':-90},'authoredChildOrientationRadians':float(orient.rotation_euler.z),'geometry':{'collection':c.name,'baselinePublisherS':base,'bounds':bounds(base),'exactOpenProfiles':profiles,'deckSocket':[0,0,.64],'groundContactZ':bounds(base)[0][2],'frameGeometryStatic':True,'nonRailMaximumZ':max(o['bounds'][1][2] for o in base if 'stationary_rail' not in o['name'] and 'connected_straight_deck' not in o['name']),'railCutFaces':'Four open longitudinal strips; no end faces, caps, overhang or gap masks.'},'motion':{'clip':'running','fps':12,'uniqueFrames':24,'closureFrame':25,'phaseFunction':'-7*i/24','periodsPerCell':7,'originalUV':originalUV,'materialOwner':m.name,'phaseNode':phase.name,'nativeAction':act.name,'curves':curves},'render':f['render'],'dependencyClosure':{'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'source':x.source,'filepath':x.filepath,'packed':bool(x.packed_file)} for x in bpy.data.images],'sceneObjects':[o.name for o in s.objects],'externalResources':[]},'frames':[],'nativeRuns':[]}
rotations={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};raw=[]
for d,a in rotations.items():
 root.rotation_euler.z=a
 for i in range(25):
  s.frame_set(i+1);update();actual=float(phase.outputs[0].default_value);assert abs(actual+7*i/24)<1e-5
  path=OUT/'frames'/f'running-{d}-{i:02d}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  row={'clip':'running','direction':d,'index':i,'blenderFrame':i+1,'path':str(path),'rootRotationDegrees':a*180/math.pi,'rootMatrix':[list(r) for r in root.matrix_world],'authoredChildRotationZ':float(orient.rotation_euler.z),'phase':actual,'sha256':H(path)}
  if i in [0,24]:row['geometry']=stats(c)
  validation['frames'].append(row)
  if i<24:raw.append({k:row[k] for k in ['clip','direction','index','path']})
  print('CAPTURE_SINGLE',d,i,actual,flush=True)
 (OUT/f'hero-{d}.png').write_bytes((OUT/'frames'/f'running-{d}-00.png').read_bytes())
 (OUT/'validation.json').write_text(json.dumps(validation,indent=2))
(OUT/'raw-frame-records.json').write_text(json.dumps(raw,indent=2))
# Read-only N reference geometry, with exact approved native shader and action.
with bpy.data.libraries.load(f['project']['path'],link=False) as (available,loaded):loaded.collections=[f['project']['collection']]
refc=loaded.collections[0];s.collection.children.link(refc);refc.hide_render=False;refc.hide_viewport=False
for o in refc.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False);o.update_tag()
refroot=next(o for o in refc.objects if '__root.' in o.name);refdeck=next(o for o in refc.objects if 'connected_straight_deck' in o.name);refphase=refdeck.data.materials[0].node_tree.nodes['Value'];refact=refdeck.data.materials[0].node_tree.animation_data.action
refdeck.data.materials[0].node_tree.animation_data.action_slot=refact.slots[0]
for tr in refdeck.data.materials[0].node_tree.animation_data.nla_tracks:tr.mute=True
refc.hide_render=True
# Capture triples with exact native one-cell contacts; both mixed orders and repeats. Reference N root rotation maps to the same E flow.
original=list(c.objects);clones=[]
for j in [-1,1]:
 mapping={}
 for o in original:q=o.copy();c.objects.link(q);mapping[o]=q
 for o,q in mapping.items():q.parent=mapping.get(o.parent,o.parent)
 clones.append((j,mapping[root],list(mapping.values())))
reforiginal=list(refc.objects);refclones=[]
for j in [-1,1]:
 mapping={}
 for o in reforiginal:q=o.copy();refc.objects.link(q);mapping[o]=q
 for o,q in mapping.items():q.parent=mapping.get(o.parent,o.parent)
 refclones.append((j,mapping[refroot],list(mapping.values())))
# expand fixed camera resolution mathematically, calibration remains256px/cell and179.2px/unitZ.
s.render.resolution_x=896;s.render.resolution_y=1216;s.camera.data.ortho_scale*=1216/704;s.camera.data.shift_y*=704/1216
validation['nativeRunCamera']=camera();validation['nativeAssemblyContract']={'frame':[896,1216],'root':[448,752],'singleFrame':[384,704],'singleRoot':[192,496],'cellPitchPixels':256,'sameFlowNMapping':{'S':'W','N':'E','E':'S','W':'N'},'independentPixelOffsets':{d:([[0,256],[256,256],[512,256]] if d in ['N','S'] else [[256,0],[256,256],[256,512]]) for d in rotations},'compositingOrder':'back-to-front screenY; horizontal left-to-right; unmodified RGBA source frames','patterns':['EEE','ENE','NEN']}
for pattern in ['EEE','ENE','NEN']:
 for d,a in rotations.items():
  nd=validation['nativeAssemblyContract']['sameFlowNMapping'][d];na=rotations[nd]
  c.hide_render=False;refc.hide_render=False
  egroups=[(-1,clones[0][1],clones[0][2]),(0,root,original),(1,clones[1][1],clones[1][2])]
  ngroups=[(-1,refclones[0][1],refclones[0][2]),(0,refroot,reforiginal),(1,refclones[1][1],refclones[1][2])]
  matrices=[]
  for index,(j,er,eobjs) in enumerate(egroups):
   _,nr,nobs=ngroups[index];pos=(j,0,0) if d in ['N','S'] else (0,j,0)
   er.rotation_euler.z=a;er.location=pos;nr.rotation_euler.z=na;nr.location=pos
   for o in eobjs:o.hide_render=pattern[index]!='E'
   for o in nobs:o.hide_render=pattern[index]!='N'
  for i in range(25):
   s.frame_set(i+1);update();assert abs(phase.outputs[0].default_value+7*i/24)<1e-5;assert abs(refphase.outputs[0].default_value+7*i/24)<1e-5
   path=OUT/'native-runs'/f'native-{pattern}-{d}-{i:02d}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   validation['nativeRuns'].append({'pattern':pattern,'direction':d,'compatibleNDirection':nd,'index':i,'path':str(path),'phaseE':float(phase.outputs[0].default_value),'phaseN':float(refphase.outputs[0].default_value),'sha256':H(path),'moduleRootMatrices':[[list(r) for r in (egroups[k][1] if p=='E' else ngroups[k][1]).matrix_world] for k,p in enumerate(pattern)]})
   print('CAPTURE_NATIVE3',pattern,d,i,flush=True)
  (OUT/'validation.json').write_text(json.dumps(validation,indent=2))
# Honest native output metadata. It contains actual capture-scale2 calibration; original historical scale4 record retained in inputs.
cam=json.loads((P/'inputs/source-camera.json').read_text());cam['captureScale']=2;cam['camera'].update({k:validation['camera'][k] for k in ['worldMatrix','projectionMatrix','pixelAspect']});cam['calibration']=validation['camera']['calibration'];cam['artStyle']={'revision':'warm-soft-native-family-v2','familySettingsSHA256':H(P/'inputs/family-settings.json'),'render':f['render']};(OUT/'camera.json').write_text(json.dumps(cam,indent=2))
asset=json.loads((P/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['artStyle']={'revision':'warm-soft-native-family-v2','familySettingsSHA256':H(P/'inputs/family-settings.json'),'materialMethod':'Exact approved native common graph, E native phase action and UV; no external raster textures'};(OUT/'assetRecord.json').write_text(json.dumps(asset,indent=2))
rig=json.loads((P/'inputs/source-rig.json').read_text());rig['status']='native-actions-preserved-round01';rig['projectSHA256']=H(project);rig['actualPhaseCurves']=curves;rig['clips']['running']['actions'][0]['materialOwnerName']=m.name;(OUT/'rig.json').write_text(json.dumps(rig,indent=2))
recipe={'round':1,'project':str(project),'projectSHA256':H(project),'sourceProject':str(source),'sourceProjectSHA256':H(source),'familySettings':str(P/'inputs/family-settings.json'),'familySettingsSHA256':H(P/'inputs/family-settings.json'),'approvedFamilyProject':f['project'],'approvedFamilyRecipe':f['recipe'],'method':'Actual E source root/orientation/deckUV/native action retained; approved native open rail mesh and common procedural shaders; native beveled honey support ladder/shoes/attached brass pegs copied into E local frame. No pixel repair, endcaps, overhang, external texture or ground shadow. All sprites/connected triples rendered from real editable scene.','authoredEOrientationRadians':math.pi/2,'sourceReferences':{'imagegen':['actual E source snapshot','plant style only'],'laterContinuityReference':'approved-family-native-S.png; not an earlier ImageGen reference'},'capture':validation['camera'],'render':f['render'],'reproduce':'blender -b --python source/build_round01.py; python3 source/package_round01.py; consumer bench separately'}
(P/'source/round-01-recipe.json').write_text(json.dumps(recipe,indent=2));print('COMPLETE_NATIVE',flush=True)
