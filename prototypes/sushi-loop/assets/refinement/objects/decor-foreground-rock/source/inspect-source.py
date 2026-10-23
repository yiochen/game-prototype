import bpy,json
from pathlib import Path
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'original-library.blend'))
col=bpy.data.collections['S33 production concept cobalt-shelf']
data={'startupScene':bpy.context.scene.name,'objects':[]}
for o in col.all_objects:
 d={'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'matrix':[list(r) for r in o.matrix_world],'parent':o.parent.name if o.parent else None}
 if o.type=='MESH':
  d.update(vertices=[list(v.co) for v in o.data.vertices],faces=[list(p.vertices) for p in o.data.polygons],materials=[m.name for m in o.data.materials],modifiers=[m.type for m in o.modifiers])
 data['objects'].append(d)
(BASE/'independent-source-audit.json').write_text(json.dumps(data,indent=2))
print(json.dumps(data,indent=2))
