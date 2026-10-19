"""Independent read-only audit of the saved environment-lighting study.

Run Blender --background STUDY/source/environment-lighting.blend --python THIS
 -- --study STUDY --production PRODUCTION --output REPORT.
Only REPORT is written. The live MCP scene and both source files stay untouched.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def matrix(value): return [[float(x) for x in row] for row in value]
def rounded(value):
    if isinstance(value, (float, int)): return round(float(value), 7)
    if isinstance(value, (list, tuple)): return [rounded(x) for x in value]
    return value


def activate(scene):
    bpy.context.window.scene = scene
    bpy.context.window.view_layer = scene.view_layers[0]
    scene.view_layers[0].update()


def socket_value(socket):
    if not hasattr(socket, 'default_value'): return None
    value = socket.default_value
    if isinstance(value, (bool, int, float, str)): return value
    try: return list(value)
    except TypeError: return str(value)


def lower_node(material):
    return next((n for n in material.node_tree.nodes
                 if n.type == 'MIX_RGB' and n.blend_type == 'MULTIPLY'
                 and n.inputs[2].is_linked
                 and n.inputs[2].links[0].from_node.type == 'VALTORGB'
                 and n.inputs[2].links[0].from_node.label == 'Dark lower half → bright crown'), None)


def graph_signature(node):
    """All upstream nodes/links, ignoring only the deliberately driven phase."""
    if node is None: return None
    pending = [node];seen = {};links = []
    while pending:
        current = pending.pop()
        if current.name in seen: continue
        value = {'type': current.type, 'label': current.label,
                 'operation': getattr(current, 'operation', None),
                 'blendType': getattr(current, 'blend_type', None),
                 'clamp': getattr(current, 'clamp', None),
                 'inputs': [socket_value(s) if not s.is_linked else '<linked>' for s in current.inputs]}
        if current.type == 'VALUE':
            value['value'] = '<study-driven-phase>' if current.label == 'Deck travel phase' else socket_value(current.outputs[0])
        if current.type == 'VALTORGB':
            value['ramp'] = {'interpolation': current.color_ramp.interpolation,
                             'elements': [[e.position, list(e.color)] for e in current.color_ramp.elements]}
        seen[current.name] = value
        for index, socket in enumerate(current.inputs):
            for link in socket.links:
                links.append([current.name, index, link.from_node.name, list(link.from_node.outputs).index(link.from_socket)])
                pending.append(link.from_node)
    return {'nodes': seen, 'links': sorted(links)}


def mesh_snapshot(scene):
    return {o['sourceAssetId'] + '::' + o['sourceObject']: {
        'vertices': [list(v.co) for v in o.data.vertices],
        'polygons': [list(p.vertices) for p in o.data.polygons],
        'polygonMaterials': [p.material_index for p in o.data.polygons],
        'uv': [list(uv.uv) for uv in o.data.uv_layers.active.data] if o.data.uv_layers.active else [],
        'matrix': matrix(o.matrix_world), 'sourceOffset': list(o['sourceOffset']),
    } for o in scene.objects if o.type == 'MESH' and o.get('sourceObject')}


def geometry_hash(objects):
    digest = hashlib.sha256()
    for key, obj in sorted(objects.items()):
        asset, name = key.split('::', 1)
        digest.update((asset + name).encode())
        digest.update(json.dumps(rounded(obj['vertices'])).encode())
        digest.update(json.dumps(obj['polygons']).encode())
        digest.update(json.dumps(rounded(obj['uv'])).encode())
    return digest.hexdigest()


def material_snapshot(scene):
    result = {}
    for obj in scene.objects:
        if obj.type != 'MESH' or not obj.get('sourceObject'): continue
        for index, slot in enumerate(obj.material_slots):
            material = slot.material
            if not material: continue
            output = next(n for n in material.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
            shader = output.inputs['Surface'].links[0].from_node
            lower = lower_node(material)
            phases = [n for n in material.node_tree.nodes if n.type == 'VALUE' and n.label == 'Deck travel phase']
            key = obj['sourceAssetId'] + '::' + obj['sourceObject'] + ':' + str(index)
            value = {'surfaceType': shader.type, 'lowerGraph': graph_signature(lower),
                     'phaseNodes': len(phases), 'copiedTreeHasAction': bool(material.node_tree.animation_data and material.node_tree.animation_data.action)}
            if shader.type == 'BSDF_PRINCIPLED':
                value.update(roughness=shader.inputs['Roughness'].default_value,
                             specular=shader.inputs['Specular IOR Level'].default_value,
                             metallic=shader.inputs['Metallic'].default_value,
                             emissionStrength=shader.inputs['Emission Strength'].default_value,
                             usesLowerGraphDirectly=shader.inputs['Base Color'].is_linked and shader.inputs['Base Color'].links[0].from_node == lower)
            result[key] = value
    return result


def phases(scene):
    materials = {slot.material for obj in scene.objects if obj.type == 'MESH'
                 for slot in obj.material_slots if slot.material}
    return {m.name: [n.outputs[0].default_value for n in m.node_tree.nodes
                    if n.type == 'VALUE' and n.label == 'Deck travel phase']
            for m in materials if any(n.label == 'Deck travel phase' for n in m.node_tree.nodes)}


def camera_record(scene, subject):
    def project(point):
        value = world_to_camera_view(scene, scene.camera, Vector(point))
        return [value.x * subject['frame'][0], (1-value.y) * subject['frame'][1]]
    root = project((0, 0, 0))
    def delta(point): return [a-b for a, b in zip(project(point), root)]
    return {'worldMatrix': matrix(scene.camera.matrix_world), 'type': scene.camera.data.type,
            'orthoScale': scene.camera.data.ortho_scale, 'shift': [scene.camera.data.shift_x, scene.camera.data.shift_y],
            'resolution': [scene.render.resolution_x, scene.render.resolution_y],
            'pixelAspect': [scene.render.pixel_aspect_x, scene.render.pixel_aspect_y],
            'root': root, 'unitX': delta((1, 0, 0)), 'unitDepth': delta((0, -1, 0)), 'unitHeight': delta((0, 0, 1))}


def check_grade(scene):
    graph = scene.compositing_node_group
    alpha = next(n for n in graph.nodes if n.bl_idname == 'CompositorNodeCombineColor').inputs['Alpha'].links[0]
    math_nodes = [n for n in graph.nodes if n.type == 'MATH']
    return {'factor': graph.get('contrastFactor'),
            'renderLayerOwners': [n.scene.name if n.scene else None for n in graph.nodes if n.type == 'R_LAYERS'],
            'alphaBypassesGrade': alpha.from_node.type == 'R_LAYERS' and alpha.from_socket.name == 'Alpha',
            'actualChannelMath': [{'operation': n.operation, 'scale': n.inputs[1].default_value,
                                   'offset': n.inputs[2].default_value, 'clamped': n.use_clamp} for n in math_nodes]}


def audit(study, production, output):
    manifest = json.loads((study / 'manifest.json').read_text())
    common = load('s33_environment_common_audit', Path(__file__).parent.parent / 'character-lighting-study/audit_saved_study.py')
    recipe = load('s33_environment_recipe_audit', study / manifest['source']['recipe'])
    report = {'studySHA256': sha(bpy.data.filepath), 'recipeSHA256': sha(study / manifest['source']['recipe']),
              'productionSHA256': sha(production / 'source/blender/sushi-loop-world-library.blend'),
              'subjects': {}, 'issues': [], 'approval': 'Lighting experiment; no visual choice established by this audit.'}
    all_baselines = {};base_materials = {}
    for subject in manifest['subjects']:
        baseline = bpy.data.scenes[subject['variants'][0]['scene']];activate(baseline)
        objects = mesh_snapshot(baseline);base_root = matrix(bpy.data.objects[baseline['studyRoot']].matrix_world)
        base_camera = camera_record(baseline, subject);materials = material_snapshot(baseline)
        all_baselines[subject['id']] = objects;base_materials[subject['id']] = materials
        subject_report = {'meshCount': len(objects), 'variants': {}}
        for item in subject['variants']:
            scene = bpy.data.scenes[item['scene']];activate(scene)
            actual = mesh_snapshot(scene);actual_materials = material_snapshot(scene)
            lights = common.lighting(scene);grade = check_grade(scene)
            settings = item['settings'];actual_camera = camera_record(scene, subject)
            entry = {'geometryAndUVIdenticalToBaseline': actual == objects,
                     'geometrySHA256': geometry_hash(actual),
                     'rootIdenticalToBaseline': matrix(bpy.data.objects[scene['studyRoot']].matrix_world) == base_root,
                     'cameraIdenticalToBaseline': actual_camera == base_camera,
                     'camera': actual_camera, 'grade': grade,
                     'worldStrength': [n.inputs['Strength'].default_value for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND'],
                     'lights': lights, 'cardinalSymmetry': common.cardinal_symmetry(lights),
                     'lowerColorAndPhaseGraphsIdenticalToBaseline': all(value['lowerGraph'] == materials[key]['lowerGraph'] for key, value in actual_materials.items()),
                     'materials': {key: {k:v for k,v in value.items() if k != 'lowerGraph'} for key, value in actual_materials.items()},
                     'phaseSamples': []}
            for frame in range(25):
                recipe.phase(scene, -7 * frame / 24)
                values = phases(scene)
                entry['phaseSamples'].append({'frameZeroBased': frame, 'expected': -7 * frame / 24, 'materials': values})
                for name, samples in values.items():
                    if len(samples) != 1 or any(abs(value + 7 * frame / 24) > 1e-6 for value in samples):
                        report['issues'].append(subject['id'] + '/' + item['id'] + ': incorrect phase at ' + str(frame) + ' ' + name)
            recipe.phase(scene, 0)
            for key in ('geometryAndUVIdenticalToBaseline', 'rootIdenticalToBaseline', 'cameraIdenticalToBaseline', 'lowerColorAndPhaseGraphsIdenticalToBaseline'):
                if not entry[key]: report['issues'].append(subject['id'] + '/' + item['id'] + ': ' + key)
            if entry['geometrySHA256'] != item['geometrySHA256']: report['issues'].append(subject['id'] + '/' + item['id'] + ': geometry manifest mismatch')
            if not entry['cardinalSymmetry']['passed']: report['issues'].append(subject['id'] + '/' + item['id'] + ': cardinal light asymmetry')
            if grade['factor'] != 1.35 or grade['renderLayerOwners'] != [scene.name] or not grade['alphaBypassesGrade']:
                report['issues'].append(subject['id'] + '/' + item['id'] + ': incorrect grade/alpha/scene ownership')
            if len(grade['actualChannelMath']) != 3 or any(n['operation'] != 'MULTIPLY_ADD' or abs(n['scale']-1.35)>1e-6 or abs(n['offset']+.175)>1e-6 or not n['clamped'] for n in grade['actualChannelMath']):
                report['issues'].append(subject['id'] + '/' + item['id'] + ': actual contrast math changed')
            expected_axes = {'root': subject['root'], 'unitX': [128,0], 'unitDepth': [0,128], 'unitHeight': [0,-89.6]}
            if any(max(abs(a-b) for a,b in zip(actual_camera[key], value)) > .001 for key,value in expected_axes.items()):
                report['issues'].append(subject['id'] + '/' + item['id'] + ': environment 70% calibration changed')
            if entry['worldStrength'] != [0.]: report['issues'].append(subject['id'] + '/' + item['id'] + ': nonzero world')
            if item['id'] != 'baseline':
                if len(lights) != 5 or sorted(l['energy'] for l in lights) != sorted([settings['topWatts']] + [100]*4):
                    report['issues'].append(subject['id'] + '/' + item['id'] + ': actual lamp power/count differs')
                for key, material in actual_materials.items():
                    if (material['surfaceType'] != 'BSDF_PRINCIPLED' or material.get('emissionStrength') != 0
                            or not material.get('usesLowerGraphDirectly') or abs(material.get('roughness',0)-.85)>1e-6
                            or abs(material.get('specular',0)-.03)>1e-6 or material.get('metallic') != 0):
                        report['issues'].append(subject['id'] + '/' + item['id'] + ': candidate material mismatch ' + key)
            elif lights or any(m['surfaceType'] != 'EMISSION' for m in actual_materials.values()):
                report['issues'].append(subject['id'] + ': baseline surface or lighting changed')
            if any(m['copiedTreeHasAction'] for m in actual_materials.values()):
                report['issues'].append(subject['id'] + '/' + item['id'] + ': copied tree retains an action')
            subject_report['variants'][item['id']] = entry
        if subject.get('maskScene'):
            scene = bpy.data.scenes[subject['maskScene']];activate(scene)
            errors=[];counts={str(i):0 for i in range(4)}
            for obj in scene.objects:
                if obj.type != 'MESH': continue
                rail = 'rail' in obj.name;deck = 'deck' in obj.name
                for polygon in obj.data.polygons:
                    selected = subject['id'] == 'crate-wood' or rail
                    expected = 1 if selected and polygon.normal.z >= .65 else 2 if selected and polygon.normal.z <= .35 else 3 if deck else 0
                    counts[str(expected)] += 1
                    if polygon.material_index != expected: errors.append(obj.name + ': incorrect material/normal class')
            if scene.render.use_compositing: errors.append('Classification mask uses grading')
            subject_report['mask']={'counts':counts,'issues':errors,'cameraMatchesColor':camera_record(scene,subject)==base_camera}
            report['issues'] += [subject['id'] + ': ' + error for error in errors]
        report['subjects'][subject['id']] = subject_report
    # Evaluate the authoritative saved production in this separate CLI process.
    original = production / 'source/blender/sushi-loop-world-library.blend'
    bpy.ops.wm.open_mainfile(filepath=str(original))
    base = production / 'source/blender';worker = load('s33_env_native_worker',base/'capture_worker.py')
    native = load('s33_env_native_actions',base/'native_actions.py');scene = worker.native_scene()
    original_assets={};original_mats={};flows={}
    native_ids={p['id'] for subject in manifest['subjects'] for p in subject['placements']}
    for aid in sorted(native_ids):
        asset,rig,_ = worker.reconstruct(aid, production/'source/native-records',{},scene)
        worker.show_only(scene,asset);native.apply_clip(asset,rig,next(iter(rig['clips'])),frame=1,direction='S',scene=scene)
        depsgraph=bpy.context.evaluated_depsgraph_get();objects={};mats={}
        for obj in asset['collection'].all_objects:
            if obj.type!='MESH' or obj.hide_render:continue
            evaluated=obj.evaluated_get(depsgraph);mesh=evaluated.to_mesh()
            try:
                objects[obj.name]={'vertices':[list(evaluated.matrix_world@v.co) for v in mesh.vertices],
                                   'polygons':[list(p.vertices) for p in mesh.polygons],
                                   'polygonMaterials':[p.material_index for p in mesh.polygons],
                                   'uv':[list(uv.uv) for uv in mesh.uv_layers.active.data] if mesh.uv_layers.active else []}
            finally:evaluated.to_mesh_clear()
            for index,slot in enumerate(obj.material_slots):
                if slot.material:mats[obj.name+':'+str(index)]=graph_signature(lower_node(slot.material))
        original_assets[aid]=objects;original_mats[aid]=mats;flows[aid]=asset.get('flow')
    for subject in manifest['subjects']:
        expected={};expected_mats={}
        for placement in subject['placements']:
            aid=placement['id'];offset=placement['offset']
            for name,obj in original_assets[aid].items():
                expected[aid+'::'+name]={**obj,'vertices':[[v[i]+offset[i] for i in range(3)] for v in obj['vertices']]}
            for key,value in original_mats[aid].items():expected_mats[aid+'::'+key]=value
        actual=all_baselines[subject['id']];errors=[];maximum=0.;uv_maximum=0.
        if set(expected)!=set(actual):errors.append('Source mesh identity set differs')
        for key in set(expected)&set(actual):
            for field in ('polygons','polygonMaterials'):
                if expected[key][field]!=actual[key][field]:errors.append(key+': '+field+' differs')
            old_uv,new_uv=expected[key]['uv'],actual[key]['uv']
            if len(old_uv)!=len(new_uv):errors.append(key+': UV loop count differs')
            else:
                uv_delta=max((abs(a-b) for old,new in zip(old_uv,new_uv) for a,b in zip(old,new)),default=0.)
                uv_maximum=max(uv_maximum,uv_delta)
                if uv_delta>2e-6:errors.append(key+': native UV delta '+str(uv_delta))
            if len(expected[key]['vertices'])!=len(actual[key]['vertices']):errors.append(key+': vertex count differs');continue
            delta=max((abs(a-b) for old,new in zip(expected[key]['vertices'],actual[key]['vertices']) for a,b in zip(old,new)),default=0.)
            maximum=max(maximum,delta)
            if delta>2e-6:errors.append(key+': native vertex delta '+str(delta))
        for key,material in base_materials[subject['id']].items():
            if material['lowerGraph']!=expected_mats.get(key):errors.append(key+': native lower/color/UV phase graph differs')
        report['subjects'][subject['id']]['originalProduction']={'nativeIds':[p['id'] for p in subject['placements']],
            'maximumVertexDeltaCells':maximum,'maximumUVDelta':uv_maximum,'geometryUVAndColorGraphsMatch':not errors,'issues':errors}
        report['issues'] += [subject['id']+': '+error for error in errors]
    positions={p['id']:p['offset'] for s in manifest['subjects'] if s['id']=='belt-connected' for p in s['placements']}
    vectors={'N':[0,.5,0],'E':[.5,0,0],'S':[0,-.5,0],'W':[-.5,0,0]}
    def port(aid,kind):
        direction=flows[aid][kind]
        return [positions[aid][i]+vectors[direction][i] for i in range(2)]+[flows[aid]['deckHeight']]
    seam_pairs=[('belt-straight-s','belt-corner-n-e'),('belt-corner-n-e','belt-straight-e')]
    report['connectedPorts']=[{'from':a,'to':b,'outgoing':port(a,'outgoing'),'incoming':port(b,'incoming'),
                               'distanceCells':(Vector(port(a,'outgoing'))-Vector(port(b,'incoming'))).length} for a,b in seam_pairs]
    if any(p['distanceCells']>1e-6 for p in report['connectedPorts']):report['issues'].append('Connected conveyor ports do not coincide')
    for field,actual in (('sha256',report['studySHA256']),('recipeSHA256',report['recipeSHA256']),('productionBlendSHA256',report['productionSHA256'])):
        if manifest['source'][field]!=actual:report['issues'].append('Source hash mismatch '+field)
    if sha(study/manifest['source']['sharedLightingRecipe'])!=manifest['source']['sharedLightingRecipeSHA256']:
        report['issues'].append('Shared Noor lighting recipe hash mismatch')
    report['passed']=not report['issues'];output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'issues':report['issues'],'production':[s['originalProduction'] for s in report['subjects'].values()]}),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--study',type=Path,required=True)
    parser.add_argument('--production',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    audit(args.study,args.production,args.output)
