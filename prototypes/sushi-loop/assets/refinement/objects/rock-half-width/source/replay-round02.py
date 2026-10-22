"""Read-only clean saved-source recapture with exact native image comparison."""
import bpy,json,pathlib,math,hashlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-02';project=P/'source/round-02.blend';before=hashlib.sha256(project.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(project));sc=bpy.context.scene;root=bpy.data.objects['rock-half-width__root.001'];ledger=[]
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(a);sc.frame_set(1);bpy.context.view_layer.update();p=O/f'replay/{d}.png';p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 ledger.append({'direction':d,'path':str(p.relative_to(P)),'actualRootMatrix':[list(r) for r in root.matrix_world],'rootRotationDegrees':math.degrees(root.rotation_euler.z),'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'filterSize':sc.render.filter_size,'cameraMatrix':[list(r) for r in sc.camera.matrix_world],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'originalRawSHA256':hashlib.sha256((O/f'native/static/{d}/000.png').read_bytes()).hexdigest(),'replayRawSHA256':hashlib.sha256(p.read_bytes()).hexdigest()})
(O/'replay/ledger.json').write_text(json.dumps({'projectSHA256':before,'projectUnchanged':before==hashlib.sha256(project.read_bytes()).hexdigest(),'renders':ledger,'savedSourceSettings':{'engine':sc.render.engine,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'dither':sc.render.dither_intensity,'transparent':sc.render.film_transparent,'fps':sc.render.fps,'frame':sc.frame_current,'colorMode':sc.render.image_settings.color_mode,'colorDepth':sc.render.image_settings.color_depth}},indent=2)+'\n')
print(json.dumps({'renders':4,'projectUnchanged':before==hashlib.sha256(project.read_bytes()).hexdigest()}))
