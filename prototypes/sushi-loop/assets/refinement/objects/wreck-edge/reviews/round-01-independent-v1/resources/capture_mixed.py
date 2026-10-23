import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Euler
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
RES=Path(__file__).resolve().parent;OBJ=RES.parents[2];OUT=RES.parent/'mixed-recapture';OUT.mkdir(exist_ok=True)
sc=bpy.context.scene;edge=bpy.data.objects['wreck-edge__root']
with bpy.data.libraries.load(str(RES/'native/canonical-middle02.blend'),link=False) as (src,dst):dst.collections=['Wreck middle authored candidate']
col=dst.collections[0];sc.collection.children.link(col);col.hide_render=False;col.hide_viewport=False;middle=next(o for o in col.objects if o.name.startswith('wreck-middle__root'));objects=list(col.objects);records=[]
for d,ang in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 edge.rotation_euler.z=ang;edge.location=(0,0,0);middle.rotation_euler.z=ang;middle.location=Vector((-1,0,0));middle.location.rotate(Euler((0,0,ang)));cp={}
 for ob in objects:cp[ob]=ob.copy();col.objects.link(cp[ob])
 for ob,cl in cp.items():cl.parent=cp.get(ob.parent);cl.matrix_parent_inverse=ob.matrix_parent_inverse.copy()
 other=cp[middle];other.rotation_euler.z=ang;other.location=Vector((1,0,0));other.location.rotate(Euler((0,0,ang)))
 vertical=d in ['E','W'];frame=(192,608) if vertical else (448,352);anchor=(96,376) if vertical else (224,248);cam=sc.camera;sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*2-base.y)/dy;bpy.context.view_layer.update()
 p=OUT/(d+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 records.append({'direction':d,'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'canonicalSourceSHA256':hashlib.sha256((RES/'native/canonical-middle02.blend').read_bytes()).hexdigest(),'roots':{k:[list(r) for r in o.matrix_world] for k,o in [('edge',edge),('middleMinus1',middle),('middlePlus1',other)]},'cameraMatrix':[list(r) for r in cam.matrix_world],'ortho':cam.data.ortho_scale,'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'projectedRoot':list(px((0,0,0))),'unitX':list(px((1,0,0))-px((0,0,0))),'unitDepth':list(px((0,-1,0))-px((0,0,0))),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 for o in cp.values():bpy.data.objects.remove(o,do_unlink=True)
(RES.parent/'mixed-recapture-records.json').write_text(json.dumps(records,indent=2)+'\n');print('OWN_MIXED_RECAPTURE_COMPLETE')
