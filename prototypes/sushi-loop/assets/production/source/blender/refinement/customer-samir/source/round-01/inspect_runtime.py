import bpy,json
from pathlib import Path
out=[]
for o in bpy.data.objects:
 if o.type=='MESH' and 'customer_samir__' in o.name:
  out.append({'name':o.name,'materials':[m.name for m in o.data.materials],'groups':[(g.name,g.index) for g in o.vertex_groups]})
Path(__file__).with_name('runtime-material-inspection.json').write_text(json.dumps(out,indent=2))
