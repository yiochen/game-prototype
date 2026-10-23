"""Clean-background reproduction of exact immutable source exports; no resource edits."""
import bpy,json,hashlib,math
from pathlib import Path
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-01';R=O/'reproduction';R.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source=B/'source/round-01.blend';before=sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;root=bpy.data.objects['workshop-hut__root'];records=[]
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=a;bpy.context.view_layer.update();p=R/f'static-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);reference=O/'atlases'/f'static-{d}.png';records.append({'direction':d,'rootRotationZ':root.rotation_euler.z,'path':str(p.relative_to(B)),'sha256':sha(p),'reference':str(reference.relative_to(B)),'referenceSHA256':sha(reference),'identicalPNGBytes':sha(p)==sha(reference)})
# PNG Date/RenderTime metadata changes; decoded RGBA reproduction is audited separately.
(O/'reproduction.json').write_text(json.dumps({'sourceSHA256':before,'sourceUnchanged':sha(source)==before,'method':'New background Blender process opens exact standalone and renders all four wholeframes under persisted settings. No paired import/resource/recipe rewrite.','captures':records,'filterSize':sc.render.filter_size,'nativeResolution':[sc.render.resolution_x,sc.render.resolution_y]},indent=2));print('REPRODUCTION',all(r['identicalPNGBytes'] for r in records))
