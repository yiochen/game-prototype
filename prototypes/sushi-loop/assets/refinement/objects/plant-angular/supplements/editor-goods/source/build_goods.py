"""Immutable native camera-only plant goods round. No production reads or writes."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Matrix
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;sys.path.insert(0,str(HERE))
from native_state import state,camera_record,normalize_static,ensure_visible
OUT=BASE/'candidates/round-01';OUT.mkdir(parents=True,exist_ok=True)
project=HERE/'round-01.blend';assert not project.exists() and not (OUT/'goods.png').exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=BASE/'inputs/approved-world-model.blend';contract=BASE/'inputs/camera-contract.json'
assert sha(source)=='1d9bc1fa321e705154e2c36fec41fd4092ba843f233d938f02b69e761881837c'
assert sha(BASE/'reviews/criteria.json')=='64a41de342b3a5882c7fdd6d65310afb2722bcf328fe4b196be745149291ec5e'
bpy.ops.wm.open_mainfile(filepath=str(source))
normalization=normalize_static();ensure_visible();before=state();old_camera=camera_record()
cam=json.loads(contract.read_text());s=bpy.context.scene;c=s.camera
c.matrix_world=Matrix(cam['world_matrix']);c.data.ortho_scale=cam['ortho_scale'];c.data.shift_x=0;c.data.shift_y=0
s.render.resolution_x=384;s.render.resolution_y=384;s.render.resolution_percentage=100
s.render.pixel_aspect_x=1;s.render.pixel_aspect_y=1
bpy.context.view_layer.update();after=state();actual=camera_record()
assert before['sectionHashes']==after['sectionHashes']
errors={k:max(abs(actual[k][i][j]-cam[k][i][j]) for i in range(4) for j in range(4)) for k in ('world_matrix','projection_matrix')}
assert all(v<1e-6 for v in errors.values()) and actual['ortho_scale']==cam['ortho_scale']
assert after['meshCount']==14 and not any(after['dependencies'].values())
s.render.filepath=str(OUT/'goods.png')
bpy.ops.wm.save_as_mainfile(filepath=str(project),compress=True)
bpy.ops.render.render(write_still=True)
receipt={'sourceProject':'inputs/approved-world-model.blend','sourceSHA256':sha(source),
 'savedProject':'source/round-01.blend','savedProjectSHA256':sha(project),'source':before,'candidate':after,
 'normalization':normalization,'approvedWorldCamera':old_camera,'goodsCamera':actual,'lockedCamera':cam,'cameraMaximumErrors':errors,
 'allowedChanges':['Select original12static actions/originalKey slots at key1; rootS0 identity','Camera world matrix/orthographic scale/zero shift','Render384square/square pixels100percent','Outputfilepath/saved-project filepath'],
 'checks':{'baseAndEvaluatedMeshesTransformsModifiersShapesIdentical':before['sectionHashes']['objects']==after['sectionHashes']['objects'],
 'completeActionKeySlotCurveDataIdentical':before['sectionHashes']['actions']==after['sectionHashes']['actions'],
 'materialsIdentical':before['sectionHashes']['materials']==after['sectionHashes']['materials'],
 'lightsIdentical':before['sectionHashes']['lights']==after['sectionHashes']['lights'],
 'worldCompositorDisplayAndRenderResponseIdentical':before['sectionHashes']['pipeline']==after['sectionHashes']['pipeline'],
 'cameraWithin1e6':all(e<1e-6 for e in errors.values()),'native14Meshes':after['meshCount']==14,
 'selfContainedNoExternalImagesOrLibraries':not any(after['dependencies'].values()),'sourceBytesPreserved':sha(source)=='1d9bc1fa321e705154e2c36fec41fd4092ba843f233d938f02b69e761881837c'},
 'nativeRenderSHA256':sha(OUT/'goods.png')}
(OUT/'native-parity.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'source':str(project),'render':str(OUT/'goods.png'),'checks':receipt['checks'],'cameraErrors':errors}))
