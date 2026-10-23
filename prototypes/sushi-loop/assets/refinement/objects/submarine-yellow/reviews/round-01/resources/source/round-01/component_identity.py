"""Exact signed neutral resource schemas; never imports component builders."""
import bpy,json,hashlib
from mathutils import Matrix

def val(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 try:return [val(v) for v in x]
 except:return str(x)
def hd(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def matrix(x):return [list(r) for r in x]
def panel_identity(c):
 records=[]
 for ob in sorted(c.all_objects,key=lambda o:o.name):
  if ob.type!='MESH':continue
  me=ob.data;r={'name':ob.name,'vertices':[list(v.co) for v in me.vertices],'polygons':[list(p.vertices) for p in me.polygons],'smooth':[p.use_smooth for p in me.polygons],'loopNormals':[list(n.vector) for n in me.corner_normals],'uvLayers':{u.name:[list(v.uv) for v in u.data] for u in me.uv_layers},'materials':[m.name for m in me.materials],'objectLocalMatrix':matrix(ob.matrix_local),'modifiers':[m.type for m in ob.modifiers]};r['sha256']=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest();records.append(r)
 mats=[]
 for m in sorted({m for o in c.all_objects if o.type=='MESH' for m in o.data.materials},key=lambda m:m.name):mats.append({'name':m.name,'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':{s.identifier:val(s.default_value) for s in n.inputs if hasattr(s,'default_value')}} for n in m.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in m.node_tree.links]})
 return {'meshes':records,'materials':mats,'images':[],'externalResources':[]}
def harpoon_identity(c):
 def matrec(m):return {'name':m.name,'diffuse':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[{'identifier':i.identifier,'value':val(getattr(i,'default_value',None))} for i in n.inputs]} for n in m.node_tree.nodes],'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.identifier,'toNode':l.to_node.name,'toSocket':l.to_socket.identifier} for l in m.node_tree.links]}
 out=[]
 for o in sorted(c.all_objects,key=lambda o:o.name):
  if o.type!='MESH':continue
  d=o.data;d.calc_loop_triangles();out.append({'object':o.name,'mesh':d.name,'vertices':[list(v.co) for v in d.vertices],'vertexNormals':[list(v.normal) for v in d.vertices],'cornerNormals':[list(n.vector) for n in d.corner_normals],'polygons':[{'vertices':list(f.vertices),'material':f.material_index,'smooth':f.use_smooth,'normal':list(f.normal)} for f in d.polygons],'uvLayers':[{'name':u.name,'data':[list(v.uv) for v in u.data]} for u in d.uv_layers],'materials':[matrec(m) for m in d.materials if m],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'matrixBasis':matrix(o.matrix_basis),'parentInverse':matrix(o.matrix_parent_inverse),'parent':o.parent.name if o.parent else None})
 return out

def collector_identity(c):
 out=[]
 for o in sorted(c.all_objects,key=lambda o:o.name):
  d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'localMatrix':matrix(o.matrix_local)}
  if o.type=='MESH':
   me=o.data;d['mesh']={'vertices':[list(v.co) for v in me.vertices],'edges':[list(e.vertices) for e in me.edges],'polygons':[{'v':list(f.vertices),'material':f.material_index,'smooth':f.use_smooth} for f in me.polygons],'cornerNormals':[list(n.vector) for n in me.corner_normals],'uvs':{u.name:[list(x.uv) for x in u.data] for u in me.uv_layers},'materials':[]}
   for m in me.materials:
    nd=[]
    for n in m.node_tree.nodes:
     ins={}
     for i in n.inputs:
      if hasattr(i,'default_value'):
       v=i.default_value
       try:v=list(v)
       except TypeError:pass
       if isinstance(v,(str,int,float,bool,list)):ins[i.identifier]=v
     nd.append({'name':n.name,'type':n.bl_idname,'inputs':ins})
    d['mesh']['materials'].append({'name':m.name,'diffuse':list(m.diffuse_color),'nodes':nd,'links':sorted([[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in m.node_tree.links])})
  out.append(d)
 return out

def persistent(c):
 """Exact persistent neutral data; derived inverse-parent local products excluded."""
 out=[]
 for o in sorted(c.all_objects,key=lambda o:o.name):
  d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixBasis':matrix(o.matrix_basis),'parentInverse':matrix(o.matrix_parent_inverse)}
  if o.type=='MESH':
   me=o.data;d.update(vertices=[list(v.co) for v in me.vertices],vertexNormals=[list(v.normal) for v in me.vertices],cornerNormals=[list(n.vector) for n in me.corner_normals],polygons=[(list(p.vertices),p.material_index,p.use_smooth,list(p.normal)) for p in me.polygons],UV={u.name:[list(x.uv) for x in u.data] for u in me.uv_layers},materials=[{'name':m.name,'nodes':[{'type':n.bl_idname,'name':n.name,'inputs':{i.identifier:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'operation':getattr(n,'operation',None)} for n in m.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links]} for m in me.materials],modifiers=[(m.name,m.type) for m in o.modifiers])
  out.append(d)
 return out
