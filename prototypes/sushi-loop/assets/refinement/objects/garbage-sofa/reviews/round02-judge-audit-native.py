import bpy, json, pathlib, hashlib, math, bisect
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
O=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-sofa');R=O/'reviews';P=O/'candidates/round-02'
SRC=pathlib.Path(bpy.data.filepath);source_sha=hashlib.sha256(SRC.read_bytes()).hexdigest();sc=bpy.context.scene
root=bpy.data.objects['garbage-sofa__root'];coll=next(c for c in bpy.data.collections if root in list(c.objects));rig=json.loads((O/'inputs/source-rig.json').read_text());original=json.loads((R/'source-audit-raw.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(m):return [[float(v)for v in row]for row in m]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def curves(a):
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    yield from bag.fcurves
def assign(clip):
 for o in coll.all_objects:
  if o.animation_data:
   o.animation_data.action=None
   for t in o.animation_data.nla_tracks:t.mute=True
 for t in rig['clips'][clip]['actions']:
  o=bpy.data.objects[t['ownerName']];a=bpy.data.actions[t['action']];o.animation_data_create();o.animation_data.action=a
  slot=next(s for s in a.slots if s.identifier==t['slotIdentifier']);o.animation_data.action_slot=slot
def setframe(f,d='S'):
 root.rotation_euler.z={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d]
 sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
def bounds(ps):return {'min':[min(p[i] for p in ps)for i in range(3)],'max':[max(p[i] for p in ps)for i in range(3)]}
def measure(contacts=False):
 dg=bpy.context.evaluated_depsgraph_get();inv=root.matrix_world.inverted();ps=[];parts=[]
 for o in coll.all_objects:
  if o.type not in ('MESH','CURVE'):continue
  ev=o.evaluated_get(dg);m=ev.to_mesh();v=[inv@ev.matrix_world@v.co for v in m.vertices];ps+=v
  p={'name':o.name,'parent':o.parent.name if o.parent else None,'bounds':bounds(v),'vertices':len(m.vertices),'polygons':len(m.polygons)}
  if contacts:p['groundPoints']=[list(x)for x in v if abs(x.z)<=.002]
  parts.append(p);ev.to_mesh_clear()
 return bounds(ps),parts
def expected(c,f):
 ks=c['keys'];times=[k['co'][0]for k in ks];i=bisect.bisect_right(times,f)
 if i==0:return ks[0]['co'][1]
 if i==len(ks):return ks[-1]['co'][1]
 x,y=ks[i-1]['co'];xx,yy=ks[i]['co'];return y+(yy-y)*(f-x)/(xx-x)
out={'packetSHA256':sha(P/'packet.json'),'projectSHA256':source_sha,'briefSHA256':sha(O/'brief.json'),'blender':bpy.app.version_string,'scene':sc.name,'collection':coll.name,'actions':[],'samples':[],'fractionalSamples':[],'driverErrors':{},'objects':[]}
for clip in rig['clips']:
 for rec in original['actions'][clip]:
  a=bpy.data.actions[rec['action']];cs=[{'path':fc.data_path,'index':fc.array_index,'keys':[{'co':list(k.co),'interpolation':k.interpolation}for k in fc.keyframe_points]}for fc in curves(a)]
  out['actions'].append({'name':a.name,'sourceHash':rec['sha256'],'actualHash':digest(cs),'equal':digest(cs)==rec['sha256']})
 assign(clip);err={'location':0.,'rotation_euler':0.,'scale':0.}
 for d in ['N','E','S','W']:
  for f in range(1,rig['clips'][clip]['frames']+1):
   setframe(f,d);bb,parts=measure();out['samples'].append({'clip':clip,'direction':d,'frame':f,'localBounds':bb,'root':rows(root.matrix_world),'parts':parts})
 for i in range((rig['clips'][clip]['frames']-1)*4+1):
  f=1+i/4;setframe(f);bb,parts=measure()
  for rec in original['actions'][clip]:
   ob=bpy.data.objects[rec['ownerName']]
   for c in rec['curves']:
    actual=getattr(ob,c['path'])[c['index']];err[c['path']]=max(err[c['path']],abs(actual-expected(c,f)))
  out['fractionalSamples'].append({'clip':clip,'frame':f,'bounds':bb})
 out['driverErrors'][clip]=err
 if clip=='highlighted':
  setframe(1);first={t['ownerName']:rows(bpy.data.objects[t['ownerName']].matrix_local)for t in rig['clips'][clip]['actions']};setframe(13);out['closureMaxMatrixError']=max(abs(bpy.data.objects[n].matrix_local[i][j]-m[i][j])for n,m in first.items()for i in range(4)for j in range(4))
assign('idle');setframe(1);out['idleBounds'],out['idleParts']=measure(True);dg=bpy.context.evaluated_depsgraph_get()
for o in coll.all_objects:
 ob={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'constraints':[c.type for c in o.constraints],'drivers':len(o.animation_data.drivers)if o.animation_data else 0,'semanticCarrier':o.get('semantic_carrier',o.get('semantic_source_role')),'modifiers':[{'name':m.name,'type':m.type}for m in o.modifiers]}
 if o.type in('MESH','CURVE'):
  ev=o.evaluated_get(dg);m=ev.to_mesh();edges={tuple(sorted(e.vertices)):0 for e in m.edges}
  for p in m.polygons:
   for k in p.edge_keys:edges[tuple(sorted(k))]=edges.get(tuple(sorted(k)),0)+1
  ob['topology']={'vertices':len(m.vertices),'faces':len(m.polygons),'boundaryEdges':sum(v==1 for v in edges.values()),'nonmanifoldEdges':sum(v!=2 for v in edges.values()),'zeroAreaFaces':sum(p.area<1e-10 for p in m.polygons),'smoothFaces':sum(p.use_smooth for p in m.polygons)};ev.to_mesh_clear()
 out['objects'].append(ob)
cam=sc.camera
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
out['camera']={'name':cam.name,'matrix':rows(cam.matrix_world),'projectionMatrix':rows(cam.calc_matrix_camera(dg,x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'resolution':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'ortho':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'rootPx':px((0,0,0)),'XPx':px((1,0,0)),'DPx':px((0,-1,0)),'HPx':px((0,0,1)),'filmTransparent':sc.render.film_transparent}
out['materials']=[]
for m in bpy.data.materials:
 out['materials'].append({'name':m.name,'animated':bool(m.animation_data or(m.use_nodes and m.node_tree.animation_data)),'nodes':[{'name':n.name,'type':n.type,'inputs':{s.name:([float(v)for v in s.default_value]if hasattr(s.default_value,'__iter__')and not isinstance(s.default_value,str)else s.default_value)for s in n.inputs if hasattr(s,'default_value')and isinstance(s.default_value,(int,float,str,bool,Vector))},'image':n.image.name if n.type=='TEX_IMAGE'and n.image else None}for n in m.node_tree.nodes]if m.use_nodes else[],'links':[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name}for l in m.node_tree.links]if m.use_nodes else[]})
out['resources']={'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)}for i in bpy.data.images],'fonts':[f.filepath for f in bpy.data.fonts]}
out['lights']=[{'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)}for o in sc.objects if o.type=='LIGHT']
out['render']={'engine':sc.render.engine,'samples':sc.cycles.samples,'useDenoising':sc.cycles.use_denoising,'seed':sc.cycles.seed,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'worldNodes':[{'type':n.type,'strength':n.inputs['Strength'].default_value if n.type=='BACKGROUND'else None}for n in sc.world.node_tree.nodes]}
out['allActionsEqual']=all(a['equal']for a in out['actions']);out['sourceUnchanged']=sha(SRC)==source_sha
(R/'round02-judge-native-audit.json').write_text(json.dumps(out,indent=2)+'\n')
# Replay only a chosen witness. This diagnoses reproducibility of these settings, never all-frame identity.
assign('clearance');setframe(6,'E');sc.render.filepath=str(R/'round02-judge-witness-clearance-E-005.png');bpy.ops.render.render(write_still=True)
print('JUDGE_NATIVE_COMPLETE',json.dumps({'actionsEqual':out['allActionsEqual'],'driverErrors':out['driverErrors'],'samples':len(out['samples']),'fractionalSamples':len(out['fractionalSamples']),'bounds':out['idleBounds'],'sourceUnchanged':out['sourceUnchanged']}))
