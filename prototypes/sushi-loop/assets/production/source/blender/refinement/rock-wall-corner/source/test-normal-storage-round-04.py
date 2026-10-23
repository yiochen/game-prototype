import bpy,json
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-04';bpy.ops.wm.open_mainfile(filepath=str(B/'source/round-04.blend'));me=bpy.data.objects['rock-wall-corner__unified_worn_stone'].data
intent={(p['index'],p['port']):Vector(p['expectedNormal']) for p in json.loads((O/'boundary-intent.json').read_text())};want={}
for poly in me.polygons:
 for li in poly.loop_indices:
  lp=me.loops[li];v=me.vertices[lp.vertex_index].co
  for port in ['W','N']:
   on=lambda p:abs(p.x+.5)<1e-7 if port=='W' else abs(p.y-.5)<1e-7
   if (lp.vertex_index,port) in intent and on(v) and any(vi!=lp.vertex_index and on(me.vertices[vi].co) for vi in poly.vertices):want[li]=intent[(lp.vertex_index,port)]
inputs=[Vector(n.vector) for n in me.corner_normals]
for i,n in want.items():inputs[i]=n
out=[]
for step in range(10):
 me.normals_split_custom_set(inputs);stored=[Vector(n.vector) for n in me.corner_normals];errs=[(stored[i]-n).length for i,n in want.items()];out.append({'step':step,'maxDelta':max(errs),'over001':sum(e>.001 for e in errs)})
 for i,n in want.items():inputs[i]=(inputs[i]+(n-stored[i])).normalized()
(O/'normal-storage-experiment.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
