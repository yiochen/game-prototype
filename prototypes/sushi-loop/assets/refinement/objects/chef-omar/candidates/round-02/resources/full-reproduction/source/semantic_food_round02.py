"""Compact semantic fingerprints plus in-memory numeric evaluated geometry comparisons."""
import bpy,json,hashlib,math
import numpy as np
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def packed_hash(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def plain(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 if isinstance(v,bpy.types.ID):return {'idType':v.bl_rna.identifier,'name':v.name}
 try:return [plain(x) for x in v]
 except TypeError:return str(v)
def props(o,skip=()):
 r={}
 for p in o.bl_rna.properties:
  if p.identifier in {'rna_type',*skip} or p.is_readonly or p.type=='COLLECTION':continue
  try:r[p.identifier]=plain(getattr(o,p.identifier))
  except (TypeError,ValueError,AttributeError):pass
 return r
def fcurve(fc):
 return {'path':fc.data_path,'index':fc.array_index,'extrapolation':fc.extrapolation,'mute':fc.mute,'keys':[{'co':list(k.co),'interpolation':k.interpolation,'left':list(k.handle_left),'right':list(k.handle_right),'leftType':k.handle_left_type,'rightType':k.handle_right_type,'easing':k.easing,'amplitude':k.amplitude,'back':k.back,'period':k.period} for k in fc.keyframe_points],'modifiers':[props(m) for m in fc.modifiers]}
def drivers(o):
 result=[]
 for fc in (o.animation_data.drivers if o.animation_data else []):
  d={'mapping':fcurve(fc),'expression':fc.driver.expression,'type':fc.driver.type,'useSelf':fc.driver.use_self,'variables':[]}
  for v in fc.driver.variables:
   d['variables'].append({'name':v.name,'type':v.type,'targets':[{'id':t.id.name if t.id else None,'data_path':t.data_path,'bone':t.bone_target,'transform':t.transform_type,'space':t.transform_space,'rotationMode':t.rotation_mode} for t in v.targets]})
  result.append(d)
 return result
def array_prop(collection,prop,n,width,dtype=np.float32):
 a=np.empty(n*width,dtype=dtype);collection.foreach_get(prop,a);return a.reshape(n,width)
def mesh_static(o):
 me=o.data
 co=array_prop(me.vertices,'co',len(me.vertices),3)
 ed=array_prop(me.edges,'vertices',len(me.edges),2,np.int32)
 lo=array_prop(me.loops,'vertex_index',len(me.loops),1,np.int32)
 po=[(p.loop_start,p.loop_total,p.material_index,p.use_smooth) for p in me.polygons]
 uv={u.name:packed_hash(array_prop(u.data,'uv',len(u.data),2)) for u in me.uv_layers}
 vn=array_prop(me.vertices,'normal',len(me.vertices),3)
 cn=array_prop(me.corner_normals,'vector',len(me.corner_normals),3)
 weights=[[(g.group,float(g.weight)) for g in v.groups] for v in me.vertices]
 record={'counts':{'vertices':len(me.vertices),'edges':len(me.edges),'polygons':len(me.polygons),'loops':len(me.loops),'uvLayers':len(me.uv_layers)},'coordinatesSHA256':packed_hash(co),'edgesSHA256':packed_hash(ed),'loopVerticesSHA256':packed_hash(lo),'polygonsSHA256':digest(po),'uvLayers':uv,'vertexNormalsSHA256':packed_hash(vn),'cornerNormalsSHA256':packed_hash(cn),'weightsSHA256':digest(weights),'vertexGroups':[(g.name,g.lock_weight) for g in o.vertex_groups],'materialNames':[m.name if m else None for m in me.materials],'modifiers':[props(m,('execution_time',)) for m in o.modifiers]}
 record['semanticSHA256']=digest(record);return record
def material(m):
 if not m.use_nodes:return {'properties':props(m)}
 nodes=[]
 for n in m.node_tree.nodes:
  # The texture image pointer is the sole image-binding whitelist; all node settings remain.
  nodes.append({'type':n.bl_idname,'name':n.name,'properties':props(n,('image','location','width','height','select','parent')),'inputs':[(s.identifier,plain(s.default_value) if hasattr(s,'default_value') else None) for s in n.inputs]})
 links=sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links)
 return {'properties':props(m,('node_tree','texture_paint_images','texture_paint_slots')),'nodes':nodes,'links':links}
def static_scene(sc,coll,plane,rig,native):
 objects={}
 for o in sc.objects:
  if o==plane:continue
  r={'type':o.type,'parent':o.parent.name if o.parent else None,'parentType':o.parent_type,'parentBone':o.parent_bone,'matrixParentInverse':[list(v) for v in o.matrix_parent_inverse],'location':list(o.location),'rotationMode':o.rotation_mode,'rotation':list(o.rotation_euler),'scale':list(o.scale),'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'properties':{k:plain(v) for k,v in o.items()},'drivers':drivers(o),'constraints':[props(c) for c in o.constraints]}
  if o.type=='MESH':r['mesh']=mesh_static(o)
  elif o.type=='ARMATURE':
   r['restBones']=[{'name':b.name,'parent':b.parent.name if b.parent else None,'matrix':[list(v) for v in b.matrix_local],'deform':b.use_deform,'head':list(b.head_local),'tail':list(b.tail_local)} for b in o.data.bones]
   r['poseConstraints']={b.name:[props(c) for c in b.constraints] for b in o.pose.bones}
  elif o.data:r['dataProperties']=props(o.data)
  r['semanticSHA256']=digest(r);objects[o.name]=r
 mats={m.name:material(m) for o in sc.objects if o.type=='MESH' for m in o.data.materials if m}
 actions={n:digest([fcurve(fc) for fc in native._fcurves(bpy.data.actions[n])]) for n in {t['action'] for r in rig['clips'].values() for t in r['actions']}}
 renderer={'render':props(sc.render,('filepath','stamp_note_text')),'cycles':props(sc.cycles),'viewSettings':props(sc.view_settings),'world':{'properties':props(sc.world,('node_tree',)),'nodes':[{'type':n.bl_idname,'name':n.name,'properties':props(n,('location','width','height','select')),'inputs':[(s.identifier,plain(s.default_value) if hasattr(s,'default_value') else None) for s in n.inputs]} for n in sc.world.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in sc.world.node_tree.links]}}
 return {'objects':objects,'materials':{n:{'semanticSHA256':digest(v),'semantic':v} for n,v in mats.items()},'actions':actions,'renderer':{'semanticSHA256':digest(renderer),'semantic':renderer},'foodShaderSHA256':digest(material(plane.data.materials[0])),'foodDrivers':drivers(plane)}
def evaluated(o,dg):
 e=o.evaluated_get(dg);me=e.to_mesh();m=np.array(e.matrix_world,dtype=np.float64)
 co=array_prop(me.vertices,'co',len(me.vertices),3).astype(np.float64);co=co@m[:3,:3].T+m[:3,3]
 normals=array_prop(me.vertices,'normal',len(me.vertices),3).astype(np.float64)
 corner=array_prop(me.corner_normals,'vector',len(me.corner_normals),3).astype(np.float64)
 nm=np.linalg.inv(m[:3,:3]).T
 def transform(n):
  q=n@nm.T;l=np.linalg.norm(q,axis=1);q[l>0]/=l[l>0,None];return q.astype(np.float32)
 normals=transform(normals);corner=transform(corner)
 e.to_mesh_clear();return co,normals,corner
def rigid_geometry_from_evaluated_parent(o,dg):
 # Blender omits culled rigid meshes from viewport evaluation. Their fixed mesh
 # has no modifiers/constraints/shape keys. Reconstruct only their native rigid
 # transform using the actual evaluated, visible utensil parent and native basis.
 assert len(o.modifiers)==0 and len(o.constraints)==0 and o.data.shape_keys is None
 assert o.parent and o.parent_type=='OBJECT' and not o.parent.hide_viewport and not o.parent.hide_get()
 m=o.parent.evaluated_get(dg).matrix_world@o.matrix_parent_inverse@o.matrix_basis
 me=o.data;mm=np.array(m,dtype=np.float64)
 co=array_prop(me.vertices,'co',len(me.vertices),3).astype(np.float64);co=co@mm[:3,:3].T+mm[:3,3]
 nm=np.linalg.inv(mm[:3,:3]).T
 def normal(prop,collection):
  n=array_prop(collection,prop,len(collection),3).astype(np.float64);q=n@nm.T;l=np.linalg.norm(q,axis=1);q[l>0]/=l[l>0,None];return q.astype(np.float32)
 return (co,normal('normal',me.vertices),normal('vector',me.corner_normals)),m

def frame_geometry(coll,plane):
 result={};dg=bpy.context.evaluated_depsgraph_get()
 for o in coll.all_objects:
  if o.type!='MESH' or o==plane:continue
  if o.hide_viewport or o.hide_get():
   assert '__knife_' in o.name
   result[o.name]=rigid_geometry_from_evaluated_parent(o,dg)[0]
  else:result[o.name]=evaluated(o,dg)
 return result
def compact_geometry(gs,ref=None):
 rows={};maxpos=maxnormal=maxcorner=0
 for name,arrays in gs.items():
  a,n,c=arrays;r={'vertices':len(a),'corners':len(c),'worldVerticesSHA256':packed_hash(a),'worldVertexNormalsSHA256':packed_hash(n),'worldCornerNormalsSHA256':packed_hash(c)}
  if ref is not None:
   aa,nn,cc=ref[name];dp=float(np.max(np.abs(a-aa))) if len(a) else 0;dn=float(np.max(np.abs(n-nn))) if len(n) else 0;dc=float(np.max(np.abs(c-cc))) if len(c) else 0
   r.update(maxPositionDeltaWorld=dp,maxVertexNormalDelta=dn,maxCornerNormalDelta=dc);maxpos=max(maxpos,dp);maxnormal=max(maxnormal,dn);maxcorner=max(maxcorner,dc)
  rows[name]=r
 return rows,(maxpos,maxnormal,maxcorner)
def controls(coll,root,arm,plane,gs):
 dg=bpy.context.evaluated_depsgraph_get();ae=arm.evaluated_get(dg)
 bones=np.array([np.array(ae.matrix_world@b.matrix) for b in ae.pose.bones])
 points={}
 for side in ['L','R']:
  palm=next(o for o in coll.all_objects if '__palm_'+side in o.name);foot=next(o for o in coll.all_objects if '__minimal_foot_'+side in o.name)
  points['palm'+side]=gs[palm.name][0].mean(axis=0);points['foot'+side]=np.stack([gs[foot.name][0].min(axis=0),gs[foot.name][0].max(axis=0)])
 matrices={o.name:np.array(o.evaluated_get(dg).matrix_world,dtype=np.float64) for o in coll.all_objects if o.type=='EMPTY' and o!=root or '__knife_' in o.name}
 return {'bones':bones,'points':points,'matrices':matrices,'rootMatrix':np.array(root.matrix_world,dtype=np.float64),'parentMatrix':np.array(plane.parent.evaluated_get(dg).matrix_world,dtype=np.float64)}
