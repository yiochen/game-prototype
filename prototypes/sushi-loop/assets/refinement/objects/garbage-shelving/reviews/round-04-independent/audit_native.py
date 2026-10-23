import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
O=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-shelving');OUT=O/'reviews/round-04-independent';B=O/'candidates/round-04';R=json.loads((B/'rig.json').read_text());ORIG=json.loads((O/'reviews/source-audit/native-audit.json').read_text());BP=json.loads((O/'brief.json').read_text());S=bpy.context.scene;C=bpy.data.collections['S33_PROP_garbage-shelving'];ROOT=bpy.data.objects['garbage-shelving__root'];OBS=list(C.all_objects)
def pl(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 if isinstance(x,dict):return {k:pl(v) for k,v in x.items()}
 try:return [pl(v) for v in x]
 except:return str(x)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def curves(a):
 result=[]
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for f in bag.fcurves:result.append(f)
 return result
def assign(c,f,d):
 for o in OBS:
  if o.animation_data:
   o.animation_data.action=None
   for tr in o.animation_data.nla_tracks:tr.mute=True
 for e in R['clips'][c]['actions']:
  owner=bpy.data.objects[e['ownerName']];act=bpy.data.actions[e['action']];owner.animation_data_create();owner.animation_data.action=act;owner.animation_data.action_slot=next(sl for sl in act.slots if sl.identifier==e['slotIdentifier'])
 ROOT.rotation_euler=(0,0,{'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d]);S.frame_set(int(f),subframe=float(f)%1);bpy.context.view_layer.update()
origActions={x['action']:x for x in ORIG['actions']};actionChecks=[]
for c,cf in R['clips'].items():
 for e in cf['actions']:
  ac=bpy.data.actions[e['action']];vals={(f.data_path,f.array_index):[[float(k.co.x),float(k.co.y),k.interpolation] for k in f.keyframe_points] for f in curves(ac)};old={(f['dataPath'],f['index']):f['keys'] for f in origActions[e['action']]['curves']};actionChecks.append({'clip':c,'owner':e['ownerName'],'action':ac.name,'exactSourceCurveKeys':vals==old,'paths':sorted(set(k[0] for k in vals))})
materials={sl.material for o in OBS if o.type=='MESH' for sl in o.material_slots if sl.material};matinfo=[]
for m in sorted(materials,key=lambda x:x.name):
 matinfo.append({'name':m.name,'library':m.library.filepath if m.library else None,'materialAnimation':bool(m.animation_data and (m.animation_data.action or m.animation_data.drivers)),'nodeAnimation':bool(m.node_tree.animation_data and (m.node_tree.animation_data.action or m.node_tree.animation_data.drivers)),'nodes':[{'name':n.name,'type':n.type,'image':n.image.filepath if hasattr(n,'image') and n.image else None,'inputs':{v.name:pl(v.default_value) for v in n.inputs if hasattr(v,'default_value') and not v.is_linked}} for n in m.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links]})
objinfo=[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'library':o.library.filepath if o.library else None,'location':pl(o.location),'properties':pl(dict(o.items())),'meshVertices':len(o.data.vertices) if o.type=='MESH' else None,'meshFaces':len(o.data.polygons) if o.type=='MESH' else None,'meshDataLibrary':o.data.library.filepath if o.data and o.data.library else None,'constraints':[{'type':c.type,'target':getattr(getattr(c,'target',None),'name',None)} for c in o.constraints],'modifiers':[{'type':m.type,'target':getattr(getattr(m,'object',None),'name',None)} for m in o.modifiers],'driverPaths':[d.data_path for d in o.animation_data.drivers] if o.animation_data else [],'shapeKeys':bool(o.type=='MESH' and o.data.shape_keys)} for o in OBS]
phases=[];contacts=[];renders=[]
for d in ['S','E','N','W']:
 for c,cf in R['clips'].items():
  fs=[float(i+1) for i in range(cf['frames'])]
  if c=='highlighted':fs.append(13.)
  if c!='idle':
   last=13 if c=='highlighted' else 12
   fs+= [i+q for i in range(1,last) for q in [.25,.5,.75]]
  for f in sorted(fs):
   assign(c,f,d);dg=bpy.context.evaluated_depsgraph_get();vs=[];oo=[]
   for o in OBS:
    row={'name':o.name,'location':pl(o.location),'rotation':pl(o.rotation_euler),'scale':pl(o.scale),'matrix':pl(o.matrix_world),'hiddenRender':o.hide_render,'hiddenViewport':o.hide_viewport}
    if o.type=='MESH':
     eo=o.evaluated_get(dg);me=eo.to_mesh();v=[eo.matrix_world@v.co for v in me.vertices];vs+=v;row.update(boundsMin=[min(x[i] for x in v) for i in range(3)],boundsMax=[max(x[i] for x in v) for i in range(3)],evaluatedMeshLocalSHA256=hashlib.sha256(json.dumps([list(x.co) for x in me.vertices]).encode()).hexdigest())
     if c=='idle' and d=='S' and ('old_upright' in o.name or 'fallen_board' in o.name or 'loose_debris' in o.name):
      z=min(x.z for x in v);low=[x for x in v if x.z<=z+.002];contacts.append({'owner':o.name,'minimumZ':z,'lowBandVertices':[list(x) for x in low],'lowBandCentroid':[sum(x[i] for x in low)/len(low) for i in range(3)]})
     eo.to_mesh_clear()
    oo.append(row)
   local=[ROOT.matrix_world.inverted()@v for v in vs];proj=[world_to_camera_view(S,S.camera,v) for v in vs]
   phases.append({'clip':c,'direction':d,'frame1':f,'rootMatrix':pl(ROOT.matrix_world),'rootLocation':pl(ROOT.location),'rootScale':pl(ROOT.scale),'rootLocalMin':[min(v[i] for v in local) for i in range(3)],'rootLocalMax':[max(v[i] for v in local) for i in range(3)],'projectedNativeBounds':[min(p.x*896 for p in proj),min((1-p.y)*1344 for p in proj),max(p.x*896 for p in proj),max((1-p.y)*1344 for p in proj)],'cameraMatrix':pl(S.camera.matrix_world),'objects':oo})
   if (c=='idle' and f==1) or (c=='highlighted' and f==4) or (c=='clearance' and f in [6,12]):
    p=OUT/'native-rerender'/f'{c}-{d}-{int(f):02d}.png';p.parent.mkdir(exist_ok=True);S.render.filepath=str(p);bpy.ops.render.render(write_still=True);renders.append({'path':str(p),'clip':c,'direction':d,'frame1':f,'sha256':sha(p)})
   print('JUDGE_PHASE',d,c,f,flush=True)
final={'project':bpy.data.filepath,'projectSHA256':sha(bpy.data.filepath),'packetSHA256':sha(B/'packet.json'),'briefSHA256':sha(O/'brief.json'),'blenderVersion':bpy.app.version_string,'scene':S.name,'activeCamera':S.camera.name,'camera':{'matrix':pl(S.camera.matrix_world),'projection':pl(S.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=S.render.resolution_x,y=S.render.resolution_y,scale_x=S.render.pixel_aspect_x,scale_y=S.render.pixel_aspect_y)),'orthoScale':S.camera.data.ortho_scale,'shift':[S.camera.data.shift_x,S.camera.data.shift_y],'pixelAspect':[S.render.pixel_aspect_x,S.render.pixel_aspect_y]},'render':{'frame':[S.render.resolution_x,S.render.resolution_y],'transparent':S.render.film_transparent,'engine':S.render.engine,'fps':S.render.fps,'viewTransform':S.view_settings.view_transform,'exposure':S.view_settings.exposure,'gamma':S.view_settings.gamma},'objects':objinfo,'sceneMeshes':[o.name for o in S.objects if o.type=='MESH'],'materials':matinfo,'libraries':[{'path':l.filepath,'absolute':bpy.path.abspath(l.filepath),'exists':Path(bpy.path.abspath(l.filepath)).exists(),'sha256':sha(bpy.path.abspath(l.filepath)) if Path(bpy.path.abspath(l.filepath)).exists() else None} for l in bpy.data.libraries],'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'lights':[{'name':o.name,'type':o.data.type,'position':pl(o.location),'rotation':pl(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'color':pl(o.data.color)} for o in S.objects if o.type=='LIGHT'],'actionChecks':actionChecks,'contacts':contacts,'phases':phases,'independentSampleRenders':renders,'noBlendSavePerformed':True}
(OUT/'native-independent-audit.json').write_text(json.dumps(final,indent=2)+'\n')
print('JUDGE_AUDIT_DONE',len(phases),len(renders),flush=True)
