import bpy,pathlib,math,json,hashlib
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parent; O=P/'renders';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'main.blend'))
s=bpy.context.scene;c=bpy.data.collections['S33_FB_belt-straight-w.001']
c.hide_render=False;c.hide_viewport=False
for o in c.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False);o.update_tag()
def unhide(l):
 l.exclude=False;l.hide_viewport=False
 for x in l.children:unhide(x)
unhide(bpy.context.view_layer.layer_collection)
root=next(o for o in c.objects if '__root.' in o.name)
records=[]
for d,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=a
 for i in range(25):
  s.frame_set(i+1);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
  path=O/f'running-{d}-{i:02d}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  records.append({'direction':d,'index':i,'relativePath':str(path.relative_to(P)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(P/'record.json').write_text(json.dumps({'blender':bpy.app.version_string,'projectSHA256':hashlib.sha256((P/'main.blend').read_bytes()).hexdigest(),'relativeSourceOnly':True,'records':records},indent=2))
