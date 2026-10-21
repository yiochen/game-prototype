"""Read-only project replay and one exact-frame reproducibility check."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-06'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc
root=bpy.data.objects['stool_wood__root.001'];cam=sc.camera
before=sha(Path(bpy.data.filepath));root.rotation_euler.z=0;sc.frame_set(1);sc.view_layers[0].update()
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return [p.x*384,(1-p.y)*704]
sc.render.filepath=str(OUT/'replay-S.png');bpy.ops.render.render(write_still=True,scene=sc.name)
replay={'project':str(Path(bpy.data.filepath).relative_to(BASE)),'projectSHA256':before,'projectUnchangedAfterReplay':sha(Path(bpy.data.filepath))==before,'scene':sc.name,'rootObject':root.name,'cameraObject':cam.name,'rootPixel':px((0,0,0)),'seatPixel':px((0,0,.655)),'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'renderEngine':sc.render.engine,'useCompositing':sc.render.use_compositing,'meshObjects':[o.name for o in sc.objects if o.type=='MESH'],'allObjects':len(sc.objects),'externalLibraries':[l.filepath for l in bpy.data.libraries],'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE'],'savedProjectSFrameSHA256':sha(OUT/'replay-S.png'),'submittedSFrameSHA256':sha(OUT/'raw/static-S-0000.png'),'pngFileByteExactReplay':sha(OUT/'replay-S.png')==sha(OUT/'raw/static-S-0000.png')}
(OUT/'validation-replay.json').write_text(json.dumps(replay,indent=2)+'\n');print(json.dumps(replay,indent=2))
