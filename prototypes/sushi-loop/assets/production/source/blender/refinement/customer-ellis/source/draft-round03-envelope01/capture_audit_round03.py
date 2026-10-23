"""Capture all required actual native frames with source-bound contact/bounds evidence."""
import bpy, json, sys, math, hashlib, importlib.util, time
from pathlib import Path
from mathutils import Vector
import numpy as np
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['main']
MODE=args[0];RENDER='measure' not in args
OUT=OBJ/'candidates/round-03';OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('ellis_native',HERE/'resources/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
rec=json.loads((HERE/'resources'/f'{MODE}-rig.json').read_text())
baseline=json.loads((OBJ/'reviews'/f'{MODE}-audit.json').read_text())
brief=json.loads((OBJ/'brief.json').read_text());env=brief['constraints']['functionalGeometryEnvelope']
mapping=json.loads((OBJ/'reviews/proposed-food-mappings.json').read_text())['dish-cucumber' if MODE=='main' else 'dish-salmon']
root=bpy.data.objects[rec['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects)
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
coll=next(c for c in sc.collection.children if root.name in c.all_objects);asset={'root':root,'collection':coll}
arm=next(o for o in coll.all_objects if o.type=='ARMATURE');food=next(o for o in coll.all_objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi')
sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.fps=12
cam=sc.camera
from bpy_extras.object_utils import world_to_camera_view
def plain(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [plain(a) for a in v]
 except:return str(v)
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def project(p):
 q=world_to_camera_view(sc,cam,Vector(p));return [q.x*384,(1-q.y)*640,q.z]
def coords(o,dg):
 e=o.evaluated_get(dg);m=e.to_mesh();a=np.empty(len(m.vertices)*3,dtype=np.float64);m.vertices.foreach_get('co',a);a=a.reshape((-1,3));mat=np.array(e.matrix_world);a=a@mat[:3,:3].T+mat[:3,3];e.to_mesh_clear();return a
def bounds(a):return [a.min(axis=0).tolist(),a.max(axis=0).tolist()]
def maxerr(a,b):return float(np.max(np.abs(np.array(a)-np.array(b))))
rest=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':plain(b.head_local),'tail':plain(b.tail_local),'matrix':plain(b.matrix_local),'deform':b.use_deform} for b in arm.data.bones]
actions={}
for clip,c in rec['clips'].items():
 actions[clip]=[]
 for t in c['actions']:
  a=bpy.data.actions[t['action']];curves=[{'path':f.data_path,'index':f.array_index,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in f.keyframe_points]} for f in native._fcurves(a)]
  actions[clip].append({**t,'curveDigest':digest(curves)})
base={(s['clip'],s['direction'],s['frame']):s for s in baseline['samples']}
inventory=json.loads((HERE/'native-inventory.json').read_text())
restByName={b['name']:np.array(b['matrix']) for b in baseline['armature']['rest']}
palmWitnesses={}
for o in coll.all_objects:
 if o.type=='MESH' and ('__palm_' in o.name or '__thumb_' in o.name):
  original=next(x for x in inventory if x['name'].split('customer_ellis__')[-1]==o.name.split('customer_ellis__')[-1]);box=np.array(original['bounds']);co=(box.min(axis=0)+box.max(axis=0))/2;co[2]=box.max(axis=0)[2];palmWitnesses[o.name]={'local':co,'bone':original['groups'][0]}

report={'asset':'customer-ellis','mode':MODE,'renderer':bpy.app.version_string,'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'renderSettings':{'engine':sc.render.engine,'samples':sc.eevee.taa_render_samples,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'compositor':sc.use_nodes,'alpha':sc.render.image_settings.color_mode},'camera':{'name':cam.name,'matrix':plain(cam.matrix_world),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'rootProjection':project((0,0,0)),'unitXProjection':project((1,0,0)),'unitYProjection':project((0,1,0)),'unitZProjection':project((0,0,1)),'logicalFrame':[192,320],'logicalRoot':[96,248],'captureScale':2},'armature':{'rest':rest,'restSHA256':digest(rest),'restCount':len(rest)},'actions':actions,'samples':[],'dependencies':[],'maxErrors':{'root':0,'contacts':0,'foodRoot':0,'foodPlane':0,'canonicalProjectedCorners':0,'semanticSupportProjected':0,'sourceSoleHeight':0,'sourcePalmCenters':0,'handSurfaceWitness':0},'envelopeFailures':[]}
for image in bpy.data.images:
 if image.packed_file:report['dependencies'].append({'type':'packed-image','name':image.name,'filepath':image.filepath,'sha256':hashlib.sha256(bytes(image.packed_file.data)).hexdigest(),'size':list(image.size)})
for lib in bpy.data.libraries:report['dependencies'].append({'type':'linked-library','path':lib.filepath})
report['bodyGeometry']={o.name:{'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'coordinateSHA256':digest([plain(v.co) for v in o.data.vertices]),'vertexGroups':[g.name for g in o.vertex_groups],'weightsSHA256':digest([[[g.group,g.weight] for g in v.groups] for v in o.data.vertices]),'modifiers':[{'type':m.type,'name':m.name,'object':getattr(getattr(m,'object',None),'name',None)} for m in o.modifiers],'materials':[m.name for m in o.data.materials]} for o in coll.all_objects if o.type=='MESH' and o!=food}
report['lights']=[{'name':o.name,'location':plain(o.location),'energy':o.data.energy,'size':o.data.size,'color':plain(o.data.color)} for o in sc.objects if o.type=='LIGHT' and not o.hide_render]
report['food']={'vertices':plain([v.co for v in food.data.vertices]),'UV':plain([uv.uv for uv in food.data.uv_layers.active.data]),'mappingCanonicalSHA256':mapping['canonicalTexture']['sha256'],'sourceVisibleWidthWorldCells':mapping['sourceVisibleWidthWorldCells'],'fullQuadWorld':[mapping['canonicalFullQuadWidthWorldCells'],mapping['canonicalFullQuadHeightWorldCells']],'depthScalar':.6,'threshold':128,'sensitivity':mapping['sensitivity'],'visible_shadow':food.visible_shadow,'surfaceRenderMethod':food.data.materials[0].surface_render_method,'drivers':[{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression} for f in food.animation_data.drivers]}
for clip,c in rec['clips'].items():
 for direction in ['N','E','S','W']:
  for frame in range(1,13):
   native.apply_clip(asset,rec,clip,frame,direction,sc)
   authored=food.hide_viewport;food.hide_viewport=False;food.hide_set(False);food.update_tag();bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
   visible=[o for o in coll.all_objects if o.type=='MESH' and o!=food and not o.hide_render]
   arrays=[coords(o,dg) for o in visible];world=np.concatenate(arrays);ri=np.array(root.matrix_world.inverted());local=world@ri[:3,:3].T+ri[:3,3]
   bone={b.name:{'head':plain(arm.matrix_world@b.head),'tail':plain(arm.matrix_world@b.tail),'matrix':plain(arm.matrix_world@b.matrix)} for b in arm.pose.bones if b.name in ['pelvis','spine','head','hand_L','hand_R','foot_L','foot_R','hand_goal_L','hand_goal_R','foot_goal_L','foot_goal_R']}
   b=base[(clip,direction,frame)];errors={'root':maxerr(plain(root.matrix_world),b['rootMatrix']),'contacts':max(maxerr(bone[k][v],b['contacts'][k][v]) for k in bone for v in bone[k]),'foodRoot':maxerr(plain(food.parent.matrix_world),b['food']['rootMatrix']),'foodPlane':maxerr(plain(food.matrix_world),b['food']['planeMatrix'])}
   expected=[np.array(b['food']['planeMatrix'])@np.array(v+[1]) for v in mapping['proposedVerticesPlaneLocal']]
   corners=coords(food,dg);errors['canonicalProjectedCorners']=max(maxerr(project(v)[:2],project(e[:3])[:2]) for v,e in zip(corners,expected))
   support=food.matrix_world@Vector(mapping['sourceSupportPlaneLocal']+[0]);source_support=np.array(b['food']['planeMatrix'])@np.array(mapping['sourceSupportPlaneLocal']+[0,1]);errors['semanticSupportProjected']=maxerr(project(support)[:2],project(source_support[:3])[:2])
   sole=[(o,a) for o,a in zip(visible,arrays) if 'minimal_foot_' in o.name or 'shoe_sole_' in o.name]
   oldsoles=[v for k,v in b['perMeshBoundsWorld'].items() if 'minimal_foot_' in k]
   palms=[(o,a) for o,a in zip(visible,arrays) if '__palm_' in o.name or '__thumb_' in o.name]
   errors['sourcePalmCenters']=max(float(np.max(np.abs(np.mean(bounds(a),axis=0)-np.mean(b['perMeshBoundsWorld'][o.name],axis=0)))) for o,a in palms)
   handWitnessEvidence={}
   for o,a in palms:
    w=palmWitnesses[o.name];matrix=np.array(b['contacts'][w['bone']]['matrix'])@np.linalg.inv(restByName[w['bone']])@np.array(arm.matrix_world.inverted())@np.array(root.matrix_world);expected=(matrix@np.append(w['local'],1))[:3];distances=np.linalg.norm(a-expected,axis=1);nearest=a[int(distances.argmin())];handWitnessEvidence[o.name]={'intendedBone':w['bone'],'actualGroups':[g.name for g in o.vertex_groups],'sourceSurfaceWitness':expected.tolist(),'nativeSurfaceWitness':nearest.tolist(),'errorWorld':float(distances.min())}
   errors['handSurfaceWitness']=max(x['errorWorld'] for x in handWitnessEvidence.values())
   errors['sourceSoleHeight']=abs(min(a[:,2].min() for o,a in sole)-min(v[0][2] for v in oldsoles))
   lo,hi=bounds(world);zmin,zmax=env['perClipBodyZWorld'][clip.replace('_','-')]
   if min(lo[0],lo[1])<-.50001 or max(hi[0],hi[1])>.50001 or lo[2]<zmin-1e-5 or hi[2]>zmax+1e-5:report['envelopeFailures'].append({'clip':clip,'direction':direction,'frame':frame,'actual':[lo,hi],'allowedZ':[zmin,zmax]})
   for k,v in errors.items():report['maxErrors'][k]=max(report['maxErrors'][k],v)
   sample={'clip':clip,'direction':direction,'frame':frame,'rootMatrix':plain(root.matrix_world),'nativeBodyBoundsWorld':[lo,hi],'nativeBodyBoundsRoot':bounds(local),'contacts':bone,'food':{'visible':not food.hide_render,'authoredHideViewport':authored,'rootMatrix':plain(food.parent.matrix_world),'planeMatrix':plain(food.matrix_world),'cornersWorld':corners.tolist(),'cornersProjected':[project(v) for v in corners],'semanticSupportProjected':project(support),'yaw':food.rotation_euler.z},'errors':errors,'handSurfaceWitnesses':handWitnessEvidence,'perMeshBoundsWorld':{o.name:bounds(a) for o,a in zip(visible,arrays)}}
   if RENDER:
    path=OUT/('frames' if MODE=='main' else 'runtime-frames')/(clip.replace('_','-')+'-'+direction)/f'{frame-1:03}.png';path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True,scene=sc.name);sample['render']=str(path.relative_to(OBJ));sample['renderSHA256']=hashlib.sha256(path.read_bytes()).hexdigest()
   report['samples'].append(sample)
  print('ELLIS_CAPTURE_PROGRESS',MODE,clip,direction,len(report['samples']),flush=True)
report['sampleCount']=len(report['samples']);report['sampleDigest']=digest(report['samples']);report['restMatchesSource']=report['armature']['restSHA256']==baseline['armature']['restSHA256']
report['actionsMatchSource']=all(all(a['curveDigest']==b['curveDigest'] for a,b in zip(actions[c],baseline['actions'][c])) for c in actions)
(OUT/(MODE+'-native-audit'+('' if RENDER else '-measure')+'.json')).write_text(json.dumps(report,separators=(',',':'))+'\n')
print('ELLIS_AUDIT_COMPLETE',MODE,report['sampleCount'],report['maxErrors'],'envelopeFailures',len(report['envelopeFailures']),'rest/actions',report['restMatchesSource'],report['actionsMatchSource'],flush=True)
