import bpy,json
from pathlib import Path
out=Path(__file__).resolve().parent
r=[]
for o in bpy.data.objects:
 if 'rock-shelf-end' in o.name:
  r.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render,'collection':[c.name for c in o.users_collection],'location':list(o.location),'scale':list(o.scale),'vertices':len(o.data.vertices) if o.type=='MESH' else None,'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],'bounds':[[min(v[i] for v in o.bound_box),max(v[i] for v in o.bound_box)] for i in range(3)] if o.type=='MESH' else None})
(out/'original-inspection.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r))
