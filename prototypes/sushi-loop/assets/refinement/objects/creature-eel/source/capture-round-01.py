import sys
sys.dont_write_bytecode=True
import bpy,bmesh,json,math,hashlib,time
import numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent;E=P.parent
STUDY='--study' in sys.argv
C=E/'candidates'/(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--study-name=')),'study-v03') if STUDY else 'round-01');C.mkdir(parents=True,exist_ok=True)
PROJECT=P/'round-01.blend';PROJECT_SHA=hashlib.sha256(PROJECT.read_bytes()).hexdigest()
assert Path(bpy.data.filepath)==PROJECT
sc=bpy.context.scene;cam=sc.camera
root=bpy.data.objects['creature-eel__ground_root.003'];arm=bpy.data.objects['creature-eel__armature.003'];col=root.users_collection[0]
meshes=sorted([o for o in col.all_objects if o.type=='MESH'],key=lambda o:o.name)
record=json.loads(root['native_action_record']);recipes=json.loads(root['animation_recipes'])
FACINGS={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
for o in col.all_objects:o.hide_set(False);o.hide_render=False;o.hide_viewport=False
col.hide_render=False;col.hide_viewport=False
for lc in bpy.context.view_layer.layer_collection.children:lc.exclude=False;lc.hide_viewport=False
def plain(m):return [list(r) for r in m]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def project(v):
 p=world_to_camera_view(sc,cam,Vector(v));return np.array([p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y])
bpy.context.view_layer.update()
origin=project((0,0,0));basis=np.stack([project(v)-origin for v in [(1,0,0),(0,1,0),(0,0,1)]],axis=0)
assert max(abs(origin-np.array([896,1408])))<.05
camera={'projection':'character-orthographic','frame':[448,512],'anchor':[224,352],'cellSize':128,'captureScale':4,'fps':12,
 'nativeFrame':[1792,2048],'logicalRoot':[224,352],'nativeRoot':origin.tolist(),
 'camera':{'type':'orthographic','worldMatrix':plain(cam.matrix_world),'projectionMatrix':plain(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1792,y=2048,scale_x=1,scale_y=1)),
 'pixelAspect':[1,1],'worldUnitsPerCell':1,'elevationDegrees':35,'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y]},
 'calibration':{'root':origin.tolist(),'unitX':basis[0].tolist(),'unitDepth':(-basis[1]).tolist(),'unitHeight':basis[2].tolist()},
 'sourceSHA256':PROJECT_SHA,'blenderVersion':bpy.app.version_string,
 'lights':[{'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'power':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT'],
 'render':{'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'filterSize':sc.render.filter_size,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'filmTransparent':sc.render.film_transparent,'worldStrength':sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value,'compositor':None}}
(C/'native-camera.json').write_text(json.dumps(camera,indent=2)+'\n')
topology=[]
for o in meshes:
 bm=bmesh.new();bm.from_mesh(o.data)
 topology.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'parent':o.parent.name,'armatureTargets':[m.object.name for m in o.modifiers if m.type=='ARMATURE'],'smoothPolygons':sum(p.use_smooth for p in o.data.polygons),'materialNames':[m.name for m in o.data.materials]})
 bm.free()
def pose(clip,frame,direction):
 a=bpy.data.actions[record['clips'][clip][0]];arm.animation_data_create();arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0]
 root.location=(0,0,0);root.rotation_euler=(0,0,FACINGS[direction]);root.scale=(1,1,1)
 sc.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update();return dg
def coords(o,dg,evaluated=True):
 e=o.evaluated_get(dg) if evaluated else o;me=e.to_mesh() if evaluated else e.data
 ar=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',ar);ar=ar.reshape(-1,3)
 m=np.array(e.matrix_world,dtype=np.float64);out=ar@m[:3,:3].T+m[:3,3]
 if evaluated:e.to_mesh_clear()
 return out
def bounds(ar):return [ar.min(axis=0).tolist(),ar.max(axis=0).tolist()]
def inspect(clip,frame,direction,dg):
 by={o.name:coords(o,dg) for o in meshes};pp=np.concatenate(list(by.values()));raw=np.concatenate([coords(o,dg,False) for o in meshes])
 rot=np.array(root.matrix_world)[:3,:3];canonical=pp@rot
 screen=pp@basis+origin
 ea=arm.evaluated_get(dg)
 bones={b.name:plain(ea.matrix_world@b.matrix) for b in ea.pose.bones}
 deform=ea.pose.bones[0].matrix@arm.data.bones[0].matrix_local.inverted()
 head_matrix=np.array(ea.matrix_world@deform)
 residual=0.0
 for o in meshes:
  if any(s in o.name for s in ['eye_','mouth']):
   ar=np.empty(len(o.data.vertices)*3,dtype=np.float32);o.data.vertices.foreach_get('co',ar);ar=ar.reshape(-1,3)
   expected=ar@head_matrix[:3,:3].T+head_matrix[:3,3]
   residual=max(residual,float(np.max(np.linalg.norm(by[o.name]-expected,axis=1))))
 b=bounds(canonical);budget=[[-1.30,-.75,.04],[1.30,1.45,1.00]]
 inside=all(b[0][i]>=budget[0][i]-1e-5 and b[1][i]<=budget[1][i]+1e-5 for i in range(3))
 rec={'clip':clip,'direction':direction,'frame':frame,'index':frame-1 if frame<=12 else None,'rootRotationZ':root.rotation_euler.z,'actualRootMatrix':plain(root.matrix_world),'rootLocation':list(root.location),
 'cameraWorldMatrix':plain(cam.matrix_world),'cameraProjectionMatrix':camera['camera']['projectionMatrix'],'cameraShift':[cam.data.shift_x,cam.data.shift_y],'nativeRootPixel':origin.tolist(),
 'rawAuthoredBounds':bounds(raw),'evaluatedBounds':bounds(pp),'canonicalSEvaluatedBounds':b,'withinCanonicalBudget':inside,'finite':bool(np.isfinite(pp).all()),
 'projectedNativeBounds':[screen.min(axis=0).tolist(),screen.max(axis=0).tolist()],'projectedInsideFrame':bool((screen.min(axis=0)>1).all() and (screen.max(axis=0)<np.array([1791,2047])).all()),
 'meshBounds':{k:bounds(v) for k,v in by.items()},'evaluatedBoneWorldMatrices':bones,'armatureObjectMatrix':plain(ea.matrix_world),'headAttachmentVertexResidual':residual}
 return rec,pp
measure={'asset':'creature-eel','round':1,'projectSHA256':PROJECT_SHA,'scriptSHA256':sha(Path(__file__)),'camera':'native-camera.json','ownership':topology,'views':{},'closures':{},'limits':'Analytical manifold/finite/attachment/budget/projection checks plus actual pixels; no claim of exhaustive triangle self-intersection proof.','rigRepair':'Actual seven bones XYZ matching Euler channels; evaluated matrices/vertices below.'}
for clip in record['clips']:
 for direction in FACINGS:
  ledger=measure['views'].setdefault(direction,[])
  for frame in range(1,13):
   dg=pose(clip,frame,direction);r,_=inspect(clip,frame,direction,dg);ledger.append(r)
 samples={}
 for frame in [1,12,13,24]:
  dg=pose(clip,frame,'S');r,pp=inspect(clip,frame,'S',dg);samples[frame]=(r,pp)
 measure['closures'][clip]={'loop':recipes[clip]['loop'],'maxVertexDelta1to13':float(np.linalg.norm(samples[1][1]-samples[13][1],axis=1).max()),'maxVertexDelta12to13':float(np.linalg.norm(samples[12][1]-samples[13][1],axis=1).max()),'maxVertexDelta12to24':float(np.linalg.norm(samples[12][1]-samples[24][1],axis=1).max()),'controls':{str(k):v[0] for k,v in samples.items()}}
(C/'native-measurements.json').write_text(json.dumps(measure,indent=2)+'\n')
fail=[(f,r['clip'],r['frame'],r['canonicalSEvaluatedBounds']) for f,rs in measure['views'].items() for r in rs if not r['withinCanonicalBudget'] or not r['finite'] or not r['projectedInsideFrame'] or r['headAttachmentVertexResidual']>1e-5]
print('MEASURED',sum(len(v) for v in measure['views'].values()),'FAIL',len(fail),json.dumps(fail[:12]),flush=True)
if fail:raise RuntimeError('Native candidate failed allphase geometry budget/attachment/frame checks')
if '--measure-only' in sys.argv:sys.exit()
jobs=[('normal',f,1) for f in FACINGS]+[('caught','E',6)] if STUDY else [(clip,f,frame) for clip in record['clips'] for f in FACINGS for frame in range(1,13)]
if not STUDY:
 jobs += [(clip,'S',13) for clip in list(record['clips'])[:8]]+[(clip,'S',frame) for clip in list(record['clips'])[8:] for frame in [13,24]]
captures=[]
for idx,(clip,direction,frame) in enumerate(jobs):
 dg=pose(clip,frame,direction);r,_=inspect(clip,frame,direction,dg)
 p=C/('native' if frame<=12 else 'controls')/clip/direction/f'{frame-1:03}.png';p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  sc.render.filepath=str(p);t=time.monotonic();bpy.ops.render.render(write_still=True,scene=sc.name);elapsed=time.monotonic()-t
 else:elapsed=None
 r.update({'path':str(p.relative_to(E)),'sha256':sha(p),'nativeDimensions':[1792,2048],'renderSeconds':elapsed,'captureProjectSHA256':PROJECT_SHA})
 captures.append(r)
 (C/'capture-records.json').write_text(json.dumps({'asset':'creature-eel','projectSHA256':PROJECT_SHA,'nativeFrame':[1792,2048],'nativeScale':4,'camera':'native-camera.json','records':captures},indent=2)+'\n')
 print('CAPTURE',idx+1,len(jobs),clip,direction,frame,elapsed,flush=True)
assert sha(PROJECT)==PROJECT_SHA
print('FINISHED',len(captures),flush=True)
