"""Blender --background --python source/build_goods.py. Creates one immutable goods round."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Matrix
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;sys.path.insert(0,str(HERE))
from native_state import state,camera_record
OUT=BASE/'candidates/round-01';OUT.mkdir(parents=True,exist_ok=True)
project=HERE/'round-01.blend';assert not project.exists() and not (OUT/'goods.png').exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=BASE/'inputs/approved-world-model.blend';contract=BASE/'inputs/camera-contract.json'
assert sha(source)=='fc1e870d0675150bf4cb8a2fa78b0c17c3a060546e7b89a1618db97d11de22de'
bpy.ops.wm.open_mainfile(filepath=str(source));before=state();old_camera=camera_record()
root=bpy.data.objects['stool_wood__root.001'];assert list(root.location)==[0,0,0] and list(root.rotation_euler)==[0,0,0] and list(root.scale)==[1,1,1]
cam=json.loads(contract.read_text());s=bpy.context.scene;c=s.camera
c.matrix_world=Matrix(cam['world_matrix']);c.data.ortho_scale=cam['ortho_scale'];c.data.shift_x=0;c.data.shift_y=0
s.render.resolution_x=384;s.render.resolution_y=384;s.render.resolution_percentage=100;s.render.pixel_aspect_x=1;s.render.pixel_aspect_y=1
bpy.context.view_layer.update();after=state();actual=camera_record()
assert before['sectionHashes']==after['sectionHashes']
errors={k:max(abs(actual[k][i][j]-cam[k][i][j]) for i in range(4) for j in range(4)) for k in ('world_matrix','projection_matrix')}
assert all(e<1e-6 for e in errors.values()) and actual['ortho_scale']==cam['ortho_scale']
assert after['meshCount']==11 and not any(after['dependencies'].values())
s.render.filepath=str(OUT/'goods.png')
bpy.ops.wm.save_as_mainfile(filepath=str(project),compress=True)
bpy.ops.render.render(write_still=True)
(OUT/'native-parity.json').write_text(json.dumps({'sourceProject':'inputs/approved-world-model.blend','sourceSHA256':sha(source),'savedProject':'source/round-01.blend','savedProjectSHA256':sha(project),'source':before,'candidate':after,'approvedWorldCamera':old_camera,'goodsCamera':actual,'lockedCamera':cam,'cameraMaximumErrors':errors,'allowedChanges':['Camera world matrix/orthographic scale/zero shift','Render dimensions384x384/square pixels at100percent','Outputfilepath and saved-project filepath only'],'checks':{'geometryModifiersUVTransformsParentingUnchanged':before['sectionHashes']['objects']==after['sectionHashes']['objects'],'materialGraphsBindingsUnchanged':before['sectionHashes']['materials']==after['sectionHashes']['materials'],'lightsUnchanged':before['sectionHashes']['lights']==after['sectionHashes']['lights'],'nativePipelineWorldColorUnchanged':before['sectionHashes']['pipeline']==after['sectionHashes']['pipeline'],'cameraWithin1e-6':all(e<1e-6 for e in errors.values()),'native11Meshes':after['meshCount']==11,'selfContainedNoImagesOrLibraries':not any(after['dependencies'].values())},'sourceSHA256After':sha(source),'sourceUnchanged':sha(source)=='fc1e870d0675150bf4cb8a2fa78b0c17c3a060546e7b89a1618db97d11de22de','rootAlreadyIdentityS0':True,'nativeRenderSHA256':sha(OUT/'goods.png')},indent=2)+'\n')
print(json.dumps({'project':str(project),'nativeRender':str(OUT/'goods.png'),'parity':before['sectionHashes']==after['sectionHashes'],'cameraErrors':errors}))
