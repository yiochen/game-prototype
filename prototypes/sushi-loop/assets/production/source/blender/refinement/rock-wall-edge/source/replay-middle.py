import bpy,math,json
from pathlib import Path
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-01/middle-replay';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(B/'inputs/approved-middle/project.blend'));sc=bpy.context.scene;root=bpy.data.objects['rock-wall-middle__root']
for d,z in {'S':0,'E':90,'N':180,'W':-90}.items():
 root.rotation_euler.z=math.radians(z);bpy.context.view_layer.update();sc.render.filepath=str(O/f'native-static-{d}.png');bpy.ops.render.render(write_still=True)
