import bpy,sys,json,math,hashlib,time,bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;Q=R.parent;E=Q/'evidence';sys.path.insert(0,str(R));import native_actions as na
rig=json.loads((R/'rig.json').read_text());D=json.loads((R/'assetRecord.json').read_text());sc=bpy.context.scene;root=bpy.data.objects[rig['groundRootObject']];col=bpy.data.collections[D['collection']]
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
def layers(l):
 yield l
 for c in l.children:yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
col.hide_render=False;col.hide_viewport=False;sc.view_layers[0].update()
asset={'root':root,'collection':col};objs=list(col.all_objects)
def apply(clip,d,f):
 for o in objs:
  for owner in [o,o.data.shape_keys if o.type=='MESH' else None]:
   if owner is not None and owner.animation_data:
    owner.animation_data.action=None
    for tr in owner.animation_data.nla_tracks:tr.mute=True
  if o.type=='MESH' and o.data.shape_keys:
   for key in o.data.shape_keys.key_blocks[1:]:key.value=0
 for tar in rig['clips'][clip]['actions']:na._assign(bpy.data.objects[tar['ownerName']].data.shape_keys if tar['ownerType']=='Key' else na._resolve_owner(tar),bpy.data.actions[tar['action']],tar.get('slotIdentifier'))
 root.rotation_euler.z={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d];sc.frame_set(f);sc.view_layers[0].update()
def evalpts():
 dg=bpy.context.evaluated_depsgraph_get();out={}
 for o in objs:
  if o.type!='MESH':continue
  e=o.evaluated_get(dg);m=e.to_mesh();out[o.name]=[tuple(e.matrix_world@v.co) for v in m.vertices];e.to_mesh_clear()
 return out
def bounds(pts):return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
def plain(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 try:return list(v)
 except:return str(v)
apply('static','S',1);base=evalpts();objrows=[];rocktrees=[];tubes=[]
for o in objs:
 row={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'custom':{k:plain(o[k]) for k in o.keys()},'matrix':[list(r) for r in o.matrix_world],'modifiers':[{'type':m.type,'object':getattr(getattr(m,'object',None),'name',None)} for m in o.modifiers],'constraints':[{'type':c.type,'target':getattr(getattr(c,'target',None),'name',None)} for c in o.constraints],'drivers':len(o.animation_data.drivers) if o.animation_data else 0,'NLA':len(o.animation_data.nla_tracks) if o.animation_data else 0}
 if o.type=='MESH':
  bm=bmesh.new();bm.from_mesh(o.data);row.update(vertices=len(o.data.vertices),faces=len(o.data.polygons),nonManifoldEdges=sum(not e.is_manifold for e in bm.edges),degenerateFaces=sum(p.area<1e-12 for p in o.data.polygons),uv=list(o.data.uv_layers.keys()),colorAttributes=[{'name':a.name,'type':a.data_type,'domain':a.domain} for a in o.data.color_attributes],materials=[m.name for m in o.data.materials if m],shapeKeys=list(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else [],shapeKeyDatablockName=o.data.shape_keys.name if o.data.shape_keys else None,staticBounds=bounds(base[o.name]));bm.free()
  if o.data.shape_keys:tubes.append(o)
  # Actual role and finite native rock mesh, not AABB support inference.
  if 'rock' in str(o.get('role','')).lower() or o.name.lower().startswith('reef rock'):
   rocktrees.append((o,BVHTree.FromPolygons([Vector(p) for p in base[o.name]],[list(p.vertices) for p in o.data.polygons],all_triangles=False)))
 objrows.append(row)
# Fallback identifies native base-rock material-bearing meshes, excluding foliage/tubes/buttons.
if not rocktrees:
 for o in objs:
  if o.type=='MESH' and any('rock' in m.name.lower() or 'cobalt' in m.name.lower() for m in o.data.materials if m):rocktrees.append((o,BVHTree.FromPolygons([Vector(p) for p in base[o.name]],[list(p.vertices) for p in o.data.polygons],all_triangles=False)))
samples=[];contacts=[];closure=[];renderRecords=[]
for d in ['N','E','S','W']:
 for clip,frames in [('static',[1,13]),('idle',range(1,14))]:
  first=None
  for f in frames:
   apply(clip,d,f);ev=evalpts();pts=[p for v in ev.values() for p in v]
   if f==1:first=ev
   delta=max((Vector(p)-Vector(q)).length for n in ev for p,q in zip(ev[n],first[n]));samples.append({'direction':d,'clip':clip,'frame':f,'bounds':bounds(pts),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world],'maxDeltaFromFrame1':delta,'tubeShapeValues':{o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks[1:]} for o in tubes}})
   if f==13:closure.append({'clip':clip,'direction':d,'maxWorldVertexDelta1vs13':delta})
   if d=='S':
    for o in tubes:
     bp=base[o.name];z=min(p[2] for p in bp);ids=[i for i,p in enumerate(bp) if abs(p[2]-z)<1e-5];basal=[Vector(ev[o.name][i]) for i in ids];center=sum(basal,Vector())/len(basal);probe=[]
     for p in [center,*basal]:
      hits=[]
      for rock,tree in rocktrees:
       hit=tree.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)),3)[0]
       if hit is not None:hits.append({'rock':rock.name,'topZ':hit.z,'baseZ':p.z,'embed':hit.z-p.z})
      probe.append({'point':list(p),'embedded':any(-1e-5<=p.z<=h['topZ']+1e-5 for h in hits),'hits':hits})
     contacts.append({'clip':clip,'frame':f,'tube':o.name,'baseVertices':len(ids),'allEmbedded':all(p['embedded'] for p in probe),'minEmbedding':min((max(h['embed'] for h in p['hits']) for p in probe if p['hits']),default=None)})
   # Bounded independent replays all4 static + both extrema and closure in S; camera/materials/render settings loaded unchanged.
   if (clip=='static' and f==1) or (clip=='idle' and d=='S' and f in [1,7,13]):
    dest=E/'native-replay-v2'/clip/d/f'{f-1:03d}.png';dest.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(dest);t=time.monotonic();bpy.ops.render.render(write_still=True);renderRecords.append({'clip':clip,'direction':d,'index':f-1,'path':str(dest.relative_to(Q.parent.parent)),'rootMatrix':[list(r) for r in root.matrix_world],'rootRotationDegrees':math.degrees(root.rotation_euler.z),'renderSeconds':time.monotonic()-t,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
cam=sc.camera;dg=bpy.context.evaluated_depsgraph_get();px=lambda p:[world_to_camera_view(sc,cam,Vector(p)).x*sc.render.resolution_x,(1-world_to_camera_view(sc,cam,Vector(p)).y)*sc.render.resolution_y]
matset={m for o in objs if o.type=='MESH' for m in o.data.materials if m};mats=[]
for m in matset:mats.append({'name':m.name,'users':[o.name for o in bpy.data.objects if o.type=='MESH' and m in list(o.data.materials)],'nodes':[{'type':n.type,'name':n.name,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value') and not i.is_linked}} for n in m.node_tree.nodes] if m.node_tree else [],'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links] if m.node_tree else []})
actions=[{'clip':clip,'owner':t['ownerName'],'action':t['action'],'curves':[{'path':c.data_path,'index':c.array_index,'keys':[{'co':list(k.co),'interp':k.interpolation} for k in c.keyframe_points]} for c in na._fcurves(bpy.data.actions[t['action']])]} for clip,rr in rig['clips'].items() for t in rr['actions']]
report={'candidatePacketSHA256':hashlib.sha256((R/'packet.json').read_bytes()).hexdigest(),'sourceSHA256':hashlib.sha256((R/'selected.blend').read_bytes()).hexdigest(),'method':'Independent savedsource reopen; no construction/recipe import or source save. Active collection enabled before evaluated sampling. Rig ownerName uses mesh carrier identity for Key owners, matching provided native apply_clip; independently resolve mesh.data.shape_keys. V1 generic native_actions resolver failure retained, not hidden.','blender':bpy.app.version_string,'buildHash':bpy.app.build_hash.decode(),'scene':sc.name,'collection':col.name,'objects':objrows,'materials':mats,'actions':actions,'samples':samples,'contactSummary':{'rockMeshes':[o.name for o,_ in rocktrees],'allTubeBasalVerticesEmbedded':all(r['allEmbedded'] for r in contacts),'contacts':contacts},'closure':closure,'renderRecords':renderRecords,'camera':{'name':cam.name,'matrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'frameStartEnd':[sc.frame_start,sc.frame_end],'fps':sc.render.fps,'fpsBase':sc.render.fps_base,'calibration':{'root':px((0,0,0)),'unitX':px((1,0,0)),'unitDepth':px((0,-1,0)),'unitHeight':px((0,0,1))}},'render':{'engine':sc.render.engine,'filterSize':sc.render.filter_size,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'animatedSeed':sc.cycles.use_animated_seed,'filmTransparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'compositor':sc.compositing_node_group.name if sc.compositing_node_group else None},'lights':[{'name':o.name,'type':o.data.type,'location':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT'],'world':{'nodes':[{'type':n.type,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value') and not i.is_linked}} for n in sc.world.node_tree.nodes]},'externalLibraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'file':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images]}
(E/'independent-native-v2.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'renders':len(renderRecords),'objects':len(objrows),'tubes':len(tubes),'rocks':len(rocktrees),'allContactsEmbedded':report['contactSummary']['allTubeBasalVerticesEmbedded'],'closure':closure,'render':report['render']}))
