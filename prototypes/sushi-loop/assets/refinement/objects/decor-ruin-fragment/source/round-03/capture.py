"""Reopen project and render registered four-view native captures. No external modules."""
import bpy,math,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=Path(args[0]).resolve() if args else HERE.parent.parent/'candidates'/'round-03'/'native'
OUT.mkdir(parents=True,exist_ok=True)
sc=bpy.context.scene;root=bpy.data.objects['decor-ruin-fragment__ground_root'];col=bpy.data.collections['decor-ruin-fragment'];meshes=[o for o in col.all_objects if o.type=='MESH']
sc.cycles.seed=0;sc.render.threads_mode='FIXED';sc.render.threads=8
bpy.context.view_layer.update()
def rows(m):return [list(r) for r in m]
def bounds():
 dg=bpy.context.evaluated_depsgraph_get();pts=[];stats=[]
 for o in meshes:
  ev=o.evaluated_get(dg);me=ev.to_mesh();ps=[ev.matrix_world@v.co for v in me.vertices];pts+=ps;stats.append({'name':o.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'materials':[m.name for m in o.data.materials],'min':[min(p[i] for p in ps) for i in range(3)],'max':[max(p[i] for p in ps) for i in range(3)]});ev.to_mesh_clear()
 return {'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)],'dimensions':[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)],'meshes':stats},pts
def px(p):
 p=world_to_camera_view(sc,sc.camera,Vector(p));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
root.rotation_euler.z=0;bpy.context.view_layer.update();undeformed,_=bounds()
cam=sc.camera;origin=px((0,0,0))
cal={'root':origin,'unitX':[a-b for a,b in zip(px((1,0,0)),origin)],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),origin)],'unitHeight':[a-b for a,b in zip(px((0,0,1)),origin)]}
rec={'scene':sc.name,'cameraObject':cam.name,'projection':'character-orthographic','frame':[192,480],'anchor':[96,384],'cellSize':128,'captureScale':4,'fps':12,'camera':{'worldMatrix':rows(cam.matrix_world),'projectionMatrix':rows(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=768,y=1920,scale_x=1,scale_y=1)),'pixelAspect':[1,1],'elevationDegrees':35,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'sensorFit':cam.data.sensor_fit},'calibration':cal}
views=[]
for direction,degrees in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(degrees);sc.frame_set(1);bpy.context.view_layer.update();before,_=bounds();saved=[]
 try:
  for o in meshes:
   orig=[v.co.copy() for v in o.data.vertices];saved.append((o,orig));inv=o.matrix_world.inverted()
   for v in o.data.vertices:
    world=o.matrix_world@v.co;blend=max(0,1-max(0,world.z)/.42)**2;world.y*=1+(1/math.sin(math.radians(35))-1)*blend;v.co=inv@world
   o.data.update()
  bpy.context.view_layer.update();captured,pts=bounds();projected=[px(p) for p in pts]
  geom={'undeformed':before,'capture':captured,'captureCorrectionCount':1,'footingWorldYFactorAtGround':1/math.sin(math.radians(35)),'transitionHeight':.42,'worldYCorrectionAfterRootRotation':True,'projectedPixelBounds':{'min':[min(p[i] for p in projected) for i in range(2)],'max':[max(p[i] for p in projected) for i in range(2)]},'projectedSilhouetteCells':(max(p[1] for p in projected)-min(p[1] for p in projected))/512}
  dest=OUT/('static-'+direction+'.png');sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True,scene=sc.name)
  views.append({'clip':'static','direction':direction,'index':0,'degrees':degrees,'rootMatrix':rows(root.matrix_world),'rootLocation':list(root.location),'rootScale':list(root.scale),'geometry':geom,'image':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
 finally:
  for o,orig in saved:
   for v,co in zip(o.data.vertices,orig):v.co=co
   o.data.update()
  bpy.context.view_layer.update()
root.rotation_euler.z=0;bpy.context.view_layer.update()
lighting=[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'location':list(o.location),'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT']
report={'project':bpy.data.filepath,'blenderVersion':bpy.app.version_string,'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'nativeCaptureScale':4,'nativeFrame':[768,1920],'publicationScale':2,'publicationFrame':[384,960],'wholeCanvasPublication':'Pillow LANCZOS native768x1920 to published384x960; no fitting/crop/recolor','camera':rec,'undeformedGeometry':undeformed,'views':views,'lights':lighting,'horizontalLightSymmetry':'one centered overhead and four identical lights at90deg intervals','world':{'strength':sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value},'compositor':{'group':sc.compositing_node_group.name,'nodes':[{'type':n.bl_idname,'scene':n.scene.name if n.bl_idname=='CompositorNodeRLayers' and n.scene else None} for n in sc.compositing_node_group.nodes]},'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'filmTransparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'resources':{'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'source':x.source,'filepath':x.filepath,'packed':bool(x.packed_file)} for x in bpy.data.images if x.type!='RENDER_RESULT']},'staticContract':{'actions':len(bpy.data.actions),'armatures':len(bpy.data.armatures),'frames':1,'fps':12,'loop':False,'ports':{},'sockets':{}},'sourceRestoredAfterCaptures':True}
(OUT/'capture-validation.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'camera.json').write_text(json.dumps(rec,indent=2)+'\n')
print('CAPTURE_COMPLETE',str(OUT))
