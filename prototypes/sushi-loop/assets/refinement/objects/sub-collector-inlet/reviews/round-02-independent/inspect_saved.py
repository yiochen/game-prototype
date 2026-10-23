import bpy,json,pathlib
O=pathlib.Path(__file__).resolve().parent;s=bpy.context.scene;c=bpy.data.collections['REFINED__sub-collector-inlet'];d={'objects':[],'actions':[]}
for o in c.all_objects:d['objects'].append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'loc':list(o.location),'rot':list(o.rotation_euler),'scale':list(o.scale),'dimensions':list(o.dimensions),'modifiers':[m.type for m in o.modifiers]})
for a in bpy.data.actions:
 if a.name.startswith('INLET_NATIVE'):d['actions'].append({'name':a.name,'curves':[{'path':f.data_path,'i':f.array_index,'keys':[[*k.co,k.interpolation] for k in f.keyframe_points]} for l in a.layers for st in l.strips for b in st.channelbags for f in b.fcurves]})
(O/'saved-data.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
