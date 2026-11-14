"""Build, animate, save and export the Boulderhead Parrotfish. From this folder:
    blender -b --factory-startup --python export.py
"""
import os
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.dirname(os.path.dirname(HERE))
bpy.ops.wm.read_homefile(use_empty=True)
exec(open(os.path.join(HERE, "build_model.py")).read())
exec(open(os.path.join(HERE, "build_actions.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "boulderhead-parrotfish.blend"))
bpy.ops.object.select_all(action="DESELECT")
for ob in (bpy.data.objects["boulderhead_parrotfish"], bpy.data.objects["parrot_rig"]): ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(os.path.dirname(HERE), "export", "boulderhead-parrotfish.glb"),
                          export_format="GLB", use_selection=True, export_yup=True, export_animations=True,
                          export_animation_mode="ACTIONS", export_force_sampling=True, export_apply=False)
print("exported")
