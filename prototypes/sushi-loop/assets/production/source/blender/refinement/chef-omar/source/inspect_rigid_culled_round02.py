import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from food_common_round02 import *
c=config();sc,coll,root,arm,rig,asset,plane=setup(c)
for clip in rig['clips']:
 native.apply_clip(asset,rig,clip,1,'N',sc);dg=bpy.context.evaluated_depsgraph_get()
 for o in coll.all_objects:
  if '__knife_' in o.name or '__utensil' in o.name:
   print('RIGID',clip,o.name,'hide',o.hide_viewport,o.hide_get(),'parent',o.parent.name if o.parent else None,'constraints',len(o.constraints),'modifiers',len(o.modifiers),'loc',list(o.location),'basis',[list(r) for r in o.matrix_basis],'eval',[list(r) for r in o.evaluated_get(dg).matrix_world],flush=True)
