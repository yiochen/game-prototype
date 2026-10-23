import bpy,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;sc=bpy.context.scene
v=lambda p:[float(x) for x in p]
def value(x):
 if isinstance(x,str):return x
 try:return v(x)
 except TypeError:return x
def graph(nt):return {'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[{'index':i,'identifier':s.identifier,'value':value(s.default_value)} for i,s in enumerate(n.inputs) if hasattr(s,'default_value') and s.type not in ['SHADER','CUSTOM']]} for n in nt.nodes],'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in nt.links]}
r={'worldGraph':graph(sc.world.node_tree),'lights':[{'name':o.name,'nodeGraph':graph(o.data.node_tree) if o.data.use_nodes else None} for o in sc.objects if o.type=='LIGHT']}
(R.parent/'canonical-rig-independent.json').write_text(json.dumps(r,indent=2)+'\n')
