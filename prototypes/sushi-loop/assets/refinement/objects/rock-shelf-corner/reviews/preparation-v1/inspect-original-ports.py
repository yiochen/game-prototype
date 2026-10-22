import bpy,json,pathlib,sys,math
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent
s=next(sc for sc in bpy.data.scenes if sc.get('source')=='native_actions.py' and sc.get('issue')==33);bpy.context.window.scene=s;bpy.context.window.view_layer=s.view_layers[0]
c=bpy.data.collections['S33_PROP_rock-shelf-corner.001']
def layer(n):
 n.exclude=False
 for q in n.children:layer(q)
layer(s.view_layers[0].layer_collection)
for q in s.collection.children:q.hide_viewport=q!=c
s.frame_set(1);s.view_layers[0].update();o=next(o for o in c.all_objects if 'continuous_core' in o.name);m=o.data
r={'collection':c.name,'object':o.name,'ports':{},'materials':[]}
for name,axis,val in [('W',0,-.5),('N',1,.5)]:
 vi={v.index for v in m.vertices if abs(v.co[axis]-val)<1e-7};faces=[]
 for f in m.polygons:
  if len(vi.intersection(f.vertices))<2:continue
  faces.append({'polygon':f.index,'cap':set(f.vertices).issubset(vi),'faceNormal':list(f.normal),'material':f.material_index,'corners':[{'position':list(m.vertices[m.loops[k].vertex_index].co),'normal':list(m.corner_normals[k].vector)} for k in f.loop_indices]})
 r['ports'][name]={'axis':axis,'value':val,'vertices':[list(m.vertices[k].co) for k in sorted(vi)],'faces':faces}
for mat in m.materials:
 nodes=[]
 for n in mat.node_tree.nodes:
  q={'name':n.name,'type':n.type,'inputs':{i.identifier:list(i.default_value) if hasattr(i.default_value,'__len__') and not isinstance(i.default_value,str) else i.default_value for i in n.inputs if hasattr(i,'default_value') and (isinstance(i.default_value,(int,float,str,bool)) or hasattr(i.default_value,'__len__'))}}
  for k in ['operation','blend_type','interpolation_type','clamp']:
   if hasattr(n,k):q[k]=getattr(n,k)
  if n.type=='VALTORGB':q['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[[e.position,list(e.color)] for e in n.color_ramp.elements]}
  nodes.append(q)
 r['materials'].append({'name':mat.name,'diffuseColor':list(mat.diffuse_color),'nodes':nodes,'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in mat.node_tree.links]})
(P/'original-port-field.json').write_text(json.dumps(r,indent=2)+'\n');print('ORIGINAL PORT FIELD COMPLETE')
