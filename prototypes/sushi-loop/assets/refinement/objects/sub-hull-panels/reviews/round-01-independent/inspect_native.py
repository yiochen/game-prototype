import sys
sys.dont_write_bytecode=True
import bpy,json,pathlib
out=pathlib.Path(__file__).resolve().parent
print('SCENE',bpy.context.scene.name,'OBJECTS',[(o.name,o.type,o.parent.name if o.parent else None,o.hide_render) for o in bpy.context.scene.objects])
for name in ['sub-hull-panels__root','sub-hull-panels__motion']:
 o=bpy.data.objects[name];print('PROPS',name,{k:str(v) for k,v in o.items()})
for a in bpy.data.actions:
 print('ACTION',a.name,'slots',[(s.identifier,s.target_id_type) for s in a.slots])
 for l in a.layers:
  for st in l.strips:
   for slot in a.slots:
    bag=st.channelbag(slot,ensure=False)
    if not bag:continue
    for f in bag.fcurves:
     print('FC',f.data_path,f.array_index,[(k.co[:],k.interpolation) for k in f.keyframe_points],[(m.type,{p.identifier:str(getattr(m,p.identifier)) for p in m.bl_rna.properties if not p.is_readonly and p.identifier not in ['rna_type']}) for m in f.modifiers])
with bpy.data.libraries.load(str(out/'resources/neutral.blend'),link=False) as (a,b):print('NEUTRAL_COLLECTIONS',a.collections)
