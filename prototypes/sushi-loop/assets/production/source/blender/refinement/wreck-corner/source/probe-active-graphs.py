import bpy,json,sys,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
args=sys.argv[sys.argv.index('--')+1:];out=Path(args[0]);asset=args[1]
def value(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [value(x) for x in v]
 except:return str(v)
def tree(t):
 if not t:return None
 nodes=[]
 for n in t.nodes:
  row={'name':n.name,'type':n.bl_idname,'inputs':{i.identifier:value(i.default_value) for i in n.inputs if hasattr(i,'default_value')}}
  for k in ['operation','blend_type','clamp','use_clamp','vector_type','convert_from','convert_to','attribute_name','interpolation','distribution','component','space','invert','data_type','mode']:
   if hasattr(n,k):row[k]=value(getattr(n,k))
  if hasattr(n,'color_ramp'):
   cr=n.color_ramp;row['colorRamp']={'interpolation':cr.interpolation,'colorMode':cr.color_mode,'hueInterpolation':cr.hue_interpolation,'elements':[{'position':e.position,'color':value(e.color)} for e in cr.elements]}
  if hasattr(n,'node_tree') and n.node_tree:row['groupTree']=tree(n.node_tree)
  nodes.append(row)
 return {'nodes':sorted(nodes,key=lambda x:x['name']),'links':sorted([{'from':[l.from_node.name,l.from_socket.identifier],'to':[l.to_node.name,l.to_socket.identifier]} for l in t.links],key=lambda x:str(x))}
col=bpy.data.collections['S33_PROP_wreck-corner.001'] if asset=='candidate' else bpy.data.collections['Wreck middle authored candidate']
mats={m for o in col.objects if o.type in ['MESH','CURVE'] for m in o.data.materials if m}
sc=bpy.context.scene;data={'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'materials':{m.name:tree(m.node_tree) for m in mats},'world':tree(sc.world.node_tree),'compositor':tree(getattr(sc,'compositing_node_group',None) or getattr(sc,'node_tree',None)),'lights':[{'name':o.name,'dataType':o.data.type,'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'color':value(o.data.color),'useShadow':o.data.use_shadow,'matrixWorld':[list(r) for r in o.matrix_world],'nodes':tree(o.data.node_tree) if o.data.use_nodes else None} for o in sc.objects if o.type=='LIGHT']}
out.write_text(json.dumps(data,indent=2)+'\n');print('GRAPH_PROBE',asset,len(mats),out)
