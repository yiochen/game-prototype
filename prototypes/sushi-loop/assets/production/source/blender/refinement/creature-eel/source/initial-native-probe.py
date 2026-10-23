import bpy
import json
import hashlib
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).with_suffix('.json')
SOURCE = Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend')
EXPECTED = 'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
assert Path(bpy.data.filepath) == SOURCE
COLLECTION = 'S33_CFX_creature-eel.003'
ROOT = 'creature-eel__ground_root.003'

def serial(v):
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if isinstance(v, dict):
        return {str(k): serial(x) for k, x in v.items()}
    if isinstance(v, bpy.types.ID):
        return {'id_name': v.name, 'id_type': type(v).__name__}
    try:
        return [serial(x) for x in v]
    except TypeError:
        return str(v)

def props(x):
    return {k: serial(x[k]) for k in x.keys() if k != '_RNA_UI'}

def matrix(m):
    return [list(row) for row in m]

def bounds(o, depsgraph):
    e = o.evaluated_get(depsgraph)
    if e.type != 'MESH':
        return None
    mesh = e.to_mesh()
    try:
        coords = [e.matrix_world @ v.co for v in mesh.vertices]
        return {'world_min': [min(v[i] for v in coords) for i in range(3)],
                'world_max': [max(v[i] for v in coords) for i in range(3)],
                'evaluated_vertices': len(mesh.vertices),
                'evaluated_polygons': len(mesh.polygons)} if coords else None
    finally:
        e.to_mesh_clear()

collection = bpy.data.collections.get(COLLECTION)
assert collection is not None
objects = sorted(collection.all_objects, key=lambda x:x.name)
assert bpy.data.objects.get(ROOT) in objects

# First record saved visibility, then enable actual own collection and its ancestor
# path in the active scene/layer. No project save is ever performed by this probe.
saved_visibility = {o.name: {'hide_render': o.hide_render, 'hide_viewport': o.hide_viewport,
                           'hide_get': o.hide_get()} for o in objects}
path_names = []
def enable_path(layer):
    own = layer.collection == collection
    descendant = False
    for child in layer.children:
        if enable_path(child):
            descendant = True
    if own or descendant:
        layer.exclude = False
        layer.hide_viewport = False
        layer.collection.hide_viewport = False
        path_names.append(layer.name)
        if own:
            def enable_subtree(l):
                l.exclude = False
                l.hide_viewport = False
                l.collection.hide_viewport = False
                l.collection.hide_render = False
                for child in l.children:
                    enable_subtree(child)
            enable_subtree(layer)
    return own or descendant

assert enable_path(bpy.context.view_layer.layer_collection)
for o in objects:
    o.hide_viewport = False
    o.hide_render = False
    o.hide_set(False)
bpy.context.scene.frame_set(bpy.context.scene.frame_current)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
depsgraph.update()

def animation_info(o):
    a = o.animation_data
    if not a:
        return None
    return {'action': a.action.name if a.action else None,
            'action_slot': a.action_slot.identifier if a.action_slot else None,
            'nla_tracks': [{'name': t.name, 'mute': t.mute,
                            'strips': [{'name': s.name, 'action': s.action.name if s.action else None,
                                        'frame_start': s.frame_start, 'frame_end': s.frame_end,
                                        'action_frame_start': s.action_frame_start,
                                        'action_frame_end': s.action_frame_end} for s in t.strips]}
                           for t in a.nla_tracks],
            'drivers': [{'data_path': f.data_path, 'array_index': f.array_index,
                         'expression': f.driver.expression,
                         'variables': [{'name': v.name, 'type': v.type,
                                        'targets': [{'id': t.id.name if t.id else None,
                                                     'data_path': t.data_path,
                                                     'bone_target': t.bone_target} for t in v.targets]}
                                       for v in f.driver.variables]} for f in a.drivers]}

def node_info(n):
    ins = {}
    for i in n.inputs:
        if hasattr(i, 'default_value'):
            ins[i.identifier] = serial(i.default_value)
    return {'name': n.name, 'type': n.bl_idname, 'inputs': ins,
            'image': n.image.name if hasattr(n, 'image') and n.image else None}

materials = {}
data = []
for o in objects:
    e = o.evaluated_get(depsgraph)
    item = {'name': o.name, 'type': o.type, 'data': o.data.name if o.data else None,
            'collections': [c.name for c in o.users_collection],
            'parent': o.parent.name if o.parent else None, 'parent_type': o.parent_type,
            'parent_bone': o.parent_bone, 'custom_properties': props(o),
            'location': list(o.location), 'rotation_mode': o.rotation_mode,
            'rotation_euler': list(o.rotation_euler), 'scale': list(o.scale),
            'matrix_parent_inverse': matrix(o.matrix_parent_inverse),
            'evaluated_matrix_world': matrix(e.matrix_world),
            'evaluated_bounds': bounds(o, depsgraph),
            'constraints': [{'name': c.name, 'type': c.type,
                             'target': c.target.name if hasattr(c, 'target') and c.target else None,
                             'subtarget': c.subtarget if hasattr(c, 'subtarget') else None}
                            for c in o.constraints],
            'modifiers': [{'name': m.name, 'type': m.type,
                           'object': m.object.name if hasattr(m, 'object') and m.object else None,
                           'show_viewport': m.show_viewport, 'show_render': m.show_render}
                          for m in o.modifiers],
            'animation': animation_info(o)}
    if o.type == 'MESH':
        mesh = o.data
        group_weights = {}
        for v in mesh.vertices:
            for g in v.groups:
                name = o.vertex_groups[g.group].name
                entry = group_weights.setdefault(name, {'vertex_count': 0, 'min_weight': 1.0, 'max_weight': 0.0})
                entry['vertex_count'] += 1
                entry['min_weight'] = min(entry['min_weight'], g.weight)
                entry['max_weight'] = max(entry['max_weight'], g.weight)
        item['mesh'] = {'vertices': len(mesh.vertices), 'edges': len(mesh.edges),
                        'polygons': len(mesh.polygons), 'smooth_polygons': sum(p.use_smooth for p in mesh.polygons),
                        'materials': [m.name if m else None for m in mesh.materials],
                        'material_polygon_counts': {str(i): sum(p.material_index == i for p in mesh.polygons)
                                                    for i in range(len(mesh.materials))},
                        'vertex_groups': group_weights,
                        'uv_layers': [u.name for u in mesh.uv_layers],
                        'shape_keys': [k.name for k in mesh.shape_keys.key_blocks] if mesh.shape_keys else []}
        for mat in mesh.materials:
            if mat and mat.name not in materials:
                materials[mat.name] = {'use_nodes': mat.use_nodes, 'diffuse_color': list(mat.diffuse_color),
                                       'custom_properties': props(mat),
                                       'nodes': [node_info(n) for n in mat.node_tree.nodes] if mat.use_nodes else [],
                                       'links': [{'from_node': l.from_node.name, 'from_socket': l.from_socket.identifier,
                                                  'to_node': l.to_node.name, 'to_socket': l.to_socket.identifier}
                                                 for l in mat.node_tree.links] if mat.use_nodes else []}
    if o.type == 'ARMATURE':
        item['armature'] = {'bones': [{'name': b.name, 'parent': b.parent.name if b.parent else None,
                                      'head_local': list(b.head_local), 'tail_local': list(b.tail_local),
                                      'use_deform': b.use_deform, 'custom_properties': props(b)}
                                     for b in o.data.bones],
                            'pose': [{'name': b.name, 'location': list(b.location),
                                      'rotation_mode': b.rotation_mode, 'rotation_euler': list(b.rotation_euler),
                                      'scale': list(b.scale), 'custom_properties': props(b),
                                      'constraints': [{'name': c.name, 'type': c.type} for c in b.constraints]}
                                     for b in o.pose.bones]}
    data.append(item)

# Only own BODY source actions: directly referenced by this actor, or its exact ID prefix.
own_actions = set()
for o in objects:
    if o.animation_data:
        if o.animation_data.action:
            own_actions.add(o.animation_data.action)
        for track in o.animation_data.nla_tracks:
            for strip in track.strips:
                if strip.action:
                    own_actions.add(strip.action)
for action in bpy.data.actions:
    if action.name.startswith('creature-eel__'):
        own_actions.add(action)

def fcurves(action):
    result = []
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for f in bag.fcurves:
                    result.append({'slot_handle': bag.slot_handle, 'data_path': f.data_path,
                                   'array_index': f.array_index,
                                   'keyframes': [{'co': list(k.co), 'interpolation': k.interpolation} for k in f.keyframe_points]})
    return result

actions = [{'name': a.name, 'frame_range': list(a.frame_range),
            'custom_properties': props(a),
            'slots': [{'identifier': s.identifier, 'target_id_type': s.target_id_type} for s in a.slots],
            'fcurves': fcurves(a)} for a in sorted(own_actions, key=lambda a:a.name)]
scene = bpy.context.scene
camera = scene.camera
result = {'scope': 'Independent untouched raw eel BODY source inspection; memory-only visibility enabling; no saves, renders, or candidate edits.',
          'source_path': str(SOURCE), 'source_sha256': EXPECTED,
          'blender_version': bpy.app.version_string,
          'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'scene': scene.name, 'view_layer': bpy.context.view_layer.name,
          'frame_current': scene.frame_current, 'frame_start': scene.frame_start, 'frame_end': scene.frame_end,
          'render': {'resolution_x': scene.render.resolution_x, 'resolution_y': scene.render.resolution_y,
                     'resolution_percentage': scene.render.resolution_percentage,
                     'pixel_aspect_x': scene.render.pixel_aspect_x, 'pixel_aspect_y': scene.render.pixel_aspect_y,
                     'engine': scene.render.engine, 'film_transparent': scene.render.film_transparent},
          'raw_active_camera': {'name': camera.name, 'type': camera.data.type,
                                'ortho_scale': camera.data.ortho_scale,
                                'matrix_world': matrix(camera.matrix_world),
                                'custom_properties': props(camera)} if camera else None,
          'collection': {'name': collection.name, 'custom_properties': props(collection),
                         'enabled_layer_path': path_names},
          'saved_visibility': saved_visibility, 'objects': data, 'materials': materials, 'actions': actions}
OUT.write_text(json.dumps(result, indent=2) + '\n')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
print(json.dumps({'output': str(OUT), 'objects': len(objects), 'actions': len(actions),
                  'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest()}))
