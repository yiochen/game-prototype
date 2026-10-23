"""Replay exact saved standalone blend; never resave the project."""
import bpy,json,math,hashlib
from pathlib import Path
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-03/standalone-replay';O.mkdir(exist_ok=True);sc=bpy.context.scene;root=bpy.data.objects['dock-floor__root'];original=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();records=[]
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=a;bpy.context.view_layer.update();p=O/('static-'+d+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'direction':d,'path':str(p.relative_to(B)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rootRotationZ':root.rotation_euler.z,'rootMatrix':[list(r) for r in root.matrix_world]})
(O/'replay-records.json').write_text(json.dumps({'sourceSHA256':original,'sourceBytesUnchanged':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()==original,'nativeCaptures':records},indent=2))
