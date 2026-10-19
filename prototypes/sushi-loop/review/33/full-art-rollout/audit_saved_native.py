"""Read-only audit of a frozen issue-33 native project.

Run Blender --background PROJECT --python THIS -- --export EXPORT --output JSON.
The audit changes evaluated poses in memory only; it never saves the project.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import bpy


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def main(export, output, ids=None):
    repo = Path(__file__).resolve().parents[5]
    base = repo / 'prototypes/sushi-loop/assets/production/source/blender'
    native = module('s33_independent_native_audit', base / 'native_actions.py')
    worker = module('s33_independent_worker_audit', base / 'capture_worker.py')
    scene = worker.native_scene()
    report = {'project': str(Path(bpy.data.filepath)), 'projectSHA256': hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
              'blenderVersion': bpy.app.version_string, 'scenes': [s.name for s in bpy.data.scenes],
              'issues': [], 'assets': {}, 'materials': {}}
    graph = scene.compositing_node_group
    report['compositor'] = {'enabled': scene.render.use_compositing,
                            'group': graph.name if graph else None,
                            'contrast': graph.get('contrastFactor') if graph else None,
                            'renderLayersScene': [n.scene.name if n.scene else None for n in graph.nodes if n.type == 'R_LAYERS'] if graph else []}
    if not graph or graph.get('contrastFactor') != 1.35:
        report['issues'].append('Saved native scene lacks approved135 compositor')
    elif any(n.scene not in (None, scene) for n in graph.nodes if n.type == 'R_LAYERS'):
        report['issues'].append('Compositor renders a different scene')
    if graph:
        layers = next((n for n in graph.nodes if n.type == 'R_LAYERS'), None)
        combines = [n for n in graph.nodes if n.bl_idname == 'CompositorNodeCombineColor']
        alpha_bypass = len(combines) == 1 and combines[0].inputs['Alpha'].is_linked and combines[0].inputs['Alpha'].links[0].from_node == layers and combines[0].inputs['Alpha'].links[0].from_socket.name == 'Alpha'
        report['compositor']['alphaBypassesRGBGrade'] = bool(alpha_bypass)
        if not alpha_bypass: report['issues'].append('Compositor alpha does not bypass RGB grade')
    report['lights'] = [{'name': o.name, 'energy': o.data.energy} for o in scene.objects if o.type == 'LIGHT']
    if any(o.data.energy != 0 for o in scene.objects if o.type == 'LIGHT'):
        report['issues'].append('Nonzero native directional light')
    report['worldStrength'] = [n.inputs['Strength'].default_value for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND'] if scene.world else []
    if any(report['worldStrength']): report['issues'].append('Nonzero world strength')
    source = export / 'source'
    records = json.loads((source / 'native-actions/library-actions.json').read_text())['assets']
    directions = {'S': 0., 'E': math.pi / 2, 'N': math.pi, 'W': -math.pi / 2}
    for aid in records:
        if ids and aid not in ids: continue
        asset, rig, _ = worker.reconstruct(aid, source, records, scene)
        worker.show_only(scene, asset)
        used = {slot.material for obj in asset['collection'].all_objects if obj.type == 'MESH' for slot in obj.material_slots if slot.material}
        surfaces = []
        for material in used:
            if material.name not in report['materials']:
                outputs = [n for n in material.node_tree.nodes if n.type == 'OUTPUT_MATERIAL']
                types = [n.inputs['Surface'].links[0].from_node.type if n.inputs['Surface'].is_linked else 'NONE' for n in outputs]
                report['materials'][material.name] = {'surfaceTypes': types, 'approvedRevision': material.get('s33ArtRevision'), 'lowerTone': material.get('lowerTone')}
            surfaces += report['materials'][material.name]['surfaceTypes']
        bad = [t for t in surfaces if t not in ('EMISSION', 'MIX_SHADER')]
        if bad: report['issues'].append(aid + ': lit/nonemission surfaces ' + str(sorted(set(bad))))
        camera = json.loads((source / aid / 'camera.json').read_text())
        scale = camera['captureScale']
        axes = camera['calibration']
        if asset['projection'] != 'character-orthographic':
            if abs(axes['unitHeight'][1] / scale + 89.6) > .001 or abs(axes['unitDepth'][1] / scale - 128) > .001:
                report['issues'].append(aid + ': wrong70 projection')
        poses = []
        for clip, recipe in rig['clips'].items():
            count = int(recipe['frames'])
            if count != 1 and count < 6: report['issues'].append(aid + '/' + clip + ': fewer than6 authored frames')
            # Entire temporal range is checked for designated short/tall decor;
            # other objects retain the three representative unique samples.
            frames = range(count) if aid.startswith('decor-') or aid in ('boulder-underwater', 'column-broken', 'garbage-car', 'dock-cover') else sorted({0, count // 2, count - 1})
            for index in frames:
                for facing in asset.get('directions', directions):
                    native.apply_clip(asset, rig, clip, frame=index + 1, direction=facing, scene=scene)
                    with worker.capture_footing(asset):
                        depsgraph = bpy.context.evaluated_depsgraph_get()
                        points = []
                        for obj in asset['collection'].all_objects:
                            if obj.type != 'MESH' or obj.hide_render: continue
                            evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh()
                            try: points.extend(evaluated.matrix_world @ v.co for v in mesh.vertices)
                            finally: evaluated.to_mesh_clear()
                        if not points: continue
                        xs = [p.x * axes['unitX'][0] / scale for p in points]
                        ys = [(-p.y * axes['unitDepth'][1] + p.z * axes['unitHeight'][1]) / scale for p in points]
                        fw, fh = asset['frame']; rx, ry = asset['anchor']
                        bounds = [min(xs) + rx, min(ys) + ry, max(xs) + rx, max(ys) + ry]
                        # Opaque tiled panels intentionally overrun their image
                        # edges slightly to avoid antialiased clear seams.
                        tolerance = .5 if aid.startswith('floor-') else .1
                        if bounds[0] < -tolerance or bounds[1] < -tolerance or bounds[2] > fw + tolerance or bounds[3] > fh + tolerance:
                            report['issues'].append(aid + '/' + clip + '/' + facing + '/' + str(index) + ': geometry outside fixed frame ' + str(bounds))
                        poses.append({'clip': clip, 'index': index, 'direction': facing, 'projectedHeightTiles': (max(ys) - min(ys)) / 128, 'frameBounds': bounds})
        highest = max(poses, key=lambda x: x['projectedHeightTiles']) if poses else None
        if aid in ('boulder-underwater', 'column-broken', 'decor-background-rock', 'decor-foreground-rock', 'decor-foreground-coral', 'decor-midground-coral', 'decor-kelp', 'decor-ruin-fragment') and highest and highest['projectedHeightTiles'] > 3.001:
            report['issues'].append(aid + ': projected silhouette exceeds3tiles')
        report['assets'][aid] = {'materials': len(used), 'surfaceTypes': sorted(set(surfaces)), 'posesMeasured': len(poses), 'highest': highest}
        print('AUDIT_NATIVE ' + aid, flush=True)
    report['passed'] = not report['issues']
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'assets': len(report['assets']), 'issues': report['issues'], 'output': str(output)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ids', nargs='+')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    main(args.export, args.output, args.ids)
