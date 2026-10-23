import bpy,json,os
from mathutils import Vector
p=os.path.dirname(__file__)
bpy.context.window.scene=bpy.data.scenes['S33 Native Asset Library Export']
for vl in bpy.context.scene.view_layers:
 def activate(lc):
  lc.exclude=False;lc.hide_viewport=False
  for child in lc.children:activate(child)
 activate(vl.layer_collection)
c=bpy.data.collections['S33_PROP_workshop-hut.001'];c.hide_viewport=False;c.hide_render=False
for ob in c.all_objects:ob.hide_viewport=False;ob.hide_set(False)
r=bpy.data.objects['workshop-hut__root.001'];r.location=(0,0,0);r.rotation_euler=(0,0,0);r.scale=(1,1,1)
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
rows=[]
for c in bpy.data.collections:
 if 'hut' in c.name.lower():
  for o in c.all_objects:
   rows.append({'collection':c.name,'name':o.name,'type':o.type,'location':list(o.location),'dimensions':list(o.dimensions),'bounds': [[min((o.matrix_world@Vector(v))[i] for v in o.bound_box),max((o.matrix_world@Vector(v))[i] for v in o.bound_box)] for i in range(3)] if o.type=='MESH' else None,'materials':[m.name for m in o.data.materials] if o.type=='MESH' else []})
json.dump({'blender':bpy.app.version_string,'collections':[c.name for c in bpy.data.collections],'hut':rows},open(p+'/native-source-independent.json','w'),indent=2)
print(json.dumps(rows))
