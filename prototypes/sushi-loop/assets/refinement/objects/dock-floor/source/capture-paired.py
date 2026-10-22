"""Read saved standalone floor and append immutable entry in memory only."""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-03';PAIR=OBJ/'inputs/paired-native/dock-entry-round-05.blend'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(PAIR)=='ebdf5fc2add5399590bf8fad36b8ba59b6304a91505e999d07516066ac8c4ec5'
originalsha=sha(bpy.data.filepath);sc=bpy.context.scene;floor=bpy.data.objects['dock-floor__root']
with bpy.data.libraries.load(str(PAIR),link=False) as (src,dst):dst.collections=['S33_PROP_dock-entry']
entrycol=dst.collections[0];sc.collection.children.link(entrycol);entrycol.hide_render=False;entrycol.hide_viewport=False;entry=bpy.data.objects['dock-entry__root'];entry.location=(0,-1.5,0);bpy.context.view_layer.update()
# Dense native top/face sample correspondence at exact common plane.
def bvh(col):
 dg=bpy.context.evaluated_depsgraph_get();v=[];f=[]
 for o in col.all_objects:
  if o.type!='MESH' or o.hide_render:continue
  e=o.evaluated_get(dg);m=e.to_mesh();s=len(v);v += [e.matrix_world@p.co for p in m.vertices];f += [tuple(s+i for i in p.vertices) for p in m.polygons];e.to_mesh_clear()
 return BVHTree.FromPolygons(v,f,epsilon=1e-9),v,f
floor.rotation_euler=(0,0,0);entry.rotation_euler=(0,0,0);bpy.context.view_layer.update()
fb,fv,ff=bvh(bpy.data.collections['WarmSoft_dock-floor']);eb,ev,ef=bvh(entrycol)
profiles=[]
for i in range(163):
 x=-.405+.81*i/162
 fp,fn,_,_=fb.ray_cast(Vector((x,-1.5+1e-7,1)),Vector((0,0,-1)),2);ep,en,_,_=eb.ray_cast(Vector((x,-1.5-1e-7,1)),Vector((0,0,-1)),2)
 profiles.append({'x':x,'floorPoint':list(fp) if fp else None,'entryPoint':list(ep) if ep else None,'floorNormal':list(fn) if fn else None,'entryNormal':list(en) if en else None,'topMismatch':abs(fp.z-ep.z) if fp and ep else None})
cam=sc.camera;frame=(576,640);anchor=(288,352);sc.render.resolution_x=1152;sc.render.resolution_y=1280;cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*2-base.y)/dy;bpy.context.view_layer.update()
records=[]
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 R=Matrix.Rotation(a,3,'Z');floor.rotation_euler.z=a;entry.rotation_euler.z=a;entry.location=R@Vector((0,-1.5,0));bpy.context.view_layer.update();path=OUT/('native-pair-'+d+'.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 records.append({'direction':d,'path':str(path.relative_to(OBJ)),'sha256':sha(path),'rootRotationZ':floor.rotation_euler.z,'floorMatrix':[list(r) for r in floor.matrix_world],'entryMatrix':[list(r) for r in entry.matrix_world],'cameraMatrix':[list(r) for r in cam.matrix_world],'nativeFrame':[1152,1280],'logicalFrame':list(frame),'logicalRoot':list(anchor),'cameraProjection':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1152,y=1280,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)]})
report={'method':'Append immutable standalone entry into saved floor scene in memory only; use only saved floor camera/lights; no saved project modification','floor':{'path':str(Path(bpy.data.filepath).relative_to(OBJ)),'sha256':originalsha},'entry':{'path':str(PAIR.relative_to(OBJ)),'sha256':sha(PAIR)},'nativeProfiles':profiles,'maxProfileMismatch':max(p['topMismatch'] for p in profiles if p['topMismatch'] is not None),'missingProfileSamples':sum(p['topMismatch'] is None for p in profiles),'entryBoundsInSWorld':[[min(v[i] for v in ev) for i in range(3)],[max(v[i] for v in ev) for i in range(3)]],'nativeCaptures':records,'savedFloorUnchanged':sha(bpy.data.filepath)==originalsha}
(OUT/'paired-native-validation.json').write_text(json.dumps(report,indent=2));print('PAIR_NATIVE_MEASURED',report['maxProfileMismatch'],report['missingProfileSamples'],report['savedFloorUnchanged'])
