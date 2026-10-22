import sys
sys.dont_write_bytecode=True
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parent;EXP=BASE.parent;OUT=EXP/'candidates/round-01'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'round-01.blend'))
s=bpy.context.scene;root=bpy.data.objects['rock-shelf-end__root'];coll=root.users_collection[0];core=bpy.data.objects['rock-shelf-end__rounded_shelf'];cam=s.camera
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def camera(frame=(192,352),anchor=(96,248),scale=4):
 s.render.resolution_x=frame[0]*scale;s.render.resolution_y=frame[1]*scale;s.render.resolution_percentage=100;s.render.pixel_aspect_x=math.sqrt(1+.7*.7);s.render.pixel_aspect_y=1
 cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
 el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(s,cam,Vector(v));return Vector((p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*scale-base.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update();origin=px((0,0,0))
 return {'frame':list(frame),'anchor':list(anchor),'captureScale':scale,'nativeFrame':[frame[0]*scale,frame[1]*scale],'filterSize':s.render.filter_size,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'elevationDegrees':math.degrees(el),'camera':{'type':'orthographic','worldMatrix':[list(row) for row in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]},'calibration':{'root':list(origin),'unitX':list(px((1,0,0))-origin),'unitDepth':list(px((0,-1,0))-origin),'unitHeight':list(px((0,0,1))-origin)},'fps':s.render.fps}
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};ledger={'views':{},'family':{},'canonicalMiddle':{}}
for d,a in angles.items():
 root.rotation_euler.z=a;bpy.context.view_layer.update();r=camera();r.update(direction=d,rootRotationZ=root.rotation_euler.z,rootMatrix=[list(row) for row in root.matrix_world],sourceProjectSHA256=h(BASE/'round-01.blend'),nativeFrameNumber=s.frame_current)
 p=OUT/f'native/static/{d}/000.png';p.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True);ledger['views'][d]=r
root.rotation_euler.z=0;bpy.context.view_layer.update()
# Append exact normative middle objects; no rebuilding of neighboring geometry.
with bpy.data.libraries.load(str(BASE/'resources/canonical-middle03.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('rock-shelf-middle__')]
mc=bpy.data.collections.new('capture_only_exact_canonical_middle03');s.collection.children.link(mc)
for ob in dst.objects:
 if ob:mc.objects.link(ob)
mr=next(o for o in mc.objects if o.type=='EMPTY')
for d,a in angles.items():
 coll.hide_render=True;mc.hide_render=False;mr.location=(0,0,0);mr.rotation_euler.z=a;bpy.context.view_layer.update();r=camera();r.update(direction=d,rootRotationZ=mr.rotation_euler.z,rootMatrix=[list(row) for row in mr.matrix_world],sourceProjectSHA256=h(BASE/'resources/canonical-middle03.blend'));p=OUT/f'canonical-middle/native/{d}.png';p.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True);ledger['canonicalMiddle'][d]=r
mr.rotation_euler.z=0;coll.hide_render=False;mc.hide_render=False;bpy.context.view_layer.update()
plan=json.loads((BASE/'resources/evidence-plan.json').read_text())['minimumCandidateNative']['assemblies']
assembly=bpy.data.collections.new('capture_only_family_instances');s.collection.children.link(assembly)
def instance(asset,direction,location):
 source=coll if asset=='candidate-end' else mc;rr=bpy.data.objects.new('instance_'+asset,None);assembly.objects.link(rr);rr.location=location;rr.rotation_euler.z=angles[direction]
 for original in source.objects:
  if original.type!='MESH':continue
  ob=original.copy();ob.data=original.data;assembly.objects.link(ob);ob.parent=rr;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=original.matrix_basis.copy()
 return rr
for d in angles:
 for kind in ['pair','closedRun']:
  for ob in list(assembly.objects):bpy.data.objects.remove(ob,do_unlink=True)
  coll.hide_render=True;mc.hide_render=True
  roots=[instance(p['asset'],p['direction'],p['rootNative']) for p in plan[d][kind]];bpy.context.view_layer.update();r=camera((448,608),(224,376));r['instances']=[{'name':o.name,'rootMatrix':[list(row) for row in o.matrix_world]} for o in roots]
  p=OUT/f'family-native/{kind}-{d}.png';p.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True);ledger['family'][kind+'-'+d]=r
write(OUT/'capture-ledger.json',ledger)
write(OUT/'native-camera.json',ledger['views']['S'])
print('CAPTURE COMPLETE',flush=True)
