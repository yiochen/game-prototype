import bpy
import json
from pathlib import Path
from mathutils import Vector

OUT = Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/salvage-metal/source/initial-native-probe.json')
ROOT_NAMES = ['salvage_a__root.001', 'salvage_b__root.001', 'salvage_c__root.001']

def v(x):
    return [float(i) for i in x]

def mat(x):
    return [v(row) for row in x]

def descendants(obj):
    return [obj] + [c for child in obj.children if child.name not in ROOT_NAMES for c in descendants(child)]

def bounds(obj, dg):
    eo = obj.evaluated_get(dg)
    pts = [eo.matrix_world @ Vector(p) for p in eo.bound_box]
    return {'min': [min(p[i] for p in pts) for i in range(3)], 'max': [max(p[i] for p in pts) for i in range(3)]}

def action_info(obj):
    ad = obj.animation_data
    if not ad:
        return None
    actions = []
    if ad.action:
        actions.append(ad.action)
    for track in ad.nla_tracks:
        for strip in track.strips:
            if strip.action and strip.action not in actions:
                actions.append(strip.action)
    out = []
    for action in actions:
        curves = []
        if hasattr(action, 'fcurves'):
            curves.extend(action.fcurves)
        for layer in getattr(action, 'layers', []):
            for strip in layer.strips:
                for bag in getattr(strip, 'channelbags', []):
                    curves.extend(bag.fcurves)
        out.append({'name': action.name, 'frame_range': v(action.frame_range), 'curves': [{'path': f.data_path, 'index': f.array_index, 'keys': [v(k.co) for k in f.keyframe_points]} for f in curves]})
    return {'active_action': ad.action.name if ad.action else None, 'actions': out}

scene = bpy.context.scene
roots = [bpy.data.objects[n] for n in ROOT_NAMES]
groups = [(root, descendants(root)) for root in roots]
own = set(obj for root, objects in groups for obj in objects)
own_colls = set(coll for obj in own for coll in obj.users_collection)
saved_visibility = {obj.name: {'hide_render': obj.hide_render, 'hide_viewport': obj.hide_viewport, 'hide_set': obj.hide_get()} for obj in own}

def enable_layers(lc):
    child_own = False
    for child in lc.children:
        child_own = enable_layers(child) or child_own
    is_own = lc.collection in own_colls or child_own
    if is_own:
        lc.exclude = False
        lc.hide_viewport = False
        lc.collection.hide_viewport = False
        lc.collection.hide_render = False
    return is_own

for layer in scene.view_layers:
    enable_layers(layer.layer_collection)
for obj in own:
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)
scene.frame_set(1)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
report = {
    'probe_kind': 'untouched original native structural inspection; runtime visibility enable only; no source save',
    'blender_version': bpy.app.version_string,
    'source': bpy.data.filepath,
    'scene': scene.name,
    'frame_range': [scene.frame_start, scene.frame_end],
    'fps': scene.render.fps,
    'active_frame_for_initial_measurement': scene.frame_current,
    'view_layer': bpy.context.view_layer.name,
    'camera': None,
    'render': {'resolution_x': scene.render.resolution_x, 'resolution_y': scene.render.resolution_y, 'resolution_percentage': scene.render.resolution_percentage, 'pixel_aspect_x': scene.render.pixel_aspect_x, 'pixel_aspect_y': scene.render.pixel_aspect_y, 'engine': scene.render.engine, 'film_transparent': scene.render.film_transparent},
    'variants': [],
    'saved_own_visibility_before_enabling': saved_visibility,
    'diagnostic_renders': [],
}
if scene.camera:
    camera = scene.camera
    report['camera'] = {'name': camera.name, 'type': camera.data.type, 'ortho_scale': camera.data.ortho_scale, 'lens': camera.data.lens, 'matrix_world': mat(camera.matrix_world)}
for root, objects in groups:
    variant = {'root': root.name, 'root_collections': [c.name for c in root.users_collection], 'root_matrix_world': mat(root.evaluated_get(dg).matrix_world), 'objects': []}
    mesh_bounds = []
    for obj in objects:
        info = {'name': obj.name, 'type': obj.type, 'parent': obj.parent.name if obj.parent else None, 'collections': [c.name for c in obj.users_collection], 'location': v(obj.location), 'rotation_euler': v(obj.rotation_euler), 'scale': v(obj.scale), 'matrix_world_evaluated': mat(obj.evaluated_get(dg).matrix_world), 'animation': action_info(obj), 'modifiers': [{'name': m.name, 'type': m.type, 'width': getattr(m, 'width', None), 'segments': getattr(m, 'segments', None)} for m in obj.modifiers]}
        if obj.type == 'MESH':
            mesh = obj.data
            bb = bounds(obj, dg)
            mesh_bounds.append(bb)
            info.update({'vertices': len(mesh.vertices), 'polygons': len(mesh.polygons), 'smooth_polygons': sum(p.use_smooth for p in mesh.polygons), 'evaluated_world_bounds': bb, 'materials': []})
            for material in mesh.materials:
                if not material:
                    continue
                mi = {'name': material.name, 'diffuse_color': v(material.diffuse_color), 'use_nodes': material.use_nodes}
                if material.use_nodes:
                    mi['nodes'] = [{'name': n.name, 'type': n.type, 'inputs': {s.name: (v(s.default_value) if hasattr(s.default_value, '__len__') and not isinstance(s.default_value, str) else s.default_value) for s in n.inputs if hasattr(s, 'default_value') and s.name in ['Base Color', 'Metallic', 'Roughness', 'Alpha']}} for n in material.node_tree.nodes]
                    mi['links'] = [{'from_node': l.from_node.name, 'from_socket': l.from_socket.name, 'to_node': l.to_node.name, 'to_socket': l.to_socket.name} for l in material.node_tree.links]
                info['materials'].append(mi)
        variant['objects'].append(info)
    variant['evaluated_mesh_bounds'] = {'min': [min(b['min'][i] for b in mesh_bounds) for i in range(3)], 'max': [max(b['max'][i] for b in mesh_bounds) for i in range(3)]}
    report['variants'].append(variant)
for root, objects in groups:
    mesh_set = {obj for obj in objects if obj.type == 'MESH'}
    for obj in scene.objects:
        if obj.type == 'MESH':
            obj.hide_render = obj not in mesh_set
    scene.frame_set(1)
    bpy.context.view_layer.update()
    render_path = OUT.parent / ('initial-raw-' + root.name.split('__')[0] + '.png')
    scene.render.filepath = str(render_path)
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    bpy.ops.render.render(write_still=True)
    report['diagnostic_renders'].append({'root': root.name, 'path': str(render_path), 'frame': 1, 'geometry_material_camera_lighting_unchanged': True, 'runtime_changes': ['enable own collection ancestors and own objects', 'hide other scene meshes for single variant inspection', 'PNG RGBA output path']})
OUT.write_text(json.dumps(report, indent=2) + '\n')
print('INITIAL_NATIVE_PROBE_WRITTEN', str(OUT))
