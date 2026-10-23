import bpy,json
from pathlib import Path
out=Path(__file__).parent
cs=[c for c in bpy.data.collections if 'reef' in c.name.lower() or 'ruin' in c.name.lower()]
report={'collections':[],'scenes':[]}
for c in cs:
 report['collections'].append({'name':c.name,'objects':[{'name':o.name,'type':o.type,'location':list(o.location),'scale':list(o.scale),'dimensions':list(o.dimensions),'parent':o.parent.name if o.parent else None,'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],'modifiers':[{ 'type':m.type,'name':m.name} for m in o.modifiers]} for o in c.all_objects]})
for sc in bpy.data.scenes:
 report['scenes'].append({'name':sc.name,'camera':sc.camera.name if sc.camera else None,'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y], 'collections':[c.name for c in sc.collection.children]})
(out/'source-inspection.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
