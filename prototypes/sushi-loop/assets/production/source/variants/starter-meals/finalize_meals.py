"""Make the MCP-authored library open directly on its owned editable scene.

Run headlessly against starter-meals.blend. Do not change render source bytes;
that frozen library remains the SHA-bound source for all capture receipts.
"""
from pathlib import Path
import hashlib
import json
import bpy

HERE = Path(__file__).resolve().parent
source = Path(bpy.data.filepath)
scene = next(scene for scene in bpy.data.scenes if scene.get('meal_variants'))
bpy.context.window.scene = scene
bpy.context.window.view_layer = scene.view_layers[0]
for extra in list(bpy.data.scenes):
    if extra != scene and not extra.objects:
        bpy.data.scenes.remove(extra)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
project = HERE / 'starter-meals-project.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(project), compress=True)
(HERE / 'finalized-project.json').write_text(json.dumps({'captureSource': {'file': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}, 'editableProject': {'file': project.name, 'sha256': hashlib.sha256(project.read_bytes()).hexdigest()}, 'activeScene': scene.name, 'geometryOrAnimationEdits': False}, indent=2) + '\n')
