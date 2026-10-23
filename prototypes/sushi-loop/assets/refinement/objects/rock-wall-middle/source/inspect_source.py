import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parents[1]
sc=bpy.context.scene
cols=[c for c in bpy.data.collections if 'rock-wall-middle' in c.name]
rows=[]
for c in cols:
 obs=[]
 for o in c.all_objects:
  d={'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':[list(x) for x in o.matrix_world],'parent':o.parent.name if o.parent else None}
  if o.type=='MESH':
   vs=[o.matrix_world@v.co for v in o.data.vertices]
   d.update(vertices=len(vs),faces=len(o.data.polygons),bounds={'min':[min(v[i] for v in vs) for i in range(3)],'max':[max(v[i] for v in vs) for i in range(3)]},materials=[m.name if m else None for m in o.data.materials],modifiers=[{'type':m.type,'name':m.name} for m in o.modifiers])
  obs.append(d)
 rows.append({'collection':c.name,'objects':obs})
out={'blender':bpy.app.version_string,'scenes':[s.name for s in bpy.data.scenes],'activeScene':sc.name,'collections':rows,'camera':{'name':sc.camera.name,'matrix':[list(x) for x in sc.camera.matrix_world],'ortho_scale':sc.camera.data.ortho_scale,'shift_x':sc.camera.data.shift_x,'shift_y':sc.camera.data.shift_y} if sc.camera else None,'images':[{'name':i.name,'filepath':i.filepath,'source':i.source,'packed':bool(i.packed_file)} for i in bpy.data.images]}
(BASE/'source/original-native-audit.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
