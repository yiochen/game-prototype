"""Read-only audit: load saved study, inspect it, then evaluate original Noor.

Run Blender --background noor-lighting.blend --python THIS -- --study STUDY
 --production PRODUCTION_ASSET_FOLDER --output REPORT.
Only the requested JSON report is written. Neither Blender file is saved.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec);sys.modules[name] = module;spec.loader.exec_module(module)
    return module


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def matrix(value): return [[float(x) for x in row] for row in value]


def activate(scene):
    bpy.context.window.scene = scene
    bpy.context.window.view_layer = scene.view_layers[0]
    scene.view_layers[0].update()


def maximum_delta(left, right):
    return max((abs(float(a) - float(b)) for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b)), default=0.)


def meshes(scene):
    return {obj['sourceObject']: {'vertices': [[float(v) for v in vertex.co] for vertex in obj.data.vertices],
                                   'polygons': [list(poly.vertices) for poly in obj.data.polygons],
                                   'matrix': matrix(obj.matrix_world)}
            for obj in scene.objects if obj.type == 'MESH' and obj.get('sourceObject')}


def geometry_hash(objects):
    digest = hashlib.sha256()
    for name, value in sorted(objects.items()):
        digest.update(name.encode());digest.update(json.dumps([[round(x, 7) for x in vertex] for vertex in value['vertices']]).encode())
        digest.update(json.dumps(value['polygons']).encode())
    return digest.hexdigest()


def root_matrix(scene): return matrix(bpy.data.objects[scene['studyRoot']].matrix_world)


def camera(scene):
    return {'worldMatrix': matrix(scene.camera.matrix_world), 'type': scene.camera.data.type,
            'orthoScale': scene.camera.data.ortho_scale, 'shift': [scene.camera.data.shift_x, scene.camera.data.shift_y],
            'resolution': [scene.render.resolution_x, scene.render.resolution_y],
            'pixelAspect': [scene.render.pixel_aspect_x, scene.render.pixel_aspect_y]}


def lighting(scene):
    result = []
    for obj in scene.objects:
        if obj.type != 'LIGHT' or obj.data.energy <= 0: continue
        direction = obj.matrix_world.to_quaternion() @ Vector((0, 0, -1))
        result.append({'name': obj.name, 'type': obj.data.type, 'shape': obj.data.shape,
                       'position': list(obj.matrix_world.translation), 'direction': list(direction),
                       'energy': obj.data.energy, 'size': obj.data.size, 'color': list(obj.data.color)})
    return result


def cardinal_symmetry(lights):
    errors = []
    for turns in (1, 2, 3):
        angle = turns * math.pi / 2;c, s = math.cos(angle), math.sin(angle)
        def rotate(v): return [c * v[0] - s * v[1], s * v[0] + c * v[1], v[2]]
        for light in lights:
            target = rotate(light['position']);direction = rotate(light['direction'])
            matches = [other for other in lights
                       if max(abs(a - b) for a, b in zip(other['position'], target)) < 2e-5
                       and max(abs(a - b) for a, b in zip(other['direction'], direction)) < 2e-5
                       and all(abs(other[key] - light[key]) < 1e-6 for key in ('energy', 'size'))
                       and other['type'] == light['type'] and other['shape'] == light['shape']
                       and other['color'] == light['color']]
            if not matches: errors.append(str(turns * 90) + ' degrees: ' + light['name'])
    return {'passed': not errors, 'errors': errors,
            'meaning': 'The actual position/direction/power/shape/color light set is unchanged by cardinal world-yaw rotation; asymmetric character views need not have identical RGB averages.'}


def materials(scene):
    result = {}
    for obj in scene.objects:
        if obj.type != 'MESH' or not obj.get('sourceObject'): continue
        for index, slot in enumerate(obj.material_slots):
            if not slot.material: continue
            nodes = slot.material.node_tree.nodes
            output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
            shader = output.inputs['Surface'].links[0].from_node
            ramps = [{'elements': [{'position': item.position, 'color': list(item.color)} for item in n.color_ramp.elements]}
                     for n in nodes if n.type == 'VALTORGB']
            entry = {'material': slot.material.name, 'surfaceType': shader.type, 'ramps': ramps}
            if shader.type == 'BSDF_PRINCIPLED':
                entry.update(roughness=shader.inputs['Roughness'].default_value,
                             specular=shader.inputs['Specular IOR Level'].default_value,
                             metallic=shader.inputs['Metallic'].default_value,
                             emissionStrength=shader.inputs['Emission Strength'].default_value)
                base = shader.inputs['Base Color']
                lower = base.links[0].from_node if base.is_linked else None
                entry['baseColorSource'] = lower.type if lower else None
                entry['retainsLowerRampDirectly'] = bool(lower and lower.type == 'MIX_RGB' and lower.blend_type == 'MULTIPLY'
                    and lower.inputs[2].is_linked and lower.inputs[2].links[0].from_node.type == 'VALTORGB')
            result[obj['sourceObject'] + ':' + str(index)] = entry
    return result


def audit(study, production, output):
    manifest = json.loads((study / 'manifest.json').read_text())
    report = {'studySHA256': sha(bpy.data.filepath), 'productionSHA256': sha(production / 'source/blender/sushi-loop-world-library.blend'),
              'issues': [], 'variants': {}, 'visualApproval': 'not-established; study pending user review'}
    baseline = bpy.data.scenes[manifest['variants'][0]['scene']]
    activate(baseline)
    base_geometry, base_root, base_camera, base_materials = meshes(baseline), root_matrix(baseline), camera(baseline), materials(baseline)
    for variant in manifest['variants']:
        scene = bpy.data.scenes[variant['scene']];activate(scene);graph = scene.compositing_node_group
        actual_materials = materials(scene);actual_lights = lighting(scene);actual_geometry = meshes(scene)
        same_geometry = actual_geometry == base_geometry
        group_alpha = next(n for n in graph.nodes if n.bl_idname == 'CompositorNodeCombineColor').inputs['Alpha'].links[0]
        entry = {'geometryIdenticalToBaseline': same_geometry, 'geometrySHA256': geometry_hash(actual_geometry),
                 'rootIdenticalToBaseline': root_matrix(scene) == base_root, 'cameraIdenticalToBaseline': camera(scene) == base_camera,
                 'rootMatrix': root_matrix(scene), 'camera': camera(scene), 'lights': actual_lights,
                 'cardinalLightingSymmetry': cardinal_symmetry(actual_lights),
                 'worldStrength': [n.inputs['Strength'].default_value for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND'],
                 'contrast': graph.get('contrastFactor'), 'renderLayerOwners': [n.scene.name if n.scene else None for n in graph.nodes if n.type == 'R_LAYERS'],
                 'alphaBypassesRGBGrade': group_alpha.from_node.type == 'R_LAYERS' and group_alpha.from_socket.name == 'Alpha',
                 'lowerRampsIdenticalToBaseline': all(value['ramps'] == base_materials[key]['ramps'] for key, value in actual_materials.items()),
                 'materials': actual_materials}
        report['variants'][variant['id']] = entry
        for key in ('geometryIdenticalToBaseline', 'rootIdenticalToBaseline', 'cameraIdenticalToBaseline', 'alphaBypassesRGBGrade', 'lowerRampsIdenticalToBaseline'):
            if not entry[key]: report['issues'].append(variant['id'] + ': ' + key)
        if entry['geometrySHA256'] != variant['geometrySHA256']: report['issues'].append(variant['id'] + ': manifest geometry hash mismatch')
        if entry['contrast'] != 1.35: report['issues'].append(variant['id'] + ': wrong contrast grade')
        if entry['renderLayerOwners'] != [scene.name]: report['issues'].append(variant['id'] + ': compositor scene owner mismatch')
        if not entry['cardinalLightingSymmetry']['passed']: report['issues'].append(variant['id'] + ': asymmetric lighting rig')
        if variant['id'] != 'baseline':
            if len(actual_lights) != 5: report['issues'].append(variant['id'] + ': expected top key and four fills')
            for key, material in actual_materials.items():
                if material['surfaceType'] != 'BSDF_PRINCIPLED' or material.get('emissionStrength') != 0 or not material.get('retainsLowerRampDirectly'):
                    report['issues'].append(variant['id'] + ': nonphysical or missing lower ramp ' + key)
    mask_scene = bpy.data.scenes['S33 Noor lighting hat mask'];activate(mask_scene)
    classified = {'top': 0, 'side': 0, 'excluded': 0};mask_errors = []
    for obj in mask_scene.objects:
        if obj.type != 'MESH': continue
        for polygon in obj.data.polygons:
            expected = 1 if 'beret_' in obj.name and polygon.normal.z >= .65 else 2 if 'beret_' in obj.name and polygon.normal.z <= .35 else 0
            classified[{0: 'excluded', 1: 'top', 2: 'side'}[expected]] += 1
            if polygon.material_index != expected: mask_errors.append(obj.name + ': incorrect normal classification')
    report['hatNormalMask'] = {'classification': classified, 'issues': mask_errors,
                              'thresholds': {'topNormalZMinimum': .65, 'sideNormalZMaximum': .35},
                              'compositorDisabled': not mask_scene.render.use_compositing}
    report['issues'] += mask_errors
    if mask_scene.render.use_compositing: report['issues'].append('Mask classification is affected by compositor')
    # Open the original file in this isolated audit process, never in live MCP.
    original = production / 'source/blender/sushi-loop-world-library.blend'
    bpy.ops.wm.open_mainfile(filepath=str(original))
    base = production / 'source/blender'
    worker = load('s33_light_audit_worker', base / 'capture_worker.py')
    native = load('s33_light_audit_native', base / 'native_actions.py')
    scene = worker.native_scene();source = production / 'source/native-records'
    asset, rig, _ = worker.reconstruct('chef-noor', source, {}, scene)
    worker.show_only(scene, asset);native.apply_clip(asset, rig, 'idle', frame=4, direction='S', scene=scene)
    depsgraph = bpy.context.evaluated_depsgraph_get();source_geometry = {}
    for obj in asset['collection'].all_objects:
        if obj.type != 'MESH' or obj.hide_render: continue
        evaluated = obj.evaluated_get(depsgraph);mesh = evaluated.to_mesh()
        try:
            source_geometry[obj.name] = {'vertices': [list(evaluated.matrix_world @ vertex.co) for vertex in mesh.vertices],
                                         'polygons': [list(poly.vertices) for poly in mesh.polygons]}
        finally: evaluated.to_mesh_clear()
    mismatch = [];largest = 0.
    if set(source_geometry) != set(base_geometry): mismatch.append('Mesh identity set differs')
    for name in set(source_geometry) & set(base_geometry):
        left, right = source_geometry[name], base_geometry[name]
        if left['polygons'] != right['polygons'] or len(left['vertices']) != len(right['vertices']): mismatch.append(name + ': topology differs');continue
        delta = maximum_delta(left['vertices'], right['vertices']);largest = max(largest, delta)
        if delta > 2e-6: mismatch.append(name + ': evaluated vertex delta ' + str(delta))
    report['originalProductionPose'] = {'clip': 'idle', 'frame': 4, 'direction': 'S', 'meshes': len(source_geometry),
                                        'maximumVertexDeltaCells': largest, 'issues': mismatch, 'matched': not mismatch}
    report['issues'] += mismatch
    if report['studySHA256'] != manifest['source']['sha256']: report['issues'].append('Study source hash mismatch')
    if report['productionSHA256'] != manifest['source']['productionBlendSHA256']: report['issues'].append('Production source hash mismatch')
    report['passed'] = not report['issues'];output.parent.mkdir(parents=True, exist_ok=True);output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'issues': report['issues'], 'originalProductionPose': report['originalProductionPose']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--production', type=Path, required=True);parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    audit(args.study, args.production, args.output)
