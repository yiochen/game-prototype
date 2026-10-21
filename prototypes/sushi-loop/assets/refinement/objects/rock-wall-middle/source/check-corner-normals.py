import bpy,json
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1];p=B/'candidates/round-03/native-audit.json';a=json.loads(p.read_text());m=bpy.data.objects['rock-wall-middle__continuous_carved_stone'].data
cn={}
for loop,n in zip(m.loops,m.corner_normals):cn.setdefault(loop.vertex_index,n.vector.copy())
w=sorted([v for v in m.vertices if abs(v.co.x+.5)<1e-7],key=lambda v:(round(v.co.y,7),round(v.co.z,7)));e=sorted([v for v in m.vertices if abs(v.co.x-.5)<1e-7],key=lambda v:(round(v.co.y,7),round(v.co.z,7)))
a['connectorsMeasured']['calculatedVertexNormalPairMaxDelta']=a['connectorsMeasured'].pop('maxPairNormalDelta')
a['connectorsMeasured']['actualCustomCornerNormalPairMaxDelta']=max((cn[x.index]-cn[y.index]).length for x,y in zip(w,e))
a['connectorsMeasured']['actualCustomCornerNormalMaxAbsoluteXAtCuts']=max(abs(cn[v.index].x) for v in w+e)
p.write_text(json.dumps(a,indent=2));print(a['connectorsMeasured'])
