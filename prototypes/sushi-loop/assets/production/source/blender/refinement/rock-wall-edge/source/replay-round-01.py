"""Render-only replay. Run against a byte-for-byte relocated saved candidate, no authoring script."""
import bpy,json,math,sys
from pathlib import Path
B=Path(__file__).resolve().parents[1];out=B/'candidates/round-01/replay';out.mkdir(exist_ok=True)
if '--' in sys.argv:out=B/('candidates/round-01/'+sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=True)
sc=bpy.context.scene;root=bpy.data.objects['rock-wall-edge__root'];rows=[]
for d,z in {'S':0,'E':90,'N':180,'W':-90}.items():
 root.rotation_euler.z=math.radians(z);bpy.context.view_layer.update();sc.render.filepath=str(out/f'native-static-{d}.png');bpy.ops.render.render(write_still=True);rows.append({'clip':'static','direction':d,'index':0,'actualRootMatrix':[list(v) for v in root.matrix_world]})
(out/'replay.json').write_text(json.dumps({'project':bpy.data.filepath,'method':'Saved .blend reopened without authoring code; render-only rotation and filepath updates','actualRootMatrices':rows,'images':[i.filepath for i in bpy.data.images if i.source=='FILE'],'externalLibraries':[l.filepath for l in bpy.data.libraries]},indent=2))
