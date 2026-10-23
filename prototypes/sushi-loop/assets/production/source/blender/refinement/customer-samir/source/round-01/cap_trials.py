import bpy
from pathlib import Path
D=Path(__file__).resolve().parent;OUT=D.parent.parent/'candidates/round-01/light-trials'
s=bpy.context.scene;m=bpy.data.materials['Samir R01 golden yellow cap'];p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
def lin(x):return ((x+.055)/1.055)**2.4 if x>.04045 else x/12.92
for he in ['C68B1D','B87B0F','D59A28']:
 col=tuple(lin(int(he[i:i+2],16)/255) for i in [0,2,4])+(1,);p.inputs['Base Color'].default_value=col;p.inputs['Emission Color'].default_value=col
 s.render.filepath=str(OUT/('cap-'+he+'.png'));bpy.ops.render.render(write_still=True)
