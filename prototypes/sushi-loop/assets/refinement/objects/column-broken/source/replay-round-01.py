import bpy,math,sys,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(bpy.data.filepath).resolve().parent.parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=Path(args[0]).resolve() if args else BASE/'candidates/round-01'
OUT.mkdir(parents=True,exist_ok=True)
sc=bpy.context.scene;root=bpy.data.objects[sc['sourceRootObject']];col=bpy.data.collections[sc['assetCollection']]
def rows(m):return [list(r) for r in m]
def measure():
 pts=[o.matrix_world@v.co for o in col.all_objects if o.type=='MESH' for v in o.data.vertices]
 return {'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]}
records={};physical=measure();root.rotation_euler.z=0;bpy.context.view_layer.update()
for direction,angle in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(angle);bpy.context.view_layer.update();sc.frame_set(1)
 saved=[];phys=measure();rm=rows(root.matrix_world)
 for o in col.all_objects:
  if o.type!='MESH':continue
  old=[v.co.copy() for v in o.data.vertices];saved.append((o,old));inv=o.matrix_world.inverted()
  for v in o.data.vertices:
   w=o.matrix_world@v.co;blend=max(0,1-max(0,w.z)/.42)**2;w.y*=1+(1/math.sin(math.radians(35))-1)*blend;v.co=inv@w
  o.data.update()
 bpy.context.view_layer.update();capture=measure()
 sc.render.filepath=str(OUT/f'native-static-{direction}.png');bpy.ops.render.render(write_still=True)
 records[direction]={'rootMatrix':rm,'physicalBounds':phys,'captureBounds':capture,'nativeFrame':1,'clip':'static','frameIndex':0,'path':f'native-static-{direction}.png'}
 for o,old in saved:
  for v,co in zip(o.data.vertices,old):v.co=co
  o.data.update()
 bpy.context.view_layer.update()
root.rotation_euler.z=0;bpy.context.view_layer.update()
cam=sc.camera;dep=bpy.context.evaluated_depsgraph_get()
def px(p):
 v=world_to_camera_view(sc,cam,Vector(p));return [v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y]
camera={'projection':'height-dependent-35-square-footing','frame':[192,320],'anchor':[96,248],'cellSize':128,'captureScale':4,'fps':12,'camera':{'type':'orthographic','worldMatrix':rows(cam.matrix_world),'projectionMatrix':rows(cam.calc_matrix_camera(dep,x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=1,scale_y=1)),'pixelAspect':[1,1],'worldUnitsPerCell':1,'elevationDegrees':35},'calibration':{'root':px((0,0,0))},'render':{'resolution':[sc.render.resolution_x,sc.render.resolution_y],'engine':sc.render.engine,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look},'footing':{'transition':.42,'afterFacing':True},'views':records}
(OUT/'native-capture.json').write_text(json.dumps(camera,indent=2)+'\n')
print('NATIVE_CAPTURE_COMPLETE '+str(OUT),flush=True)
