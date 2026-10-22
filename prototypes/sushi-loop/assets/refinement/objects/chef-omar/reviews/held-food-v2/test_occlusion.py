"""Read-only analytic canonical-plane occlusion test; does not edit geometry or save .blend."""
import bpy,pathlib,json,hashlib,importlib.util,sys,math,array
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
B=pathlib.Path(__file__).resolve().parents[2];R=B/'reviews/held-food-v2';H=B.parents[2]/'production/source/blender';brief=json.loads((B/'brief-v2-held-food.json').read_text())
s=importlib.util.spec_from_file_location('omar_v2_occ_native',H/'native_actions.py');native=importlib.util.module_from_spec(s);sys.modules[s.name]=native;s.loader.exec_module(native)
results={}
for name,project,rp,gp,clip,key in [('salmon',B/'../../../production/source/blender/refinement/chef-omar/source/round-01.blend',B/'source/recipe-round01.json',B/'source/rig-round01.json','hold','foodDependency'),('cucumber',B/'source/runtime-round-01.blend',B/'source/runtime-recipe-round01.json',B/'source/runtime-rig-round01.json','hold-cucumber','runtimeVariantFoodDependency')]:
 bpy.ops.wm.open_mainfile(filepath=str(project.resolve()));recipe=json.loads(rp.read_text());rig=json.loads(gp.read_text());sc=bpy.data.scenes[recipe['scene']];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];coll=bpy.data.collections[recipe['collection']];root=bpy.data.objects[recipe['root']];native.apply_clip({'root':root,'collection':coll},rig,clip,6,'N',sc);dg=bpy.context.evaluated_depsgraph_get();plane=next(o for o in coll.all_objects if '__image_plane' in o.name);M=plane.evaluated_get(dg).matrix_world.copy();cam=sc.camera;forward=(cam.matrix_world.to_3x3()@Vector((0,0,-1))).normalized()
 verts=[];polys=[]
 for o in coll.all_objects:
  if o.type!='MESH' or o==plane or o.hide_render:continue
  e=o.evaluated_get(dg);me=e.to_mesh();offset=len(verts);verts.extend(e.matrix_world@v.co for v in me.vertices);polys.extend(tuple(offset+i for i in p.vertices) for p in me.polygons);e.to_mesh_clear()
 bvh=BVHTree.FromPolygons(verts,polys,all_triangles=False);dep=brief[key];im=bpy.data.images.load(str((B/dep['artwork']).resolve()),check_existing=False);w,h=im.size;px=array.array('f',[0])*(w*h*4);im.pixels.foreach_get(px);width=max(v.co.x for v in plane.data.vertices)-min(v.co.x for v in plane.data.vertices);height=width*h/w
 visible=[];overlay=[];sampled=0;occluded=0
 def project_point(v):
  p=world_to_camera_view(sc,cam,v);return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
 for y in range(2,h,4):
  for x in range(2,w,4):
   if px[(y*w+x)*4+3]<.5:continue
   sampled+=1;point=M@Vector((((x+.5)/w-.5)*width,((y+.5)/h)*height,0));hit,normal,face,dist=bvh.ray_cast(point-forward*10,forward,20)
   if hit is not None and dist<10-1e-5:occluded+=1;continue
   uv=project_point(point);visible.append(uv)
   hit2,normal2,face2,dist2=bvh.ray_cast(point+forward*1e-4,forward,2)
   if hit2 is not None:overlay.append(uv)
 def bounds(xs):return [[min(v[i] for v in xs),max(v[i] for v in xs)] for i in range(2)] if xs else None
 results[name]={'sourceSHA256':hashlib.sha256(project.read_bytes()).hexdigest(),'method':'At original hold N frame05, map approved canonical alpha samples to the mathematically required fullUV plane at unchanged source width/origin/matrix, new aspect height; ray-test against evaluated opaque native actor only. No geometry/image-node change and no canonical candidate rendering. Sampling stride4, alpha>=0.5. Overlay samples are in front of an actor surface rather than hidden behind it.','sampledOpaquePixels':sampled,'occludedSamples':occluded,'visibleSamples':len(visible),'visibleProjectedBounds':bounds(visible),'frontOfActorSamples':len(overlay),'frontOfActorProjectedBounds':bounds(overlay),'expectedNativeLocalWidth':width,'expectedNativeLocalHeight':height,'canonicalSize':[w,h]}
(R/'canonical-source-law-occlusion-test.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
