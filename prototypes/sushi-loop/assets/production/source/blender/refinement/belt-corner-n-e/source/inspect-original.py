import bpy,json,pathlib
from mathutils import Vector
p=pathlib.Path(__file__).resolve().parent
asset='belt-corner-n-e'
collections=[c for c in bpy.data.collections if asset in c.name]
out={'blender':bpy.app.version_string,'activeScene':bpy.context.scene.name,'collections':[]}
for c in collections:
 co={'name':c.name,'objects':[]}
 for o in c.all_objects:
  d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'loc':list(o.location),'rotation':list(o.rotation_euler),'worldMatrix':[list(x) for x in o.matrix_world]}
  if o.type=='MESH':
   pts=[o.matrix_world@v.co for v in o.data.vertices];d.update(vertices=len(pts),polygons=len(o.data.polygons),bounds=[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],materials=[m.name for m in o.data.materials],modifiers=[{'name':m.name,'type':m.type} for m in o.modifiers])
   if 'deck' in o.name:d['uv']=[list(x.uv) for x in o.data.uv_layers.active.data] if o.data.uv_layers.active else None
  co['objects'].append(d)
 out['collections'].append(co)
for m in bpy.data.materials:
 if asset in m.name and m.use_nodes:
  out.setdefault('materials',[]).append({'name':m.name,'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None)} for n in m.node_tree.nodes],'action':m.node_tree.animation_data.action.name if m.node_tree.animation_data and m.node_tree.animation_data.action else None})
(p/'original-native-inspection.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k!='materials'},indent=2)[:22000])
