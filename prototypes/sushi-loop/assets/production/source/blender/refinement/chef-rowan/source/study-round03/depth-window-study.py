"""Round03 diagnostic only: common depth range, no saved model/full192 captures."""
import bpy,math,json,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).parent;OBJ=HERE.parents[1];OUT=HERE/'renders';OUT.mkdir(exist_ok=True)
BASE='9dffcad37fb5ba662000a919c355fe45e74416078371e82adf2aa012038be024'
assert hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()==BASE
rig=json.loads((OBJ/'inputs/source-rig.json').read_text())
spec=importlib.util.spec_from_file_location('native',OBJ/'source/resources/original-native-actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
def init():
 global scene,root,col,arm,food,plane,asset
 scene=bpy.context.scene;root=bpy.data.objects[rig['groundRootObject']];col=bpy.data.collections['S33_CHARACTER_chef_rowan.001'];arm=bpy.data.objects[rig['armatures'][0]['object']]
 col.hide_viewport=False;col.hide_render=False;arm.hide_set(False)
 def unhide(lc):
  lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_viewport=False
  for c in lc.children:unhide(c)
 unhide(bpy.context.view_layer.layer_collection);bpy.context.view_layer.update()
 food=bpy.data.objects[root.name+'__held_dish-salmon'];plane=bpy.data.objects[food.name+'__image_plane'];asset=dict(root=root,collection=col)
init()
def depth(d):
 k=d/root.scale.x*math.cos(math.radians(35));plane.location.z=d/root.scale.x*math.sin(math.radians(35))
 for f in plane.animation_data.drivers:
  if f.data_path=='location':f.driver.expression=f'-{"sin" if f.array_index==0 else "cos"}(facing)*{k!r}'
 plane['camera_ray_depth_bias_world_cells']=d;bpy.context.view_layer.update()
def samples():
 records=[]
 for clip in rig['clips']:
  for direction in ['N','E','S','W']:
   for frame in range(1,13):
    native.apply_clip(asset,rig,clip,frame,direction,scene);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();m=plane.evaluated_get(dg).matrix_world
    points=[m@v.co for v in plane.data.vertices]+[m@Vector((0,0,0))]
    pixels=[]
    for p in points:
     q=world_to_camera_view(scene,scene.camera,p);pixels.append([q.x*384,(1-q.y)*640])
    records.append(dict(clip=clip,direction=direction,frame=frame,world=[list(p) for p in points],pixels=pixels))
 return records
baseline=samples();records=[];projection=[]
poses=[('hold',1),('hold',4),('hold',10),('load',1),('load',6),('load',7),('load',12)]
for d in [.50,.525,.55,.575]:
 bpy.ops.wm.open_mainfile(filepath=str(OBJ/'inputs/baseline-round01.blend'));init();depth(d)
 variants=HERE/'variants';variants.mkdir(exist_ok=True);variant=variants/f'd{round(d*1000):03}.blend'
 bpy.ops.wm.save_as_mainfile(filepath=str(variant),relative_remap=False)
 bpy.ops.wm.open_mainfile(filepath=str(variant));init();measured=samples();ray=Vector((0,-math.cos(math.radians(35)),math.sin(math.radians(35))))*(d-.6)
 pixelerr=max(abs(a-b) for old,new in zip(baseline,measured) for p,q in zip(old['pixels'],new['pixels']) for a,b in zip(p,q));rayerr=max((Vector(n)-Vector(o)-ray).length for old,new in zip(baseline,measured) for o,n in zip(old['world'],new['world']))
 print('PROJECTION',d,pixelerr,rayerr,flush=True)
 assert pixelerr<.0001 and rayerr<1e-6
 projection.append(dict(depth=d,poseCount=len(measured),maxNativePixelError=pixelerr,maxRayDisplacementError=rayerr,localZ=plane.location.z,localHorizontalCoefficient=d/root.scale.x*math.cos(math.radians(35))))
 for clip,frame in poses:
  for direction in ['N','E','S','W']:
   native.apply_clip(asset,rig,clip,frame,direction,scene);bpy.context.view_layer.update()
   path=OUT/f'd{round(d*1000):03}-{clip}-{direction}-{frame:02}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   records.append(dict(d=d,clip=clip,frame=frame,index=frame-1,direction=direction,path=str(path.relative_to(OBJ))));print('STUDY',d,clip,direction,frame,flush=True)
report=dict(activeBrief='brief-v3-food-depth.json',baseline='inputs/baseline-round01.blend',baselineSHA256=BASE,scope='Diagnostic saved depth variants only. Each reopens the exact same baseline; only permitted globally shared ray depth, derived planeZ and existing depth property changed. No192 capture or per-view modification.',depthValues=[.5,.525,.55,.575],poses=poses,projection=projection,renders=records)
(HERE/'study-records.json').write_text(json.dumps(report,indent=2)+'\n')
