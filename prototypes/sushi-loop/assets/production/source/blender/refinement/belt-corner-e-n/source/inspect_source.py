import bpy,json,math
from pathlib import Path
p=Path(__file__).parent
result={}
result['collections']=[c.name for c in bpy.data.collections if 'corner-e-n' in c.name]
co=bpy.data.collections.get('S33_FB_belt-corner-e-n') or next(c for c in bpy.data.collections if 'corner-e-n' in c.name)
result['objects']=[]
for o in co.all_objects:
 result['objects'].append(dict(name=o.name,type=o.type,parent=o.parent.name if o.parent else None,rotation=list(o.rotation_euler),location=list(o.location),dimensions=list(o.dimensions),vertices=len(o.data.vertices) if o.type=='MESH' else None,materials=[m.name for m in o.data.materials] if o.type=='MESH' else [],bounds=[list(o.matrix_world@__import__('mathutils').Vector(v)) for v in o.bound_box] if o.type=='MESH' else []))
result['cameras']=[dict(name=o.name,matrix=[list(r) for r in o.matrix_world],ortho=o.data.ortho_scale) for o in bpy.data.objects if o.type=='CAMERA']
(p/'source-inspection.json').write_text(json.dumps(result,indent=2))
print('AUDIT',str(p/'source-inspection.json'))
