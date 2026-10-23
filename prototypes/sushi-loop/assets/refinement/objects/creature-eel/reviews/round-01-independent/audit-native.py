import sys
sys.dont_write_bytecode=True
import bpy,bmesh,json,math,hashlib,importlib.util
import numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
J=Path(__file__).resolve().parent;O=J.parent.parent;C=O/'candidates/round-01'
spec=importlib.util.spec_from_file_location('judge_eel_native',str(J/'resources/native_actions.py'));N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
rig=json.loads((J/'resources/rig.json').read_text());reference=json.loads((C/'native-measurements.json').read_text());sourceSHA=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();assert sourceSHA=='cbc7592d1c77782dbd046312bd700d31b27675ccde05c889b0fe46c192f1989c'
sc=bpy.context.scene;cam=sc.camera;root=bpy.data.objects[rig['groundRootObject']];col=root.users_collection[0];arm=bpy.data.objects[rig['armatures'][0]['object']];meshes=sorted([o for o in col.all_objects if o.type=='MESH'],key=lambda o:o.name)
def enable(lc):
 if lc.collection==col or col in list(lc.collection.children_recursive):lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_render=False;lc.collection.hide_viewport=False
 for child in lc.children:enable(child)
enable(bpy.context.view_layer.layer_collection)
for o in col.all_objects:o.hide_set(False);o.hide_render=False;o.hide_viewport=False
bpy.context.view_layer.update();asset={'collection':col,'root':root};N._all_objects(asset)
def mat(m):return np.array(m,dtype=float)
def flat(m):return [list(r) for r in m]
def points(obj,dg,eval=True):
 e=obj.evaluated_get(dg) if eval else obj;me=e.to_mesh() if eval else e.data;v=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',v);v=v.reshape(-1,3);a=mat(e.matrix_world);v=v@a[:3,:3].T+a[:3,3]
 if eval:e.to_mesh_clear()
 return v
def bounds(v):return [v.min(0).tolist(),v.max(0).tolist()]
def maxdelta(a,b):return float(np.linalg.norm(a-b,axis=1).max())
def screen(v):
 base=world_to_camera_view(sc,cam,Vector(v));return [base.x*sc.render.resolution_x,(1-base.y)*sc.render.resolution_y]
origin=np.array(screen((0,0,0)));basis=np.array([np.array(screen(v))-origin for v in [(1,0,0),(0,1,0),(0,0,1)]])
result={'asset':'creature-eel','candidatePacketSHA256':hashlib.sha256((C/'packet.json').read_bytes()).hexdigest(),'projectSHA256':sourceSHA,'blenderVersion':bpy.app.version_string,'scene':sc.name,'collection':col.name,'root':root.name,'camera':{'object':cam.name,'type':cam.data.type,'worldMatrix':flat(cam.matrix_world),'projectionMatrix':flat(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'nativeRootPixel':origin.tolist(),'basis':basis.tolist()},'render':{'engine':sc.render.engine,'filterSize':sc.render.filter_size,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'filmTransparent':sc.render.film_transparent,'useCompositing':sc.render.use_compositing},'rotationModes':{b.name:b.rotation_mode for b in arm.pose.bones},'objects':[],'views':{},'clips':{},'closures':{},'replays':[],'failures':[]}
for o in col.all_objects:
 r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'modifiers':[{'type':m.type,'target':getattr(getattr(m,'object',None),'name',None),'render':m.show_render,'viewport':m.show_viewport} for m in o.modifiers],'constraints':[c.type for c in o.constraints]}
 if o.type=='MESH':
  bm=bmesh.new();bm.from_mesh(o.data);r.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),nonManifoldEdges=sum(not e.is_manifold for e in bm.edges),shapeKeys=[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],materials=[m.name for m in o.data.materials],headRigidAllVertices=(all(len(v.groups)==1 and o.vertex_groups[v.groups[0].group].name=='spine_0' and abs(v.groups[0].weight-1)<1e-6 for v in o.data.vertices) if any(s in o.name for s in ['eye_','mouth']) else None));bm.free()
 result['objects'].append(r)
result['externalImages']=[{'material':m.name,'image':n.image.filepath} for m in {m for o in meshes for m in o.data.materials} if m.use_nodes for n in m.node_tree.nodes if getattr(n,'image',None)]
result['lights']=[{'name':o.name,'location':list(o.location),'power':o.data.energy,'color':list(o.data.color),'size':o.data.size} for o in sc.objects if o.type=='LIGHT'];result['sockets']=json.loads(root['sockets'])
all_body={};bone_mats={};ledger_ref={(f,r['clip'],r['frame']):r for f,rows in reference['views'].items() for r in rows}
for clip,cfg in rig['clips'].items():
 all_body[clip]=[];bone_mats[clip]=[]
 for f in ['N','E','S','W']:
  rows=result['views'].setdefault(f,[])
  for fr in range(1,13):
   N.apply_clip(asset,rig,clip,fr,f,sc);dg=bpy.context.evaluated_depsgraph_get();ea=arm.evaluated_get(dg);by={o.name:points(o,dg) for o in meshes};pp=np.concatenate(list(by.values()));canonical=pp@mat(root.matrix_world)[:3,:3];screenpp=pp@basis+origin
   bones={b.name:flat(ea.matrix_world@b.matrix) for b in ea.pose.bones};head=mat(ea.matrix_world@ea.pose.bones[0].matrix@arm.data.bones[0].matrix_local.inverted());headResidual=0
   for o in meshes:
    if any(s in o.name for s in ['eye_','mouth']):
     verts=np.array([v.co[:] for v in o.data.vertices]);want=verts@head[:3,:3].T+head[:3,3];headResidual=max(headResidual,maxdelta(by[o.name],want))
   bb=bounds(canonical);safe=all(bb[0][i]>=(-1.3,-.75,.04)[i]-1e-5 and bb[1][i]<=(1.3,1.45,1.)[i]+1e-5 for i in range(3));ref=ledger_ref[f,clip,fr];boxdiff=float(np.abs(np.array(bounds(pp))-np.array(ref['evaluatedBounds'])).max());bonediff=max(float(np.abs(np.array(bones[n])-np.array(ref['evaluatedBoneWorldMatrices'][n])).max()) for n in bones)
   rec={'clip':clip,'direction':f,'frame':fr,'rootRotationZ':root.rotation_euler.z,'rootMatrix':flat(root.matrix_world),'rootLocation':list(root.location),'cameraWorldMatrix':flat(cam.matrix_world),'nativeRootPixel':screen((0,0,0)),'evaluatedBounds':bounds(pp),'canonicalSEvaluatedBounds':bb,'insideBudget':safe,'finite':bool(np.isfinite(pp).all()),'projectedNativeBounds':bounds(screenpp),'insideFrame':bool((screenpp.min(0)>1).all() and (screenpp.max(0)<[1791,2047]).all()),'headAttachmentResidual':headResidual,'submittedBoundsMaxDelta':boxdiff,'submittedBoneWorldMatricesMaxDelta':bonediff}
   if not safe or not rec['finite'] or not rec['insideFrame'] or headResidual>1e-5 or boxdiff>1e-5 or bonediff>1e-5 or max(abs(v) for v in root.location)>1e-7:result['failures'].append([f,clip,fr,rec])
   rows.append(rec)
   if f=='S':
    inv=mat(ea.matrix_world.inverted());bp=by[next(n for n in by if 'continuous_body' in n)];all_body[clip].append(bp@inv[:3,:3].T+inv[:3,3]);bone_mats[clip].append({b.name:mat(b.matrix) for b in ea.pose.bones})
 values={}
 for fr in [1,12,13,24]:
  N.apply_clip(asset,rig,clip,fr,'S',sc);dg=bpy.context.evaluated_depsgraph_get();values[fr]=np.concatenate([points(o,dg) for o in meshes])
 result['closures'][clip]={'loop':cfg['loop'],'maxVertexDelta1to13':maxdelta(values[1],values[13]),'maxVertexDelta12to13':maxdelta(values[12],values[13]),'maxVertexDelta12to24':maxdelta(values[12],values[24]),'maxVertexDelta1to12':maxdelta(values[1],values[12])}
 result['clips'][clip]={'actualRigRelativeBodyMaxDeltaFromPhase1':max(maxdelta(a,all_body[clip][0]) for a in all_body[clip]),'actualRigRelativeBoneMatrixMaxDeltaFromPhase1':max(float(np.abs(b[name]-bone_mats[clip][0][name]).max()) for b in bone_mats[clip] for name in b),'nativeFrames':12,'fps':12,'loop':cfg['loop']}
# Independently render bounded exact saved-source representatives; no capture recipe changes or candidate writes.
replay_jobs=[('normal',f,1) for f in ['N','E','S','W']]+[('caught','E',7),('restless','W',4),('pursuit','N',9),('weave','S',4),('dash','E',4),('escape','N',6),('aim','W',4),('pause','N',4),('hook','S',6)]
for clip,f,fr in replay_jobs:
 N.apply_clip(asset,rig,clip,fr,f,sc);p=J/'replay'/clip/f/f'{fr-1:03}.png';p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True,scene=sc.name);result['replays'].append({'path':str(p.relative_to(O)),'submittedPath':f'candidates/round-01/native/{clip}/{f}/{fr-1:03}.png','clip':clip,'direction':f,'frame':fr,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(J/'native-audit.json').write_text(json.dumps(result,indent=2)+'\n');assert not result['failures'],result['failures'][:1];print('NATIVE_AUDIT_PASS',sum(map(len,result['views'].values())),len(result['replays']),result['clips'],flush=True)
