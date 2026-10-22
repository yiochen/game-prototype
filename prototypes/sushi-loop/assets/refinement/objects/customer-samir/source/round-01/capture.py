import bpy,json,sys,math,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
D=Path(__file__).resolve().parent;RES=D/'resources';P=D.parent.parent
AUDIT='--audit-only' in sys.argv
MODE=next((v for v in sys.argv if v in ['main','runtime']),'main');SPOT='--spot' in sys.argv
OUT=P/'candidates/round-01'/MODE;OUT.mkdir(parents=True,exist_ok=True)
rig=json.loads((RES/('source-'+MODE+'-rig.json')).read_text());base=json.loads((RES/('source-'+MODE+'-audit.json')).read_text());brief=json.loads((RES/'frozen-brief.json').read_text())
root=bpy.data.objects[rig['groundRootObject']];collection=next(c for c in bpy.data.collections if root in list(c.all_objects));scene=next(s for s in bpy.data.scenes if root in list(s.objects));bpy.context.window.scene=scene;bpy.context.window.view_layer=scene.view_layers[0]
cam=scene.camera;asset={'root':root,'collection':collection};spec=importlib.util.spec_from_file_location('samir_native',RES/'native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
body=[o for o in collection.all_objects if o.type=='MESH' and o.get('weighted_character_geometry')];arm=next(o for o in collection.all_objects if o.type=='ARMATURE');plane=next(o for o in collection.all_objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi');foodroot=plane.parent
W,H=384,640
def plain(v):return [round(float(x),9) for x in v]
def mat(v):return [plain(row) for row in v]
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def px(v):
 t=world_to_camera_view(scene,cam,Vector(v));return [round(t.x*W,7),round((1-t.y)*H,7)]
def geometry_bounds():
 dg=bpy.context.evaluated_depsgraph_get();pts=[]
 for o in body:
  e=o.evaluated_get(dg);me=e.to_mesh();pts.extend([e.matrix_world@v.co for v in me.vertices]);e.to_mesh_clear()
 return [[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]
def posed(bn,point):return arm.matrix_world@arm.pose.bones[bn].matrix@arm.data.bones[bn].matrix_local.inverted()@Vector(point)
rest=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':plain(b.head_local),'tail':plain(b.tail_local),'matrix':mat(b.matrix_local),'deform':b.use_deform} for b in arm.data.bones]
actions={t['action']:digest([{'path':f.data_path,'index':f.array_index,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in f.keyframe_points]} for f in native._fcurves(bpy.data.actions[t['action']])]) for c in rig['clips'].values() for t in c['actions']}
report={'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'mode':MODE,'blenderVersion':bpy.app.version_string,'project':str(Path(bpy.data.filepath).name),'camera':{'name':cam.name,'matrix':mat(cam.matrix_world),'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[W,H],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'projectionMatrix':mat(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=W,y=H,scale_x=1,scale_y=1))},'root':{'name':root.name,'location':plain(root.location),'scale':plain(root.scale)},'rootProjection':px((0,0,0)),'rig':{'name':arm.name,'bones':rest,'restSHA256':digest(rest),'actionSHA256':actions},'bodyMeshCount':len(body),'clips':{},'errors':[],'maxima':{}}
if report['rig']['restSHA256']!=base['rig']['restSHA256']:report['errors'].append('rest hash mismatch')
if actions!=base['rig']['actionSHA256']:report['errors'].append('action hash mismatch')
food='cucumber' if MODE=='main' else 'salmon';mapping=json.loads((RES/'food-mapping-proposal.json').read_text())['proposals'][food]['thresholdSensitivity']['128']
im=next(n.image for m in plane.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE');packed=bytes(im.packed_file.data)
report['food']={'composition':food,'representation':'exact canonical packed2D raster, not modeled3D food','packedSHA256':hashlib.sha256(packed).hexdigest(),'size':list(im.size),'vertices':[plain(v.co) for v in plane.data.vertices],'UV':[plain(u.uv) for u in plane.data.uv_layers.active.data],'mapping':mapping,'depthWorldCells':.30,'pointConvention':json.loads((RES/'food-mapping-proposal.json').read_text())['pointConvention'],'drivers':[{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression} for f in plane.animation_data.drivers]}
expected=brief['foodDependencies']['dish-'+food]['sha256']
if report['food']['packedSHA256']!=expected:report['errors'].append('canonical packed bytes mismatch')
maxcontact=maxbone=maxroot=maxfoodroot=maxdepth=maxcorner=0
loops={}
for clip in rig['clips']:
 samples=[];canon=clip.replace('_','-');env=brief['constraints']['functionalGeometryEnvelope']['perClipBodyZWorld'][canon]
 for direction in ['S','E','N','W']:
  for frame in ([5] if SPOT else range(1,13)):
   native.apply_clip(asset,rig,clip,frame,direction,scene)
   hideR,hideV=plane.hide_render,plane.hide_viewport;plane.hide_render=False;plane.hide_viewport=False;bpy.context.view_layer.update()
   b=geometry_bounds();contact={'palms':{s:plain(posed('hand_'+s,arm.data.bones['hand_'+s].head_local+Vector((0,-.002,-.046)))) for s in ['L','R']},'mouth':plain(posed('head',(0,-.255,.543))),'seat':plain(arm.matrix_world@(arm.pose.bones['pelvis'].head-Vector((0,0,.08)))),'footBoneHeads':{s:plain(arm.matrix_world@arm.pose.bones['foot_'+s].head) for s in ['L','R']}}
   bone={bn:mat(arm.matrix_world@arm.pose.bones[bn].matrix) for bn in ['ground','pelvis','head','hand_L','hand_R','foot_L','foot_R']}
   src=next(s for s in base['clips'][clip]['samples'] if s['direction']==direction and s['frame']==frame)
   def err(a,b):
    if isinstance(a,dict):return max(err(a[k],b[k]) for k in a)
    if isinstance(a,list):return max(err(x,y) for x,y in zip(a,b))
    return abs(float(a)-float(b))
   maxcontact=max(maxcontact,err(contact,src['evaluatedContactsWorld']));maxbone=max(maxbone,err(bone,src['functionalBoneWorldMatrices']));maxroot=max(maxroot,err(mat(root.matrix_world),src['rootMatrix']));maxfoodroot=max(maxfoodroot,err(plain(foodroot.matrix_world.translation),src['foodRootWorld']))
   corners=[plane.matrix_world@v.co for v in plane.data.vertices];ray=Vector((0,-.8191520442889918,.573576436351046));reference=[v+ray*.30 for v in corners]
   cerror=max(abs(px(v)[j]-px(ref)[j]) for v,ref in zip(corners,reference) for j in [0,1]);maxcorner=max(maxcorner,cerror)
   # Depth relative to native food-root, excluding semantic mesh offset.
   delta=plane.matrix_world.translation-foodroot.matrix_world.translation;depth=delta.dot(ray);perp=(delta-ray*depth).length;maxdepth=max(maxdepth,abs(depth-.30),perp)
   if any(abs(b[q][i])>.50001 for q in [0,1] for i in [0,1]):report['errors'].append(f'XY envelope {clip}/{direction}/{frame}: {b}')
   if b[1][2]>env[1]+.00001:report['errors'].append(f'upper clearance {clip}/{direction}/{frame}: {b[1][2]} > {env[1]}')
   if hideR==src['foodVisible']:report['errors'].append(f'visibility mismatch {clip}/{direction}/{frame}')
   sample={'direction':direction,'frame':frame,'bodyBounds':b,'rootMatrix':mat(root.matrix_world),'evaluatedContactsWorld':contact,'functionalBoneWorldMatrices':bone,'foodRootWorld':plain(foodroot.matrix_world.translation),'foodVisible':not hideR,'foodWorldCorners':[plain(v) for v in corners],'foodProjectedCorners':[px(v) for v in corners],'depthWorld':depth,'depthPerpendicularResidual':perp,'correctedDepthPoint6ProjectedCorners':[px(v) for v in reference],'foodProjectionErrorNativePixels':cerror}
   samples.append(sample)
   plane.hide_render=hideR;plane.hide_viewport=hideV;bpy.context.view_layer.update()
   path=OUT/'frames'/canon/direction/f'{frame-1:02}.png';path.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(path)
   if not AUDIT:bpy.ops.render.render(write_still=True)
   print('FRAME',MODE,canon,direction,frame,flush=True)
  # Source closure key13 must remain present and evaluate the same trajectory.
  if not SPOT and rig['clips'][clip]['loop']:
   native.apply_clip(asset,rig,clip,1,direction,scene);first={p.name:mat(p.matrix) for p in arm.pose.bones}
   native.apply_clip(asset,rig,clip,13,direction,scene);last={p.name:mat(p.matrix) for p in arm.pose.bones}
   loops[canon+'-'+direction]=err(first,last)
 report['clips'][canon]={'sourceClipId':clip,'loop':rig['clips'][clip]['loop'],'fps':12,'frames':12,'samples':samples,'boundsUnion':[[min(s['bodyBounds'][0][i] for s in samples) for i in range(3)],[max(s['bodyBounds'][1][i] for s in samples) for i in range(3)]]}
 report['maxima']={'contactTransformErrorWorld':maxcontact,'functionalBoneMatrixError':maxbone,'rootMatrixError':maxroot,'foodRootErrorWorld':maxfoodroot,'foodRayErrorWorld':maxdepth,'correctedProjectionErrorNativePixels':maxcorner};report['loopClosureMaxBoneMatrixError']=loops
 (OUT/('validation-native-reopened.json' if AUDIT else ('spot-validation.json' if SPOT else 'validation-native.json'))).write_text(json.dumps(report,indent=2)+'\n')
 print('CLIP_COMPLETE',MODE,canon,'errors',len(report['errors']),flush=True)
print('CAPTURE_COMPLETE',MODE,'ERRORS',report['errors'],flush=True)
