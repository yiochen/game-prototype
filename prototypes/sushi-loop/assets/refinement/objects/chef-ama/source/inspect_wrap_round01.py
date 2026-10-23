import bpy,json
from pathlib import Path
p=Path(__file__).parent
o=bpy.data.objects['chef_ama__turban.002']
print('ORIGINAL_WRAP',json.dumps({'verts':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons]}))
