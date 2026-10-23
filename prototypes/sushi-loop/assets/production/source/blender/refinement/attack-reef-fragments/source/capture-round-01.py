"""Reopen immutable round01 source and capture/measure all144 registered phases."""
import bpy,sys,json,math,time,hashlib
sys.dont_write_bytecode=True
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
S=Path(__file__).resolve().parent;B=S.parent;C=B/'candidates/round-01';R=S/'round-01-records'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def matrix(m):return [list(r) for r in m]
def bounds(points):
 return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
col=bpy.data.collections['S33_CFX_attack-reef-fragments.001'];root=bpy.data.objects['attack-reef-fragments__ground_root.001'];rig=json.loads((R/'rig.json').read_text());cam=sc.camera
def unhide(l):
 l.exclude=False;l.hide_viewport=False;l.collection.hide_render=False;l.collection.hide_viewport=False
 for child in l.children:unhide(child)
unhide(sc.view_layers[0].layer_collection)
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
def apply(clip,direction,frame):
 for rec in rig['clips'][clip]['actions']:
  o=bpy.data.objects[rec['ownerName']];a=bpy.data.actions[rec['action']];o.animation_data.action=a
  o.animation_data.action_slot=next(s for s in a.slots if s.identifier==rec['slotIdentifier'])
 root.location=(0,0,0);root.rotation_euler=(0,0,math.radians({'S':0,'E':90,'N':180,'W':-90}[direction]));root.scale=(1,1,1)
 sc.frame_set(frame);sc.view_layers[0].update();bpy.context.evaluated_depsgraph_get().update()
def px(point):
 q=world_to_camera_view(sc,cam,Vector(point));return [q.x*1280,(1-q.y)*1792,q.z]
def camera_record(scale):
 dg=bpy.context.evaluated_depsgraph_get();r=px((0,0,0));return {'projection':'top-down-oblique-square-grid','frame':[320,448],'anchor':[160,320],'cellSize':128,'captureScale':scale,'fps':12,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':matrix(cam.matrix_world),'projectionMatrix':matrix(cam.calc_matrix_camera(dg,x=1280,y=1792,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'worldUnitsPerCell':1,'elevationDegrees':55.00797980144134},'calibration':{'root':[v*scale/4 for v in r[:2]],'unitX':[(a-b)*scale/4 for a,b in zip(px((1,0,0))[:2],r[:2])],'unitDepth':[(a-b)*scale/4 for a,b in zip(px((0,-1,0))[:2],r[:2])],'unitHeight':[(a-b)*scale/4 for a,b in zip(px((0,0,1))[:2],r[:2])]},'nativeCaptureScale':4,'nativeFrame':[1280,1792],'publishedFrame':[640,896],'publication':'wholecanvas1280x1792 to640x896 PillowLANCZOS'}
sc.view_layers[0].update();nativecam=camera_record(4);publishedcam=camera_record(2)
dump(R/'camera-native.json',nativecam);dump(R/'camera.json',publishedcam)
assert max(abs(a-b) for a,b in zip(nativecam['calibration']['root'],[640,1280]))<.01
def measure(clip,direction,index):
 dg=bpy.context.evaluated_depsgraph_get();raw=[];evaluated=[];projected=[];canonical=[];objects=[];inv=root.matrix_world.inverted()
 for o in col.all_objects:
  if o.type!='MESH':continue
  rawpoints=[o.matrix_world@v.co for v in o.data.vertices];eo=o.evaluated_get(dg);em=eo.to_mesh();points=[eo.matrix_world@v.co for v in em.vertices];counts=[len(em.vertices),len(em.polygons)];eo.to_mesh_clear()
  rootpoints=[inv@v for v in points];pp=[px(v) for v in points]
  objects.append({'name':o.name,'parent':o.parent.name if o.parent else None,'matrix':matrix(o.matrix_world),'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'rawVertices':len(o.data.vertices),'rawPolygons':len(o.data.polygons),'evaluatedVertices':counts[0],'evaluatedPolygons':counts[1],'rawAuthoredBounds':bounds(rawpoints),'evaluatedBounds':bounds(points),'canonicalSBounds':bounds(rootpoints),'projectedNativeBounds':bounds(pp),'visible':o.visible_get(),'activeAction':o.animation_data.action.name if o.animation_data and o.animation_data.action else None})
  raw+=rawpoints;evaluated+=points;projected+=pp;canonical+=rootpoints
 rec={'clip':clip,'direction':direction,'index':index,'frame':index,'nativeFrame':index+1,'seconds':index/12,'rootRotationDegrees':{'S':0,'E':90,'N':180,'W':-90}[direction],'rootMatrix':matrix(root.matrix_world),'rawAuthoredBounds':bounds(raw),'evaluatedBounds':bounds(evaluated),'canonicalSBounds':bounds(canonical),'projectedEvaluatedBoundsNative':bounds(projected),'camera':nativecam,'objects':objects}
 bb=rec['canonicalSBounds'];pb=rec['projectedEvaluatedBoundsNative'];tol=1e-5
 rec['clearancePass']=all(bb['min'][j]>=lo-tol and bb['max'][j]<=hi+tol for j,(lo,hi) in enumerate([(-1.2,1.2),(-1.2,1.2),(.04,.9)]))
 rec['canvasContainmentPass']=pb['min'][0]>1 and pb['max'][0]<1279 and pb['min'][1]>1 and pb['max'][1]<1791 and pb['min'][2]>0
 assert rec['clearancePass'],(clip,direction,index,'clearance',bb)
 assert rec['canvasContainmentPass'],(clip,direction,index,'canvas',pb)
 return rec
records=[]
for clip in ['active','windup','recovery']:
 for direction in ['S','N','E','W']:
  for index in [5,0,1,2,3,4,6,7,8,9,10,11]:
   apply(clip,direction,index+1);rec=measure(clip,direction,index)
   folder=C/'native'/clip/direction;folder.mkdir(parents=True,exist_ok=True);dest=folder/f'{index:03d}.png';sc.render.filepath=str(dest)
   started=time.monotonic();bpy.ops.render.render(write_still=True,scene=sc.name)
   rec.update(path=str(dest.relative_to(B)),sha256=sha(dest),dimensions=[1280,1792],renderSeconds=time.monotonic()-started);records.append(rec)
   dump(C/'native-validation.json',{'schema':'measured-native-views-v1','project':str((S/'round-01.blend').relative_to(B)),'projectSHA256':sha(S/'round-01.blend'),'captureRecords':records,'complete':len(records)==144})
   print('ROUND01_CAPTURE',clip,direction,index,'COUNT',len(records),'SECONDS',rec['renderSeconds'],flush=True)
# Real saved-action terminal extrapolation and cross-clip boundary tests; no new renders.
def sample():
 dg=bpy.context.evaluated_depsgraph_get();out={}
 for o in col.all_objects:
  if o.type=='MESH':
   eo=o.evaluated_get(dg);me=eo.to_mesh();out[o.name]=[list(eo.matrix_world@v.co) for v in me.vertices];eo.to_mesh_clear()
 return out
def error(a,b):return max(abs(x-y) for n in a for va,vb in zip(a[n],b[n]) for x,y in zip(va,vb))
terminal=[];boundaries=[]
for direction in ['N','E','S','W']:
 for clip in ['windup','active','recovery']:
  apply(clip,direction,12);base=sample()
  for frame in [13,24]:
   apply(clip,direction,frame);terminal.append({'clip':clip,'direction':direction,'terminalNativeFrame':12,'testedNativeFrame':frame,'maximumEvaluatedVertexError':error(base,sample())})
 for previous,nextclip in [('windup','active'),('active','recovery')]:
  apply(previous,direction,12);a=sample();apply(nextclip,direction,1);boundaries.append({'from':previous,'to':nextclip,'direction':direction,'maximumEvaluatedVertexError':error(a,sample())})
assert all(r['maximumEvaluatedVertexError']<1e-6 for r in terminal+boundaries)
dump(C/'motion-validation.json',{'actualSavedActionTerminalHold':terminal,'actualSavedActionClipBoundaries':boundaries,'all27SavedActionsPresent':all(bpy.data.actions.get(a['action']) for c in rig['clips'].values() for a in c['actions']),'postterminalRule':'constant extrapolation; consumer clamp index11; no duplicate closure key'})
dump(C/'native-validation.json',{'schema':'measured-native-views-v1','project':str((S/'round-01.blend').relative_to(B)),'projectSHA256':sha(S/'round-01.blend'),'captureRecords':sorted(records,key=lambda r:(['windup','active','recovery'].index(r['clip']),['N','E','S','W'].index(r['direction']),r['index'])),'complete':True,'captureCount':144,'allphaseClearance':True,'allphaseCanvasContainment':True,'cameraNative':nativecam,'cameraPublished':publishedcam,'terminalAndBoundaryEvidence':'candidates/round-01/motion-validation.json','ownership':{'collection':col.name,'root':root.name,'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'materials':[s.material.name if s.material else None for s in o.material_slots],'modifiers':[{'type':m.type,'name':m.name} for m in o.modifiers]} for o in col.all_objects]}})
print('ROUND01_COMPLETE144',flush=True)
