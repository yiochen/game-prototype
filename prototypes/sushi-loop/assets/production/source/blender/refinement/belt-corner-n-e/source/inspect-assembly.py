import bpy,json,pathlib
s=bpy.context.scene;o=bpy.data.objects['True_unbroken_welded_native_reference']
print('OBJ',o.name,o.hide_render,o.hide_viewport,o.visible_camera,len(o.data.vertices),len(o.data.polygons),'bound',list(o.bound_box),'users',[c.name for c in o.users_collection])
print('SCENE',s.name,'viewlayers',[(v.name,v.use) for v in s.view_layers],'camera',s.camera.name,'useNodes',s.use_nodes)
print('ALL',[(x.name,x.hide_render,x.visible_get()) for x in s.objects])
print('MAT',[(m.name,len(m.node_tree.nodes)) for m in o.data.materials])
print('TRANS',o.matrix_world)
print('COMPOSITOR',[(n.name,n.type) for n in s.compositing_node_group.nodes] if s.compositing_node_group else None)
print('BOUNDS',[[min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)] for i in range(3)])
print('RENDER',s.render.engine,'nodes',s.use_nodes)
s.use_nodes=False
s.render.filepath=str(pathlib.Path(__file__).resolve().parents[1]/'candidates/round-01/debug-unbroken.png');o.hide_render=False;o.hide_viewport=False;o.hide_set(False);bpy.context.view_layer.update();bpy.ops.render.render(write_still=True)
