"""Read-only, bounded measurement of reef-end in the actual frozen original."""
import bpy
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent / 'original-measurements.json'
SOURCE = Path(bpy.data.filepath).resolve()
COLLECTION = 'S33_PROP_reef-end.001'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def vec(value):
    return [round(float(x), 9) for x in value]

def matrix(value):
    return [vec(row) for row in value]

def bounds(points):
    return {'min': [min(p[i] for p in points) for i in range(3)],
            'max': [max(p[i] for p in points) for i in range(3)]} if points else None

def authored_world(obj):
    # The library stores unlinked object matrix_world values as identity. Its
    # actual authored locations/scales are in matrix_basis. No constraints or
    # modifiers are allowed for this bounded authored-mesh inspection.
    assert not obj.constraints, ('unexpected constraints', obj.name)
    if obj.parent:
        return authored_world(obj.parent) @ obj.matrix_parent_inverse @ obj.matrix_basis
    return obj.matrix_basis.copy()

collection = bpy.data.collections[COLLECTION]
objects = sorted(collection.all_objects, key=lambda o: o.name)
root = next(o for o in objects if o.type == 'EMPTY' and '__root' in o.name)
root_inverse = authored_world(root).inverted()
source_sha_before = sha(SOURCE)
records = []
all_root_points = []
materials = {}
for obj in objects:
    record = {
        'name': obj.name, 'type': obj.type,
        'parent': obj.parent.name if obj.parent else None,
        'location': vec(obj.location), 'rotation_euler': vec(obj.rotation_euler),
        'scale': vec(obj.scale), 'matrix_world': matrix(obj.matrix_world),
        'matrix_basis': matrix(obj.matrix_basis),
        'matrix_parent_inverse': matrix(obj.matrix_parent_inverse),
        'authored_world_matrix': matrix(authored_world(obj)),
        'hide_render': obj.hide_render,
        'custom_properties': {key: obj[key] for key in obj.keys() if isinstance(obj[key], (str, int, float, bool))},
    }
    if obj.type == 'MESH':
        assert not obj.modifiers, ('unexpected modifiers', obj.name)
        mesh = obj.data
        points = [vec(root_inverse @ authored_world(obj) @ vertex.co) for vertex in mesh.vertices]
        all_root_points.extend(points)
        record.update({
            'mesh': obj.data.name,
            'vertices': len(obj.data.vertices), 'edges': len(obj.data.edges), 'polygons': len(obj.data.polygons),
            'authored_vertices': len(mesh.vertices), 'authored_edges': len(mesh.edges),
            'authored_polygons': len(mesh.polygons), 'root_local_bounds': bounds(points),
            'modifiers': [{'name': m.name, 'type': m.type, 'show_render': m.show_render} for m in obj.modifiers],
            'materials': [m.name if m else None for m in obj.data.materials],
            'smooth_polygons': sum(p.use_smooth for p in mesh.polygons),
            'authored_root_local_vertices': points,
            'authored_faces': [list(p.vertices) for p in mesh.polygons],
        })
        for material in obj.data.materials:
            if material and material.name not in materials:
                materials[material.name] = {
                    'diffuse_color': vec(material.diffuse_color),
                    'use_nodes': material.use_nodes,
                    'nodes': [{'name': n.name, 'type': n.type} for n in material.node_tree.nodes] if material.node_tree else [],
                    'external_images': [{'name': n.image.name, 'filepath': n.image.filepath, 'packed': bool(n.image.packed_file)}
                        for n in material.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image] if material.node_tree else [],
                }
    records.append(record)

source_sha_after = sha(SOURCE)
result = {
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'mode': 'actual-original read-only inspection; no scene save, render, construction, or candidate',
    'measurement_method': 'Raw original mesh vertices transformed by recursively composed parent world, matrix_parent_inverse and matrix_basis. All collection objects have no constraints and all meshes have no modifiers, asserted by driver. The saved unlinked collection matrix_world values are stale identity and are recorded but not used for bounds.',
    'source_path': str(SOURCE), 'source_sha256_before': source_sha_before,
    'source_sha256_after': source_sha_after, 'source_unchanged': source_sha_before == source_sha_after,
    'blender_version': bpy.app.version_string, 'collection': COLLECTION,
    'collection_instance_offset': vec(collection.instance_offset),
    'root': root.name, 'root_matrix_world': matrix(authored_world(root)),
    'object_count': len(objects), 'mesh_count': sum(o.type == 'MESH' for o in objects),
    'authored_root_local_bounds': bounds(all_root_points),
    'objects': records, 'materials': materials,
    'linked_libraries_used_by_collection': sorted(set(o.library.filepath for o in objects if o.library)),
}
OUT.write_text(json.dumps(result, indent=2) + '\n')
print('ORIGINAL_REEF_END_MEASUREMENTS=' + json.dumps({
    'output': str(OUT), 'source_sha256': source_sha_before, 'source_unchanged': result['source_unchanged'],
    'collection': COLLECTION, 'root': result['root'], 'object_count': result['object_count'],
    'mesh_count': result['mesh_count'], 'authored_root_local_bounds': result['authored_root_local_bounds'],
    'objects': [{k: o[k] for k in ['name', 'type', 'vertices', 'polygons', 'root_local_bounds'] if k in o} for o in records],
}))
