"""Reopen the saved native project, audit actual frames and render192 captures."""
import bpy, json, math, hashlib, importlib.util, sys, time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round01'
BASE=HERE.parents[3]/'production/source/blender'
spec=importlib.util.spec_from_file_location('mateo_capture_native',HERE/'native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
rig=json.loads((OUT/'rig.json').read_text());assetrec=json.loads((OUT/'assetRecord.json').read_text())
source=json.loads((HERE/'source-native-audit.json').read_text());sourceposes={(p['clip'],p['direction'],p['index']):p for p in source['poses']}
scene=bpy.data.scenes['Mateo warm soft native round01'];bpy.context.window.scene=scene
root=bpy.data.objects[rig['groundRootObject']];collection=next(c for c in scene.collection.children if root in list(c.all_objects))
arm=next(o for o in collection.all_objects if o.type=='ARMATURE');asset=dict(assetrec,root=root,collection=collection)
objects=list(collection.all_objects);meshes=[o for o in objects if o.type=='MESH'];body=[o for o in meshes if '__ground_root' not in o.name]
def plain(v):
 try:return [plain(x) for x in v]
 except:return v
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def meshsample(o,dg):
 ev=o.evaluated_get(dg);me=ev.to_mesh();p=[ev.matrix_world@v.co for v in me.vertices]
 r={'min':[min(v[i] for v in p) for i in range(3)],'max':[max(v[i] for v in p) for i in range(3)],'centroid':[sum(v[i] for v in p)/len(p) for i in range(3)],'vertices':len(me.vertices),'edges':len(me.edges),'polygons':len(me.polygons)}
 ev.to_mesh_clear();return r
def project(v):
 p=world_to_camera_view(scene,scene.camera,Vector(v));return [p.x*384,(1-p.y)*640]
def difference(a,b):return max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))
restBones=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrixLocal':plain(b.matrix_local),'deform':b.use_deform} for b in arm.data.bones]
assert restBones==source['restBones'],'Rest skeleton changed'
actionhashes={}
for cd in rig['clips'].values():
 for target in cd['actions']:
  ac=bpy.data.actions[target['action']]
  curves=[{'path':fc.data_path,'index':fc.array_index,'keys':[{'co':list(k.co),'interpolation':k.interpolation,'handleLeft':list(k.handle_left),'handleRight':list(k.handle_right)} for k in fc.keyframe_points]} for fc in native._fcurves(ac)]
  actionhashes[ac.name]=hashlib.sha256(json.dumps(curves,sort_keys=True).encode()).hexdigest()
assert actionhashes==source['actionFingerprints'],'Original native action curves changed'
meshRest={o.name:digest({'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'weights':[[(g.group,g.weight) for g in v.groups] for v in o.data.vertices]}) for o in meshes}
externalImages=[{'name':im.name,'filepath':im.filepath,'packed':bool(im.packed_file),'sha256':hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None} for im in bpy.data.images if im.type=='IMAGE']
assert all(i['packed'] for i in externalImages),'Unpacked external image'
salmon=next(i for i in externalImages if i['name']=='dish-salmon.png');assert salmon['sha256']==source['packedImageHashes']['dish-salmon.png'],'Source food insert bytes changed'
assert len(externalImages)==1,externalImages
records=[];topology={o.name:set() for o in meshes};maxBone=0;maxPalm=0;maxProp=0;maxShoe=0;maxKnife=0;errors=[]
started=time.time()
auditOnly='--audit-only' in sys.argv
for clip,cd in rig['clips'].items():
 for direction in ['N','E','S','W']:
  folder=OUT/'raw-frames'/(clip+'-'+direction);folder.mkdir(parents=True,exist_ok=True)
  for index in range(cd['frames']):
   native.apply_clip(asset,rig,clip,index+1,direction,scene)
   dg=bpy.context.evaluated_depsgraph_get();sp=sourceposes[(clip,direction,index)]
   sampled={o.name:meshsample(o,dg) for o in meshes}
   for n,s in sampled.items():topology[n].add((s['vertices'],s['edges'],s['polygons']))
   bb={'min':[min(sampled[o.name]['min'][i] for o in body) for i in range(3)],'max':[max(sampled[o.name]['max'][i] for o in body) for i in range(3)]}
   sourcebody=[o['bounds'] for n,o in sp['objects'].items() if o['bounds'] and '__ground_root' not in n]
   old={'min':[min(o['min'][i] for o in sourcebody) for i in range(3)],'max':[max(o['max'][i] for o in sourcebody) for i in range(3)]}
   # Source one-cell envelope is a functional clearance, not an exact old silhouette.
   if any(abs(bb[k][i])>.50001 for k in ['min','max'] for i in range(2)):errors.append([clip,direction,index,'body outside one cell'])
   if bb['max'][2]>old['max'][2]+.00001:errors.append([clip,direction,index,'body exceeds original action height',bb['max'][2],old['max'][2]])
   boneErr=max(difference(plain(arm.matrix_world@p.matrix),sp['bones'][p.name]) for p in arm.pose.bones);maxBone=max(maxBone,boneErr)
   palms={};feet={};props={}
   for side in ['L','R']:
    name='chef_mateo__palm_'+side+'.001';p=sampled[name]['centroid'];q=sp['objects'][name]['bounds']['centroid'];err=(Vector(p)-Vector(q)).length;maxPalm=max(maxPalm,err)
    palms[side]={'actual':p,'source':q,'distance':err,'projected':project(p)}
    name='chef_mateo__minimal_foot_'+side;f=sampled[name];q=sp['objects'][name]['bounds'];err=abs(f['min'][2]-q['min'][2]);maxShoe=max(maxShoe,err)
    feet[side]={'actual':f,'sourceMinZ':q['min'][2],'groundDelta':err}
   for name in ['chef_mateo__ground_root.001__held_dish-salmon','chef_mateo__ground_root.001__held_dish-salmon__image_plane','chef_mateo__ground_root.001__utensil','chef_mateo__ground_root.001__knife_handle','chef_mateo__ground_root.001__knife_blade']:
    o=bpy.data.objects[name];matrix=plain(o.evaluated_get(dg).matrix_world);err=difference(matrix,sp['objects'][name]['matrixWorld']);maxProp=max(maxProp,err)
    props[name]={'matrixWorld':matrix,'sourceMatrixDelta':err,'hidden':o.hide_render,'sourceHidden':sp['objects'][name]['hidden'],'projectedOrigin':project(o.matrix_world.translation),'bounds':sampled.get(name)}
    if o.hide_render!=sp['objects'][name]['hidden']:errors.append([clip,direction,index,'prop visibility changed',name])
   knife=bpy.data.objects['chef_mateo__ground_root.001__utensil'];knifeErr=(knife.matrix_world.translation-Vector(palms['R']['actual'])).length if clip=='work' else None
   if knifeErr is not None:maxKnife=max(maxKnife,knifeErr)
   path=folder/(str(index).zfill(3)+'.png')
   if not auditOnly:
    scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   records.append({'clip':clip,'direction':direction,'index':index,'frame':index+1,'path':str(path.relative_to(OBJ)),'rootRotationZ':float(root.rotation_euler.z),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':plain(root.matrix_world),'bodyBounds':bb,'sourceBodyBounds':old,'boneMatrixMaxDelta':boneErr,'palms':palms,'feet':feet,'props':props,'knifeToPalmDistance':knifeErr})
   if len(records)%12==0:
    (OUT/'capture-progress.json').write_text(json.dumps({'done':len(records),'total':192,'seconds':time.time()-started,'current':clip+'-'+direction},indent=2)+'\n')
    print('MATEO_CAPTURE',len(records),clip,direction,flush=True)
assert len(records)==192
assert maxBone<1e-6 and maxPalm<1e-6 and maxProp<1e-6 and maxShoe<1e-6 and maxKnife<1e-6,(maxBone,maxPalm,maxProp,maxShoe,maxKnife)
assert all(len(s)==1 for s in topology.values()),'Changing evaluated topology'
meshAfter={o.name:digest({'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'weights':[[(g.group,g.weight) for g in v.groups] for v in o.data.vertices]}) for o in meshes};assert meshAfter==meshRest,'Rest mesh or weights mutated during capture'
validation={'asset':'chef-mateo','round':'round01','pipeline':'native-3d with original explicitly2D salmon insert','sourceProjectSHA256':source['sourceSHA256'],'candidateProjectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'scene':scene.name,'frame':[384,640],'logicalFrame':[192,320],'logicalRoot':[96,248],'captureScale':2,'actualCamera':{'matrixWorld':plain(scene.camera.matrix_world),'orthoScale':scene.camera.data.ortho_scale,'shift':[scene.camera.data.shift_x,scene.camera.data.shift_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'root':project((0,0,0))},'nominalFunctionalHeight':1.3279640674591064,'rootScale':list(root.scale),'rig':{'restBonesUnchanged':True,'originalActionFingerprintsUnchanged':True,'actionFingerprints':actionhashes,'maximumEvaluatedBoneMatrixDelta':maxBone},'contacts':{'maximumPalmCentroidDelta':maxPalm,'maximumPropMatrixDelta':maxProp,'maximumFootGroundDelta':maxShoe,'maximumWorkKnifeToPalmDistance':maxKnife,'food':'Original packed dish-salmon.png2D plane; unchanged UVs, geometry, native visibility, yaw-cancellation, intentional camera-ray depth bias. Projected source attachment matrices preserved; no physical3D sushi claim.'},'topology':{'all192SamplesStable':True,'restMeshesAndWeightsUnchangedDuringPlayback':True,'meshes':{n:list(next(iter(v))) for n,v in topology.items()},'restMeshHashes':meshRest,'modifierTypes':{o.name:[m.type for m in o.modifiers] for o in meshes}},'dependencies':{'packedImages':externalImages,'linkedLibraries':[l.filepath for l in bpy.data.libraries]},'materials':{m.name:{'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value,'baseColor':list(m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value)} for m in bpy.data.materials if m.name.startswith('Mateo warm soft ')},'lighting':json.loads((OUT/'camera.json').read_text())['artStyle'],'animation':{'frames':192,'clips':{c:{'frames':d['frames'],'fps':d['fps'],'loop':d['loop'],'firstFrame':d['firstFrame'],'lastUniqueFrame':d['lastUniqueFrame'],'closingKeyFrame':d.get('closingKeyFrame')} for c,d in rig['clips'].items()}},'nativeRecords':{'camera':str((OUT/'camera.json').relative_to(OBJ)),'assetRecord':str((OUT/'assetRecord.json').relative_to(OBJ)),'rig':str((OUT/'rig.json').relative_to(OBJ))},'errors':errors,'nativeChecksPass':not errors,'renders':records,'elapsedSeconds':time.time()-started}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print('MATEO_CAPTURE_COMPLETE',json.dumps({'frames':len(records),'errors':errors,'bone':maxBone,'palm':maxPalm,'prop':maxProp,'feet':maxShoe,'knife':maxKnife,'seconds':time.time()-started}))
