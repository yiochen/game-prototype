"""Convert the isolated library subset into an ordinary editable main project.
No geometry/material/action changes: choose the native scene and source idle S1.
"""
import bpy,json,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent
spec=importlib.util.spec_from_file_location('mateo_finalize_actions',HERE/'native_actions.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
scene=bpy.data.scenes['Mateo warm soft native round01'];bpy.context.window.scene=scene
rig=json.loads((OBJ/'candidates/round01/rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']]
collection=next(c for c in scene.collection.children if root in list(c.all_objects))
n.apply_clip({'root':root,'collection':collection},rig,'idle',1,'S',scene)
for sc in list(bpy.data.scenes):
 if sc!=scene:bpy.data.scenes.remove(sc)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'round01.blend'),compress=True,check_existing=False)
print('MATEO_MAIN_PROJECT_READY',bpy.data.filepath)
