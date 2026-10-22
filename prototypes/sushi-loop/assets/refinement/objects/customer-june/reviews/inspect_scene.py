import bpy,json,hashlib
from pathlib import Path
out=Path(__file__).parent
rows={}
def val(x):
 try:return list(x)
 except:return str(x)
rows['file']=bpy.data.filepath
rows['scenes']=[{'name':s.name,'camera':s.camera.name if s.camera else None,'size':[s.render.resolution_x,s.render.resolution_y],'props':{k:val(s[k]) for k in s.keys()},'collections':[c.name for c in s.collection.children]} for s in bpy.data.scenes]
rows['collections']=[{'name':c.name,'objects':[o.name for o in c.all_objects]} for c in bpy.data.collections if 'customer_june' in c.name]
rows['objects']=[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'parent_type':o.parent_type,'parent_bone':o.parent_bone,'matrix':[list(r) for r in o.matrix_world],'props':{k:val(o[k]) for k in o.keys()},'modifiers':[{'name':m.name,'type':m.type,'object':m.object.name if m.type=='ARMATURE' and m.object else None} for m in o.modifiers],'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],'vertex_count':len(o.data.vertices) if o.type=='MESH' else 0} for o in bpy.data.objects if 'customer_june' in o.name]
(out/('runtime-inventory.json' if 'starter' in rows['file'] else 'main-inventory.json')).write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps({'file':rows['file'],'scenes':[(s['name'],len(s['collections'])) for s in rows['scenes']],'collections':[(c['name'],len(c['objects'])) for c in rows['collections']],'objects':[(o['name'],o['type'],o['vertex_count']) for o in rows['objects']]}))
