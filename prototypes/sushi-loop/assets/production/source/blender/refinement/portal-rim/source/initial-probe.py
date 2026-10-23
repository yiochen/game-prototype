import bpy
import hashlib
import json
from pathlib import Path
from mathutils import Vector

BASE = Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
RAW = BASE / 'prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'
OUT = BASE / 'prototypes/sushi-loop/assets/refinement/objects/portal-rim/source/raw-initial-probe.json'
SCENE = 'S33 Native Asset Library Export'
COLLECTION = 'S33_PROP_portal_rim.002'
ROOT = 'portal_rim__root.002'

def arr(value):
    return [round(float(v), 9) for v in value]

def mat(value):
    return [arr(row) for row in value]

def props(block):
    result = {}
    for key in block.keys():
        try:
            value = block[key]
            if hasattr(value, 'to_list'):
                value = value.to_list()
            elif hasattr(value, 'to_dict'):
                value = value.to_dict()
            json.dumps(value)
            result[key] = value
        except Exception:
            result[key] = str(block[key])
    return result

def animation(block):
    data = getattr(block, 'animation_data', None)
    if not data:
        return None
    action = data.action
    return {
        'action': action.name if action else None,
        'action_frame_range': arr(action.frame_range) if action else None,
        'drivers': [{'data_path': f.data_path, 'array_index': f.array_index} for f in data.drivers],
        'nla_tracks': [{'name': t.name, 'mute': t.mute, 'strips': [{'name': s.name, 'action': s.action.name if s.action else None, 'frame_start': s.frame_start, 'frame_end': s.frame_end} for s in t.strips]} for t in data.nla_tracks],
    }

def material(block):
    result = {'name': block.name, 'diffuse_color': arr(block.diffuse_color), 'use_nodes': block.use_nodes, 'custom_properties': props(block)}
    if block.use_nodes and block.node_tree:
        result['nodes'] = []
        for n in block.node_tree.nodes:
            item = {'name': n.name, 'type': n.bl_idname}
            values = {}
            for socket in n.inputs:
                if hasattr(socket, 'default_value'):
                    value = socket.default_value
                    if isinstance(value, (float, int, bool, str)):
                        values[socket.name] = value
                    else:
                        try:
                            values[socket.name] = arr(value)
                        except Exception:
                            values[socket.name] = str(value)
            item['inputs'] = values
            if getattr(n, 'image', None):
                item['image'] = {'name': n.image.name, 'filepath': n.image.filepath, 'packed': bool(n.image.packed_file)}
            result['nodes'].append(item)
        result['links'] = [{'from_node': l.from_node.name, 'from_socket': l.from_socket.name, 'to_node': l.to_node.name, 'to_socket': l.to_socket.name} for l in block.node_tree.links]
    return result

def bounds(points):
    if not points:
        return None
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    return {'min': arr(lo), 'max': arr(hi), 'size': arr(Vector(hi) - Vector(lo))}

source_before = hashlib.sha256(RAW.read_bytes()).hexdigest()
scene = bpy.data.scenes[SCENE]
collection = bpy.data.collections[COLLECTION]
root = bpy.data.objects[ROOT]
bpy.context.window.scene = scene

paths = []
def walk_col(col, path):
    current = path + [col]
    if col == collection:
        paths.append(current)
    for child in col.children:
        walk_col(child, current)
walk_col(scene.collection, [])
if not paths:
    raise RuntimeError('Own collection is not in requested scene')

own = list(collection.all_objects)
visibility_before = {
    'collections': [{'name': c.name, 'hide_viewport': c.hide_viewport, 'hide_render': c.hide_render} for c in dict.fromkeys(c for p in paths for c in p)],
    'objects': [{'name': o.name, 'hide_viewport': o.hide_viewport, 'hide_render': o.hide_render, 'hide_set': o.hide_get()} for o in own],
}
for p in paths:
    for c in p:
        c.hide_viewport = False
        c.hide_render = False

layer_changes = []
target_names = {c.name for p in paths for c in p}
def enable_layer(lc, vl):
    if lc.collection.name in target_names or lc.collection == collection or lc.collection.name in {c.name for c in collection.children_recursive}:
        layer_changes.append({'view_layer': vl.name, 'layer_collection': lc.name, 'exclude_before': lc.exclude, 'hide_viewport_before': lc.hide_viewport})
        lc.exclude = False
        lc.hide_viewport = False
    for child in lc.children:
        enable_layer(child, vl)
for vl in scene.view_layers:
    vl.use = True
    enable_layer(vl.layer_collection, vl)
for c in [collection] + list(collection.children_recursive):
    c.hide_viewport = False
    c.hide_render = False
for o in own:
    o.hide_render = False
    o.hide_viewport = False
    o.hide_set(False)
for o in own:
    parent = o.parent
    while parent:
        parent.hide_render = False
        parent.hide_viewport = False
        parent.hide_set(False)
        parent = parent.parent
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
depsgraph.update()
root_inverse = root.evaluated_get(depsgraph).matrix_world.inverted()

objects = []
all_world = []
all_root = []
used_materials = {}
for o in sorted(own, key=lambda x: x.name):
    eo = o.evaluated_get(depsgraph)
    entry = {
        'name': o.name, 'type': o.type, 'data': o.data.name if o.data else None,
        'parent': o.parent.name if o.parent else None, 'parent_type': o.parent_type,
        'collections': [c.name for c in o.users_collection],
        'library': o.library.filepath if o.library else None,
        'location': arr(o.location), 'rotation_mode': o.rotation_mode,
        'rotation_euler': arr(o.rotation_euler), 'rotation_quaternion': arr(o.rotation_quaternion),
        'scale': arr(o.scale), 'matrix_world_evaluated': mat(eo.matrix_world),
        'custom_properties': props(o), 'animation': animation(o),
        'constraints': [{'name': c.name, 'type': c.type, 'mute': c.mute} for c in o.constraints],
        'modifiers': [{'name': m.name, 'type': m.type, 'show_render': m.show_render, 'show_viewport': m.show_viewport} for m in o.modifiers],
        'visible_after': {'hide_render': o.hide_render, 'hide_viewport': o.hide_viewport, 'hide_set': o.hide_get(), 'visible_get': o.visible_get()},
    }
    if o.type == 'MESH':
        mesh = o.data
        coords = [v.co.copy() for v in mesh.vertices]
        evaluated = eo.to_mesh()
        world = [eo.matrix_world @ v.co for v in evaluated.vertices]
        localroot = [root_inverse @ p for p in world]
        all_world.extend(world)
        all_root.extend(localroot)
        edge_uses = {}
        for polygon in mesh.polygons:
            for key in polygon.edge_keys:
                key = tuple(sorted(key))
                edge_uses[key] = edge_uses.get(key, 0) + 1
        entry['mesh'] = {
            'vertices': len(mesh.vertices), 'edges': len(mesh.edges), 'polygons': len(mesh.polygons),
            'polygon_sizes': {str(size): sum(len(p.vertices) == size for p in mesh.polygons) for size in sorted({len(p.vertices) for p in mesh.polygons})},
            'smooth_polygons': sum(p.use_smooth for p in mesh.polygons),
            'boundary_edges': sum(count == 1 for count in edge_uses.values()),
            'overused_edges': sum(count > 2 for count in edge_uses.values()),
            'loose_edges': sum(tuple(sorted(e.vertices)) not in edge_uses for e in mesh.edges),
            'material_indices': {str(index): sum(p.material_index == index for p in mesh.polygons) for index in sorted({p.material_index for p in mesh.polygons})},
            'local_vertex_bounds': bounds(coords), 'evaluated_vertices': len(evaluated.vertices),
            'evaluated_world_bounds': bounds(world), 'evaluated_root_bounds': bounds(localroot),
            'uv_layers': [layer.name for layer in mesh.uv_layers],
            'custom_properties': props(mesh), 'animation': animation(mesh),
        }
        eo.to_mesh_clear()
    entry['materials'] = [slot.material.name if slot.material else None for slot in o.material_slots]
    for slot in o.material_slots:
        if slot.material:
            used_materials[slot.material.name] = material(slot.material)
    objects.append(entry)

camera = scene.camera
camera_data = None
if camera:
    camera_data = {
        'name': camera.name, 'type': camera.data.type, 'ortho_scale': camera.data.ortho_scale,
        'lens': camera.data.lens, 'shift_x': camera.data.shift_x, 'shift_y': camera.data.shift_y,
        'clip_start': camera.data.clip_start, 'clip_end': camera.data.clip_end,
        'matrix_world': mat(camera.evaluated_get(depsgraph).matrix_world),
    }
payload = {
    'source': str(RAW), 'source_sha256_before': source_before,
    'blender_version': bpy.app.version_string,
    'scene': scene.name, 'view_layer': bpy.context.view_layer.name, 'frame': scene.frame_current,
    'collection_paths': [[c.name for c in p] for p in paths], 'own_collection': collection.name,
    'direct_objects': [o.name for o in collection.objects], 'own_object_count': len(own),
    'root': root.name, 'root_matrix_world_evaluated': mat(root.evaluated_get(depsgraph).matrix_world),
    'collection_properties': props(collection),
    'visibility_before': visibility_before, 'layer_visibility_changes': layer_changes,
    'camera_observed_only_not_future_contract': camera_data,
    'render_observed_only_not_future_contract': {'engine': scene.render.engine, 'resolution_x': scene.render.resolution_x, 'resolution_y': scene.render.resolution_y, 'resolution_percentage': scene.render.resolution_percentage, 'pixel_aspect_x': scene.render.pixel_aspect_x, 'pixel_aspect_y': scene.render.pixel_aspect_y, 'film_transparent': scene.render.film_transparent},
    'world': {'name': scene.world.name if scene.world else None, 'use_nodes': scene.world.use_nodes if scene.world else None},
    'objects': objects, 'materials': list(used_materials.values()),
    'evaluated_world_bounds': bounds(all_world), 'evaluated_root_bounds': bounds(all_root),
    'source_sha256_after': hashlib.sha256(RAW.read_bytes()).hexdigest(),
    'scope': 'Read-only bounded raw own-collection inspection. Visibility enabled in process only; no render, construction, model save, helper, canonical resource, or external effect work.',
}
OUT.write_text(json.dumps(payload, indent=2) + '\n')
print(json.dumps({'output': str(OUT), 'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(), 'object_count': len(own), 'materials': sorted(used_materials), 'source_preserved': payload['source_sha256_before'] == payload['source_sha256_after']}))
