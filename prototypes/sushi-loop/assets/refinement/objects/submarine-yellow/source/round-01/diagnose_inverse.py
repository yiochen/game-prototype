import sys,runpy
sys.dont_write_bytecode=True
from pathlib import Path
globals().update(runpy.run_path(str(Path(__file__).parent/'native_common.py')))
s,root,col=open_source();apply('upgraded-dock-ready')
for q in json.loads(col['canonicalComponents']):
 cr=bpy.data.objects[q['root']];ob=bpy.data.objects[q['meshNames'][0]];me=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();v=me.vertices[0].co.copy();print(q['asset'],cr.name,ob.name,'mount',val(cr.matrix_world),'normalinverse',val(cr.matrix_world.inverted()@(ob.matrix_world@v)),flush=True)
 par=cr.parent;bi=cr.matrix_basis.copy();pi=cr.matrix_parent_inverse.copy();cr.parent=None;cr.matrix_parent_inverse=Matrix.Identity(4);cr.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update();print('neutral',val(cr.matrix_world),val(ob.matrix_world@v),flush=True)
 cr.parent=par;cr.matrix_parent_inverse=pi;cr.matrix_basis=bi;bpy.context.view_layer.update();print('remounted',val(cr.matrix_world.inverted()@(ob.matrix_world@v)),flush=True)
 apply('travel',3.5,'N');print('motion',val(cr.matrix_world.inverted()@(ob.matrix_world@v)),flush=True);apply('upgraded-dock-ready')
