import bpy,json
from pathlib import Path
P=Path(__file__).parent;arm=bpy.data.objects['chef_noor__armature.001'];(P/'source-bones-rest-original.json').write_text(json.dumps({b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local]} for b in arm.data.bones},indent=2))
