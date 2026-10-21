import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parent
objects=[o for o in bpy.data.objects if o.name.startswith('crate-wood__')]
def matrix(m): return [list(r) for r in m]
def val(v):
 try: return list(v)
 except TypeError: return v
meshes=[]
for o in objects:
 if o.type!='MESH': continue
 evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
 corners=[evaluated.matrix_world@Vector(c) for c in evaluated.bound_box]
 geo={'vertices':[list(v.co) for v in o.data.vertices],'polygons':[list(f.vertices) for f in o.data.polygons]}
 meshes.append({'name':o.name,'matrixWorld':matrix(o.matrix_world),'matrixLocal':matrix(o.matrix_local),'geometrySHA256':hashlib.sha256(json.dumps(geo,sort_keys=True).encode()).hexdigest(),'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'evaluatedBounds':[[min(v[i] for v in corners) for i in range(3)],[max(v[i] for v in corners) for i in range(3)]],'materials':[m.name if m else None for m in o.data.materials],'modifiers':[{'name':m.name,'type':m.type,**({'width':m.width,'segments':m.segments} if m.type=='BEVEL' else {})} for m in o.modifiers]})
materials=[]
for m in sorted(set(m for o in objects if o.type=='MESH' for m in o.data.materials if m),key=lambda m:m.name):
 nodes=[]
 for n in m.node_tree.nodes if m.use_nodes else []:
  nodes.append({'name':n.name,'type':n.bl_idname,'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')}})
 links=[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links] if m.use_nodes else []
 materials.append({'name':m.name,'diffuseColor':list(m.diffuse_color),'nodes':nodes,'links':links})
s=bpy.context.scene
audit={'role':'Independent read-only inspection of exact approved crate source; no render or save performed','source':bpy.data.filepath,'objects':[{'name':o.name,'type':o.type,'matrixWorld':matrix(o.matrix_world),'rotationEuler':list(o.rotation_euler),'parent':o.parent.name if o.parent else None} for o in objects],'meshes':meshes,'materials':materials,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':getattr(o.data,'size',None),'matrixWorld':matrix(o.matrix_world)} for o in s.objects if o.type=='LIGHT'],'render':{'engine':s.render.engine,'samples':s.cycles.samples,'filmTransparent':s.render.film_transparent,'resolution':[s.render.resolution_x,s.render.resolution_y],'percentage':s.render.resolution_percentage,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'useNodes':s.use_nodes},'dependencies':{'images':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'],'libraries':[l.filepath for l in bpy.data.libraries]}}

for label,tree in [('world',s.world.node_tree if s.world else None),('compositor',getattr(s,'compositing_node_group',None) or getattr(s,'node_tree',None))]:
 audit[label+'Nodes']={'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'operation':getattr(n,'operation',None),'blendType':getattr(n,'blend_type',None)} for n in tree.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in tree.links]} if tree else None
(p/'approved-source-inspection.json').write_text(json.dumps(audit,indent=2)+'\n')
print('SOURCE_INSPECTED '+str(p/'approved-source-inspection.json'))
