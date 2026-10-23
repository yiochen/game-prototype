import bpy,json
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parents[1]
original=BASE/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'
bpy.ops.wm.open_mainfile(filepath=str(original.resolve()))
bpy.context.view_layer.update()
cs=[c for c in bpy.data.collections if 'rock-wall-edge' in c.name]
out={'scenes':[s.name for s in bpy.data.scenes],'collections':[]}
for c in cs:
 obs=[]
 for o in c.all_objects:
  a={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'custom':{k:o[k] for k in o.keys()}}
  if o.type=='MESH':
   v=[o.matrix_world@p.co for p in o.data.vertices]
   a.update(vertices=len(v),faces=len(o.data.polygons),bounds={'min':[min(p[i] for p in v) for i in range(3)],'max':[max(p[i] for p in v) for i in range(3)]},materials=[m.name for m in o.data.materials],modifiers=[m.type for m in o.modifiers])
  obs.append(a)
 out['collections'].append({'name':c.name,'objects':obs})
(BASE/'source/original-native-inspection.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))

bpy.ops.wm.open_mainfile(filepath=str((BASE/'inputs/approved-middle/project.blend').resolve()))
bpy.context.view_layer.update()
ref={'scene':bpy.context.scene.name,'objects':[{'name':o.name,'type':o.type,'vertices':len(o.data.vertices) if o.type=='MESH' else None} for o in bpy.context.scene.objects]}
(BASE/'source/middle-native-inspection.json').write_text(json.dumps(ref,indent=2))
