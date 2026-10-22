import bpy,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
sc=bpy.context.scene;group=sc.compositing_node_group
mats=[]
for m in bpy.data.materials:
 if m.use_nodes:
  ps=[n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED']
  mats.append({'name':m.name,'nodes':[{'type':n.type,'name':n.name,'attribute':getattr(n,'layer_name',None)} for n in m.node_tree.nodes],'principled':[{'roughness':n.inputs['Roughness'].default_value,'specularIORLevel':n.inputs['Specular IOR Level'].default_value,'emissionStrength':n.inputs['Emission Strength'].default_value} for n in ps],'links':[{'from':l.from_node.type+'.'+l.from_socket.name,'to':l.to_node.type+'.'+l.to_socket.name} for l in m.node_tree.links]})
d={'scene':sc.name,'renderUseCompositing':sc.render.use_compositing,'compositingNodeGroup':None if group is None else {'name':group.name,'nodes':[n.type for n in group.nodes],'properties':dict(group.items())},'worldNodes':[{'type':n.type,'strength':n.inputs['Strength'].default_value if n.type=='BACKGROUND' else None} for n in sc.world.node_tree.nodes],'materials':mats,'animations':[a.name for a in bpy.data.actions],'sceneObjects':[{'name':o.name,'type':o.type,'constraints':[c.type for c in o.constraints],'shapeKeys':o.data.shape_keys.name if o.type=='MESH' and o.data.shape_keys else None} for o in sc.objects]}
(OUT/'canonical-effective-settings.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
