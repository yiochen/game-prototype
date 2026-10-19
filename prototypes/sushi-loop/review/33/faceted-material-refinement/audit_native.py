"""Read-only audit of the frozen Faceted material refinement.

Run with Blender --background SOURCE.blend --python THIS -- --study FOLDER.
Only the review JSON is written; no source project or image is modified.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import bpy


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


HERE = Path(__file__).resolve().parent
ENV = load('s33_refine_env_audit', HERE.parent / 'environment-lighting-study/audit_saved_study.py')
COMMON = load('s33_refine_common_audit', HERE.parent / 'character-lighting-study/audit_saved_study.py')


def light_signature(scene):
    return sorted([{k: v for k, v in item.items() if k != 'name'}
                   for item in COMMON.lighting(scene)], key=lambda item: item['position'])


def actual_materials(scene):
    result = {}
    for obj in scene.objects:
        if obj.type != 'MESH' or not obj.get('sourceObject'):
            continue
        for index, slot in enumerate(obj.material_slots):
            material = slot.material
            if not material:
                continue
            output = next(n for n in material.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
            shader = output.inputs['Surface'].links[0].from_node
            lower = ENV.lower_node(material)
            graph = ENV.graph_signature(shader)
            normalized = copy.deepcopy(graph)
            normalized['nodes'][lower.name]['inputs'][1] = '<base-color>'
            for index_input, socket in enumerate(shader.inputs):
                if socket.name in ('Roughness', 'Specular IOR Level'):
                    normalized['nodes'][shader.name]['inputs'][index_input] = '<finish>'
            key = obj['sourceAssetId'] + '::' + obj['sourceObject'] + ':' + str(index)
            result[key] = {'material': material.name,
                           'shader': shader.type,
                           'baseColor': list(lower.inputs[1].default_value),
                           'roughness': shader.inputs['Roughness'].default_value,
                           'specular': shader.inputs['Specular IOR Level'].default_value,
                           'metallic': shader.inputs['Metallic'].default_value,
                           'emission': shader.inputs['Emission Strength'].default_value,
                           'baseUsesApprovedLowerGraph': shader.inputs['Base Color'].is_linked
                               and shader.inputs['Base Color'].links[0].from_node == lower,
                           'activeGraph': graph, 'normalizedGraph': normalized,
                           'treeHasAction': bool(material.node_tree.animation_data
                                                 and material.node_tree.animation_data.action)}
    return result


def close(left, right, tolerance=1e-6):
    return len(left) == len(right) and all(abs(a-b) <= tolerance for a, b in zip(left, right))


def audit(folder):
    manifest = json.loads((folder / 'manifest.json').read_text())
    historical = folder.parent / 'environment-lighting-study'
    old_manifest = json.loads((historical / 'manifest.json').read_text())
    recipe = load('s33_refinement_recipe_audit', folder / manifest['source']['recipe'])
    source_file = folder / manifest['source']['blend']
    report = {'sourceSHA256': sha(source_file),
              'recipeSHA256': sha(folder / manifest['source']['recipe']),
              'approval': 'Faceted lighting selected; this material refinement remains awaiting visual review.',
              'issues': [], 'subjects': {}, 'sourceIntegrity': {}}
    check = lambda condition, message: report['issues'].append(message) if not condition else None
    check(report['sourceSHA256'] == manifest['source']['sha256'], 'Saved refinement source hash differs')
    check(report['recipeSHA256'] == manifest['source']['recipeSHA256'], 'Saved refinement recipe hash differs')
    production = folder.parent / 'production/source/blender/sushi-loop-world-library.blend'
    for name, path, expected in (
            ('production', production, manifest['source']['productionBlendSHA256']),
            ('historicalStudy', historical / old_manifest['source']['blend'], manifest['source']['previousStudySHA256']),
            ('historicalManifest', historical / 'manifest.json', manifest['source']['previousStudyManifestSHA256'])):
        actual = sha(path)
        report['sourceIntegrity'][name] = {'sha256': actual, 'expectedSHA256': expected, 'unchanged': actual == expected}
        check(actual == expected, name + ' hash changed')
    old_scenes = [next(v for v in s['variants'] if v['id'] == 'faceted')['scene'] for s in old_manifest['subjects']]
    old_scenes += [s['maskScene'] for s in old_manifest['subjects'] if s.get('maskScene')]
    with bpy.data.libraries.load(str(historical / old_manifest['source']['blend']), link=False) as (_, destination):
        destination.scenes = old_scenes
    for subject in manifest['subjects']:
        sid = subject['id']
        old_subject = next(s for s in old_manifest['subjects'] if s['id'] == sid)
        historical_variant = next(v for v in old_subject['variants'] if v['id'] == 'faceted')
        prior = bpy.data.scenes[historical_variant['scene']]
        ENV.activate(prior)
        expected_geometry = ENV.mesh_snapshot(prior)
        expected_camera = ENV.camera_record(prior, subject)
        expected_root = ENV.matrix(bpy.data.objects[prior['studyRoot']].matrix_world)
        expected_lights = light_signature(prior)
        expected_materials = actual_materials(prior)
        entry = {'meshCount': len(expected_geometry), 'variants': {}}
        for variant in subject['variants']:
            scene = bpy.data.scenes[variant['scene']]
            ENV.activate(scene)
            actual_geometry = ENV.mesh_snapshot(scene)
            actual_camera = ENV.camera_record(scene, subject)
            actual_root = ENV.matrix(bpy.data.objects[scene['studyRoot']].matrix_world)
            actual_lights = light_signature(scene)
            grade = ENV.check_grade(scene)
            lights = COMMON.lighting(scene)
            materials = actual_materials(scene)
            info = {'geometryUVAndFaceAssignmentsUnchanged': actual_geometry == expected_geometry,
                    'geometrySHA256': ENV.geometry_hash(actual_geometry),
                    'rootUnchanged': actual_root == expected_root,
                    'cameraUnchanged': actual_camera == expected_camera, 'camera': actual_camera,
                    'lightsUnchanged': actual_lights == expected_lights, 'lights': lights,
                    'cardinalLightingSymmetry': COMMON.cardinal_symmetry(lights),
                    'grade': grade, 'materials': {}, 'phaseSamples': []}
            for field in ('geometryUVAndFaceAssignmentsUnchanged', 'rootUnchanged', 'cameraUnchanged', 'lightsUnchanged'):
                check(info[field], sid + '/' + variant['id'] + ': ' + field)
            check(info['geometrySHA256'] == variant['geometrySHA256'], sid + ': geometry manifest hash differs')
            check(info['cardinalLightingSymmetry']['passed'], sid + ': horizontal light symmetry differs')
            check(len(lights) == 5 and sorted(l['energy'] for l in lights) == [100,100,100,100,140], sid + ': selected lamp powers differ')
            check(grade['factor'] == 1.35 and grade['renderLayerOwners'] == [scene.name]
                  and grade['alphaBypassesGrade'], sid + ': grade, scene owner or alpha bypass differs')
            check(len(grade['actualChannelMath']) == 3 and all(n['operation'] == 'MULTIPLY_ADD'
                  and abs(n['scale']-1.35) < 1e-6 and abs(n['offset']+.175) < 1e-6 and n['clamped']
                  for n in grade['actualChannelMath']), sid + ': actual135 math differs')
            check([n.inputs['Strength'].default_value for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND'] == [0.], sid + ': ambient world energy differs')
            check(set(materials) == set(expected_materials), sid + ': material slot set differs')
            for key, material in materials.items():
                before = expected_materials[key]
                expected_kind = 'rail' if 'S33_FB_red' in before['material'] else 'wood' if any(
                    name in before['material'] for name in ('S33_wood', 'S33_FB_wood')) else 'unchanged'
                tuned = variant['id'] == 'faceted-tuned' and (expected_kind == 'rail'
                        or (expected_kind == 'wood' and sid == 'crate-wood'))
                if tuned:
                    target = [v * .42 for v in before['baseColor'][:3]] + [1] if expected_kind == 'wood' else recipe.linear_hex('#966B60')
                    valid = (close(material['baseColor'], target) and material['roughness'] == 1
                             and material['specular'] == 0 and material['normalizedGraph'] == before['normalizedGraph'])
                else:
                    target = before['baseColor']
                    valid = material['activeGraph'] == before['activeGraph']
                check(valid, sid + '/' + variant['id'] + ': unapproved material change ' + key)
                check(material['shader'] == 'BSDF_PRINCIPLED' and material['baseUsesApprovedLowerGraph']
                      and material['metallic'] == 0 and material['emission'] == 0 and not material['treeHasAction'],
                      sid + '/' + variant['id'] + ': incorrect active shader ' + key)
                info['materials'][key] = {k: v for k, v in material.items() if k not in ('activeGraph', 'normalizedGraph')}
                info['materials'][key].update(expectedKind=expected_kind, expectedBaseColor=target,
                                              exactlyApprovedChange=valid)
            for frame in range(25):
                recipe.phase(scene, -7 * frame / 24)
                samples = ENV.phases(scene)
                info['phaseSamples'].append({'frame': frame, 'materials': samples})
                expected_count = 0 if sid == 'crate-wood' else 3 if sid == 'belt-connected' else 1
                check(len(samples) == expected_count and all(len(values) == 1 and abs(values[0] + 7*frame/24) < 1e-6
                      for values in samples.values()), sid + ': phase count or synchronization differs at frame ' + str(frame))
            recipe.phase(scene, 0)
            entry['variants'][variant['id']] = info
        if subject.get('maskScene'):
            mask = bpy.data.scenes[subject['maskScene']]
            ENV.activate(mask)
            old_mask = bpy.data.scenes[old_subject['maskScene']]
            def mask_snapshot(sc):
                return sorted([{'vertices': [list(v.co) for v in o.data.vertices],
                                'polygons': [list(p.vertices) for p in o.data.polygons],
                                'materialIndices': [p.material_index for p in o.data.polygons]}
                               for o in sc.objects if o.type == 'MESH'], key=lambda item: json.dumps(item))
            mask_valid = mask_snapshot(mask) == mask_snapshot(old_mask)
            check(mask_valid and not mask.render.use_compositing and ENV.camera_record(mask, subject) == expected_camera,
                  sid + ': classification mask geometry, projection or grade differs')
            entry['mask'] = {'geometryAndClassesUnchanged': mask_valid, 'compositorDisabled': not mask.render.use_compositing,
                             'cameraUnchanged': ENV.camera_record(mask, subject) == expected_camera}
        report['subjects'][sid] = entry
    report['passed'] = not report['issues']
    output = HERE / 'audit-native.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'issues': report['issues']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    audit(args.study)
