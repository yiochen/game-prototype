import bpy,json,sys,importlib.util,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;RES=D/'resources';P=D.parent.parent;TAG=sys.argv[-1]
rig=json.loads((RES/'source-main-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];c=next(c for c in bpy.data.collections if root in list(c.all_objects));s=next(s for s in bpy.data.scenes if root in list(s.objects));bpy.context.window.scene=s;bpy.context.window.view_layer=s.view_layers[0]
spec=importlib.util.spec_from_file_location('samir_native',RES/'native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
O=P/'candidates/round-01/repeatability'/TAG;O.mkdir(parents=True,exist_ok=True)
for clip,direction,frame in [('stand','S',1),('eat','S',5),('eat','N',5)]:
 native.apply_clip({'root':root,'collection':c},rig,clip,frame,direction,s);s.render.filepath=str(O/(clip+'-'+direction+'.png'));bpy.ops.render.render(write_still=True)
(O/'inputs.json').write_text(json.dumps({'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'recipe':'repeat_capture.py','samples':[['stand','S',1],['eat','S',5],['eat','N',5]],'configuration':'Unchanged saved source lighting/material/camera/render settings; independent Blender process.'},indent=2)+'\n')
