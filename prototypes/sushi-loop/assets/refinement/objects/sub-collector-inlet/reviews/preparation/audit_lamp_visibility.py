import bpy,pathlib,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
O=pathlib.Path(__file__).resolve().parent;s=bpy.context.scene;root=bpy.data.objects['submarine-yellow__root'];col=bpy.data.collections['S33_PROP_collector_inlet.001'];own=set(col.all_objects);cam=s.camera
lamps=['body__nose_lamp_lens','body__bumper_lamp_-1','body__bumper_lamp_1']
def make(objects,dg):
 pts=[];polys=[];names=[]
 for o in objects:
  if o.type!='MESH' or o.hide_render:continue
  eo=o.evaluated_get(dg);me=eo.to_mesh();off=len(pts);pts.extend(eo.matrix_world@v.co for v in me.vertices)
  for f in me.polygons:polys.append([off+i for i in f.vertices]);names.append(o.name)
  eo.to_mesh_clear()
 return BVHTree.FromPolygons(pts,polys,all_triangles=False),names
records=[]
for di,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=a;s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();baseline=[o for o in s.objects if o not in own and not o.name.startswith('PROVISIONAL__collector')];bv,names=make(baseline,dg);cv,_=make(own,dg);proj=cam.calc_matrix_camera(dg,x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y).inverted();direction=-(cam.matrix_world.to_3x3()@Vector((0,0,1))).normalized();counts={name:{'baselineVisibleRaySamples':0,'occludedByOriginalCollector':0} for name in lamps}
 for name in lamps:
  o=bpy.data.objects[name];eo=o.evaluated_get(dg);me=eo.to_mesh();coords=[world_to_camera_view(s,cam,eo.matrix_world@v.co) for v in me.vertices];eo.to_mesh_clear();xs=[p.x*s.render.resolution_x for p in coords];ys=[(1-p.y)*s.render.resolution_y for p in coords]
  for y in range(max(0,math.floor(min(ys))-1),min(s.render.resolution_y,math.ceil(max(ys))+1)):
   for x in range(max(0,math.floor(min(xs))-1),min(s.render.resolution_x,math.ceil(max(xs))+1)):
    p=proj@Vector((2*(x+.5)/s.render.resolution_x-1,1-2*(y+.5)/s.render.resolution_y,-1,1));p/=p.w;origin=cam.matrix_world@p.to_3d();hit=bv.ray_cast(origin,direction)
    if hit[0] is None or names[hit[2]]!=name:continue
    counts[name]['baselineVisibleRaySamples']+=1;ch=cv.ray_cast(origin,direction)
    if ch[0] is not None and ch[3]<hit[3]-1e-6:counts[name]['occludedByOriginalCollector']+=1
 records.append({'direction':di,'lensCounts':counts})
(O/'lamp-visibility-source-audit.json').write_text(json.dumps({'method':'Independent evaluated native BVH pixel-center orthographic rays at registered main640x768 capture. Baseline excludes collector cohort only; test adds original neutral collector at frozen mount. Baseline-visible lamp samples are compared with collector ray distance. No material edit or diagnostic geometry.','qualification':'Preparation source evidence only. This visibility audit must be repeated on exact neutral candidate; native distance/intersection clearance is separate. Lamps naturally hidden by body in a facing do not require invention of a new visible lamp.','records':records},indent=2)+'\n');print(json.dumps(records,indent=2))
