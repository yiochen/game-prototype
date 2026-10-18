"""Read-only native Blender belt verification; ROOT executes through Blender MCP.

Invocation (no procedural pose callbacks, no rendering, no model edits):
    scope = {'__file__': '/private/tmp/sushi33-production/validate_native_belt_flow.py'}
    exec(compile(open(scope['__file__']).read(), scope['__file__'], 'exec'), scope)
    result = scope['validate_native_belt_flow'](r, N)
    print({k: result[k] for k in ('ok', 'assetsChecked', 'samplesChecked', 'errors', 'report')})

Only presentation state/action bindings are temporarily changed. The original
scene, frame, camera, selections, object transforms, action slots and NLA mute
states are restored. Writes one JSON verification report, never a .blend.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import time

import bpy
from mathutils import Vector


_BELT_VERIFY_BASE = Path('/private/tmp/sushi33-production')
_BELT_VERIFY_NORMALS = {'N': (0., 1.), 'E': (1., 0.), 'S': (0., -1.), 'W': (-1., 0.)}


def _belt_verify_ports(deck, root, flow, tolerance=2e-5):
    """Find actual UV loops on physical port planes after child orientation."""
    mesh = deck.data
    layer = mesh.uv_layers.active
    if layer is None:
        raise ValueError('Deck has no active native UV layer')
    transform = root.matrix_world.inverted() @ deck.matrix_world
    positions = [transform @ vertex.co for vertex in mesh.vertices]
    observed = {}
    errors = []
    for role, expected_u in (('incoming', 0.), ('outgoing', 1.)):
        side = flow.get(role)
        if side is None:
            continue  # Closed caps are deliberately not declared open ports.
        normal = _BELT_VERIFY_NORMALS[side]
        values = []
        selected_vertices = set()
        for loop in mesh.loops:
            point = positions[loop.vertex_index]
            axial = point.x * normal[0] + point.y * normal[1]
            if abs(axial - .5) <= tolerance and abs(point.z - flow.get('deckHeight', .64)) <= tolerance:
                selected_vertices.add(loop.vertex_index)
                values.append(float(layer.data[loop.index].uv.x))
        if len(selected_vertices) < 2:
            errors.append(role + ' ' + side + ': physical open-port edge not found from mesh/orientation')
            continue
        maximum_error = max(abs(value - expected_u) for value in values)
        observed[role] = {'side': side, 'expectedU': expected_u,
                          'uvRange': [min(values), max(values)],
                          'edgeVertices': len(selected_vertices), 'loops': len(values),
                          'maximumError': maximum_error}
        if maximum_error > tolerance:
            errors.append(role + ' ' + side + ': actual UV is ' + str(observed[role]['uvRange']) + ', expected ' + str(expected_u))
    digest = hashlib.sha256()
    for vertex in positions:
        digest.update(struct.pack('<3d', *vertex))
    for loop in layer.data:
        digest.update(struct.pack('<2d', *loop.uv))
    return observed, errors, digest.hexdigest()


def _belt_verify_shader(deck):
    """Resolve the rendered material and confirm phase drives its real UV ramp."""
    indexes = {polygon.material_index for polygon in deck.data.polygons}
    if len(indexes) != 1:
        raise ValueError('Expected one deck material, found indexes ' + str(indexes))
    material = deck.data.materials[next(iter(indexes))]
    if material is None or not material.use_nodes or material.node_tree is None:
        raise ValueError('Actual deck material has no native shader graph')
    tree = material.node_tree
    phases = [node for node in tree.nodes if node.bl_idname == 'ShaderNodeValue' and node.label == 'Deck travel phase']
    if len(phases) != 1:
        raise ValueError('Expected exactly one real deck phase Value node')
    phase = phases[0]
    additions = [link.to_node for link in phase.outputs[0].links if link.to_node.bl_idname == 'ShaderNodeMath' and link.to_node.operation == 'ADD']
    if len(additions) != 1:
        raise ValueError('Phase does not drive exactly one native ADD node')
    addition = additions[0]
    multipliers = [link.from_node for socket in addition.inputs for link in socket.links if link.from_node != phase and link.from_node.bl_idname == 'ShaderNodeMath' and link.from_node.operation == 'MULTIPLY']
    if len(multipliers) != 1:
        raise ValueError('Phase ADD has no unambiguous actual UV multiplier')
    multiplier = multipliers[0]
    # ShaderNodeMath exposes a third socket even for binary MULTIPLY. Its
    # inactive default (commonly .5) is not an operand of this operation.
    active_inputs = list(multiplier.inputs)[:2]
    constants = [float(socket.default_value) for socket in active_inputs if not socket.is_linked]
    linked_inputs = [socket for socket in active_inputs if socket.is_linked]
    if len(constants) != 1 or len(linked_inputs) != 1 or abs(constants[0] - 7.) > 1e-6:
        raise ValueError('Actual shader multiplier is not seven slats per cell: ' + str(constants))
    separators = [link.from_node for socket in linked_inputs for link in socket.links if link.from_node.bl_idname == 'ShaderNodeSeparateXYZ' and link.from_socket == link.from_node.outputs[0]]
    if len(separators) != 1:
        raise ValueError('Actual shader is not driven by native UV X')
    uv_links = list(separators[0].inputs[0].links)
    if len(uv_links) != 1 or uv_links[0].from_node.bl_idname != 'ShaderNodeTexCoord' or uv_links[0].from_socket.name != 'UV':
        raise ValueError('Actual shader UV input is not the mesh UV coordinate')
    fractions = [link.to_node for link in addition.outputs[0].links if link.to_node.bl_idname == 'ShaderNodeMath' and link.to_node.operation == 'FRACT']
    if len(fractions) != 1:
        raise ValueError('Actual phase sum does not drive native FRACT')
    ramps = [link.to_node for link in fractions[0].outputs[0].links if link.to_node.bl_idname == 'ShaderNodeValToRGB']
    if len(ramps) != 1:
        raise ValueError('Actual FRACT output does not drive the deck color ramp')
    base_color_links = [link for link in ramps[0].outputs[0].links if link.to_node.type == 'BSDF_PRINCIPLED' and link.to_socket.name == 'Base Color']
    if len(base_color_links) != 1:
        raise ValueError('Actual slat ramp does not drive deck base color')
    return material, tree, phase, {'material': material.name, 'phaseNode': phase.name,
                                  'multiplier': constants[0], 'fractionNode': fractions[0].name,
                                  'colorRamp': ramps[0].name}


def _belt_verify_owner_state(owner):
    animation = owner.animation_data
    if animation is None:
        return {'owner': owner, 'hadAnimationData': False}
    return {'owner': owner, 'hadAnimationData': True, 'action': animation.action,
            'slot': getattr(getattr(animation, 'action_slot', None), 'identifier', None),
            'nla': [(track, track.mute) for track in animation.nla_tracks]}


def validate_native_belt_flow(runtime, native, report_path=None):
    """Check all 20 native modules, preserving source geometry and presentation."""
    if getattr(runtime, 'job_status', {}).get('state') == 'rendering':
        raise RuntimeError('Live Blender capture is active; wait before temporary action evaluation')
    output = Path(report_path) if report_path else _BELT_VERIFY_BASE / 'export/validation/native-belt-flow-v8.json'
    report = {'version': 1, 'ok': False, 'source': 'actual native deck UV loops, orientation matrices and evaluated baked shader actions',
              'blenderVersion': bpy.app.version_string, 'blendPath': bpy.data.filepath,
              'createdAtUnix': time.time(), 'assetsChecked': 0, 'samplesChecked': 0,
              'samplesPerAsset': 24, 'expectedPhase': '-7*i/24',
              'assets': [], 'errors': [], 'report': str(output)}
    ids = sorted(aid for aid in runtime.assets if aid.startswith('belt-'))
    if len(ids) != 20:
        report['errors'].append({'asset': 'library', 'message': 'Expected 20 native belt modules, found ' + str(len(ids))})
    production_scene = bpy.data.scenes.get(getattr(runtime, 'SCENE_NAME', 'Sushi33 Production'))
    if production_scene is None:
        raise RuntimeError('Production scene is not loaded')
    window = bpy.context.window
    original_scene = window.scene if window else bpy.context.scene
    original_layer = window.view_layer if window else bpy.context.view_layer
    original_active = original_layer.objects.active
    original_selected = list(bpy.context.selected_objects)
    original_frame = (production_scene.frame_current, production_scene.frame_subframe)
    original_settings = (production_scene.render.fps, production_scene.render.fps_base,
                         production_scene.frame_start, production_scene.frame_end, production_scene.camera)
    owner_states = {}
    root_states = []
    phase_states = []
    collection_states = []
    layer_states = {}
    try:
        if window:
            window.scene = production_scene
            window.view_layer = production_scene.view_layers[0]
        elif bpy.context.scene != production_scene:
            raise RuntimeError('Headless current scene differs from production scene')
        # Capture all affected owner bindings before evaluating any scene frame.
        for aid in ids:
            asset = runtime.assets[aid]
            collection = asset['collection']
            collection_states.append((collection, collection.hide_render, collection.hide_viewport))
            objects = native._all_objects(asset)
            nodes = native._node_sockets(objects)
            shapes = native._shape_meshes(objects)
            for owner in native._animation_owners(objects, nodes, shapes):
                owner_states.setdefault(owner.as_pointer(), _belt_verify_owner_state(owner))
            root_states.append((asset['root'], asset['root'].matrix_basis.copy(), asset['root'].rotation_mode))
            try:
                deck = asset['parts'].get('connected_turn_deck') or asset['parts'].get('connected_straight_deck')
                material, tree, phase, _ = _belt_verify_shader(deck)
                phase_states.append((phase.outputs[0], float(phase.outputs[0].default_value)))
            except Exception:
                # A concrete asset failure is recorded below; continue other assets.
                pass
        def collection_path(layer, target):
            if layer.collection == target:
                return [layer]
            for child in layer.children:
                path = collection_path(child, target)
                if path:
                    return [layer] + path
            return []
        # Hidden collections may not receive dependency-graph animation updates.
        # Enable only our belt collections while inspecting their real actions.
        for aid in ids:
            collection = runtime.assets[aid]['collection']
            collection.hide_render = False
            collection.hide_viewport = False
            for layer in collection_path(production_scene.view_layers[0].layer_collection, collection):
                layer_states.setdefault(layer.as_pointer(), (layer, layer.exclude, layer.hide_viewport))
                layer.exclude = False
                layer.hide_viewport = False
        bpy.context.view_layer.update()
        for aid in ids:
            asset = runtime.assets[aid]
            row = {'id': aid, 'ok': False, 'ports': {}, 'phaseSamples': [], 'errors': []}
            try:
                flow = asset.get('flow')
                if not isinstance(flow, dict):
                    raise ValueError('Live native asset lacks its flow record')
                row['flow'] = {'incoming': flow.get('incoming'), 'outgoing': flow.get('outgoing')}
                deck = asset['parts'].get('connected_turn_deck') or asset['parts'].get('connected_straight_deck')
                if deck is None or deck.type != 'MESH':
                    raise ValueError('Live native asset has no actual deck mesh')
                material, tree, phase, chain = _belt_verify_shader(deck)
                row['shader'] = chain
                record = getattr(runtime, 'native_records', {}).get(aid)
                if record is None:
                    record = json.loads((_BELT_VERIFY_BASE / 'export/source' / aid / 'rig.json').read_text())
                clip = record['clips']['running']
                if clip['frames'] != 24 or clip.get('fps') != 12 or not clip.get('loop'):
                    raise ValueError('Actual native running record is not a 24-frame 12fps loop')
                targets = [target for target in clip['actions'] if target['ownerType'] == 'ShaderNodeTree']
                if len(targets) != 1 or targets[0].get('materialOwnerName') != material.name:
                    raise ValueError('Native shader action cohort does not identify the exact rendered material owner')
                native.apply_clip(asset, record, 'running', frame=1, direction='S', scene=production_scene)
                if tree.animation_data is None or tree.animation_data.action is None or tree.animation_data.action.name != targets[0]['action']:
                    raise ValueError('Actual material is not bound to the recorded native running action')
                path = phase.outputs[0].path_from_id('default_value')
                if not any(curve.data_path == path for curve in native._fcurves(tree.animation_data.action)):
                    raise ValueError('Bound native action does not animate the actual connected phase socket')
                row['action'] = tree.animation_data.action.name
                row['ports'], port_errors, row['meshUvSignature'] = _belt_verify_ports(deck, asset['root'], flow)
                row['errors'].extend(port_errors)
                maximum_phase_error = 0.
                seam_error = 0.
                for index in range(24):
                    production_scene.frame_set(index + 1)
                    bpy.context.view_layer.update()
                    expected = -7. * index / 24.
                    actual = float(phase.outputs[0].default_value)
                    depsgraph = bpy.context.evaluated_depsgraph_get()
                    evaluated_material = material.evaluated_get(depsgraph)
                    evaluated_phase = float(evaluated_material.node_tree.nodes[phase.name].outputs[0].default_value)
                    row['phaseSamples'].append(actual)
                    error = max(abs(actual - expected), abs(evaluated_phase - expected))
                    maximum_phase_error = max(maximum_phase_error, error)
                    if error > 2e-5:
                        row['errors'].append('frame ' + str(index) + ': evaluated phase ' + str(evaluated_phase) + ', actual socket ' + str(actual) + ', expected ' + str(expected))
                    # Compare phase at measured UV endpoints on the unit circle,
                    # avoiding a false mismatch at FRACT's 0/1 boundary.
                    for port in row['ports'].values():
                        for value in port['uvRange']:
                            angle_error = math.remainder(math.tau * (7. * value + actual - expected), math.tau)
                            seam_error = max(seam_error, abs(angle_error) / math.tau)
                    report['samplesChecked'] += 1
                row['maximumPhaseError'] = maximum_phase_error
                row['maximumSeamPhaseCycleError'] = seam_error
                if seam_error > 2e-5:
                    row['errors'].append('Measured open-port shader phases fail directed seam agreement')
                row['ok'] = not row['errors']
            except Exception as exc:
                row['errors'].append(type(exc).__name__ + ': ' + str(exc))
            report['assetsChecked'] += 1
            report['assets'].append(row)
            report['errors'].extend({'asset': aid, 'message': error} for error in row['errors'])
    finally:
        restore_errors = []
        for state in owner_states.values():
            try:
                owner = state['owner']
                if not state['hadAnimationData']:
                    if owner.animation_data is not None:
                        owner.animation_data_clear()
                else:
                    native._assign(owner, state['action'], state['slot'])
                    for track, mute in state['nla']:
                        track.mute = mute
            except Exception as exc:
                restore_errors.append(str(exc))
        try:
            fps, fps_base, frame_start, frame_end, camera = original_settings
            production_scene.render.fps = fps
            production_scene.render.fps_base = fps_base
            production_scene.frame_start = frame_start
            production_scene.frame_end = frame_end
            production_scene.camera = camera
            production_scene.frame_set(original_frame[0], subframe=original_frame[1])
            for root, matrix_basis, rotation_mode in root_states:
                root.rotation_mode = rotation_mode
                root.matrix_basis = matrix_basis
            for socket, value in phase_states:
                socket.default_value = value
            for collection, hide_render, hide_viewport in collection_states:
                collection.hide_render = hide_render
                collection.hide_viewport = hide_viewport
            for layer, exclude, hide_viewport in layer_states.values():
                layer.exclude = exclude
                layer.hide_viewport = hide_viewport
            if window:
                window.scene = original_scene
                window.view_layer = original_layer
            # No selections are changed by this verifier; recover them only if
            # a native adapter unexpectedly changed selection while evaluating.
            if set(bpy.context.selected_objects) != set(original_selected):
                for obj in list(bpy.context.selected_objects):
                    obj.select_set(False)
                for obj in original_selected:
                    obj.select_set(True)
            original_layer.objects.active = original_active
            bpy.context.view_layer.update()
        except Exception as exc:
            restore_errors.append(str(exc))
        if restore_errors:
            report['errors'].append({'asset': 'presentation-restore', 'message': '; '.join(restore_errors)})
    report['ok'] = not report['errors'] and report['assetsChecked'] == 20 and report['samplesChecked'] == 480
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + '.' + str(os.getpid()) + '.tmp')
    temporary.write_text(json.dumps(report, indent=2) + '\n')
    os.replace(temporary, output)
    return report
