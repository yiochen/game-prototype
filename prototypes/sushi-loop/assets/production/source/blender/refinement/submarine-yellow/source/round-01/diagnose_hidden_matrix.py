import sys,runpy
sys.dont_write_bytecode=True
from pathlib import Path
globals().update(runpy.run_path(str(Path(__file__).parent/'native_common.py')))
s,root,col=open_source()
def world(o):return world(o.parent)@o.matrix_parent_inverse@o.matrix_basis if o.parent else o.matrix_basis
for clip in ['upgraded-dock-ready','travel','upgraded-travel']:
 apply(clip,3.5,'N')
 for q in json.loads(col['canonicalComponents']):
  cr=bpy.data.objects[q['root']];ob=bpy.data.objects[q['meshNames'][0]];v=ob.data.vertices[0].co;print(clip,q['asset'],'hidden',ob.hide_viewport,'actual',val(cr.matrix_world.inverted()@(ob.matrix_world@v)),'hierarchy',val(world(cr).inverted()@(world(ob)@v)))
