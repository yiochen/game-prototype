import bpy,json
from pathlib import Path
out={}
for o in bpy.data.objects:
 if o.type=='MESH' and 'samir' in o.name and 'ground_root' not in o.name:
  out[o.name]={'verts':[list(v.co) for v in o.data.vertices],'groups':[(g.name,g.index) for g in o.vertex_groups], 'weights':[[[g.group,g.weight] for g in v.groups] for v in o.data.vertices], 'mods':[(m.type,{p.identifier:str(getattr(m,p.identifier)) for p in m.bl_rna.properties if p.identifier in ['width','segments','affect','use_clamp_overlap','limit_method','levels','subdivision_type']}) for m in o.modifiers]}
materials={}
for m in bpy.data.materials:
 if 'customer-samir approved' in m.name: materials[m.name]=[(n.type,n.name,{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in n.inputs if hasattr(i,'default_value')}) for n in m.node_tree.nodes]
Path(__file__).with_name('geometry-inspection.json').write_text(json.dumps({'objects':out,'materials':materials},indent=2,default=str))
