"""Bounded read-only independent editor inspection; no scene saves or construction."""
import bpy, json, hashlib, pathlib, datetime
from mathutils import Vector

BASE = pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
SOURCE = BASE / 'prototypes/sushi-loop/assets/refinement/backups/b1765262bfa897ad-sushi-loop-world-library.blend'
OUTPUT = BASE / 'prototypes/sushi-loop/assets/refinement/objects/rock-half-width/source/actual-original-measurement-editor-v1.json'
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()
objects = [obj for obj in bpy.data.objects if obj.name.startswith('rock-half-width')]
records = []
all_world = []
materials = set()
for obj in objects:
    entry = {
        'name': obj.name, 'type': obj.type,
        'collections': [c.name for c in obj.users_collection],
        'parent': obj.parent.name if obj.parent else None,
        'matrix_world': [list(row) for row in obj.matrix_world],
        'location': list(obj.location), 'rotation_euler': list(obj.rotation_euler),
        'scale': list(obj.scale), 'hide_render': obj.hide_render,
        'custom_properties': {k: str(v) for k,v in obj.items() if k != '_RNA_UI'},
        'modifiers': [{'name': m.name, 'type': m.type} for m in obj.modifiers]
    }
    if obj.type == 'MESH':
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        points = [obj.matrix_world @ v.co for v in mesh.vertices]
        all_world.extend(points)
        entry['mesh'] = {
            'vertex_count': len(mesh.vertices), 'edge_count': len(mesh.edges),
            'polygon_count': len(mesh.polygons),
            'vertices_local': [list(v.co) for v in mesh.vertices],
            'polygon_vertex_indices': [list(p.vertices) for p in mesh.polygons],
            'smooth_polygon_count': sum(p.use_smooth for p in mesh.polygons),
            'bounds_world': {'min': [min(p[i] for p in points) for i in range(3)],
                             'max': [max(p[i] for p in points) for i in range(3)]},
            'materials': [m.name if m else None for m in obj.data.materials],
            'uv_layers': [u.name for u in mesh.uv_layers],
        }
        materials.update(m for m in obj.data.materials if m)
        evaluated.to_mesh_clear()
    records.append(entry)
material_records = []
for mat in sorted(materials, key=lambda m: m.name):
    material_records.append({
        'name': mat.name, 'diffuse_color': list(mat.diffuse_color), 'use_nodes': mat.use_nodes,
        'nodes': [{'name': n.name, 'type': n.type,
                   'inputs': {inp.name: list(inp.default_value) if hasattr(inp.default_value, '__len__') else inp.default_value
                              for inp in n.inputs if hasattr(inp, 'default_value') and not isinstance(inp.default_value, bpy.types.ID)}}
                  for n in mat.node_tree.nodes] if mat.node_tree else []
    })
camera = scene.camera
report = {
    'purpose': 'independent actual-original collection inspection before judge or canonical resources',
    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'blender_version': bpy.app.version_string,
    'source_path': str(SOURCE), 'source_sha256_before': source_hash,
    'source_sha256_after': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'opened_filepath': bpy.data.filepath,
    'matching_collection_names': [c.name for c in bpy.data.collections if c.name.startswith('rock-half-width')],
    'objects': records, 'materials': material_records,
    'collection_world_bounds': {'min': [min(p[i] for p in all_world) for i in range(3)],
                                'max': [max(p[i] for p in all_world) for i in range(3)]},
    'scene_capture': {'camera': camera.name if camera else None,
        'camera_matrix_world': [list(row) for row in camera.matrix_world] if camera else None,
        'camera_type': camera.data.type if camera else None,
        'ortho_scale': camera.data.ortho_scale if camera else None,
        'resolution': [scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage],
        'pixel_aspect': [scene.render.pixel_aspect_x, scene.render.pixel_aspect_y],
        'engine': scene.render.engine, 'frame': scene.frame_current,
        'film_transparent': scene.render.film_transparent,
        'view_transform': scene.view_settings.view_transform,
        'look': scene.view_settings.look,
        'exposure': scene.view_settings.exposure, 'gamma': scene.view_settings.gamma},
    'lights': [{'name': o.name, 'type': o.data.type, 'energy': o.data.energy,
                'location': list(o.location), 'color': list(o.data.color)}
               for o in scene.objects if o.type == 'LIGHT'],
    'mutations': 'none; no save, model, render or candidate generated'
}
OUTPUT.write_text(json.dumps(report, indent=2))
print(json.dumps({'report': str(OUTPUT), 'objects': len(records), 'bounds': report['collection_world_bounds'], 'source_integrity': source_hash == report['source_sha256_after']}))
