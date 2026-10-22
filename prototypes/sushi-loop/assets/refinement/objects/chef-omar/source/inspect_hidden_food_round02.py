import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from food_common_round02 import *
c=config();bpy.ops.wm.open_mainfile(filepath=str(P/c['candidate']));sc,coll,root,arm,rig,asset,plane=setup(c)
for clip in ['idle','work','hold','load']:
 native.apply_clip(asset,rig,clip,1,'N',sc);e=plane.evaluated_get(bpy.context.evaluated_depsgraph_get());print('HIDDEN',clip,'hideRender',plane.hide_render,'hideViewport',plane.hide_viewport,'hideGet',plane.hide_get(),'visible',plane.visible_get(),'loc',list(plane.location),'eloc',list(e.location),'rawmatrix',[list(r) for r in plane.matrix_world],'evalmatrix',[list(r) for r in e.matrix_world],flush=True)
 saved=(plane.hide_render,plane.hide_viewport,plane.hide_get());plane.hide_render=False;plane.hide_viewport=False;plane.hide_set(False);plane.update_tag();bpy.context.view_layer.update();e=plane.evaluated_get(bpy.context.evaluated_depsgraph_get());print('FORCED',clip,'loc',list(e.location),'matrix',[list(r) for r in e.matrix_world],flush=True)
 plane.hide_render,plane.hide_viewport=saved[:2];plane.hide_set(saved[2]);bpy.context.view_layer.update()
