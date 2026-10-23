import bpy,json,os
from mathutils import Vector
base=os.path.dirname(__file__)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(base+'/../../../backups/b1765262bfa897ad-sushi-loop-world-library.blend'))
obs=[o for o in bpy.data.objects if o.name.startswith('garbage-sofa__')]
data={'blender':bpy.app.version_string,'scenes':[s.name for s in bpy.data.scenes],'activeCamera':bpy.context.scene.camera.name if bpy.context.scene.camera else None,'objects':[]}
for o in obs:
 b=[o.matrix_world@Vector(c) for c in o.bound_box] if o.type=='MESH' else []
 data['objects'].append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'dimensions':list(o.dimensions),'bounds':[[min(v[i] for v in b) for i in range(3)],[max(v[i] for v in b) for i in range(3)]] if b else None,'modifiers':[(m.name,m.type) for m in o.modifiers],'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else [],'properties':{k:str(o[k]) for k in o.keys()},'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None})
json.dump(data,open(base+'/independent-native-inspection.json','w'),indent=2)
print(json.dumps(data,indent=2))
