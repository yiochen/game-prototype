import bpy,json
from pathlib import Path
B=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(B/'source/round-01.blend'))
s=bpy.context.scene
print('SCENE',s.name,'res',s.render.resolution_x,s.render.resolution_y,'cam',s.camera.name,'scale',s.camera.data.ortho_scale,'shift',s.camera.data.shift_x,s.camera.data.shift_y)
for o in s.objects:print(o.name,o.type,list(o.matrix_world.translation),[c.name for c in o.users_collection])
for m in bpy.data.materials:
 if 'blue' in m.name:
  print(m.name,[(n.name,n.type,getattr(n,'operation',''))for n in m.node_tree.nodes]);print([(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name)for l in m.node_tree.links])
s.render.filepath=str(B/'candidates/round-01/debug-standalone.png');bpy.ops.render.render(write_still=True)
