"""Render exact standalone source06 without saving/editing the native project.
Run blender -b -t6 --python source/replay-round-06.py
Fresh replay output candidates/round-06/reproduction-new; set DOCK_ENTRY_REPLAY_OUTPUT to choose another new directory. Refuses overwritten replays.
"""
import bpy,json,hashlib,math,os
from pathlib import Path
B=Path(__file__).resolve().parents[1];O=Path(os.environ.get('DOCK_ENTRY_REPLAY_OUTPUT',str(B/'candidates/round-06/reproduction-new')));O.mkdir(parents=True,exist_ok=True);P=B/'source/round-06.blend';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();before=sha(P);bpy.ops.wm.open_mainfile(filepath=str(P));sc=bpy.context.scene;root=bpy.data.objects['dock-entry__root'];assert sc.render.engine=='BLENDER_EEVEE' and sc.render.filter_size==.5 and sc.eevee.taa_render_samples==64;assert [sc.render.resolution_x,sc.render.resolution_y]==[384,704]
records=[]
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 p=O/f'static-{d}.png';assert not p.exists(),'Never overwrite a replay';root.rotation_euler.z=a;bpy.context.view_layer.update();sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'direction':d,'path':str(p.relative_to(B)),'sha256':sha(p),'rootRotationZ':root.rotation_euler.z,'rootMatrix':[list(r) for r in root.matrix_world],'frame':sc.frame_current,'filter_size':sc.render.filter_size,'taa_render_samples':sc.eevee.taa_render_samples})
(O/'native-replay.json').write_text(json.dumps({'source':'source/round-06.blend','sourceSHA256':before,'sourceUnchanged':before==sha(P),'renders':records},indent=2))
