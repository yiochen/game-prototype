import sys
sys.dont_write_bytecode=True
import bpy,json
from pathlib import Path
B=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(B/'resources/source/original.blend'))
s=bpy.context.scene;out={}
for aid in ['reef-middle','reef-corner','reef-end']:
 r=next(o for o in bpy.data.objects if o.name.startswith(aid+'__root'));c=next(c for c in s.collection.children if r in list(c.all_objects))
 for q in s.collection.children:q.hide_viewport=q!=c;q.hide_render=q!=c
 for l in s.view_layers[0].layer_collection.children:l.exclude=l.collection!=c
 r.rotation_euler.z=0;bpy.context.view_layer.update()
 core=next(o for o in c.all_objects if 'continuous_core' in o.name)
 vs=[r.matrix_world.inverted()@core.matrix_world@v.co for v in core.data.vertices]
 ports=json.loads(r['ports']);rec={'root':r.name,'collection':c.name,'authoredPorts':ports,'measuredFiniteRings':{}}
 for p in ports:
  axis=0 if p['direction'] in ['W','E'] else 1;plane=p['position'][axis]
  rec['measuredFiniteRings'][p['direction']]=[list(v) for v in vs if abs(v[axis]-plane)<1e-6]
 out[aid]=rec
(B/'evidence/context-topology.json').write_text(json.dumps(out,indent=2)+'\n')
print('CONTEXT_TOPOLOGY_MEASURED')
