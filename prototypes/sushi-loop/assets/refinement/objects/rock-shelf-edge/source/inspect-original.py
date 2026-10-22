import bpy,json
from pathlib import Path
p=Path(__file__).resolve().parent
roots=[o for o in bpy.data.objects if o.name.startswith('rock-shelf-edge__root')]
def desc(o):
 return [o]+[d for c in o.children for d in desc(c)]
rs=[]
for root in roots:
 objects=desc(root); rows=[]
 for o in objects:
  d={'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'parent':o.parent.name if o.parent else None}
  if o.type=='MESH':
   co=[root.matrix_world.inverted() @ o.matrix_world @ v.co for v in o.data.vertices]
   d.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),bounds=[[min(v[i] for v in co) for i in range(3)],[max(v[i] for v in co) for i in range(3)]],smoothCount=sum(f.use_smooth for f in o.data.polygons),materials=[m.name for m in o.data.materials if m],modifiers=[{'name':m.name,'type':m.type} for m in o.modifiers])
   if len(co)<100:d['coordinates']=[list(v) for v in co]
  rows.append(d)
 rs.append({'root':root.name,'objects':rows})
out={'scene':bpy.data.filepath,'version':bpy.app.version_string,'roots':rs,'camera':{'name':bpy.context.scene.camera.name if bpy.context.scene.camera else None},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'location':list(o.location)} for o in bpy.data.objects if o.type=='LIGHT']}
(p/'original-native-inspection.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
