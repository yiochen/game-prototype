import bpy,json,math
from mathutils import Vector
from pathlib import Path
p=Path(__file__).resolve().parent
r={'blender':bpy.app.version_string,'scenes':[],'collections':[],'objects':[],'materials':[]}
for s in bpy.data.scenes:
 r['scenes'].append({'name':s.name,'objects':[o.name for o in s.objects],'camera':s.camera.name if s.camera else None,'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'world':s.world.name if s.world else None,'view':s.view_settings.view_transform})
for c in bpy.data.collections:r['collections'].append({'name':c.name,'objects':[o.name for o in c.objects],'children':[x.name for x in c.children]})
for o in bpy.data.objects:
 d={'name':o.name,'type':o.type,'collection':[c.name for c in o.users_collection],'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'parent':o.parent.name if o.parent else None,'matrix':[list(row) for row in o.matrix_world],'hide_render':o.hide_render,'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else None,'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]}
 if o.type=='MESH':
  pts=[o.matrix_world@Vector(v) for v in o.bound_box];d.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),bounds=[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]])
 if o.type=='CAMERA':d['camera']={'type':o.data.type,'ortho_scale':o.data.ortho_scale,'shift_x':o.data.shift_x,'shift_y':o.data.shift_y,'lens':o.data.lens}
 r['objects'].append(d)
for m in bpy.data.materials:
 r['materials'].append({'name':m.name,'diffuse':list(m.diffuse_color),'nodes':[{'type':n.type,'inputs':{i.name:(list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value) for i in n.inputs if hasattr(i,'default_value') and isinstance(i.default_value,(int,float,str,list,tuple)) or hasattr(i,'default_value') and type(i.default_value).__name__ in ['bpy_prop_array','Color','Vector']}} for n in m.node_tree.nodes] if m.use_nodes else []})
(p/'source-inspection.json').write_text(json.dumps(r,indent=2))
print('INSPECTION_SAVED',len(r['objects']))
