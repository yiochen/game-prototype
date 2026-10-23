import bpy,bmesh,json
from pathlib import Path
base=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(base/'round-01.blend'));o=next(o for o in bpy.context.scene.objects if 'continuous_rounded' in o.name);m=bmesh.new();m.from_mesh(o.data)
e=[{'p':[list(v.co) for v in x.verts],'face':[(f.index,list(f.normal)) for f in x.link_faces]} for x in m.edges if not x.is_manifold]
(base/'boundary-diagnostic.json').write_text(json.dumps(e,indent=2));print(json.dumps(e,indent=2))
