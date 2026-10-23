import bpy,sys,json,math,hashlib,importlib.util
sys.dont_write_bytecode=True
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import numpy as np
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-car');C=P/'candidates/round-01';O=P/'reviews/round-01-independent'
spec=importlib.util.spec_from_file_location('independent_car_A',P/'source/resources/native_actions.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
rig=json.loads((P/'inputs/source-rig.json').read_text());mapping=json.loads((C/'semantic-mapping.json').read_text());originalActions=json.loads((P/'reviews/source-inspection/source-actions.json').read_text());originalFrames=json.loads((P/'reviews/source-inspection/evaluated-native-frames.json').read_text())['frames'];expected={(x['clip'],x['direction'],x['runtimeIndex']):x for x in originalFrames}
sc=bpy.context.scene;root=bpy.data.objects['garbage-car__root'];coll=root.users_collection[0];asset={'root':root,'collection':coll};cam=sc.camera;objs=list(coll.all_objects);meshes=[x for x in objs if x.type=='MESH'];errors=[]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(c,s):
 if not c:errors.append(s)
def maxerr(x,y):
 if isinstance(x,(list,tuple)):return max((maxerr(a,b) for a,b in zip(x,y)),default=0)
 return abs(x-y)
def jsave(name,d):(O/name).write_text(json.dumps(d,indent=2)+'\n')
def px(p):
 v=world_to_camera_view(sc,cam,Vector(p));return np.array([v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y])
p0=px((0,0,0));basis=np.array([px((1,0,0))-p0,px((0,1,0))-p0,px((0,0,1))-p0])
camera={'matrix':[list(r) for r in cam.matrix_world],'projection':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'root':p0.tolist(),'unitX':basis[0].tolist(),'unitDepth':(-basis[1]).tolist(),'unitHeight':basis[2].tolist()}
def geometry():
 deps=bpy.context.evaluated_depsgraph_get();rows=[];pts=[]
 for obj in meshes:
  ev=obj.evaluated_get(deps);me=ev.to_mesh();coords=np.empty(len(me.vertices)*3,dtype=np.float64);me.vertices.foreach_get('co',coords);local=coords.reshape((-1,3));m=np.array(ev.matrix_world);v=local@m[:3,:3].T+m[:3,3];ev.to_mesh_clear()
  if not len(v):continue
  rows.append({'name':obj.name,'parent':obj.parent.name if obj.parent else None,'bounds':[v.min(axis=0).tolist(),v.max(axis=0).tolist()],'visible':not obj.hide_render,'evaluatedVertices':len(v)})
  if not obj.hide_render:pts.append(v)
 allpts=np.concatenate(pts);pixels=allpts@basis+p0
 return {'bounds':[allpts.min(axis=0).tolist(),allpts.max(axis=0).tolist()],'projectedBounds':[pixels.min(axis=0).tolist(),pixels.max(axis=0).tolist()],'meshes':rows}
keyErrors=[];curveErrors=[]
for src in originalActions:
 action=bpy.data.actions.get(src['owner']['action']);require(action is not None,'missing action '+src['owner']['action'])
 if action is None:continue
 curves={(fc.data_path,fc.array_index):fc for fc in A._fcurves(action)};require(len(curves)==len(src['curves']),'curve count '+action.name)
 for e in src['curves']:
  fc=curves.get((e['path'],e['arrayIndex']));require(fc is not None,'missing curve '+action.name)
  if fc is None:continue
  require(len(fc.keyframe_points)==len(e['keys']),'keys '+action.name)
  for a,b in zip(fc.keyframe_points,e['keys']):
   keyErrors.append(max(abs(a.co.x-b['frame']),abs(a.co.y-b['value'])));require(a.interpolation==b['interpolation'],'interpolation '+action.name)
for name in mapping['carriers']:require(bpy.data.objects[name].type=='EMPTY','renderable old carrier '+name)
for obj in meshes:require(obj.name in mapping['renderableToCarrier'] and obj.parent and obj.parent.name==mapping['renderableToCarrier'][obj.name],'mesh carrier mapping '+obj.name)
def apply(clip,fr,d):
 A.apply_clip(asset,rig,clip,1,d,sc);sc.frame_set(math.floor(fr),subframe=fr%1);bpy.context.view_layer.update()
def sample(clip,d,fr,index=None):
 apply(clip,fr,d);g=geometry();carriers={n:{'location':list(bpy.data.objects[n].location),'rotationEuler':list(bpy.data.objects[n].rotation_euler),'scale':list(bpy.data.objects[n].scale)} for n in mapping['carriers']};e=0
 if index is not None:
  old={x['name']:x for x in expected[clip,d,index]['geometry']['objects']}
  e=max(maxerr(carriers[n][key],old[n][key]) for n in carriers for key in ['location','rotationEuler','scale']);require(e<=1e-5,'source trajectory '+str((clip,d,index)))
 env=[[-2.2091472339630127,-1.4355429601669312,-0.02999999511986971],[1.9866531085968018,1.416859884262085,3.069006700515747]] if clip=='clearance' else [[-1.51,-1,-.015],[1.5,1,1.32]]
 # All sampled facings are cardinal. Rotate world corners to source orientation.
 z=root.rotation_euler.z;c,s=math.cos(-z),math.sin(-z);corners=np.array([[c*x-s*y,s*x+c*y,h] for x in [g['bounds'][0][0],g['bounds'][1][0]] for y in [g['bounds'][0][1],g['bounds'][1][1]] for h in [g['bounds'][0][2],g['bounds'][1][2]]]);canonical=[corners.min(axis=0).tolist(),corners.max(axis=0).tolist()];excess=max([env[0][i]-canonical[0][i] for i in range(3)]+[canonical[1][i]-env[1][i] for i in range(3)]+[0]);require(excess<=2e-6,'envelope '+str((clip,d,fr,excess)))
 require(g['projectedBounds'][0][0]>0 and g['projectedBounds'][0][1]>0 and g['projectedBounds'][1][0]<1152 and g['projectedBounds'][1][1]<1664,'capture clipping '+str((clip,d,fr)))
 return {'clip':clip,'direction':d,'nativeFrame':fr,'index':index,'sourceCarrierMaxError':e,'rootMatrix':[list(r) for r in root.matrix_world],'geometry':g,'sourceOrientationBounds':canonical,'envelopeExcess':excess,'carriers':carriers}
frames=[]
for clip in ['idle','highlighted','clearance']:
 for d in ['N','E','S','W']:
  for i in range(rig['clips'][clip]['frames']):frames.append(sample(clip,d,i+1,i))
closure=[sample('highlighted',d,13) for d in ['N','E','S','W']]
inbetweens=[]
for clip in ['highlighted','clearance']:
 for d in ['N','E','S','W']:
  for fr in [i+1.5 for i in range(12 if clip=='highlighted' else 11)]:inbetweens.append(sample(clip,d,fr))
jsave('evaluated-candidate.json',{'frames':frames,'closure':closure,'inbetweens':inbetweens})
def nodes(tree):
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':{s.name:(list(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value) for s in n.inputs if hasattr(s,'default_value')},'image':getattr(getattr(n,'image',None),'name',None)} for n in tree.nodes],'links':[[x.from_node.name,x.from_socket.name,x.to_node.name,x.to_socket.name] for x in tree.links]}
def light(o):return {'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'shape':o.data.shape,'shadow':o.data.use_shadow,'matrix':[list(r) for r in o.matrix_world],'receiver':getattr(o.light_linking.receiver_collection,'name',None)}
compositor_tree=getattr(sc,'node_tree',None) or getattr(sc,'compositing_node_group',None)
mechanism={'projectSHA256':sha(bpy.data.filepath),'blenderVersion':bpy.app.version_string,'scene':sc.name,'collection':coll.name,'camera':camera,'objectCount':len(objs),'meshCount':len(meshes),'mappedMeshCount':len(mapping['renderableToCarrier']),'carriers':list(mapping['carriers']),'keyMaxError':max(keyErrors),'errors':errors,'lights':[light(o) for o in sc.objects if o.type=='LIGHT'],'world':nodes(sc.world.node_tree),'compositor':nodes(compositor_tree) if compositor_tree else None,'materials':[{'name':m.name,'nodes':nodes(m.node_tree),'nodeTreeAnimation':bool(m.node_tree.animation_data)} for m in bpy.data.materials if m.users and m.use_nodes],'resources':{'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'filepath':x.filepath,'source':x.source,'packed':bool(x.packed_file)} for x in bpy.data.images],'foreignParent':[x.name for x in objs if x.parent and x.parent not in objs],'constraints':[{'name':x.name,'type':c.type} for x in objs for c in x.constraints],'drivers':[{'name':x.name,'path':c.data_path} for x in objs if x.animation_data for c in x.animation_data.drivers]},'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'denoising':sc.cycles.use_denoising,'filmTransparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma}}
jsave('native-candidate-audit.json',mechanism)
print('AUDIT COMPLETE',len(frames),len(inbetweens),len(meshes),'errors',errors,'max key',max(keyErrors),flush=True)
if '--render' in sys.argv:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 for device in prefs.devices:device.use=device.type=='METAL'
 for d in ['N','E','S','W']:
  apply('idle',1,d);sc.render.filepath=str(O/f'independent-idle-{d}.png');bpy.ops.render.render(write_still=True)
 apply('clearance',6,'S');sc.render.filepath=str(O/'independent-clearance-S-index05.png');bpy.ops.render.render(write_still=True)
 # Supplementary construction diagnostic only: new camera below vehicle, no source save.
 apply('idle',1,'S');cam.location=(3,-4,-3);target=Vector((0,0,.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=3.5;cam.data.shift_x=0;cam.data.shift_y=0;sc.render.resolution_x=1200;sc.render.resolution_y=1000;sc.render.pixel_aspect_x=1;sc.render.filepath=str(O/'independent-underside.png');bpy.ops.render.render(write_still=True)
 print('INDEPENDENT RENDERS COMPLETE',flush=True)
