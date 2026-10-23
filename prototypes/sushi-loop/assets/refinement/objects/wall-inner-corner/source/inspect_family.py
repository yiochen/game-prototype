import bpy,json
from pathlib import Path
B=Path(__file__).resolve().parents[1];F=B.parent/'wall-middle';D=json.loads((B/'inputs/family-settings.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(F/D['project']['path']))
for o in bpy.data.objects:
 if o.type=='MESH':
  xs=sorted(set(round(v.co.x,6) for v in o.data.vertices));cnt=sum(abs(v.co.x+.5)<1e-6 for v in o.data.vertices)
  print(o.name,len(o.data.vertices),'profile',cnt,'xs',len(xs),'mat',o.data.materials[0].name,'normals',len(o.data.corner_normals))
