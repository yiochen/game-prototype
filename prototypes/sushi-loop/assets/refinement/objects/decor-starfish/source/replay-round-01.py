"""Render all four static facings from a reopened self-contained saved scene.
blender -b source/round-01.blend --python source/replay-round-01.py -- /absolute/output
No original project, PNG, target or other helper dependency is required.
"""
import bpy,math,sys,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(bpy.data.filepath).resolve().parent.parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=Path(args[0]).resolve() if args else BASE/'candidates/round-01';OUT.mkdir(parents=True,exist_ok=True)
sc=bpy.context.scene;root=bpy.data.objects[sc['sourceRootObject']];col=bpy.data.collections[sc['assetCollection']]
def rows(m):return [list(r) for r in m]
def measure():
 dep=bpy.context.evaluated_depsgraph_get();pts=[]
 for o in col.all_objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(dep);me=ev.to_mesh();pts += [ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
 return {'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)],'radialMax':max(math.hypot(p.x,p.y) for p in pts)}
records={}
for d,angle in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(angle);sc.frame_set(1);bpy.context.view_layer.update()
 records[d]={'clip':'static','sourceClipId':'idle','direction':d,'index':0,'nativeFrame':1,'rootMatrix':rows(root.matrix_world),'bounds':measure(),'path':f'native-static-{d}.png'}
 sc.render.filepath=str(OUT/f'native-static-{d}.png');bpy.ops.render.render(write_still=True)
root.rotation_euler.z=0;bpy.context.view_layer.update()
cam=sc.camera;dep=bpy.context.evaluated_depsgraph_get()
def px(p):
 q=world_to_camera_view(sc,cam,Vector(p));return Vector((q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y))
r=px((0,0,0))
camera={'projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'cellSize':128,'captureScale':4,'nativeCaptureScale':4,'fps':12,'camera':{'type':'orthographic','name':cam.name,'worldMatrix':rows(cam.matrix_world),'projectionMatrix':rows(cam.calc_matrix_camera(dep,x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'worldUnitsPerCell':1,'elevationDegrees':math.degrees(math.asin(cam.matrix_world[2][2])),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]},'calibration':{'root':list(r),'unitX':list(px((1,0,0))-r),'unitDepth':list(px((0,-1,0))-r),'unitHeight':list(px((0,0,1))-r)},'render':{'resolution':[sc.render.resolution_x,sc.render.resolution_y],'engine':sc.render.engine,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'transparent':sc.render.film_transparent},'views':records}
(OUT/'native-capture.json').write_text(json.dumps(camera,indent=2)+'\n')
print('NATIVE_CAPTURE_COMPLETE '+str(OUT),flush=True)
