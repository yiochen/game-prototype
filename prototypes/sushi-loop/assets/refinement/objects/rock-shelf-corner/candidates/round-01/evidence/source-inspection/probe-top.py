import bpy,json
from pathlib import Path
base=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(base/'round-01.blend'));o=next(o for o in bpy.context.scene.objects if 'continuous_rounded' in o.name);m=o.data;m.calc_loop_triangles()
for p in m.polygons:
 if p.index>=10519 and p.index<=10532:
  print(p.index,list(p.normal),[list(m.vertices[i].co) for i in p.vertices])
