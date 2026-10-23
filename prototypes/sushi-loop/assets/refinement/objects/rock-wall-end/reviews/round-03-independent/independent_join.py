import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).resolve().parent;BASE=OUT/'resources/experiment';DEST=OUT/'native-joined-reproduction';DEST.mkdir(exist_ok=True)
sc=bpy.context.scene;cam=sc.camera;root=bpy.data.objects['rock-wall-end__root'];root.rotation_euler=(0,0,0)
with bpy.data.libraries.load(str(BASE/'inputs/approved-middle/project.blend'),link=False) as(src,dst):dst.collections=['rock-wall-middle__asset']
mc=dst.collections[0];sc.collection.children.link(mc);mr=next(o for o in mc.objects if o.type=='EMPTY');mr.rotation_euler=(0,0,0)
assembly=bpy.data.objects.new('judge-common-pair-root',None);sc.collection.objects.link(assembly);root.parent=assembly;mr.parent=assembly;root.location=(.5,0,0);mr.location=(-.5,0,0)
bpy.data.objects['rock-wall-end__W_connector_stone'].hide_render=True
next(o for o in mc.objects if 'E_connector' in o.name).hide_render=True
sc.render.resolution_x=1280;sc.render.resolution_y=1920;cam.data.ortho_scale=2.5
def px(p):
 q=world_to_camera_view(sc,cam,Vector(p));return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
bpy.context.view_layer.update()
for _ in range(2):
 b=px((0,0,0));old=cam.data.shift_y;cam.data.shift_y=old+1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-b[1];cam.data.shift_y=old+(1280-b[1])/dy;bpy.context.view_layer.update()
audit={'method':'Exact saved end and immutable canonical middle native sources, symmetric canonical lighting. Common assembly rotated through all4; exact roots one unit apart; internal caps hidden only in ephemeral connected scene. No source saves, overlap, warps or view-specific treatment.','frame':[1280,1920],'nativeScale':4,'cameraRoot':px((0,0,0)),'endLocal':[.5,0,0],'middleLocal':[-.5,0,0],'rootPitch':1,'views':{}}
for d,deg in {'N':180,'E':90,'S':0,'W':-90}.items():
 assembly.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();sc.render.filepath=str(DEST/f'joined-{d}.png');bpy.ops.render.render(write_still=True);audit['views'][d]={'rotationDegrees':math.degrees(assembly.rotation_euler.z),'endRoot':[list(r) for r in root.matrix_world],'middleRoot':[list(r) for r in mr.matrix_world],'cameraRoot':px((0,0,0))}
(OUT/'independent-joined-audit.json').write_text(json.dumps(audit,indent=2)+'\n');print('JUDGE_NATIVE_JOINS_DONE')
