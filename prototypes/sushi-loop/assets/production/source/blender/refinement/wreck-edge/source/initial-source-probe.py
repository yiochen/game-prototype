"""Read-only bounded actual-original inspection. Does not save a Blender project."""
import bpy
import json
import hashlib
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[7]
EXP = Path(__file__).resolve().parents[1]
SOURCE = EXP / 'reviews/preparation-v1/resources/native/source-library.blend'
COLLECTION = 'S33_PROP_wreck-edge.001'

with bpy.data.libraries.load(str(SOURCE), link=False) as (src, dst):
    dst.collections = [COLLECTION]
col = bpy.data.collections.get(COLLECTION)
if col is None:
    raise RuntimeError('Missing original collection')
bpy.context.scene.collection.children.link(col)
original_visibility = {'collection_hide_viewport': col.hide_viewport, 'collection_hide_render': col.hide_render,
                       'objects': {o.name: {'hide_viewport':o.hide_viewport, 'hide_render':o.hide_render} for o in col.all_objects}}
col.hide_viewport = False
col.hide_render = False
for obj in col.all_objects:
    obj.hide_viewport = False
    obj.hide_set(False)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
objects = []
all_points = []
for obj in sorted(col.all_objects, key=lambda o: o.name):
    item = {'name': obj.name, 'type': obj.type, 'location': list(obj.location),
            'rotation_euler': list(obj.rotation_euler), 'scale': list(obj.scale),
            'parent': obj.parent.name if obj.parent else None,
            'custom_properties': {k: str(v) for k, v in obj.items()},
            'matrix_world': [list(row) for row in obj.matrix_world]}
    if obj.type == 'MESH':
        ev = obj.evaluated_get(deps)
        mesh = ev.to_mesh()
        pts = [ev.matrix_world @ v.co for v in mesh.vertices]
        all_points.extend(pts)
        item.update({'vertices': len(mesh.vertices), 'polygons': len(mesh.polygons),
                     'bounds_world': [[min(p[i] for p in pts) for i in range(3)],
                                      [max(p[i] for p in pts) for i in range(3)]],
                     'materials': [m.name if m else None for m in obj.data.materials],
                     'modifiers': [{'name': m.name, 'type': m.type} for m in obj.modifiers]})
        ev.to_mesh_clear()
    objects.append(item)
materials = []
for mat in sorted({m for o in col.all_objects if o.type == 'MESH' for m in o.data.materials if m}, key=lambda m:m.name):
    item = {'name': mat.name, 'diffuse_color': list(mat.diffuse_color), 'use_nodes': mat.use_nodes}
    if mat.node_tree:
        item['node_types'] = sorted(n.bl_idname for n in mat.node_tree.nodes)
        item['image_paths'] = [n.image.filepath for n in mat.node_tree.nodes if n.bl_idname == 'ShaderNodeTexImage' and n.image]
    materials.append(item)
result = {'purpose': 'Independent actual-original native collection inspection only; no candidate construction',
          'blender_version': bpy.app.version_string, 'source': str(SOURCE),
          'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'collection': COLLECTION, 'original_visibility':original_visibility,
          'temporary_inspection_visibility': 'collection and objects visible for dependency evaluation only; not saved',
          'objects': objects, 'materials': materials,
          'evaluated_bounds_world': [[min(p[i] for p in all_points) for i in range(3)],
                                     [max(p[i] for p in all_points) for i in range(3)]],
          'actions': [a.name for a in bpy.data.actions], 'source_written': False,
          'native_project_written': False}
(EXP / 'source/initial-source-probe.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
