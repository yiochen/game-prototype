"""Isolated native height-projection study. Root controls all Blender execution.

MCP: import this file as a module, then create_study(r, output_dir=NEW_FOLDER).
CLI: Blender --background NEW_FOLDER/projection-study.blend --python THIS_FILE --
     --capture --manifest NEW_FOLDER/study.json

Production assets are read-only. Native meshes/materials are copied; Lena's
existing hold action cohort is copied onto her cloned rig, evaluated at frame6,
then frozen. No production pose callbacks, camera runtime or source records are
modified. Capture uses actual Blender cameras, not transformed finished images.
"""

import argparse
import contextlib
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import time
import uuid

import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view


RATIOS = [('100', 1.), ('70', .7), ('50', .5), ('40', .4)]
SOLO_IDS = ['stool-wood', 'crate-wood', 'belt-straight-e',
            'rock-wall-middle', 'boulder-underwater', 'chef-lena']
CELL = 128
SOURCE_SCALE = 4
LABELS = {
    'stool-wood': 'Backless wood stool', 'crate-wood': 'Wooden crate',
    'belt-straight-e': 'East-flowing conveyor',
    'rock-wall-middle': 'Rock wall middle',
    'boulder-underwater': 'Underwater boulder',
    'chef-lena': 'Lena, fixed held-dish pose',
    'context-l-belt': 'Connected conveyor and nearby props',
}


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.writing')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def matrix_values(matrix):
    return [[round(float(value), 9) for value in row] for row in matrix]


@contextlib.contextmanager
def activate(scene):
    window = bpy.context.window
    previous = (window.scene, window.view_layer) if window else None
    try:
        if window:
            window.scene = scene
            window.view_layer = scene.view_layers[0]
        with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0]):
            scene.view_layers[0].update()
            yield
    finally:
        if window and previous:
            window.scene, window.view_layer = previous


def raw_mesh_hash(mesh):
    return canonical_hash({
        'vertices': [[round(float(v), 9) for v in vertex.co]
                     for vertex in mesh.vertices],
        'faces': [list(poly.vertices) for poly in mesh.polygons],
    })


def plain(value):
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return round(value, 9)
    try:
        return [plain(item) for item in value]
    except TypeError:
        return {'rnaType': getattr(getattr(value, 'bl_rna', None), 'identifier', type(value).__name__)}


def materials_snapshot(objects):
    """Shader colors, numeric settings, ramps and links; no camera dependence."""
    materials = {material.name: material for obj in objects
                 if hasattr(obj.data, 'materials') for material in obj.data.materials
                 if material is not None}
    result = []
    for name, material in sorted(materials.items()):
        item = {'name': name, 'diffuseColor': plain(material.diffuse_color),
                'roughness': plain(material.roughness), 'metallic': plain(material.metallic),
                'useNodes': material.use_nodes, 'nodes': [], 'links': []}
        if material.use_nodes and material.node_tree:
            for node in sorted(material.node_tree.nodes, key=lambda value: value.name):
                entry = {'name': node.name, 'type': node.bl_idname, 'label': node.label,
                         'inputs': [plain(socket.default_value) if hasattr(socket, 'default_value')
                                    else None for socket in node.inputs],
                         'outputs': [plain(socket.default_value) if hasattr(socket, 'default_value')
                                     else None for socket in node.outputs]}
                for attribute in ('operation', 'blend_type', 'distribution', 'interpolation', 'extension'):
                    if hasattr(node, attribute):
                        entry[attribute] = plain(getattr(node, attribute))
                if hasattr(node, 'color_ramp'):
                    entry['colorRamp'] = {'interpolation': node.color_ramp.interpolation,
                                         'elements': [[plain(element.position), plain(element.color)]
                                                      for element in node.color_ramp.elements]}
                item['nodes'].append(entry)
            item['links'] = sorted([link.from_node.name, link.from_socket.identifier,
                                    link.to_node.name, link.to_socket.identifier]
                                   for link in material.node_tree.links)
        result.append(item)
    return result


def source_snapshot(assets):
    objects = {}
    for asset in assets.values():
        for obj in asset['collection'].all_objects:
            item = {'basis': matrix_values(obj.matrix_basis),
                    'parent': obj.parent.name if obj.parent else None,
                    'hidden': [bool(obj.hide_render), bool(obj.hide_viewport)],
                    'action': obj.animation_data.action.name
                    if obj.animation_data and obj.animation_data.action else None}
            if obj.type == 'MESH':
                item['mesh'] = raw_mesh_hash(obj.data)
            if obj.type == 'ARMATURE':
                item['bones'] = {bone.name: matrix_values(bone.matrix_basis)
                                 for bone in obj.pose.bones}
            objects[obj.name] = item
    source_objects = {obj.name: obj for asset in assets.values()
                      for obj in asset['collection'].all_objects}
    return canonical_hash({'objects': objects,
                           'materials': materials_snapshot(source_objects.values())})


def material_copy(material, prefix, cache):
    if material is None:
        return None
    key = material.as_pointer()
    if key in cache:
        return cache[key]
    clone = material.copy()
    clone.name = prefix + '__' + material.name
    clone.animation_data_clear()
    if clone.use_nodes and clone.node_tree:
        if clone.node_tree == material.node_tree:
            raise RuntimeError('Material node tree was not copied independently')
        clone.node_tree.animation_data_clear()
        for node in clone.node_tree.nodes:
            if node.type == 'VALUE' and node.label == 'Deck travel phase':
                node.outputs[0].default_value = 0.
    cache[key] = clone
    return clone


def clone_asset(asset, target, prefix, material_cache):
    mapping, bindings = {}, []
    originals = [asset['root']] + list(asset['root'].children_recursive)
    for original in originals:
        clone = original.copy()
        clone.name = prefix + '__' + original.name
        clone.animation_data_clear()
        if original.data is not None:
            clone.data = original.data.copy()
            if hasattr(clone.data, 'animation_data_clear'):
                clone.data.animation_data_clear()
            if original.type == 'MESH':
                if original.data.shape_keys and clone.data.shape_keys == original.data.shape_keys:
                    raise RuntimeError('Shape keys were not copied independently')
                if clone.data.shape_keys:
                    clone.data.shape_keys.animation_data_clear()
                clone.data.materials.clear()
                for material in original.data.materials:
                    clone.data.materials.append(material_copy(material, prefix, material_cache))
                bindings.append({'sourceObject': original.name,
                                 'cloneObject': clone.name,
                                 'sourceMeshHash': raw_mesh_hash(original.data),
                                 'cloneMeshHash': raw_mesh_hash(clone.data)})
        target.objects.link(clone)
        clone.hide_viewport = False
        clone['projection_study_source_object'] = original.name
        mapping[original.name] = clone
    for original in originals:
        clone = mapping[original.name]
        clone.parent = mapping.get(original.parent.name) if original.parent else None
        clone.matrix_parent_inverse = original.matrix_parent_inverse.copy()
        clone.matrix_basis = original.matrix_basis.copy()
        for modifier in clone.modifiers:
            source = getattr(modifier, 'object', None)
            if source is not None:
                if source.name not in mapping:
                    raise RuntimeError('Foreign modifier dependency ' + source.name)
                modifier.object = mapping[source.name]
        constraints = list(clone.constraints)
        if clone.type == 'ARMATURE':
            constraints += [constraint for bone in clone.pose.bones
                            for constraint in bone.constraints]
        for constraint in constraints:
            source = getattr(constraint, 'target', None)
            if source is not None:
                if source.name not in mapping:
                    raise RuntimeError('Foreign constraint dependency ' + source.name)
                constraint.target = mapping[source.name]
    root = mapping[asset['root'].name]
    root.parent = None
    root.matrix_parent_inverse = Matrix.Identity(4)
    root.matrix_basis = Matrix.Identity(4)
    return root, mapping, bindings


def native_record(runtime, asset_id):
    records = getattr(runtime, 'native_records', {})
    if isinstance(records, dict) and 'assets' in records:
        records = records['assets']
    if asset_id in records:
        return records[asset_id]
    path = Path(runtime.OUT) / 'source' / asset_id / 'rig.json'
    if not path.exists():
        raise FileNotFoundError('Need current native pose record: ' + str(path))
    return json.loads(path.read_text())


def freeze_character(runtime, scene, mapping, frame=6):
    record = native_record(runtime, 'chef-lena')
    cohort = record['clips']['hold']['actions']
    copies = []
    for target in cohort:
        if target['ownerType'] != 'Object':
            raise RuntimeError('Unexpected non-object chef action owner: ' + str(target))
        owner = mapping.get(target['ownerName'])
        action = bpy.data.actions.get(target['action'])
        if owner is None or action is None:
            raise KeyError('Missing cloned native action owner/source ' + str(target))
        clone_action = action.copy()
        clone_action.name = 'S33 Projection Pose__' + action.name
        clone_action.use_fake_user = False
        copies.append(clone_action)
        owner.animation_data_create()
        owner.animation_data.action = clone_action
        if hasattr(owner.animation_data, 'action_slot'):
            slots = list(clone_action.slots)
            slot = next((slot for slot in slots
                         if slot.identifier == target.get('slotIdentifier')), None)
            if slot is None and len(slots) == 1:
                slot = slots[0]
            if slot is not None:
                owner.animation_data.action_slot = slot
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    states = {}
    for obj in mapping.values():
        states[obj.name] = {
            'basis': obj.matrix_basis.copy(), 'hideRender': bool(obj.hide_render),
            'hideViewport': bool(obj.hide_viewport),
            'bones': {bone.name: bone.matrix_basis.copy() for bone in obj.pose.bones}
            if obj.type == 'ARMATURE' else {},
        }
    for obj in mapping.values():
        state = states[obj.name]
        obj.animation_data_clear()
        obj.matrix_basis = state['basis']
        obj.hide_render = state['hideRender']
        obj.hide_viewport = False
        for name, matrix in state['bones'].items():
            obj.pose.bones[name].matrix_basis = matrix
    for action in copies:
        bpy.data.actions.remove(action)
    bpy.context.view_layer.update()
    return {'asset': 'chef-lena', 'clip': 'hold', 'nativeFrame': frame,
            'direction': 'S', 'method': 'Cloned native action cohort, frozen rig pose and held-food transforms.',
            'sourceActions': [target['action'] for target in cohort]}


def geometry_snapshot(collection):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    meshes, transforms = [], []
    for obj in sorted(collection.all_objects, key=lambda item: item.name):
        transforms.append({'object': obj.name, 'worldMatrix': matrix_values(obj.matrix_world),
                           'visible': not obj.hide_render})
        if obj.type != 'MESH' or obj.hide_render:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            meshes.append({'object': obj.name,
                           'worldVertices': [[round(float(v), 7) for v in
                                              (evaluated.matrix_world @ vertex.co)]
                                             for vertex in mesh.vertices],
                           'faces': [list(poly.vertices) for poly in mesh.polygons]})
        finally:
            evaluated.to_mesh_clear()
    return canonical_hash(meshes), canonical_hash(transforms), transforms


def render_settings(scene, samples=32):
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'
    scene.render.image_settings.compression = 30
    scene.render.resolution_percentage = 100
    scene.render.use_file_extension = True
    scene.render.use_persistent_data = True
    scene.render.fps = 12
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    eevee = getattr(scene, 'eevee', None)
    for key in ('taa_render_samples', 'taa_samples'):
        if eevee is not None and hasattr(eevee, key):
            setattr(eevee, key, samples)
            break


def configure_camera(scene, group, ratio=1., ordinary=False):
    frame, root, scale = group['frameSize'], group['root'], SOURCE_SCALE
    camera = scene.camera
    scene.render.resolution_x, scene.render.resolution_y = frame[0] * scale, frame[1] * scale
    scene.render.pixel_aspect_x = 1. if ordinary else math.sqrt(1. + ratio * ratio)
    scene.render.pixel_aspect_y = 1.
    angle = math.radians(35.) if ordinary else math.atan(1. / ratio)
    camera.data.type = 'ORTHO'
    camera.data.sensor_fit = 'HORIZONTAL'
    camera.data.ortho_scale = frame[0] / CELL
    camera.location = (0., -10 * math.cos(angle), 10 * math.sin(angle))
    camera.rotation_euler = (-camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.shift_x, camera.data.shift_y = 0., 0.
    bpy.context.view_layer.update()
    def px(point):
        value = world_to_camera_view(scene, camera, Vector(point))
        return Vector((value.x * scene.render.resolution_x,
                       (1. - value.y) * scene.render.resolution_y))
    origin = px((0, 0, 0))
    camera.data.shift_x = 1.
    bpy.context.view_layer.update()
    dx = px((0, 0, 0)).x - origin.x
    camera.data.shift_x = (root[0] * scale - origin.x) / dx
    camera.data.shift_y = 1.
    bpy.context.view_layer.update()
    dy = px((0, 0, 0)).y - origin.y
    camera.data.shift_y = (root[1] * scale - origin.y) / dy
    bpy.context.view_layer.update()
    projected = px((0, 0, 0))
    vectors = [px(point) - projected for point in ((1, 0, 0), (0, -1, 0), (0, 0, 1))]
    pitch = CELL * scale
    expected_depth = pitch * math.sin(angle) if ordinary else pitch
    expected_height = pitch * math.cos(angle) if ordinary else pitch * ratio
    assert (projected - Vector((root[0] * scale, root[1] * scale))).length < .05
    assert abs(vectors[0].x - pitch) < .05
    assert abs(vectors[1].y - expected_depth) < .05
    assert abs(vectors[2].y + expected_height) < .05
    calibration = dict(zip(('unitX', 'unitDepth', 'unitHeight'), [list(value) for value in vectors]))
    calibration['root'] = list(projected)
    matrix = camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),
        x=scene.render.resolution_x, y=scene.render.resolution_y,
        scale_x=scene.render.pixel_aspect_x, scale_y=scene.render.pixel_aspect_y)
    return {
        'groupId': group['id'], 'projection': 'ordinary-orthographic-character-reference'
        if ordinary else 'square-ground-height-ratio-study',
        'heightRatio': None if ordinary else ratio,
        'frameSize': frame, 'frame': frame, 'root': root, 'anchor': root,
        'sourceScale': scale, 'captureScale': scale, 'cellSize': CELL,
        'axes': {'x': 'X', 'depth': '-Y', 'height': 'Z'},
        'geometryHash': group['source']['geometryHash'],
        'placementsHash': group['source']['placementsHash'],
        'materialsHash': group['source'].get('materialsHash'),
        'camera': {'type': 'orthographic', 'elevationDegrees': math.degrees(angle),
                   'worldMatrix': matrix_values(camera.matrix_world),
                   'projectionMatrix': matrix_values(matrix),
                   'pixelAspect': [scene.render.pixel_aspect_x, 1.],
                   'orthoScale': camera.data.ortho_scale, 'sensorFit': 'HORIZONTAL',
                   'shift': [camera.data.shift_x, camera.data.shift_y]},
        'calibration': calibration,
        'calibrationLogical': {key: [number / scale for number in value]
                               for key, value in calibration.items()},
        'notes': ['Same frozen native geometry, materials, pose and world transforms across profiles.',
                  'Character reference is the current ordinary35-degree camera; environment100% is not its production baseline.']
                 if group['id'] == 'chef-lena' else
                 ['Projection configured before capture; no finished PNG transformation.'],
    }


def copy_lighting(source, scene, prefix):
    if source.world:
        scene.world = source.world.copy()
        scene.world.name = prefix + '__World'
    else:
        scene.world = bpy.data.worlds.new(prefix + '__World')
        scene.world.use_nodes = True
        background = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
        background.inputs['Color'].default_value = (.72, .80, 1., 1.)
        background.inputs['Strength'].default_value = .7
    lights = [obj for obj in source.objects if obj.type == 'LIGHT' and obj.name.startswith('S33 ')]
    for original in lights:
        clone = original.copy()
        clone.name = prefix + '__' + original.name
        clone.data = original.data.copy()
        clone.animation_data_clear()
        clone.parent = None
        clone.matrix_world = original.matrix_world.copy()
        scene.collection.objects.link(clone)
    if not lights:
        for name, position, energy, size in [('Key', (-3, -4, 7), 450, 5),
                                            ('Fill', (4, -1, 3), 160, 4),
                                            ('Rim', (1, 4, 5), 200, 3)]:
            data = bpy.data.lights.new(prefix + '__' + name, 'AREA')
            light = bpy.data.objects.new(data.name, data)
            scene.collection.objects.link(light)
            data.energy, data.shape, data.size = energy, 'DISK', size
            light.location = position
            light.rotation_euler = (-light.location).to_track_quat('-Z', 'Y').to_euler()


def create_study(runtime, output_dir='/private/tmp/sushi33-projection-study', keep_scene=False):
    """Clone/freeze seven study groups and save only their isolated new scene."""
    required = set(SOLO_IDS + ['belt-corner-w-s', 'belt-straight-s'])
    assets = {aid: runtime.assets[aid] for aid in required}
    before = source_snapshot(assets)
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    project = output / 'projection-study.blend'
    if project.exists():
        raise FileExistsError('Use a new study folder; refusing to replace ' + str(project))
    prefix = 'S33 Projection Study ' + uuid.uuid4().hex[:8]
    source_scene = bpy.data.scenes.get(getattr(runtime, 'SCENE_NAME', '')) or bpy.context.scene
    scene = bpy.data.scenes.new(prefix)
    scene['role'] = 'Isolated native height-projection study; production assets unchanged'
    own_collections = []
    material_cache = {}
    manifest = {'version': 1, 'schemaVersion': 1, 'title': 'Native height projection comparison',
                'status': 'native-models-frozen-capture-pending',
                'sourceScale': SOURCE_SCALE, 'cellSize': CELL,
                'ratios': [{'id': ident, 'label': ident + '%', 'heightRatio': ratio, 'heightScale': ratio}
                           for ident, ratio in RATIOS],
                'scene': scene.name, 'nativeProject': project.name,
                'groups': [], 'sourceScriptSHA256': file_hash(__file__),
                'hashMethod': 'SHA256 canonical JSON sort_keys=True separators=(comma,colon); geometry uses actual evaluated world vertices rounded7dp; placements use actual world matrices rounded9dp.',
                'productionPresentationHashBefore': before,
                'createdAtUnix': time.time()}
    try:
        with activate(scene):
            render_settings(scene)
            copy_lighting(source_scene, scene, prefix)
            camera = bpy.data.objects.new(prefix + '__Camera', bpy.data.cameras.new(prefix + '__Camera'))
            scene.collection.objects.link(camera)
            scene.camera = camera
            group_specs = [(aid, [(aid, [0., 0., 0.])]) for aid in SOLO_IDS]
            group_specs.append(('context-l-belt', [
                ('belt-straight-e', [-1., 0., 0.]),
                ('belt-corner-w-s', [0., 0., 0.]),
                ('belt-straight-s', [0., -1., 0.]),
                ('stool-wood', [-1., -1.25, 0.]),
                ('crate-wood', [-2., -.25, 0.]),
                ('boulder-underwater', [1.2, -.9, 0.]),
            ]))
            for group_id, instances in group_specs:
                collection = bpy.data.collections.new(prefix + '__' + group_id)
                scene.collection.children.link(collection)
                own_collections.append(collection)
                frame, anchor = list(runtime.assets[instances[0][0]].get('frame', [192, 320])), list(runtime.assets[instances[0][0]].get('anchor', [96, 248]))
                if group_id == 'chef-lena':
                    frame, anchor = [256, 384], [128, 304]
                elif group_id == 'context-l-belt':
                    frame, anchor = [768, 704], [384, 352]
                group = {'id': group_id, 'name': LABELS[group_id], 'frameSize': frame,
                         'kind': 'assembly' if group_id == 'context-l-belt' else 'object',
                         'groundRoot': [0, 0],
                         'root': anchor, 'direction': 'S',
                         'gridSize': [5, 4] if group_id == 'context-l-belt' else [1, 1],
                         'gridOrigin': [64, 224] if group_id == 'context-l-belt'
                         else [anchor[0] - 64, anchor[1] - 64],
                         'images': {}, 'source': {'collection': collection.name,
                                                  'placements': [], 'meshBindings': [], 'cameras': {}}}
                for index, (aid, position) in enumerate(instances):
                    root, mapping, bindings = clone_asset(assets[aid], collection,
                        prefix + '__' + group_id + '__' + str(index), material_cache)
                    pose = freeze_character(runtime, scene, mapping) if aid == 'chef-lena' else {'clip': 'static', 'direction': 'S', 'shaderPhase': 0.}
                    root.location = position
                    group['source']['placements'].append({'asset': aid, 'nativeRoot': root.name,
                                                          'position': position, 'direction': 'S', 'pose': pose})
                    group['source']['meshBindings'].extend(bindings)
                    if aid == 'chef-lena':
                        group['source']['pose'] = pose
                scene.frame_set(1)
                bpy.context.view_layer.update()
                geometry_hash, placements_hash, transforms = geometry_snapshot(collection)
                group['source'].update(geometryHash=geometry_hash, placementsHash=placements_hash,
                                       transforms=transforms,
                                       materialsHash=canonical_hash(materials_snapshot(collection.all_objects)))
                for ident, ratio in RATIOS:
                    group['images'][ident] = 'sprites/' + group_id + '/' + ident + '.png'
                    group['source']['cameras'][ident] = 'cameras/' + group_id + '/' + ident + '.json'
                if group_id == 'chef-lena':
                    group['reference'] = {'id': 'ordinary-35', 'label': 'Current ordinary 35° character camera',
                                          'image': 'sprites/chef-lena/ordinary-35.png',
                                          'camera': 'cameras/chef-lena/ordinary-35.json'}
                manifest['groups'].append(group)
                collection.hide_render = True
            first = manifest['groups'][0]
            bpy.data.collections[first['source']['collection']].hide_render = False
            configure_camera(scene, first, 1.)
            after = source_snapshot(assets)
            manifest['productionPresentationHashAfter'] = after
            if before != after:
                raise RuntimeError('Production presentation changed during read-only study cloning')
            bpy.data.libraries.write(str(project), {scene}, fake_user=True, compress=True)
            manifest['nativeProjectSHA256'] = file_hash(project)
            write_json(output / 'study.json', manifest)
    finally:
        if not keep_scene:
            objects = list(scene.objects)
            bpy.data.scenes.remove(scene)
            for collection in own_collections:
                bpy.data.collections.remove(collection)
            for obj in objects:
                if obj.name in bpy.data.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
    return {'manifest': str(output / 'study.json'), 'project': str(project),
            'groups': len(manifest['groups']), 'captures': 29,
            'productionUnchanged': before == manifest.get('productionPresentationHashAfter')}


def png_dimensions(path):
    data = Path(path).read_bytes()[:24]
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Not a PNG: ' + str(path))
    return list(struct.unpack('>II', data[16:24]))


def migrate_manifest(manifest_path):
    """Metadata-only compatibility update for the already frozen v1 study."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    manifest['schemaVersion'] = 1
    manifest.setdefault('creationScriptSHA256', manifest['sourceScriptSHA256'])
    manifest['sourceScriptSHA256'] = file_hash(__file__)
    for ratio in manifest['ratios']:
        ratio['heightScale'] = ratio['heightRatio']
    for group in manifest['groups']:
        group['kind'] = 'assembly' if group['id'] == 'context-l-belt' else 'object'
        group['groundRoot'] = [0, 0]
        group['images'] = {key: value.replace('renders/', 'sprites/', 1)
                           for key, value in group['images'].items()}
        if 'reference' in group:
            group['reference']['image'] = group['reference']['image'].replace('renders/', 'sprites/', 1)
    write_json(manifest_path, manifest)
    return {'manifest': str(manifest_path), 'nativeProjectSHA256': manifest['nativeProjectSHA256'],
            'geometryRebuilt': False}


def capture_study(manifest_path, groups=None, ratios=None, limit=None):
    """Render the frozen isolated study project; does not rebuild any geometry."""
    manifest_path = Path(manifest_path).resolve()
    output = manifest_path.parent
    manifest = json.loads(manifest_path.read_text())
    loaded = Path(bpy.data.filepath).resolve()
    expected = (output / manifest['nativeProject']).resolve()
    if loaded != expected or file_hash(loaded) != manifest['nativeProjectSHA256']:
        raise RuntimeError('Load the exact isolated study project from this manifest')
    scene = bpy.data.scenes.get(manifest['scene'])
    if scene is None:
        raise KeyError('Missing isolated study scene')
    completed = 0
    with activate(scene):
        render_settings(scene)
        for group in manifest['groups']:
            if groups and group['id'] not in groups:
                continue
            for candidate in manifest['groups']:
                bpy.data.collections[candidate['source']['collection']].hide_render = candidate['id'] != group['id']
            collection = bpy.data.collections[group['source']['collection']]
            collection.hide_viewport = False
            bpy.context.view_layer.update()
            geometry_hash, placements_hash, _ = geometry_snapshot(collection)
            if geometry_hash != group['source']['geometryHash'] or placements_hash != group['source']['placementsHash']:
                raise RuntimeError('Frozen study geometry/transforms differ: ' + group['id'])
            material_values = materials_snapshot(collection.all_objects)
            material_hash = canonical_hash(material_values)
            if group['source'].get('materialsHash') and material_hash != group['source']['materialsHash']:
                raise RuntimeError('Frozen study material/colors differ: ' + group['id'])
            group['source']['materialsHash'] = material_hash
            group['source']['materials'] = material_values
            write_json(manifest_path, manifest)
            profiles = [(ident, ratio, False, group['images'][ident], group['source']['cameras'][ident])
                        for ident, ratio in RATIOS if not ratios or ident in ratios]
            if 'reference' in group and (not ratios or 'ordinary-35' in ratios):
                reference = group['reference']
                profiles.append(('ordinary-35', None, True, reference['image'], reference['camera']))
            for ident, ratio, ordinary, image_relative, camera_relative in profiles:
                if canonical_hash(materials_snapshot(collection.all_objects)) != material_hash:
                    raise RuntimeError('Material/color state changed across profiles: ' + group['id'])
                camera = configure_camera(scene, group, ratio, ordinary)
                image_path, camera_path = output / image_relative, output / camera_relative
                image_path.parent.mkdir(parents=True, exist_ok=True)
                scene.render.filepath = str(image_path)
                bpy.ops.render.render(write_still=True, scene=scene.name)
                dimensions = png_dimensions(image_path)
                if dimensions != [number * SOURCE_SCALE for number in group['frameSize']]:
                    raise RuntimeError('Unexpected native PNG dimensions')
                camera['png'] = {'path': image_relative, 'sha256': file_hash(image_path),
                                 'dimensions': dimensions, 'sourceScale': SOURCE_SCALE}
                camera['nativeProjectSHA256'] = manifest['nativeProjectSHA256']
                camera['sourcePose'] = group['source'].get('pose')
                write_json(camera_path, camera)
                completed += 1
                print('S33_PROJECTION_CAPTURE ' + group['id'] + '/' + ident, flush=True)
                if limit and completed >= limit:
                    return {'captures': completed, 'limited': True, 'manifest': str(manifest_path)}
    manifest['status'] = 'captured' if not groups and not ratios else 'partial-capture-selection'
    manifest['capturedAtUnix'] = time.time()
    write_json(manifest_path, manifest)
    return {'captures': completed, 'manifest': str(manifest_path), 'status': manifest['status']}


if __name__ == '__main__' and '--capture' in sys.argv:
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', action='store_true')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--groups', nargs='*')
    parser.add_argument('--ratios', nargs='*')
    parser.add_argument('--limit', type=int)
    args = parser.parse_args(arguments)
    print(json.dumps(capture_study(args.manifest, args.groups, args.ratios, args.limit)))
