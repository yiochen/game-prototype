import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
base=Path(__file__).resolve().parents[1];path=base/'source/round-03.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
scene=bpy.data.scenes['stool-blue warm soft native'];bpy.context.window.scene=scene;root=bpy.data.objects['stool_blue__root.001'];bpy.context.view_layer.update()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pts=[];topology=[]
for o in scene.objects:
 if o.type=='MESH':
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();pts += [e.matrix_world@v.co for v in me.vertices];topology.append({'name':o.name,'vertices':len(me.vertices),'polygons':len(me.polygons)});e.to_mesh_clear()
def pixel(point):
 p=world_to_camera_view(scene,scene.camera,Vector(point));return [p.x*384,(1-p.y)*704]
record={'openedProject':'source/round-03.blend','projectSha256':sha(path),'scene':scene.name,'sceneCount':len(bpy.data.scenes),'root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'meshBounds':{'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]},'topology':topology,'partTransforms':[{'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale)} for o in scene.objects if o.type=='MESH'],'camera':{'name':scene.camera.name,'worldMatrix':[list(r) for r in scene.camera.matrix_world],'orthoScale':scene.camera.data.ortho_scale,'shift':[scene.camera.data.shift_x,scene.camera.data.shift_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'frame':[scene.render.resolution_x,scene.render.resolution_y]},'rootPixel':pixel((0,0,0)),'seatPixel':pixel((0,0,.685)),'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE'],'linkedLibraries':[l.filepath for l in bpy.data.libraries]}

import numpy as np,runpy,math
helper=runpy.run_path(str(base/'source/round-03.py'),run_name='round03_audit_helper');mapping=helper['mapping'];convention=helper['convention']
validation=json.loads((base/'candidates/round-03/validation.json').read_text());record['approvedRenderIdentitySignature']=helper['identity']();record['approvedGeometryMaterialsLightsUnchanged']=record['approvedRenderIdentitySignature']==validation['previousApprovedRound']['renderIdentitySignature']
def pixelhash(path):
 image=bpy.data.images.load(str(path),check_existing=False);array=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(array);digest=hashlib.sha256(array.tobytes()).hexdigest();bpy.data.images.remove(image);return digest
record['directionConvention']=convention;record['facings']={}
for d in ['N','E','S','W']:
 root.rotation_euler.z=mapping[d];bpy.context.view_layer.update();scene.frame_set(1);scene.render.filepath=str(base/f'candidates/round-03/reopened-{d}.png');bpy.ops.render.render(write_still=True)
 actual=pixelhash(scene.render.filepath);candidate=pixelhash(base/f'candidates/round-03/static-{d}.png');old_direction=convention['previousRoundCorrespondence'][d];previous=pixelhash(base/f'candidates/round-02/static-{old_direction}.png')
 record['facings'][d]={'path':f'candidates/round-03/reopened-{d}.png','sha256':sha(scene.render.filepath),'rotationDegrees':math.degrees(mapping[d]),'rotationRadians':mapping[d],'actualEvaluatedRootRadians':root.rotation_euler.z,'actualEvaluatedRootMatrix':[list(r) for r in root.matrix_world],'sourceConventionLine':convention['line'],'sourceConventionCode':convention['code'],'reopenedPixelHash':actual,'submittedPixelHash':candidate,'matchesSubmittedNPixels':actual==candidate,'matchesSubmittedPixels':actual==candidate,'round02Facing':old_direction,'round02PixelHash':previous,'matchesPriorApprovedFacingPixels':actual==previous}
record['reopenedNativeRender']=record['facings']['N'];record['allCandidateFacingsMatchReopenedNativeSource']=all(r['matchesSubmittedPixels'] for r in record['facings'].values());record['allCorrectedFacingsMatchPriorApprovedPixels']=all(r['matchesPriorApprovedFacingPixels'] for r in record['facings'].values());record['containerDifferenceNote']='PNG source-filename metadata may differ; decoded RGBA pixels are verified for every facing.'
(base/'candidates/round-03/reopened-source.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ['approvedGeometryMaterialsLightsUnchanged','allCandidateFacingsMatchReopenedNativeSource','allCorrectedFacingsMatchPriorApprovedPixels']}))
