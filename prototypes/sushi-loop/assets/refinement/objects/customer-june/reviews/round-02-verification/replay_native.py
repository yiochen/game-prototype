import bpy,json,sys,importlib.util,hashlib
sys.dont_write_bytecode=True
from pathlib import Path
P=Path(__file__).parent;O=P.parents[1];runtime='runtime' in bpy.data.filepath;mode='runtime' if runtime else 'main';record=json.loads((O/('inputs/runtime-variants/export/source/customer-june/rig.json' if runtime else 'inputs/source-rig.json')).read_text());spec=importlib.util.spec_from_file_location('native',O/'source/native_actions.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n);root=bpy.data.objects[record['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];col=next(c for c in sc.collection.children if root in list(c.all_objects))
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
col.hide_render=False;col.hide_viewport=False
controls=[('eat-salmon','W',7),('seated-wait-empty','S',1)] if runtime else [('stand','S',1),('stand','N',1),('walk','E',4),('eat','S',7)]
for clip,d,f in controls:
 n.apply_clip({'root':root,'collection':col},record,clip,f,d,sc);sc.render.filepath=str(P/(mode+'-replay-'+clip+'-'+d+'-'+str(f)+'.png'));bpy.ops.render.render(write_still=True)
