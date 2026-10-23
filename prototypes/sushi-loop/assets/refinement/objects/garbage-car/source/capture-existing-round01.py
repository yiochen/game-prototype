import bpy,json,math,sys,pathlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent.parent;RES=P/'source/resources';OUT=P/'candidates/round-01';sys.path.insert(0,str(RES));import native_actions as A
rig=json.loads((RES/'source-rig.json').read_text());sc=bpy.context.scene;cam=sc.camera;root=bpy.data.objects['garbage-car__root'];coll=root.users_collection[0];asset={'root':root,'collection':coll};data=json.loads((OUT/'semantic-mapping.json').read_text());mapping=data['renderableToCarrier'];new=[bpy.data.objects[n] for n in mapping];drivers={n:bpy.data.objects[n] for n in data['carriers']};lights=[o for o in sc.objects if o.type=='LIGHT'];FULL=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='METAL'
def direct_px(p):
 v=world_to_camera_view(sc,cam,Vector(p));return [v.x*1152,(1-v.y)*1664]
# Actual orthographic camera is affine. Measure its basis once rather than asking
# Blender to invert the same camera for every vertex four times per phase.
PX0=direct_px((0,0,0));PXA=[a-b for a,b in zip(direct_px((1,0,0)),PX0)];PXY=[a-b for a,b in zip(direct_px((0,1,0)),PX0)];PXZ=[a-b for a,b in zip(direct_px((0,0,1)),PX0)]
def px(p):return [PX0[i]+p[0]*PXA[i]+p[1]*PXY[i]+p[2]*PXZ[i] for i in range(2)]

def geometry():
 deps=bpy.context.evaluated_depsgraph_get();deps.update();pts=[];rows=[]
 for o in new:
  ev=o.evaluated_get(deps);me=ev.to_mesh();v=[ev.matrix_world@p.co for p in me.vertices];ev.to_mesh_clear()
  if not v:continue
  pts.extend(v);rows.append({'name':o.name,'carrier':mapping[o.name],'bounds':[[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]],'vertices':len(v)})
 return {'bounds':[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],'objects':rows,'projectedBounds':[[min(px(p)[i] for p in pts) for i in range(2)],[max(px(p)[i] for p in pts) for i in range(2)]]}

def carrier_states():return {n:{'location':list(d.location),'rotationEuler':list(d.rotation_euler),'scale':list(d.scale),'matrix':[list(row) for row in d.matrix_world]} for n,d in drivers.items()}

def apply(clip,frame,direction):
 A.apply_clip(asset,rig,clip,1,direction,sc);sc.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()

def render(clip,direction,frame,path):
 apply(clip,frame,direction);sc.render.filepath=str(path);path.parent.mkdir(parents=True,exist_ok=True)
 if not path.exists():bpy.ops.render.render(write_still=True)
 return {'clip':clip,'direction':direction,'index':int(frame-1),'sourceFrame':frame,'path':str(path.relative_to(P)),'rootRotationZ':float(root.rotation_euler.z),'rootMatrix':[list(row) for row in root.matrix_world],'geometry':geometry(),'carriers':carrier_states()}
frames=[]
if FULL:
 for clip,c in rig['clips'].items():
  for dr in ('N','E','S','W'):
   for fr in range(1,c['frames']+1):frames.append(render(clip,dr,fr,OUT/'frames'/f'{clip}-{dr}'/f'{fr-1:03d}.png'))
 closure=[]
 for dr in ('N','E','S','W'):closure.append(render('highlighted',dr,13,OUT/'diagnostics'/f'highlighted-{dr}-key13.png'))
 # Inbetween bounds and copied-carrier evidence at every half phase.
 inbetweens=[]
 for clip in ('highlighted','clearance'):
  for fr in [1.5+i for i in range(11)]+([12.5] if clip=='highlighted' else []):
   apply(clip,fr,'S');inbetweens.append({'clip':clip,'frame':fr,'direction':'S','rootRotationZ':float(root.rotation_euler.z),'geometry':geometry(),'carriers':carrier_states()})
 (OUT/'native-audit.json').write_text(json.dumps({'blender':bpy.app.version_string,'project':'source/round-01.blend','frames':frames,'closure':closure,'inbetweens':inbetweens,'lights':[{'name':o.name,'location':list(o.location),'energy':o.data.energy,'size':o.data.size,'shadow':o.data.use_shadow} for o in lights],'materials':[{'name':m.name,'alpha':m.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value,'nodes':[n.bl_idname for n in m.node_tree.nodes]} for m in bpy.data.materials if m.users>0],'resources':{'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'filepath':x.filepath} for x in bpy.data.images if x.users>0]}},indent=2))
else:
 for dr in ('N','E','S','W'):frames.append(render('idle',dr,1,OUT/'draft04'/f'idle-{dr}.png'))
 for fr in (4,8,12):frames.append(render('clearance','S',fr,OUT/'draft04'/f'clearance-S-{fr:02d}.png'))
 (OUT/'draft04/audit.json').write_text(json.dumps({'frames':frames},indent=2))
zero=px((0,0,0));camera={'projection':'top-down-oblique-square-grid','frame':[576,832],'anchor':[288,544],'cellSize':128,'captureScale':2,'fps':12,'camera':{'type':'orthographic','worldMatrix':[list(row) for row in cam.matrix_world],'projectionMatrix':[list(row) for row in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1152,y=1664,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'pixelAspect':[sc.render.pixel_aspect_x,1],'worldUnitsPerCell':1,'elevationDegrees':55.00797980144134,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]},'calibration':{'root':zero,'unitX':[a-b for a,b in zip(px((1,0,0)),zero)],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),zero)],'unitHeight':[a-b for a,b in zip(px((0,0,1)),zero)]}}
(OUT/'camera.json').write_text(json.dumps(camera,indent=2));ar=json.loads((P/'inputs/source-assetRecord.json').read_text());ar['scale']=2;ar['artStyle']={'revision':'warm-soft-native-round01','lighting':'overhead plus four identical cardinal soft fills and uniform world; no ground/shadow mesh'};(OUT/'assetRecord.json').write_text(json.dumps(ar,indent=2))
print('NATIVE ROUND01 COMPLETE',len(new),len(frames))
