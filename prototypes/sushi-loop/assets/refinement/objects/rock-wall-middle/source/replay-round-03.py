import bpy,json,math
from pathlib import Path
B=Path(__file__).resolve().parents[1];out=B/'candidates/round-03/replay';out.mkdir(exist_ok=True)
sc=bpy.context.scene;root=bpy.data.objects['rock-wall-middle__root'];rows=[]
for d,z in {'S':0,'E':90,'N':180,'W':-90}.items():
 root.rotation_euler.z=math.radians(z);bpy.context.view_layer.update();sc.render.filepath=str(out/f'native-static-{d}.png');bpy.ops.render.render(write_still=True);rows.append({'direction':d,'rootMatrix':[list(v) for v in root.matrix_world]})
(out/'replay.json').write_text(json.dumps({'project':bpy.data.filepath,'actualRootMatrices':rows,'images':len(bpy.data.images),'externalLibraries':len(bpy.data.libraries)},indent=2))
