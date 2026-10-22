import bpy,json,sys,importlib.util,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-01/diagnostics';OUT.mkdir(exist_ok=True)
MODE=sys.argv[sys.argv.index('--')+1]
spec=importlib.util.spec_from_file_location('ellis_native',HERE/'resources/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
isOriginal=MODE=='original';recordMode='main' if isOriginal else MODE
rec=json.loads((HERE/'resources'/f'{recordMode}-rig.json').read_text());root=bpy.data.objects[rec['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];coll=next(c for c in sc.collection.children if root.name in c.all_objects);asset={'root':root,'collection':coll}
for c in sc.collection.children:c.hide_render=c!=coll;c.hide_viewport=c!=coll
def show(l):
 l.exclude=False;l.hide_viewport=False
 for ch in l.children:show(ch)
show(sc.view_layers[0].layer_collection)
for c in [coll]+list(coll.children_recursive):c.hide_render=False;c.hide_viewport=False
food=next(o for o in coll.all_objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi')
sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100
report={'mode':MODE,'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'foodFlags':{'visible_shadow':food.visible_shadow,'surface_render_method':food.data.materials[0].surface_render_method,'use_transparency_overlap':food.data.materials[0].use_transparency_overlap,'use_transparent_shadow':food.data.materials[0].use_transparent_shadow},'renders':[]}
if isOriginal:
 for direction in 'NESW':
  native.apply_clip(asset,rec,'stand',1,direction,sc);p=OUT/('original-native-stand-'+direction+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True,scene=sc.name);report['renders'].append(str(p.relative_to(OBJ)))
else:
 for clip in (['seated_wait','eat'] if MODE=='main' else ['eat-salmon','seated-wait-empty']):
  for direction in 'NESW':
   native.apply_clip(asset,rec,clip,5,direction,sc)
   for setting in ['source-alpha-flags','final-alpha-flags']:
    food.visible_shadow=(setting=='source-alpha-flags');m=food.data.materials[0];m.surface_render_method='DITHERED' if setting=='source-alpha-flags' else 'BLENDED';m.use_transparency_overlap=(setting=='source-alpha-flags')
    p=OUT/(MODE+'-'+clip.replace('_','-')+'-'+direction+'-'+setting+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True,scene=sc.name);report['renders'].append(str(p.relative_to(OBJ)))
 # Renderer repeatability is measured, never asserted from repeated settings alone.
 food.visible_shadow=False;food.data.materials[0].surface_render_method='BLENDED';food.data.materials[0].use_transparency_overlap=False
 for clip,direction,frame in ([('stand','S',5),('eat','E',12),('panic','N',7)] if MODE=='main' else [('eat-salmon','S',5)]):
  native.apply_clip(asset,rec,clip,frame,direction,sc)
  for repeat in range(2):
   p=OUT/(MODE+'-'+clip.replace('_','-')+'-'+direction+f'-repeat-{repeat}.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True,scene=sc.name);report['renders'].append(str(p.relative_to(OBJ)))
(OUT/(MODE+'-diagnostics.json')).write_text(json.dumps(report,indent=2)+'\n')
print('ELLIS_DIAGNOSTICS_COMPLETE',MODE,flush=True)
