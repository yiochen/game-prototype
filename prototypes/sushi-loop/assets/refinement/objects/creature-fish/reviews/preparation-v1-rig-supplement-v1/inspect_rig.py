import bpy,sys,json,math,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent/'preparation-v1';S=B/'resources/inputs/untouched.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mat(m):return [list(r) for r in m]
def bounds(points):return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def write(name,obj):(P/name).write_text(json.dumps(obj,indent=2)+'\n')
s=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33);bpy.context.window.scene=s;bpy.context.window.view_layer=s.view_layers[0]
rig=json.loads((B/'resources/inputs/source-rig.json').read_text());asset=json.loads((B/'resources/inputs/source-assetRecord.json').read_text());root=bpy.data.objects[rig['groundRootObject']];coll=next(c for c in s.collection.children if root in list(c.all_objects));arm=next(o for o in coll.all_objects if o.type=='ARMATURE')
def enable(lc):
 for c in lc.children:enable(c)
 lc.exclude=False;lc.hide_viewport=False
 if lc.collection==coll:lc.collection.hide_render=False;lc.collection.hide_viewport=False
 enable_path=False
for lc in s.view_layers[0].layer_collection.children:enable(lc);lc.exclude=lc.collection!=coll
for c in s.collection.children:c.hide_render=c!=coll;c.hide_viewport=c!=coll
for o in coll.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
s.view_layers[0].update();bpy.context.evaluated_depsgraph_get().update();asset.update(root=root,collection=coll)
spec=importlib.util.spec_from_file_location('fish_rig_supplement_native',B/'resources/native/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
channels={}
for clip,c in rig['clips'].items():
 action=bpy.data.actions[c['actions'][0]['action']];curves=list(native._fcurves(action));channels[clip]={'action':action.name,'range':list(action.frame_range),'curves':[{'dataPath':f.data_path,'arrayIndex':f.array_index,'keyCount':len(f.keyframe_points),'extrapolation':f.extrapolation,'phaseSamples':{str(i):f.evaluate(i) for i in [1,4,7,10,12,13,24]}} for f in curves]}
modes={b.name:b.rotation_mode for b in arm.pose.bones}
metadata={'asset':'creature-fish','sourceSHA256Before':sha(S),'blender':bpy.app.version_string,'scene':s.name,'collection':coll.name,'root':root.name,'armature':arm.name,'objectRotationMode':arm.rotation_mode,'poseBoneRotationModes':modes,'actionChannels':channels,'originalGeometryDigest':{o.name:hashlib.sha256(b''.join(float(v).hex().encode()+b',' for p in o.data.vertices for v in p.co)).hexdigest() for o in coll.all_objects if o.type=='MESH'}}
write('raw-modes-channels.json',metadata)
meshes=[o for o in coll.all_objects if o.type=='MESH'];results={}
# Actual source first; second branch changes ONLY pose bone mode if Euler curves are on a non-Euler mode.
has_euler=all(any(f.data_path.startswith('pose.bones[') and f.data_path.endswith('rotation_euler') for f in native._fcurves(bpy.data.actions[r['actions'][0]['action']])) for r in rig['clips'].values())
for branch in ['actual-authored-modes','temporary-euler-interpretation'] if has_euler and any(m in ['QUATERNION','AXIS_ANGLE'] for m in modes.values()) else ['actual-authored-modes']:
 if branch=='temporary-euler-interpretation':
  for bone in arm.pose.bones:bone.rotation_mode='XYZ'
 entries=[];summary=[];global_points=[]
 for clip,c in rig['clips'].items():
  for d in ['N','E','S','W']:
   baseline=None;baseline_bones=None;baseline_arm=None;last_unique=None;clipentries=[]
   fs=list(range(1,13))+([13] if c['loop'] else [24])
   for frame in fs:
    native.apply_clip(asset,rig,clip,frame,d,s);s.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get();dg.update();inv=arm.matrix_world.inverted();points=[];local={};raw=[]
    for o in meshes:
     raw.extend(o.matrix_world@v.co for v in o.data.vertices);e=o.evaluated_get(dg);m=e.to_mesh();world=[e.matrix_world@v.co for v in m.vertices];points.extend(world);local[o.name]=[inv@p for p in world];e.to_mesh_clear()
    bones={b.name:mat(b.matrix) for b in arm.pose.bones};armmat=mat(arm.matrix_world)
    if baseline is None:baseline=local;baseline_bones=bones;baseline_arm=armmat
    residual={n:max((a-b).length for a,b in zip(baseline[n],pts)) for n,pts in local.items()}
    bonevariation={n:max(abs(x-y) for a,b in zip(baseline_bones[n],m) for x,y in zip(a,b)) for n,m in bones.items()}
    entry={'clip':clip,'direction':d,'frame':frame,'isUniquePublished':frame<=12,'rootRotationZ':root.rotation_euler.z,'rawAuthoredBounds':bounds(raw),'evaluatedBounds':bounds(points),'armatureMatrix':armmat,'boneMatricesArmatureLocal':bones,'maxBoneMatrixDifferenceFromFrame1':max(bonevariation.values()),'boneMatrixDifferenceFromFrame1':bonevariation,'maxRelativeMeshVertexDistanceFromFrame1':max(residual.values()),'relativeMeshVertexDistanceFromFrame1':residual}
    if frame==1:entry['boneRotationChannels']={b.name:{'mode':b.rotation_mode,'euler':list(b.rotation_euler),'quaternion':list(b.rotation_quaternion),'axisAngle':list(b.rotation_axis_angle),'matrixBasis':mat(b.matrix_basis)} for b in arm.pose.bones}
    if frame==12:last_unique=(local,bones,armmat)
    if frame>12:
     compare=baseline if c['loop'] else last_unique[0];compare_bones=baseline_bones if c['loop'] else last_unique[1];compare_arm=baseline_arm if c['loop'] else last_unique[2]
     entry['boundaryType']='loopClosingKey13Vs1' if c['loop'] else 'oneShotExtrapolatedFrame24Vs12'
     entry['boundaryMaxRelativeVertexDistance']=max((a-b).length for n,pts in local.items() for a,b in zip(compare[n],pts));entry['boundaryMaxBoneMatrixResidual']=max(abs(x-y) for n,m in bones.items() for a,b in zip(compare_bones[n],m) for x,y in zip(a,b));entry['boundaryMaxArmatureMatrixResidual']=max(abs(x-y) for a,b in zip(compare_arm,armmat) for x,y in zip(a,b))
    if frame<=12:global_points.extend(points)
    clipentries.append(entry);entries.append(entry)
   summary.append({'clip':clip,'direction':d,'maxBoneMatrixDifferenceFromFrame1':max(e['maxBoneMatrixDifferenceFromFrame1'] for e in clipentries[:12]),'maxRelativeMeshVertexDistanceFromFrame1':max(e['maxRelativeMeshVertexDistanceFromFrame1'] for e in clipentries[:12]),'boundary':{k:v for k,v in clipentries[-1].items() if k.startswith('boundary')}})
 results[branch]={'boneRotationModes':{b.name:b.rotation_mode for b in arm.pose.bones},'globalUniqueFrameBounds':bounds(global_points),'uniquePublishedFrameEvaluations':528,'additionalBoundaryEvaluations':44,'summary':summary,'phaseRecords':entries}
 write(branch+'.json',results[branch])
# Original source bytes and mesh local coords must remain unchanged even in temporary in-memory branch.
metadata['sourceSHA256After']=sha(S);metadata['sourceBytesUnchanged']=metadata['sourceSHA256Before']==metadata['sourceSHA256After'];metadata['method']='No .blend save. Actual original geometry/material/action/key timing untouched; only temporary second branch pose bone rotation_mode XYZ to interpret existing Euler FCurves. Object modes unchanged. World vertices evaluated per mesh and transformed back through armature.world inverse to measure relative body response independently from object movement. Source references remain byte unchanged.'
write('raw-modes-channels.json',metadata)
write('summary.json',{'asset':'creature-fish','preparationOnly':True,'noCandidateNoApproval':True,'actualModes':modes,'objectRotationMode':arm.rotation_mode,'allClipsHaveBoneEulerCurves':has_euler,'sourceBytesUnchanged':metadata['sourceBytesUnchanged'],'sourceSHA256':metadata['sourceSHA256After'],'method':metadata['method'],'branches':{k:{a:b for a,b in v.items() if a!='phaseRecords'} for k,v in results.items()}})
print('FISH_RIG_SUPPLEMENT_COMPLETE',json.dumps({'modes':modes,'branches':list(results),'sourceUnchanged':metadata['sourceBytesUnchanged']}),flush=True)
