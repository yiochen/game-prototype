"""Capture and measure the actual saved native candidate without saving any scene changes."""
import sys
sys.dont_write_bytecode=True
import bpy, math, json, hashlib, struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
DRAFT=any(a.startswith('--draft') for a in sys.argv)
OUT=HERE/next((a.removeprefix('--') for a in sys.argv if a.startswith('--draft')), 'draft-v1') if DRAFT else BASE/'candidates/round-01'
OUT.mkdir(parents=True,exist_ok=False)
SC=bpy.context.scene;ROOT=bpy.data.objects['safe-passage__root']
COL=next(c for c in ROOT.users_collection)
PROJECT=Path(bpy.data.filepath);PROJECTSHA=hashlib.sha256(PROJECT.read_bytes()).hexdigest()
OBJECTS=sorted(COL.all_objects,key=lambda o:o.name)

def write(name,v):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def mat(m):return [list(r) for r in m]
def bound(ps):return {'min':[min(p[i] for p in ps) for i in range(3)],'max':[max(p[i] for p in ps) for i in range(3)]}
def pxy(v):
 p=world_to_camera_view(SC,SC.camera,Vector(v));return [p.x*SC.render.resolution_x,(1-p.y)*SC.render.resolution_y]
def sub(a,b):return [a[i]-b[i] for i in range(len(a))]
def vecsha(ps):return hashlib.sha256(b''.join(struct.pack('<3f',*p) for p in ps)).hexdigest()
def hull_area(points):
 pts=sorted(set((round(p.x,8),round(p.y,8)) for p in points))
 if len(pts)<3:return 0
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 lower=[];upper=[]
 for p in pts:
  while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
  lower.append(p)
 for p in reversed(pts):
  while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
  upper.append(p)
 h=lower[:-1]+upper[:-1]
 return abs(sum(h[i][0]*h[(i+1)%len(h)][1]-h[(i+1)%len(h)][0]*h[i][1] for i in range(len(h))))/2

def enable():
 COL.hide_render=COL.hide_viewport=False
 for o in OBJECTS:o.hide_render=o.hide_viewport=False;o.hide_set(False)
 def walk(l):
  l.exclude=False;l.hide_viewport=False
  for c in l.children:walk(c)
 walk(bpy.context.view_layer.layer_collection)
 bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
enable()

def measure():
 dg=bpy.context.evaluated_depsgraph_get();dg.update();inv=ROOT.matrix_world.inverted()
 records=[];rawall=[];evall=[];trees={};meshcache={};support=[]
 for o in OBJECTS:
  if o.type!='MESH':continue
  eo=o.evaluated_get(dg);me=eo.to_mesh()
  raw=[inv@o.matrix_world@v.co for v in o.data.vertices]
  ev=[inv@eo.matrix_world@v.co for v in me.vertices]
  faces=[list(p.vertices) for p in me.polygons]
  rawall+=raw;evall+=ev
  rec={'object':o.name,'role':o.get('role'),'parent':o.parent.name if o.parent else None,'matrixWorld':mat(eo.matrix_world),'matrixLocal':mat(o.matrix_local),'rawAuthoredBoundsCanonicalS':bound(raw),'evaluatedBoundsCanonicalS':bound(ev),'rawVertexCount':len(raw),'evaluatedVertexCount':len(ev),'rawPolygonCount':len(o.data.polygons),'evaluatedPolygonCount':len(me.polygons),'evaluatedVerticesSHA256':vecsha(ev),'materialSlots':[m.name for m in o.data.materials],'visibility':{'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'hideSet':o.hide_get(),'visible':o.visible_get()}}
  if o.get('role')=='stable_stone':
   trees[o.name]=BVHTree.FromPolygons(ev,faces,all_triangles=False)
   cuts=[]
   for e in me.edges:
    a,b=ev[e.vertices[0]],ev[e.vertices[1]]
    if abs(a.z)<1e-8:cuts.append(a)
    if a.z*b.z<0:cuts.append(a+(b-a)*(-a.z/(b.z-a.z)))
   rec['groundSection']={'planeZ':0,'points':[list(p) for p in cuts],'convexHullArea':hull_area(cuts),'finiteContact':len(cuts)>=3 and hull_area(cuts)>0,'minZ':min(p.z for p in ev)}
   support.append({'object':o.name,**rec['groundSection']})
  meshcache[o.name]=(ev,faces)
  records.append(rec);eo.to_mesh_clear()
 attachments=[]
 for o in OBJECTS:
  if o.get('role')!='attached_foliage':continue
  pivot=inv@o.matrix_world.translation
  target=o['attachmentStone'];nearest,normal,index,distance=trees[target].find_nearest(pivot)
  signed=(pivot-nearest).dot(normal)
  attachments.append({'object':o.name,'stone':target,'pivotCanonicalS':list(pivot),'nearestSurfaceCanonicalS':list(nearest),'distance':distance,'signedSurfaceDistance':signed,'pivotInsideStone':signed<=1e-6,'baseVertexAtPivot':o.data.vertices[0].co.length<=1e-10})
 world=[ROOT.matrix_world@p for p in evall]
 return {'rawAuthoredBoundsCanonicalS':bound(rawall),'evaluatedBoundsCanonicalS':bound(evall),'evaluatedBoundsWorld':bound(world),'objects':records,'stoneSupports':support,'foliageAttachments':attachments,'geometryFingerprint':vecsha(evall)}

root_px=pxy((0,0,0))
camera={'projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'cellSize':128,'captureScale':4,'fps':12,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':mat(SC.camera.matrix_world),'projectionMatrix':mat(SC.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=SC.render.resolution_x,y=SC.render.resolution_y,scale_x=SC.render.pixel_aspect_x,scale_y=SC.render.pixel_aspect_y)),'pixelAspect':[SC.render.pixel_aspect_x,SC.render.pixel_aspect_y],'worldUnitsPerCell':1,'elevationDegrees':math.degrees(math.atan(1/.7)),'orthoScale':SC.camera.data.ortho_scale,'sensorFit':SC.camera.data.sensor_fit,'shift':[SC.camera.data.shift_x,SC.camera.data.shift_y]},'calibration':{'root':root_px,'unitX':sub(pxy((1,0,0)),root_px),'unitDepth':sub(pxy((0,-1,0)),root_px),'unitHeight':sub(pxy((0,0,1)),root_px)},'nativeFrame':[SC.render.resolution_x,SC.render.resolution_y],'nativeCaptureScale':4,'nativeRoot':root_px}
write('native-camera.json',camera)
materials=[]
for m in sorted({m for o in OBJECTS if o.type=='MESH' for m in o.data.materials},key=lambda m:m.name):
 def plain(v):
  try:return list(v)
  except TypeError:return v
 materials.append({'name':m.name,'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value') and not i.is_linked},'ramp':[(e.position,list(e.color)) for e in n.color_ramp.elements] if n.type=='VALTORGB' else None} for n in m.node_tree.nodes],'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocket':l.to_socket.name} for l in m.node_tree.links]})
actions=[]
for o in OBJECTS:
 if not o.animation_data or not o.animation_data.action:continue
 a=o.animation_data.action
 curves=[f for l in a.layers for s in l.strips for cb in s.channelbags for f in cb.fcurves]
 actions.append({'ownerType':'Object','ownerName':o.name,'action':a.name,'slotIdentifier':o.animation_data.action_slot.identifier,'keyframeCount':sum(len(f.keyframe_points) for f in curves),'curves':[{'dataPath':f.data_path,'arrayIndex':f.array_index,'keys':[list(k.co) for k in f.keyframe_points]} for f in curves]})
write('native-scene-record.json',{'sourceProject':str(PROJECT.relative_to(BASE)),'sourceSHA256':PROJECTSHA,'scene':SC.name,'root':ROOT.name,'rootMetadata':{k:ROOT[k] for k in ROOT.keys()},'collection':COL.name,'objectOwnership':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'collections':[c.name for c in o.users_collection],'modifiers':[{'name':m.name,'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None),'levels':getattr(m,'levels',None),'renderLevels':getattr(m,'render_levels',None)} for m in o.modifiers]} for o in OBJECTS],'materials':materials,'actions':actions,'lights':[{'name':o.name,'matrixWorld':mat(o.matrix_world),'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'color':list(o.data.color)} for o in SC.objects if o.type=='LIGHT'],'world':{'color':list(SC.world.node_tree.nodes.get('Background').inputs['Color'].default_value),'strength':SC.world.node_tree.nodes.get('Background').inputs['Strength'].default_value},'render':{'engine':SC.render.engine,'resolution':[SC.render.resolution_x,SC.render.resolution_y],'pixelAspect':[SC.render.pixel_aspect_x,SC.render.pixel_aspect_y],'viewTransform':SC.view_settings.view_transform,'look':SC.view_settings.look,'exposure':SC.view_settings.exposure,'gamma':SC.view_settings.gamma,'dither':SC.render.dither_intensity,'filmTransparent':SC.render.film_transparent,'fps':SC.render.fps,'compositor':getattr(getattr(SC,'compositing_node_group',None),'name',None)},'externalResources':{'libraries':[l.filepath for l in bpy.data.libraries],'usedImageTextures':[n.image.filepath for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]}})
records=[];closures={}
for direction in 'NESW':
 ROOT.rotation_euler.z={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[direction]
 for index in ([0] if DRAFT else range(12)):
  SC.frame_set(index+1);enable();gm=measure()
  p=OUT/'native/ambient'/direction/f'{index:03d}.png';p.parent.mkdir(parents=True,exist_ok=True)
  rec={'clip':'ambient','direction':direction,'index':index,'blenderFrame':SC.frame_current,'rootRotationZ':ROOT.rotation_euler.z,'rootRotationDegrees':math.degrees(ROOT.rotation_euler.z),'rootMatrix':mat(ROOT.matrix_world),'cameraMatrix':mat(SC.camera.matrix_world),'nativeFrame':[768,1408],'nativeRoot':pxy((0,0,0)),'path':str(p.relative_to(BASE)),'sourceSHA256':PROJECTSHA,'geometry':gm}
  SC.render.filepath=str(p);bpy.ops.render.render(write_still=True);rec['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();records.append(rec)
  print('CAPTURE '+direction+' '+str(index),flush=True)
 SC.frame_set(13);enable();closures[direction]={'blenderFrame':13,'rootMatrix':mat(ROOT.matrix_world),'geometry':measure()}
write('native-validation.json',{'asset':'safe-passage','sourceSHA256':PROJECTSHA,'captureRecords':records,'closureFrame13':closures,'runtimeFrames':12,'runtimeFrameOrder':list(range(12)),'fps':12,'periodSeconds':1,'loop':True,'closureExcludedFromAtlas':True,'nativeFrame':[768,1408],'camera':'native-camera.json','sceneRecord':'native-scene-record.json','rawAuthoredAndEvaluatedMeasuredSeparately':True,'noSceneSaveDuringCapture':True,'sourceUnchangedAfterCapture':hashlib.sha256(PROJECT.read_bytes()).hexdigest()==PROJECTSHA})
print('CAPTURE_COMPLETE '+str(OUT),flush=True)
