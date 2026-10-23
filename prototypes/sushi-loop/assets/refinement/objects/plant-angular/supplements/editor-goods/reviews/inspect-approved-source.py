import bpy
import hashlib
import json
from pathlib import Path

output = Path(__file__).resolve().parent
source = Path(bpy.data.filepath)
scene = bpy.context.scene

def matrix(value):
    return [list(row) for row in value]

objects = []
for obj in scene.objects:
    record = {"name": obj.name, "type": obj.type, "matrix_world": matrix(obj.matrix_world), "hide_render": obj.hide_render}
    if obj.type == 'MESH':
        mesh = obj.data
        record.update(vertices=len(mesh.vertices), polygons=len(mesh.polygons), materials=[slot.material.name if slot.material else None for slot in obj.material_slots], shape_keys=bool(mesh.shape_keys))
    if obj.type == 'LIGHT':
        record.update(light_type=obj.data.type, energy=obj.data.energy, color=list(obj.data.color))
    objects.append(record)

record = {
    "source": str(source), "sourceSHA256": hashlib.sha256(source.read_bytes()).hexdigest(), "scene": scene.name,
    "frame": scene.frame_current, "renderEngine": scene.render.engine,
    "renderSize": [scene.render.resolution_x, scene.render.resolution_y],
    "resolutionPercentage": scene.render.resolution_percentage,
    "pixelAspect": [scene.render.pixel_aspect_x, scene.render.pixel_aspect_y],
    "camera": {"name": scene.camera.name, "matrix_world": matrix(scene.camera.matrix_world), "type": scene.camera.data.type, "orthoScale": scene.camera.data.ortho_scale},
    "world": scene.world.name if scene.world else None,
    "worldNodes": [{"name": n.name, "type": n.type} for n in scene.world.node_tree.nodes] if scene.world and scene.world.use_nodes else [],
    "colorManagement": {"displayDevice": scene.display_settings.display_device, "viewTransform": scene.view_settings.view_transform, "look": scene.view_settings.look, "exposure": scene.view_settings.exposure, "gamma": scene.view_settings.gamma},
    "compositorProperties": [name for name in scene.bl_rna.properties.keys() if 'composit' in name or 'node' in name],
    "externalLibraries": [str(lib.filepath) for lib in bpy.data.libraries],
    "externalImages": [{"name": im.name, "source": im.source, "packed": bool(im.packed_file), "filepath": im.filepath} for im in bpy.data.images if im.source == 'FILE'],
    "objects": objects
}
(output / 'approved-source-inspection.json').write_text(json.dumps(record, indent=2) + '\n')
scene.render.filepath = str(output / 'approved-source-saved-view.png')
bpy.ops.render.render(write_still=True)
print('APPROVED_SOURCE_INSPECTED', record['sourceSHA256'], record['scene'])
