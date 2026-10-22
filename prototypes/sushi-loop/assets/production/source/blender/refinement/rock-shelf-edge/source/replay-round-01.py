"""One clean saved-source replay; no rebuild, source save or image repair."""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;EXP=BASE.parent;OUT=EXP/'candidates/round-01/replay-control';OUT.mkdir(exist_ok=True)
assert not (OUT/'pose-ledger.json').exists()
s=bpy.context.scene;root=bpy.data.objects['rock-shelf-edge__root'];coll=root.users_collection[0];cam=s.camera
source=BASE/'round-01.blend';assert Path(bpy.data.filepath).resolve()==source
expected=json.loads((EXP/'candidates/round-01/pose-ledger.json').read_text())['views']['S']['sourceProjectSHA256'];assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};pose_ledger={'sourceProjectSHA256':expected,'sourceResaved':False,'views':{}}
def camera(frame,anchor,scale=4):
 s.render.resolution_x=frame[0]*scale;s.render.resolution_y=frame[1]*scale;s.render.resolution_percentage=100;s.render.pixel_aspect_x=math.sqrt(1+.7*.7);s.render.pixel_aspect_y=1
 cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
 el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(s,cam,Vector(v));return Vector((p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*scale-base.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update()
 origin=px((0,0,0));record={'frame':list(frame),'anchor':list(anchor),'scale':scale,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'elevationDegrees':math.degrees(el),'orthoScale':cam.data.ortho_scale,'worldMatrix':[list(row) for row in cam.matrix_world],'projectionMatrix':[list(row) for row in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)],'calibration':{'root':list(origin),'unitX':list(px((1,0,0))-origin),'unitDepth':list(px((0,-1,0))-origin),'unitHeight':list(px((0,0,1))-origin)}}
 assert (origin-Vector((anchor[0]*scale,anchor[1]*scale))).length<.05
 return record

for d,angle in angles.items():
 root.rotation_euler.z=angle;bpy.context.view_layer.update();r=camera((192,352),(96,248));r.update(rootRotationZ=float(root.rotation_euler.z),rootMatrix=[list(row) for row in root.matrix_world]);pose_ledger['views'][d]=r;s.render.filepath=str(OUT/f'native-{d}-4x.png');bpy.ops.render.render(write_still=True)
root.rotation_euler.z=0;bpy.context.view_layer.update()
# Exact accepted middle is a distinct native input, used without regeneration.
approved=EXP/'inputs/approved-shelf-middle-v1/project.blend'
with bpy.data.libraries.load(str(approved),link=False) as (fr,to):
 to.collections=['rock-shelf-middle canonical LOW shelf']
middle=to.collections[0];s.collection.children.link(middle)
mr=next(ob for ob in middle.objects if ob.type=='EMPTY')
mr.rotation_euler.z=0;bpy.context.view_layer.update()
coll.hide_render=True
for d,angle in angles.items():
 mr.rotation_euler.z=angle;bpy.context.view_layer.update();r=camera((192,352),(96,248));r.update(direction=d,rootRotationZ=float(mr.rotation_euler.z),rootMatrix=[list(row) for row in mr.matrix_world],sourceProjectSHA256=hashlib.sha256(approved.read_bytes()).hexdigest());s.render.filepath=str(OUT/f'middle-native-{d}-4x.png');bpy.ops.render.render(write_still=True);(OUT/f'middle-camera-{d}.json').write_text(json.dumps(r,indent=2))
mr.rotation_euler.z=0;bpy.context.view_layer.update();middle.hide_render=True
assembly_records={}
for label,parts,fr,anchor in [
  ('strip',[(-1,middle),(0,coll),(1,middle)],(448,608),(224,376)),
  ('port-W',[(-1,middle),(0,coll)],(448,608),(224,376)),
  ('port-E',[(0,coll),(1,middle)],(448,608),(224,376)),
  ('extended',[(-2,middle),(-1,coll),(0,middle),(1,coll),(2,middle)],(704,864),(352,504))]:
 assembly=bpy.data.collections.new('capture_only_'+label);s.collection.children.link(assembly);ar=bpy.data.objects.new('capture_only_'+label+'_root',None);assembly.objects.link(ar)
 for offset,cc in parts:
  for original in list(cc.objects):
   if original.type!='MESH':continue
   ob=original.copy();ob.data=original.data;assembly.objects.link(ob);ob.parent=ar;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=original.matrix_world.copy();ob.location.x+=offset
 assembly_records[label]={}
 for d,angle in angles.items():
  ar.rotation_euler.z=angle;bpy.context.view_layer.update();r=camera(fr,anchor);r.update(direction=d,rootRotationZ=float(ar.rotation_euler.z),rootMatrix=[list(row) for row in ar.matrix_world],parts=[{'offset':off,'asset':'rock-shelf-edge' if cc==coll else 'rock-shelf-middle'} for off,cc in parts]);assembly_records[label][d]=r;s.render.filepath=str(OUT/f'native-{label}-{d}-4x.png');bpy.ops.render.render(write_still=True)
 assembly.hide_render=True
(OUT/'assembly-ledger.json').write_text(json.dumps(assembly_records,indent=2)+'\n')
(OUT/'pose-ledger.json').write_text(json.dumps(pose_ledger,indent=2)+'\n');print('ALL4 NATIVE CAPTURE COMPLETE')