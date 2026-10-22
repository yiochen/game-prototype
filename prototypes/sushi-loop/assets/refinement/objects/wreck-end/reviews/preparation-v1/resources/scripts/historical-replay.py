import bpy,sys,importlib.util,json,math
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[2];R=P/'resources'
p=R/'historical/capture_runtime.py';spec=importlib.util.spec_from_file_location('history',p);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
sc=h.scene();col=next(c for c in bpy.data.collections if 'wreck-end' in c.name)
if col.name not in sc.collection.children:sc.collection.children.link(col)
for c in bpy.data.collections:c.hide_viewport=False;c.hide_render=c!=col
for o in sc.objects:o.hide_render=o.type=='MESH' and o.name not in col.all_objects;o.hide_viewport=False;o.hide_set(False)
def en(lc):
 lc.exclude=False;lc.hide_viewport=False
 for c in lc.children:en(c)
en(bpy.context.view_layer.layer_collection)
for o in col.all_objects:o.hide_render=False
root=next(o for o in col.all_objects if o.type=='EMPTY');root.rotation_euler=(0,0,0);root.location=(0,0,0)
bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
record=h.configure_camera('square-top-front-oblique',(192,352),(96,248),4)
sc.render.filter_size=1.5
p=P/'baseline/historical-original4-S.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
(P/'historical-replay-record.json').write_text(json.dumps({'scope':'Historical provenance replay only; no canonical reset','camera':record,'filter':sc.render.filter_size,'source':'resources/source/original.blend','output':str(p.relative_to(P)),'actualRootMatrix':[list(row) for row in root.matrix_world]},indent=2)+'\n')
