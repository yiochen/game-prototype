import bpy,json,sys,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;col=bpy.data.collections['S33_PROP_portal_rim.002'];sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc
rows=[]
for o in col.all_objects:
 a=o.animation_data.action if o.animation_data else None
 curves=[]
 if a:
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for f in bag.fcurves:curves.append({'dataPath':f.data_path,'arrayIndex':f.array_index,'keys':[[float(k.co.x),float(k.co.y)] for k in f.keyframe_points],'interpolation':sorted(set(k.interpolation for k in f.keyframe_points))})
 rows.append({'object':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'action':a.name if a else None,'actionRange':list(a.frame_range) if a else None,'curves':curves,'constraints':[c.type for c in o.constraints],'drivers':[d.data_path for d in o.animation_data.drivers] if o.animation_data else []})
(P/'native-controls.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'controls':rows,'activeActionCount':sum(bool(r['action']) for r in rows),'approval':False},indent=2)+'\n')
print('ACTIVE_ACTIONS',sum(bool(r['action']) for r in rows))
