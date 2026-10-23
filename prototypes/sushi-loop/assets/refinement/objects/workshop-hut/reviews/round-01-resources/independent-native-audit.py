import bpy,json,math,hashlib,pathlib,re
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
OUT=pathlib.Path(__file__).resolve().parent;B=OUT.parents[1];C=B/'candidates/round-01';S=B/'source';SRC=S/'round-01.blend'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
before=sha(SRC);sc=bpy.context.scene;hr=bpy.data.objects['workshop-hut__root'];hc=bpy.data.collections['WarmSoft_workshop-hut'];cam=sc.camera
def plain(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return {str(k):plain(v[k]) for k in v.keys()}
 except:return [plain(x) for x in v]
def bounds(ps):return {'min':[min(p[i] for p in ps) for i in range(3)],'max':[max(p[i] for p in ps) for i in range(3)]}
def geo(col,raw=False):
 dg=bpy.context.evaluated_depsgraph_get();vs=[];fs=[];rows=[]
 for o in col.all_objects:
  if o.type!='MESH' or o.hide_render:continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();ps=[ev.matrix_world@v.co for v in me.vertices];off=len(vs);vs+=ps;faces=[list(p.vertices) for p in me.polygons];fs.extend([[off+i for i in f] for f in faces])
  row={'name':o.name,'bounds':bounds(ps),'matrix':[list(r) for r in ev.matrix_world],'parent':o.parent.name if o.parent else None,'vertices':len(ps),'faces':len(faces),'materials':[m.name for m in me.materials if m],'uvLayers':[u.name for u in me.uv_layers],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'shapeKeys':o.data.shape_keys.name if o.data.shape_keys else None,'normalCount':len(me.corner_normals),'polygonAreaMinimum':min(p.area for p in me.polygons)}
  if raw:row.update(vertexData=[list(p) for p in ps],faceData=faces,faceNormals=[list(p.normal) for p in me.polygons],smoothFaces=[p.use_smooth for p in me.polygons],materialIndices=[p.material_index for p in me.polygons])
  rows.append(row);ev.to_mesh_clear()
 return rows,vs,fs,BVHTree.FromPolygons(vs,fs)
def px(p):
 q=world_to_camera_view(sc,cam,Vector(p));return Vector((q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y))
sc.frame_set(1);bpy.context.view_layer.update();rows,vs,fs,ht=geo(hc,True);origin=px((0,0,0))
r={'candidatePacketSHA256':sha(C/'packet.json'),'sourceSHA256':before,'blenderVersion':bpy.app.version_string,'scene':sc.name,'collections':[c.name for c in sc.collection.children],'root':{'location':list(hr.location),'rotation':list(hr.rotation_euler),'scale':list(hr.scale),'props':{k:plain(hr[k]) for k in hr.keys()}},'camera':{'name':cam.name,'matrix':[list(x) for x in cam.matrix_world],'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'rootPx':list(origin),'unitX':list(px((1,0,0))-origin),'unitDepth':list(px((0,-1,0))-origin),'unitHeight':list(px((0,0,1))-origin)},'bounds':bounds(vs),'objects':rows,'settings':{'engine':sc.render.engine,'filterSize':sc.render.filter_size,'fps':sc.render.fps,'transparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'allSceneObjects':[{'name':o.name,'type':o.type,'hideRender':o.hide_render,'parent':o.parent.name if o.parent else None} for o in sc.objects],'images':[{'name':i.name,'source':i.source,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries],'rigs':[o.name for o in bpy.data.objects if o.type=='ARMATURE'],'drivers':[o.name for o in bpy.data.objects if o.animation_data and o.animation_data.drivers],'lights':[{'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT'],'materials':[]}
for m in bpy.data.materials:
 tree=m.node_tree
 r['materials'].append({'name':m.name,'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'image':n.image.name if hasattr(n,'image') and n.image else None} for n in tree.nodes] if tree else [],'links':[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in tree.links] if tree else []})
low=[]
for o in rows:
 for p in o['vertexData']:
  if p[2]<-1e-6:low.append((o['name'],p))
r['lowRepairVertices']={'count':len(low),'bounds':bounds([p for n,p in low]),'objects':sorted(set(n for n,p in low)),'allInsideFrozenRepairBox':all(-.43751<=p[0]<=.43751 and -.56001<=p[1]<=.45001 and -.01201<=p[2]<=.06501 for n,p in low)}
r['replay']=[];folder=OUT/'replay';folder.mkdir(exist_ok=True)
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 hr.rotation_euler.z=a;bpy.context.view_layer.update();sc.render.filepath=str(folder/(d+'.png'));bpy.ops.render.render(write_still=True)
 r['replay'].append({'direction':d,'rootRotationZ':hr.rotation_euler.z,'path':'replay/'+d+'.png','sha256':sha(folder/(d+'.png'))})
hr.rotation_euler.z=0;bpy.context.view_layer.update()
with bpy.data.libraries.load(str(S/'resources/paired-floor-round-04.blend'),link=False) as (a,b):b.collections=['WarmSoft_dock-floor']
fc=bpy.data.collections['WarmSoft_dock-floor'];sc.collection.children.link(fc);fr=next(o for o in fc.objects if o.type=='EMPTY' and not o.parent)
with bpy.data.libraries.load(str(S/'resources/customer-rosa-approved.blend'),link=False) as (a,b):b.collections=['S33_CHARACTER_customer_rosa.001'];b.actions=[n for n in a.actions if 'customer-rosa' in n]
rc=bpy.data.collections['S33_CHARACTER_customer_rosa.001'];sc.collection.children.link(rc);rr=next(o for o in rc.objects if o.type=='EMPTY' and not o.parent);authoredScale=list(rr.scale)
rig=json.loads((S/'resources/family-rigs/customer-rosa.json').read_text());resolved=[]
def lookup(data,n):return data.get(n) or data.get(n+'.001') or next((o for o in data if re.sub(r'\.\d+$','',o.name)==re.sub(r'\.\d+$','',n)),None)
for o in rc.all_objects:
 o.hide_viewport=False;o.hide_set(False)
 if o.animation_data:
  o.animation_data.action=None
  for t in o.animation_data.nla_tracks:t.mute=True
for rec in rig['clips']['stand']['actions']:
 owner=lookup(bpy.data.objects,rec['ownerName']) if rec['ownerType']=='Object' else lookup(bpy.data.shape_keys,rec['ownerName']) if rec['ownerType']=='Key' else lookup(bpy.data.materials,rec['materialOwnerName']).node_tree
 act=lookup(bpy.data.actions,rec['action']);assert owner and act,rec;owner.animation_data_create();owner.animation_data.action=act;slot=next((s for s in act.slots if s.identifier==rec.get('slotIdentifier')),None)
 if slot:owner.animation_data.action_slot=slot
 resolved.append({'owner':owner.name,'action':act.name,'slot':slot.identifier if slot else None})
sc.frame_set(1);r['paired']={'floorSHA256':sha(S/'resources/paired-floor-round-04.blend'),'RosaSHA256':sha(S/'resources/customer-rosa-approved.blend'),'RosaAuthoredScaleBeforeAnyContextTransform':authoredScale,'actions':resolved,'contactAndHuman':[]}
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 R=Matrix.Rotation(a,4,'Z');hr.location=R@Vector((.78,.35,.23));hr.rotation_euler.z=a;fr.location=(0,0,0);fr.rotation_euler.z=a;bpy.context.view_layer.update();hrows,hv,hf,ht=geo(hc);frows,fv,ff,ft=geo(fc);patches=[]
 for box in [(-.21,-.15,-.32,-.24),(-.21,-.15,.23,.31),(.29,.35,.23,.31)]:
  x0,x1,y0,y1=box;samples=[]
  for i in range(21):
   for j in range(21):
    p=R@Vector((.78+x0+(x1-x0)*i/20,.35+y0+(y1-y0)*j/20,.18));h,hn,_,_=ht.ray_cast(p,Vector((0,0,1)),.1);f,fn,_,_=ft.ray_cast(p+Vector((0,0,.32)),Vector((0,0,-1)),.4)
    samples.append({'xy':list(p)[:2],'hut':list(h) if h else None,'floor':list(f) if f else None,'normalHut':list(hn) if hn else None,'normalFloor':list(fn) if fn else None,'delta':h.z-f.z if h and f else None})
  patches.append({'box':box,'area':(x1-x0)*(y1-y0),'allSamplesPresent':all(s['delta'] is not None for s in samples),'maxAbsoluteDelta':max(abs(s['delta']) for s in samples if s['delta'] is not None),'samples':samples})
 threshold=[]
 for x in [-.25,-.12,.01]:
  p=R@Vector((.78+x,.35-.5,.18));h,_,_,_=ht.ray_cast(p,Vector((0,0,1)),.1);f,_,_,_=ft.ray_cast(p+Vector((0,0,.32)),Vector((0,0,-1)),.4);threshold.append({'xy':list(p)[:2],'hutUnderside':list(h) if h else None,'deck':list(f) if f else None})
 humans=[]
 for idx,y in enumerate([-.9,-.67]):
  rr.location=R@Vector((.66,y,.22));rr.rotation_euler.z=a+math.pi;bpy.context.view_layer.update();rows,vs,fs,rt=geo(rc);solePatches=[]
  for x in [.55,.82]:
   ss=[]
   for i in range(7):
    for j in range(7):
     p=R@Vector((x-.015+i*.005,y+.012+j*.005,.18));h,_,_,_=rt.ray_cast(p,Vector((0,0,1)),.1);f,_,_,_=ft.ray_cast(p+Vector((0,0,.1)),Vector((0,0,-1)),.2);ss.append(h.z-f.z if h and f else None)
   solePatches.append({'area':.0009,'allSamplesPresent':all(v is not None for v in ss),'maxAbsoluteDelta':max(abs(v) for v in ss if v is not None),'deltas':ss})
  mins=[rt.find_nearest(v)[3] for v in hv]+[ht.find_nearest(v)[3] for v in vs]
  humans.append({'index':idx,'root':list(rr.location),'scale':list(rr.scale),'visibleBounds':bounds(vs),'visibleMeshCount':len(rows),'visibleFootMeshes':[o for o in rows if 'shoe' in o['name'].lower() or 'foot' in o['name'].lower()],'hutTriangleIntersections':len(rt.overlap(ht)),'sampledVertexToOppositeSurfaceMinimum':min(v for v in mins if v is not None),'solePatches':solePatches})
 r['paired']['contactAndHuman'].append({'direction':d,'root':list(hr.location),'rootRotationZ':hr.rotation_euler.z,'doorSocket':list(bpy.data.objects['workshop-hut__door_socket'].matrix_world.translation),'patches':patches,'threshold':threshold,'humans':humans})
r['sourceUnchanged']=sha(SRC)==before;r['noBlendSaved']=True
(OUT/'independent-native-audit.json').write_text(json.dumps(r,indent=2))
print('INDEPENDENT_NATIVE',r['bounds'],len(r['objects']),r['camera'],r['paired']['RosaAuthoredScaleBeforeAnyContextTransform'],[(x['direction'],max(p['maxAbsoluteDelta'] for p in x['patches']),[(h['index'],h['hutTriangleIntersections'],h['sampledVertexToOppositeSurfaceMinimum']) for h in x['humans']]) for x in r['paired']['contactAndHuman']])
