"""One ordinary clean-saved-source all4+strip control. No source resave or retries."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent.parent;O=B/'candidates/round-03/replay-control';SOURCE=B/'source/round-03.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (O/'pose-ledger.json').exists();assert Path(bpy.data.filepath).resolve()==SOURCE
expected=json.loads((B/'candidates/round-03/pose-ledger.json').read_text())['views']['S']['sourceProjectSHA256'];assert sha(SOURCE)==expected
s=bpy.context.scene;root=bpy.data.objects['rock-shelf-middle__root'];cam=s.camera
collection=root.users_collection[0];parts=[o for o in collection.all_objects if o.type=='MESH']
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};ledger={'asset':'rock-shelf-middle','round':'round-03','purpose':'One unchanged clean-reopen empirical native replay control; no universal bitidentity claim','sourceProjectSHA256':expected,'views':{},'strips':{}}
def measure(rr,frame,anchor):
 bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();er=rr.evaluated_get(dep)
 def px(p):
  v=world_to_camera_view(s,cam,Vector(p));return Vector((v.x*s.render.resolution_x,(1-v.y)*s.render.resolution_y))
 origin=px((0,0,0))
 return {'rootRotationZ':float(rr.rotation_euler.z),'rootMatrix':[list(row) for row in er.matrix_world],'nativeFrame':s.frame_current,'fps':s.render.fps,'logicalFrame':frame,'logicalRoot':anchor,'captureScale':4,'rasterFrame':[s.render.resolution_x,s.render.resolution_y],'camera':{'type':cam.data.type,'sensorFit':cam.data.sensor_fit,'orthoScale':cam.data.ortho_scale,'worldMatrix':[list(row) for row in cam.matrix_world],'projectionMatrix':[list(row) for row in cam.calc_matrix_camera(dep,x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]},'calibration':{'root':list(origin),'unitX':list(px((1,0,0))-origin),'unitDepth':list(px((0,-1,0))-origin),'unitHeight':list(px((0,0,1))-origin)},'filterSize':s.render.filter_size,'samples':s.eevee.taa_render_samples}
for d,a in angles.items():
 root.rotation_euler.z=a;s.frame_set(1);rec=measure(root,[192,352],[96,248]);path=O/f'native-{d}-4x.png';assert not path.exists();s.render.filepath=str(path);bpy.ops.render.render(write_still=True);rec.update(path=str(path.relative_to(B)),sha256=sha(path));ledger['views'][d]=rec
root.rotation_euler.z=0;bpy.context.view_layer.update()
ac=bpy.data.collections.new('replay-only-3middle');s.collection.children.link(ac);ar=bpy.data.objects.new('replay-strip-root',None);ac.objects.link(ar)
for k in (-1,0,1):
 for source in parts:
  o=source.copy();o.data=source.data;ac.objects.link(o);o.parent=ar;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=source.matrix_world.copy();o.location.x+=k
collection.hide_render=True
# Exact original joined registration; preserve all source render/material/light settings.
s.render.resolution_x=448*4;s.render.resolution_y=608*4;cam.data.ortho_scale=448/128;cam.data.shift_y=0;cam.data.shift_x=0;bpy.context.view_layer.update()
def pp(p):
 v=world_to_camera_view(s,cam,Vector(p));return Vector((v.x*s.render.resolution_x,(1-v.y)*s.render.resolution_y))
base=pp((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();delta=pp((0,0,0)).y-base.y;cam.data.shift_y=(376*4-base.y)/delta;bpy.context.view_layer.update()
for d,a in angles.items():
 ar.rotation_euler.z=a;rec=measure(ar,[448,608],[224,376]);path=O/f'strip-{d}-4x.png';assert not path.exists();s.render.filepath=str(path);bpy.ops.render.render(write_still=True);rec.update(path=str(path.relative_to(B)),sha256=sha(path));ledger['strips'][d]=rec
ledger['sourceSHAAfter']=sha(SOURCE);ledger['sourceResaved']=False;assert ledger['sourceSHAAfter']==expected
(O/'pose-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n');print(json.dumps({'sourceSHA256':expected,'sourceResaved':False,'all4ActualRotations':{d:r['rootRotationZ'] for d,r in ledger['views'].items()}},indent=2))
