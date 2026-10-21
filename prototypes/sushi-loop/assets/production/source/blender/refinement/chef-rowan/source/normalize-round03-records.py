"""Metadata-only normalizer: reopen final source, measure, never save .blend."""
import bpy,json,hashlib,copy,math,importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=HERE/'round03-metadata';OUT.mkdir(exist_ok=True)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
brief=read(OBJ/'brief-v4-food-occlusion.json');base_rig=read(OBJ/'inputs/source-rig.json')
oldcamera=read(OBJ/'inputs/source-camera.json');assetrecord=read(OBJ/'inputs/source-assetRecord.json')
audit=read(OBJ/'candidates/round-03/native-audit.json');supplement=read(OBJ/'candidates/round-03/native-supplement.json')
food=read(OBJ/'candidates/round-03/food-native-audit.json');validation=read(OBJ/'candidates/round-03/validation.json')
project=Path(bpy.data.filepath);projectsha=sha(project)
assert projectsha==audit['sourceProjectSHA256']==supplement['nativeSourceSHA256']==food['sourceSHA256']
assert audit['allChecksPassed'] and supplement['allChecksPassed'] and food['allChecksPassed'] and validation['allTechnicalChecksPassed']
scene=bpy.context.scene;cam=scene.camera;root=bpy.data.objects[base_rig['groundRootObject']]
col=bpy.data.collections['S33_CHARACTER_chef_rowan.001'];col.hide_viewport=False;col.hide_render=False
def visible(lc):
 lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_viewport=False
 for c in lc.children:visible(c)
visible(bpy.context.view_layer.layer_collection)
bpy.context.view_layer.update()
lights=[]
for o in scene.objects:
 if o.type=='LIGHT':lights.append(dict(name=o.name,type=o.data.type,energy=o.data.energy,size=getattr(o.data,'size',None),worldPosition=list(o.matrix_world.translation),color=list(o.data.color)))
style=dict(revision='warm-soft-chef-rowan-round03-candidate',status='pending-independent-visual-review',
           style='Warm softly lit cartoon',nativeEditable=True,worldLighting=True,
           lighting='Centered170W overhead plus four equal cardinal95W area fills, all4.5 size; neutral worldstrength0.22; no ground plane or directional ground shadow',
           lightingRig=lights,world=dict(color=list(scene.world.node_tree.nodes['Background'].inputs['Color'].default_value),strength=scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value),
           colorManagement=supplement['colorManagement'],
           materialPolicy='Native per-part Principled materials with soft local AO; original world-height material ramp removed. Exact canonical salmon is packed2D emission/alpha, knife remains native mesh.')
def project_point(point):
 p=world_to_camera_view(scene,cam,Vector(point));return [p.x*384,(1-p.y)*640]
origin=project_point((0,0,0))
projection=cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=640,scale_x=1,scale_y=1)
camera=dict(projection='character-orthographic',frame=[192,320],anchor=[96,248],cellSize=128,captureScale=2,sourceCaptureScale=2,fps=12,
            axes=copy.deepcopy(oldcamera['axes']),
            camera=dict(type='orthographic',worldMatrix=[list(r) for r in cam.matrix_world],projectionMatrix=[list(r) for r in projection],pixelAspect=[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],worldUnitsPerCell=1,elevationDegrees=35,orthoScale=cam.data.ortho_scale,shiftX=cam.data.shift_x,shiftY=cam.data.shift_y),
            calibration=dict(root=origin,**{k:[a-b for a,b in zip(project_point(p),origin)] for k,p in dict(unitX=(1,0,0),unitDepth=(0,-1,0),unitHeight=(0,0,1)).items()}),
            declaredLogicalRegistration=dict(frame=[192,320],anchor=[96,248],nativeFrame=[384,640],nativeAnchor=[192,496]),
            artStyle=style,
            provenance=dict(kind='Saved-source measured metadata, no art/source mutation',activeBrief='brief-v4-food-occlusion.json',project='source/round-03.blend',projectSHA256=projectsha,priorCamera='inputs/source-camera.json',priorCameraSHA256=sha(OBJ/'inputs/source-camera.json'),revision='Actual output captureScale2 replaces original source record4; round01 body/rig/camera/light retained; one continuous frozen native ray occlusion law measured from final saved source.'))
assert camera['camera']['worldMatrix']==audit['camera']['matrix']
assert max(abs(projection[i][j]-oldcamera['camera']['projectionMatrix'][i][j]) for i in range(4) for j in range(4))<1e-6
assert max(abs(a-b) for a,b in zip(origin,[192,496]))<.001
write('camera.json',camera)

assetrecord=copy.deepcopy(assetrecord);assetrecord['scale']=2;assetrecord['captureScale']=2;assetrecord['sourceCaptureScale']=2
assetrecord['artStyle']=style
assetrecord['foodDependency']=brief['foodDependency']
assetrecord['nativeRefinement']=dict(activeBrief='brief-v4-food-occlusion.json',project='source/round-03.blend',projectSHA256=projectsha,
                                    rig='source/round03-metadata/rig.json',nativeAudit='candidates/round-03/native-audit.json',nativeAuditSHA256=sha(OBJ/'candidates/round-03/native-audit.json'),
                                    originalAssetRecord='inputs/source-assetRecord.json',originalAssetRecordSHA256=sha(OBJ/'inputs/source-assetRecord.json'),
                                    changes='Capture scale metadata4->2 and truthful final artStyle/packed canonical food provenance. Original logical registration, footprint, nominal height, clips, directions, locomotion metadata and static socket contract retained exactly.')
write('asset.json',assetrecord)
rig=copy.deepcopy(base_rig)
rig['status']='native-actions-preserved-audited-pending-independent-visual-review'
rig['notes']=['Original25-bone rest and all24 native action cohorts retained exactly; keyframe/slot identities audited.',
              'Native body and native knife; exact approved canonical731x505 salmon remains explicitly packed2D raster, not modeled sushi.',
              'Runtime frames exclude duplicate loop closure13; load retains original nonlooping out-and-back12 frames.',
              'Original controlsByFrame are preserved source local attachment records; final all192 world-space evaluated contacts are in the bound native audit.']
rig['nativeRefinement']=dict(activeBrief='brief-v4-food-occlusion.json',project='source/round-03.blend',projectSHA256=projectsha,
                            originalRig='inputs/source-rig.json',originalRigSHA256=sha(OBJ/'inputs/source-rig.json'),
                            nativeAudit='candidates/round-03/native-audit.json',nativeAuditSHA256=sha(OBJ/'candidates/round-03/native-audit.json'),
                            foodNativeAudit='candidates/round-03/food-native-audit.json',foodNativeAuditSHA256=sha(OBJ/'candidates/round-03/food-native-audit.json'),
                            foodDependency=brief['foodDependency'],foodOcclusionPolicy=brief['foodOcclusionPolicy'],depthOnlyAudit='candidates/round-03/occlusion-native-audit.json',representation='Native body/knife plus declared packed2D salmon')
write('rig.json',rig)

spec=importlib.util.spec_from_file_location('native',HERE/'resources/original-native-actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
asset=dict(root=root,collection=col);renders=[]
for clip in ['idle','work','hold','load']:
 for direction in ['N','E','S','W']:
  for index in range(12):
   native.apply_clip(asset,base_rig,clip,index+1,direction,scene);bpy.context.view_layer.update()
   m=root.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
   rotation=math.atan2(m[1][0],m[0][0])
   renders.append(dict(clip=clip,direction=direction,index=index,sourceNativeFrame=index+1,
                       path=f'candidates/round-03/frames/{clip}-{direction}-{index:02}.png',
                       rootMatrix=[list(r) for r in m],rootRotationZ=rotation,
                       rootRotationDegrees=math.degrees(rotation)))
assert len(renders)==192
for r in renders:
 expected={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[r['direction']]
 assert abs(math.atan2(math.sin(r['rootRotationZ']-expected),math.cos(r['rootRotationZ']-expected)))<1e-6
native_records=dict(camera='source/round03-metadata/camera.json',assetRecord='source/round03-metadata/asset.json',rig='source/round03-metadata/rig.json')
wrapper=dict(asset='chef-rowan',round='round-03',activeBrief='brief-v4-food-occlusion.json',projectSHA256=projectsha,
             allTechnicalChecksPassed=True,appearance='Pending independent judge; metadata normalization is not aesthetic approval.',
             lighting=style['lighting'],captureScale=2,frame=[192,320],anchor=[96,248],nativeFrame=[384,640],
             nativeRecords={key:dict(path=path,sha256=sha(OBJ/path)) for key,path in native_records.items()},
             evidence={name:dict(path=path,sha256=sha(OBJ/path)) for name,path in dict(captureValidation='candidates/round-03/validation.json',nativeAudit='candidates/round-03/native-audit.json',nativeSupplement='candidates/round-03/native-supplement.json',foodNativeAudit='candidates/round-03/food-native-audit.json',browserPlaybackQA='candidates/round-03/browser-playback-qa.json',depthOnlyAudit='candidates/round-03/occlusion-native-audit.json',visibleProjectionAudit='candidates/round-03/visible-projection-audit.json',hiddenFoodPixelAudit='candidates/round-03/hidden-food-pixel-audit.json',closedPackageReceipt='source/portability-proof-round03/receipt.json').items()},
             provenance='Metadata-only measurement from saved/reopened round03 source, compared with exact9dff round01 baseline. No rendering, source save, captured art change, brief change, original delivery change, sealing or self-approval.',
             renders=renders)
write('validation.json',wrapper)
print(json.dumps(dict(status='metadata-only normalized',nativeRecords=native_records,measuredRootRecords=len(renders),projectSHA256=projectsha),indent=2))
