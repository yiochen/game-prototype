import bpy,json
from pathlib import Path
from mathutils import Vector
bpy.context.scene.frame_set(1);bpy.context.view_layer.update();c=bpy.data.collections['S33_CHARACTER_customer_rosa.001'];ps=[];records=[]
for o in c.all_objects:
 if o.type!='MESH' or o.hide_render:continue
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=[ev.matrix_world@v.co for v in m.vertices];ps+=p
 records.append({'name':o.name,'parent':o.parent.name if o.parent else None,'scale':list(o.scale),'bounds':[[min(v[i] for v in p),max(v[i] for v in p)] for i in range(3)]});ev.to_mesh_clear()
d={'bounds':[[min(v[i] for v in ps),max(v[i] for v in ps)] for i in range(3)],'objects':records,'actions':[{'owner':o.name,'action':o.animation_data.action.name if o.animation_data.action else None} for o in c.all_objects if o.animation_data]};Path(__file__).with_suffix('.json').write_text(json.dumps(d,indent=2));print(d['bounds']);print(d['actions'])
