"""Deterministic native-data audit. Hashes cover full source data, not only metadata."""
import bpy,json,hashlib,math
from mathutils import Vector,Matrix,Quaternion,Euler
ROOT='chef_ellis__ground_root.001';PLANE=ROOT+'__held_dish-salmon__image_plane';SCENE='Ellis warm soft round04';COLL='S33_CHARACTER_chef_ellis.001'
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def plain(v):
 if v is None or isinstance(v,(str,bool,int)):return v
 if isinstance(v,float):return v if math.isfinite(v) else str(v)
 if isinstance(v,bpy.types.ID):return {'idType':type(v).__name__,'name':v.name}
 if hasattr(v,'bl_rna'):return {'rnaType':v.bl_rna.identifier,'name':getattr(v,'name',None)}
 if isinstance(v,(Vector,Quaternion,Euler)):return [plain(x) for x in v]
 if isinstance(v,Matrix):return [[plain(x) for x in r] for r in v]
 try:return [plain(x) for x in v]
 except TypeError:return str(v)
def props(v,skip=()):
 out={}
 for p in v.bl_rna.properties:
  if p.identifier in set(skip)|{'rna_type'} or p.type=='COLLECTION' or p.is_readonly:continue
  try:out[p.identifier]=plain(getattr(v,p.identifier))
  except Exception:pass
 return out
def custom(o):return {k:plain(o[k]) for k in o.keys() if k!='_RNA_UI'}
def anim(o):
 ad=o.animation_data
 if not ad:return None
 drivers=[]
 for f in ad.drivers:
  drivers.append({'path':f.data_path,'index':f.array_index,'props':props(f,('driver',)),'driver':props(f.driver),'vars':[{'props':props(v),'targets':[props(t) for t in v.targets]} for v in f.driver.variables]})
 return {'action':ad.action.name if ad.action else None,'slot':ad.action_slot.identifier if ad.action_slot else None,'props':props(ad,('action','action_slot')),'drivers':drivers,'nla':[{'props':props(t),'strips':[props(s) for s in t.strips]} for t in ad.nla_tracks]}
def mesh(me):
 arrays={'vertices':[list(v.co) for v in me.vertices],'edges':[list(e.vertices) for e in me.edges],'loops':[(l.vertex_index,l.edge_index) for l in me.loops],'polygons':[(p.loop_start,p.loop_total,p.material_index,p.use_smooth) for p in me.polygons],'cornerNormals':[list(x.vector) for x in me.corner_normals],'attributes':{a.name:{'props':props(a),'data':[props(x) for x in a.data]} for a in me.attributes},'uvs':{uv.name:[list(x.uv) for x in uv.data] for uv in me.uv_layers},'materials':[m.name if m else None for m in me.materials],'custom':custom(me),'props':props(me),'shapeKeys':None}
 if me.shape_keys:arrays['shapeKeys']={'props':props(me.shape_keys),'blocks':[{'props':props(k),'data':[list(x.co) for x in k.data]} for k in me.shape_keys.key_blocks],'animation':anim(me.shape_keys)}
 return {'sha256':digest(arrays),'sections':{k:digest(v) for k,v in arrays.items()},'counts':[len(me.vertices),len(me.edges),len(me.polygons)],'hasCustomNormals':me.has_custom_normals}
def graph(nt):
 return {'props':props(nt),'custom':custom(nt),'nodes':{n.name:{'type':n.bl_idname,'props':props(n,('parent',)),'inputs':[{'name':s.name,'identifier':s.identifier,'default':plain(s.default_value) if hasattr(s,'default_value') else None} for s in n.inputs],'outputs':[{'name':s.name,'identifier':s.identifier,'default':plain(s.default_value) if hasattr(s,'default_value') else None} for s in n.outputs]} for n in nt.nodes},'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in nt.links],'animation':anim(nt)}
def snapshot():
 sc=bpy.data.scenes[SCENE];bpy.context.window.scene=sc;bpy.context.view_layer.update();coll=bpy.data.collections[COLL];objects={};armatures={}
 for o in coll.all_objects:
  data={'props':props(o,('data',)),'dataName':o.data.name if o.data else None,'custom':custom(o),'animation':anim(o),'modifiers':[props(m) for m in o.modifiers],'constraints':[props(c) for c in o.constraints],'groups':[{'name':g.name,'lock':g.lock_weight} for g in o.vertex_groups]}
  if o.type=='MESH':data['mesh']=mesh(o.data);data['weightsSHA256']=digest([[(g.group,g.weight) for g in v.groups] for v in o.data.vertices])
  if o.type=='ARMATURE':
   data['armature']={'props':props(o.data),'bones':{b.name:{'props':props(b),'matrix':plain(b.matrix_local),'head':plain(b.head_local),'tail':plain(b.tail_local),'custom':custom(b)} for b in o.data.bones},'pose':{b.name:{'props':props(b),'constraints':[props(c) for c in b.constraints],'custom':custom(b)} for b in o.pose.bones}}
  objects[o.name]=data
 materials={m.name:{'props':props(m),'custom':custom(m),'graph':graph(m.node_tree) if m.node_tree else None} for m in {m for o in coll.all_objects if o.type=='MESH' for m in o.data.materials if m}}
 actions={}
 for a in bpy.data.actions:
  curves=[]
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     curves.extend({'path':f.data_path,'index':f.array_index,'props':props(f),'keys':[{'props':props(k),'co':plain(k.co),'left':plain(k.handle_left),'right':plain(k.handle_right)} for k in f.keyframe_points],'modifiers':[props(m) for m in f.modifiers]} for f in bag.fcurves)
  actions[a.name]={'props':props(a),'slots':[props(x) for x in a.slots],'curvesSHA256':digest(curves),'custom':custom(a)}
 camera={'name':sc.camera.name,'object':props(sc.camera),'data':props(sc.camera.data)};lights={o.name:{'object':props(o),'data':props(o.data),'nodes':graph(o.data.node_tree) if o.data.node_tree else None} for o in sc.objects if o.type=='LIGHT'}
 return {'objects':objects,'materials':materials,'actions':actions,'camera':camera,'lights':lights,'world':{'name':sc.world.name,'props':props(sc.world),'graph':graph(sc.world.node_tree)},'render':{'render':props(sc.render),'image':props(sc.render.image_settings),'cycles':props(sc.cycles),'view':props(sc.view_settings),'display':props(sc.display_settings),'sequencer':sc.render.use_sequencer,'compositing':sc.render.use_compositing},'scene':{'name':sc.name,'props':props(sc,('world','camera')),'objects':sorted(o.name for o in sc.objects),'collectionProps':props(coll),'collectionMembers':sorted(o.name for o in coll.all_objects)},'images':{im.name:{'props':props(im),'size':list(im.size),'colorspace':im.colorspace_settings.name,'packedSHA256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None} for im in bpy.data.images if im.type!='RENDER_RESULT'},'foodPlane':{'vertices':[list(v.co) for v in bpy.data.objects[PLANE].data.vertices],'uv':[list(v.uv) for v in bpy.data.objects[PLANE].data.uv_layers.active.data]},'libraries':[l.filepath for l in bpy.data.libraries]}
def compare(a,b,path=''):
 if isinstance(a,(list,tuple)) and isinstance(b,(list,tuple)):a=list(a);b=list(b)
 if type(a)!=type(b):return [(path,a,b)]
 if isinstance(a,dict):
  out=[]
  for k in sorted(a.keys()|b.keys()):
   pp=path+'/'+k
   if k not in a:out.append((pp,None,b[k]))
   elif k not in b:out.append((pp,a[k],None))
   else:out+=compare(a[k],b[k],pp)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [(path,a,b)]
  out=[]
  for i,(x,y) in enumerate(zip(a,b)):out+=compare(x,y,path+'/'+str(i))
  return out
 return [] if a==b else [(path,a,b)]
