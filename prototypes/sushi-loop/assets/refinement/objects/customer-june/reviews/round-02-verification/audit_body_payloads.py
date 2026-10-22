import bpy,json,sys,hashlib,re
sys.dont_write_bytecode=True
from pathlib import Path
P=Path(__file__).parent;mode='runtime' if 'runtime' in bpy.data.filepath else 'main';col=next(c for c in bpy.data.collections if 'CHARACTER_customer_june' in c.name)
def val(v):
 if isinstance(v,(str,int,float,bool)):return v
 try:return [val(x) for x in v]
 except:return str(v)
def graph(t):
 return {'nodes':[{'id':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'blend':getattr(n,'blend_type',None),'inputs':[(s.identifier,val(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],'group':graph(n.node_tree) if n.type=='GROUP' else None} for n in t.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links]}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
rows={}
for o in col.all_objects:
 if o.type!='MESH' or o.get('representation'):continue
 key=o.name.replace('S10 meal ','');data=o.data
 material=[graph(m.node_tree) if m.use_nodes else list(m.diffuse_color) for m in data.materials]
 groups={g.index:g.name for g in o.vertex_groups};payload={'vertices':[list(v.co) for v in data.vertices],'polygons':[{'vertices':list(p.vertices),'smooth':p.use_smooth,'mat':p.material_index,'normal':list(p.normal)} for p in data.polygons],'edges':[list(e.vertices) for e in data.edges],'cornerNormals':[list(n.vector) for n in data.corner_normals],'weights':[[(groups[g.group],g.weight) for g in v.groups] for v in data.vertices],'uv':[[list(uv.uv) for uv in layer.data] for layer in data.uv_layers],'materials':material,'modifiers':[{'type':m.type,'settings':{p.identifier:val(getattr(m,p.identifier)) for p in m.bl_rna.properties if p.type in ['BOOLEAN','INT','FLOAT','ENUM'] and not p.is_readonly}} for m in o.modifiers]}
 rows[key]={'payloadSHA256':digest(payload),'vertices':len(data.vertices),'polygons':len(data.polygons),'materialsSHA256':digest(material),'visible':not o.hide_render}
sc=bpy.context.scene;lights=[{'position':list(o.matrix_world.translation),'rotation':list(o.rotation_euler),'energy':o.data.energy,'color':list(o.data.color),'type':o.data.type,'size':getattr(o.data,'size',None),'hideRender':o.hide_render,'hideViewport':o.hide_viewport} for o in sc.objects if o.type=='LIGHT'];out={'body':rows,'lights':lights,'compositor':graph(sc.compositing_node_group) if getattr(sc,'compositing_node_group',None) else None,'world':graph(sc.world.node_tree) if sc.world and sc.world.use_nodes else None};(P/(mode+'-body-payload-signatures.json')).write_text(json.dumps(out,indent=2)+'\n');print(mode,len(rows),'bodymeshes')
