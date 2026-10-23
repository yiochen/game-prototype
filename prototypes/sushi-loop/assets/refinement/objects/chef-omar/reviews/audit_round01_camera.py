import bpy,json,pathlib,math,hashlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=pathlib.Path(__file__).resolve().parent.parent;out={};ref=json.loads((B/'inputs/source-camera.json').read_text())['camera']
for name,prefix,blend in [('catalog','','round-01.blend'),('runtimeVariants','runtime-','runtime-round-01.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(B/'source'/blend));r=json.loads((B/'source'/(prefix+'recipe-round01.json')).read_text());s=bpy.data.scenes[r['scene']];bpy.context.window.scene=s;bpy.context.window.view_layer=s.view_layers[0];s.view_layers[0].update();c=s.camera;root=bpy.data.objects[r['root']];coll=bpy.data.collections[r['collection']];arm=bpy.data.objects[r['armature']];dg=bpy.context.evaluated_depsgraph_get();proj=c.calc_matrix_camera(dg,x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)
 def px(v):
  p=world_to_camera_view(s,c,Vector(v));return [p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y]
 lights=[{'name':o.name,'type':o.data.type,'position':list(o.location),'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size} for o in s.objects if o.type=='LIGHT']
 old=arm.data.pose_position;arm.data.pose_position='REST';root.rotation_euler.z=0;s.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get();points=[]
 for o in coll.all_objects:
  if o.type=='MESH' and '__image_plane' not in o.name and '__knife_' not in o.name:
   e=o.evaluated_get(dg);points.extend(e.matrix_world@Vector(v) for v in e.bound_box)
 bounds=[[min(v[i] for v in points),max(v[i] for v in points)] for i in range(3)]
 out[name]={'source':str(B/'source'/blend),'sha256':hashlib.sha256((B/'source'/blend).read_bytes()).hexdigest(),'scene':s.name,'camera':c.name,'cameraWorldDifference':max(abs(c.matrix_world[i][j]-ref['worldMatrix'][i][j]) for i in range(4) for j in range(4)),'cameraProjectionDifference':max(abs(proj[i][j]-ref['projectionMatrix'][i][j]) for i in range(4) for j in range(4)),'nativeFrame':[s.render.resolution_x,s.render.resolution_y],'percentage':s.render.resolution_percentage,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'rootPixel':px((0,0,0)),'rootScale':list(root.scale),'rootLocation':list(root.location),'restActorBounds':bounds,'restHeight':bounds[2][1]-bounds[2][0],'lights':lights,'transparent':s.render.film_transparent,'engine':s.render.engine,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'frameRate':s.render.fps,'nonActorMeshes':[o.name for o in s.objects if o.type=='MESH' and o not in list(coll.all_objects)],'resourceAudit':'round-01-native-reopen-audit.json'}
(B/'reviews/round-01-camera-reopen-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
