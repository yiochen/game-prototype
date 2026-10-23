import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).parent
names=[c.name for c in bpy.data.collections]
col=[c for c in bpy.data.collections if 'cover' in c.name.lower()]
res={'blenderVersion':bpy.app.version_string,'collections':names,'matchingCollections':[]}
for c in col:
 d={'name':c.name,'objects':[]}
 for o in c.all_objects:
  q={'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'parent':o.parent.name if o.parent else None,'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'materials':[m.name for m in o.data.materials] if o.type=='MESH' else []}
  if o.type=='MESH':
   v=[o.matrix_world@Vector(v) for v in o.bound_box]
   q['vertices']=len(o.data.vertices);q['bounds']=[[min(v[i] for v in v),max(v[i] for v in v)] for i in range(3)]
  d['objects'].append(q)
 res['matchingCollections'].append(d)
res['scenes']=[{'name':s.name,'camera':s.camera.name if s.camera else None,'engine':s.render.engine,'frame':[s.frame_start,s.frame_end],'fps':s.render.fps,'resolution':[s.render.resolution_x,s.render.resolution_y],'filter_size':s.render.filter_size} for s in bpy.data.scenes]
res['actions']=[a.name for a in bpy.data.actions]
(OUT/'original-native-inspection.json').write_text(json.dumps(res,indent=2))
print(json.dumps(res,indent=2))
