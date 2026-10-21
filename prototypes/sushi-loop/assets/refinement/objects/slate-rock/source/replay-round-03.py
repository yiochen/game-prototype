import bpy,math,sys
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=Path(args[0]).resolve() if args else Path(bpy.data.filepath).resolve().parents[1]/'replay-round-03'
OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene;root=bpy.data.objects['slate-rock__root.001']
for direction,angle in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(angle);bpy.context.view_layer.update();scene.frame_set(1)
 scene.render.filepath=str(OUT/f'static-{direction}.png');bpy.ops.render.render(write_still=True)
