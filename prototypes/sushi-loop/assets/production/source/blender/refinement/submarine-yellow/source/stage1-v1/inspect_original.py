import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parents[2]
src=base/'reviews/preparation-v1/resources/original-library.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
cs=[c for c in bpy.data.collections if 'submarine' in c.name.lower()]
report={'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'collections':[]}
for c in cs:
 r={'name':c.name,'properties':dict(c.items()),'objects':[]}
 for o in c.all_objects:
  if o.type not in ['MESH','EMPTY']:continue
  pts=[o.matrix_world@Vector(v) for v in o.bound_box] if o.type=='MESH' else []
  r['objects'].append({'name':o.name,'type':o.type,'location':list(o.location),'scale':list(o.scale),'rotation':list(o.rotation_euler),'parent':o.parent.name if o.parent else None,'vertices':len(o.data.vertices) if o.type=='MESH' else 0,'modifiers':[m.type for m in o.modifiers],'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],'bounds':[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]] if pts else None,'properties':dict(o.items())})
 report['collections'].append(r)
(base/'source/stage1-v1/original-native-inspection.json').write_text(json.dumps(report,indent=2,default=str))
print(json.dumps({'collections':[(c['name'],len(c['objects'])) for c in report['collections']],'sha256':report['sha256']},indent=2))
