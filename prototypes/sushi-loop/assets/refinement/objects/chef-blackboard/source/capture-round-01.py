"""Closed native capture replay; requires only saved .blend and resources beside this script.
Optional --output PATH, --probe (idle only), --measure-only.
No geometry, material, camera, lighting or rig reconstruction occurs here.
"""
import bpy,json,hashlib,sys,argparse,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent;O=P.parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path);p.add_argument('--probe',action='store_true');p.add_argument('--measure-only',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=a.output or O/'candidates/round-01';OUT.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene;root=bpy.data.objects['chef-blackboard__root'];c=bpy.data.collections['S33_PROP_chef-blackboard'];cam=s.camera
rig=json.loads((P/'resources/original-rig.json').read_text());ref=json.loads((P/'resources/registered-camera.json').read_text())
assert Path(bpy.data.filepath).is_file()
project_sha=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
for x in c.all_objects:x.hide_render=False;x.hide_viewport=False;x.hide_set(False)
c.hide_render=False;c.hide_viewport=False
for la in bpy.context.view_layer.layer_collection.children:la.exclude=False;la.hide_viewport=False
bpy.context.view_layer.update()
def matrix(m):return [list(r) for r in m]
def proj():return cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)
def bind(clip):
 for r in rig['clips'][clip]['actions']:
  o=bpy.data.objects[r['ownerName']];ac=bpy.data.actions[r['action']];o.animation_data_create();o.animation_data.action=ac;o.animation_data.action_slot=next(t for t in ac.slots if t.identifier==r['slotIdentifier'])
  for tr in o.animation_data.nla_tracks:tr.mute=True
 s.frame_set(1);bpy.context.view_layer.update()
def points(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
 try:return [ev.matrix_world@v.co for v in mesh.vertices]
 finally:ev.to_mesh_clear()
def bound(v):return [list(map(min,zip(*v))),list(map(max,zip(*v)))]
def xyz(v):return [float(x) for x in v]
def pixel(v):
 q=world_to_camera_view(s,cam,Vector(v));return [q.x*s.render.resolution_x,(1-q.y)*s.render.resolution_y]
def frame_record(clip,frame):
 s.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
 verts=[];by=[]
 for o in c.all_objects:
  if o.type=='MESH':
   v=points(o);verts+=v;by.append({'name':o.name,'bounds':bound(v),'vertices':len(v)})
 face=bpy.data.objects['chef-blackboard__blank_dynamic_face'];facev=points(face);front=min(v.y for v in facev);fc=face.matrix_world@Vector((0,-.0275,0));socket=root.matrix_world@Vector((0,-.434,.61))
 # Closest face point to display socket: front plane remains parallel to XZ.
 rec={'clip':clip,'frame':frame,'index':frame-1,'view':'S','rootMatrix':matrix(root.matrix_world),'cameraWorldMatrix':matrix(cam.matrix_world),'cameraProjectionMatrix':matrix(proj()),'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'bounds':bound(verts),'face':{'matrix':matrix(face.matrix_world),'frontY':front,'frontCenter':xyz(fc),'dimensions':[.62,.055,.57],'blank':True,'outwardNormal':[0,-1,0]},'socket':{'authoredLocal':[0,-.434,.61],'actualWorld':xyz(socket),'nativeAttachmentWorld':xyz(bpy.data.objects['CB01_socket_recipe_face'].matrix_world.translation),'projectedRawPixels':pixel(socket),'facePlaneOutwardClearance':front-socket.y,'insideFaceXZ':abs(socket.x-fc.x)<.295 and abs(socket.z-fc.z)<.270},'groundRootRawPixel':pixel(root.matrix_world.translation),'bindings':[{'owner':r['ownerName'],'action':bpy.data.objects[r['ownerName']].animation_data.action.name,'slot':bpy.data.objects[r['ownerName']].animation_data.action_slot.identifier} for r in rig['clips'][clip]['actions']]}
 return rec,by
records=[];structure=None
for clip in ['idle','selected','recipe_change']:
 if a.probe and clip!='idle':continue
 bind(clip)
 for frame in range(1,rig['clips'][clip]['frames']+1):
  r,by=frame_record(clip,frame)
  if structure is None:structure=by
  out=OUT/'raw'/((clip.replace('_','-'))+'-S')/f'{frame-1:03d}.png';out.parent.mkdir(parents=True,exist_ok=True)
  if not a.measure_only:
   s.render.filepath=str(out);bpy.ops.render.render(write_still=True)
   r['path']=str(out.relative_to(O)) if out.is_relative_to(O) else str(out);r['sha256']=hashlib.sha256(out.read_bytes()).hexdigest()
  records.append(r)
# Actual native selected loop closure, excluding frame13 from runtime images.
bind('selected');first,_=frame_record('selected',1);close,_=frame_record('selected',13)
closure={'firstFrame':1,'closingKeyFrame':13,'duplicateClosureExcluded':True,'boundsMaxDelta':max(abs(first['bounds'][i][j]-close['bounds'][i][j]) for i in range(2) for j in range(3)),'faceMatrixMaxDelta':max(abs(first['face']['matrix'][i][j]-close['face']['matrix'][i][j]) for i in range(4) for j in range(4))}
# Saved native action values are compared against the exact unmodified original action records.
def curves(action):
 for la in action.layers:
  for st in la.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:yield fc
observed={ac.name:[{'path':f.data_path,'index':f.array_index,'keys':[[float(x.co.x),float(x.co.y),x.interpolation] for x in f.keyframe_points]} for f in curves(ac)] for ac in bpy.data.actions}
original=json.loads((P/'resources/original-actions.json').read_text())
assert observed==original,'Original native action curves changed'
camdelta=max(abs(records[0]['cameraWorldMatrix'][i][j]-ref['camera']['worldMatrix'][i][j]) for i in range(4) for j in range(4));projdelta=max(abs(records[0]['cameraProjectionMatrix'][i][j]-ref['camera']['projectionMatrix'][i][j]) for i in range(4) for j in range(4))
assert camdelta<1e-6 and projdelta<1e-6,(camdelta,projdelta)
external={'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'filepath':x.filepath,'packed':bool(x.packed_file)} for x in bpy.data.images if x.source=='FILE'],'fonts':[x.filepath for x in bpy.data.fonts if x.filepath and not x.packed_file]}
validation={'asset':'chef-blackboard','project':'source/round-01.blend','projectSHA256':project_sha,'blender':bpy.app.version_string,'nativeRecords':records,'restMeshes':structure,'registeredCameraMaxDelta':camdelta,'registeredProjectionMaxDelta':projdelta,'captureSettings':{'frame':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'fps':s.render.fps,'engine':s.render.engine,'samples':s.cycles.samples,'denoise':s.cycles.use_denoising,'seed':s.cycles.seed,'alpha':s.render.film_transparent,'colorMode':s.render.image_settings.color_mode,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'groundPlane':False,'singleCaptureSetup':True},'root':{'location':xyz(root.location),'scale':xyz(root.scale),'rotation':xyz(root.rotation_euler),'footprint':[1,1],'declaredHeight':1.0,'compositionBandY':[-.5,-.27]},'actionIntegrity':{'allOriginalKeysEqual':observed==original,'actionCount':len(observed),'clipCounts':{k:v['frames'] for k,v in rig['clips'].items()},'originalTimingAndSlots':True},'selectedLoopClosure':closure,'dependencies':external,'notes':['Measurements are actual evaluated native vertices; only compact bounds/counts retained.','Both physical attachment Empties are local [0,-.434,.61]. Writing surface actual front plane remains the original y=-.4275; no display content is baked.','Four-view-sheet is a generic repeated-S alias, not additional facings.']}
(OUT/'native-validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print('CAPTURE_COMPLETE',len(records),'cameraDelta',camdelta,'projectionDelta',projdelta,'closure',closure)
print('REST_BOUNDS',records[0]['bounds'],'FACE',records[0]['face'],'SOCKET',records[0]['socket'])
