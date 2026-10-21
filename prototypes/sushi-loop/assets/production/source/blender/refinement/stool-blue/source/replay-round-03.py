"""Render the self-contained round-03.blend at its saved capture contract.
Usage: blender -b source/round-03.blend --python source/replay-round-03.py -- /absolute/output
"""
import bpy,math,sys
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
out=Path(args[0]) if args else Path(bpy.data.filepath).parent.parent/'candidates/replay-round-03'
out.mkdir(parents=True,exist_ok=True)
scene=bpy.data.scenes['stool-blue warm soft native'];bpy.context.window.scene=scene
# Source convention: production/source/blender/native_actions.py:468.
root=bpy.data.objects['stool_blue__root.001']
for direction,angle in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(angle);bpy.context.view_layer.update();scene.frame_set(1)
 scene.render.filepath=str(out/f'static-{direction}.png');bpy.ops.render.render(write_still=True)
