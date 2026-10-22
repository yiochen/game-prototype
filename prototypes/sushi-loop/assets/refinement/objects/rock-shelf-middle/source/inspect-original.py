import bpy,json
from pathlib import Path
base=Path(__file__).resolve().parent
out={'scenes':[s.name for s in bpy.data.scenes],'collections':[c.name for c in bpy.data.collections if 'shelf' in c.name.lower()], 'objects':[]}
for o in bpy.data.objects:
 if 'shelf' in o.name.lower() or any('shelf' in c.name.lower() for c in o.users_collection):
  out['objects'].append({'name':o.name,'type':o.type,'collection':[c.name for c in o.users_collection], 'location':list(o.location),'dimensions':list(o.dimensions),'rotation':list(o.rotation_euler),'bounds':[list(o.matrix_world@__import__('mathutils').Vector(v)) for v in o.bound_box], 'vertices':len(o.data.vertices) if o.type=='MESH' else None,'polygons':len(o.data.polygons) if o.type=='MESH' else None,'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else [],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]})
(base/'original-native-inspection.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
