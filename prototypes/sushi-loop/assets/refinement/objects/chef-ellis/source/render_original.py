exec(open(__file__.replace('render_original.py','inspect_original.py')).read())
from math import radians
orig=bpy.data.scenes.get('S33 Native Asset Library Export')
cam=next(o for o in bpy.data.objects if o.type=='CAMERA');sc.collection.objects.link(cam);sc.camera=cam
for o in bpy.data.objects:
 if o.type=='LIGHT':sc.collection.objects.link(o);print('LIGHT',o.name,o.data.type,o.data.energy,list(o.location),o.data.size)
sc.world=orig.world.copy();sc.render.engine='CYCLES';sc.cycles.samples=16
sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.film_transparent=True
sc.view_settings.view_transform=orig.view_settings.view_transform;sc.view_settings.look=orig.view_settings.look
sc.view_settings.exposure=orig.view_settings.exposure;sc.view_settings.gamma=orig.view_settings.gamma
root=bpy.data.objects['chef_ellis__ground_root.001']
sc.frame_set(1)
for d,a in [('S',0),('E',90),('N',180),('W',-90)]:
 root.rotation_euler.z=radians(a);bpy.context.view_layer.update();sc.render.filepath=base+'/candidates/inspection/idle-'+d+'.png';bpy.ops.render.render(write_still=True)
print('MATERIALS')
for m in {m for o in col.all_objects if o.type=='MESH' for m in o.data.materials}:
 print(m.name,[(n.type,[(i.name,str(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]) for n in m.node_tree.nodes])
print('BONES',[(b.name,list(b.head_local),list(b.tail_local)) for b in bpy.data.objects['chef_ellis__armature.001'].data.bones])
