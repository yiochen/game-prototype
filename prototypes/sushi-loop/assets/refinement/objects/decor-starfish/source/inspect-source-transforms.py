"""Follow-up actual source evaluation; original scene excluded this collection from active view layer.
No source save. This isolates the real collection so child transforms evaluate.
"""
import bpy,json,math
from pathlib import Path
base=Path(__file__).parent
col=next(c for c in bpy.data.collections if c.name=='S33_PROP_starfish.001')
sc=bpy.data.scenes.new('temporary source starfish inspection');bpy.context.window.scene=sc
col.hide_viewport=False;col.hide_render=False;sc.collection.children.link(col)
for o in col.all_objects:o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
bpy.context.view_layer.update();out=[]
for o in col.all_objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=[ev.matrix_world@x.co for x in me.vertices]
 out.append({'name':o.name,'localLocation':list(o.location),'localScale':list(o.scale),'worldMatrix':[list(r) for r in ev.matrix_world],'bounds':{'min':[min(x[i] for x in v) for i in range(3)],'max':[max(x[i] for x in v) for i in range(3)]}});ev.to_mesh_clear()
(base/'source-transforms-evaluated.json').write_text(json.dumps({'note':'Initial active library view layer excluded starfish; raw initial spot matrix values were not evaluated. This temporary source scene evaluates the collection independently. Source file is never saved.','collection':col.name,'objects':out},indent=2)+'\n')
