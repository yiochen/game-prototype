"""Headless structural verification of the MCP-authored native meal derivative."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import bpy

HERE = Path(__file__).resolve().parent
PRODUCTION = HERE.parents[2]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

native = load('s10_audit_native', PRODUCTION / 'source/blender/native_actions.py')
author = load('s10_audit_author', HERE / 'author_chef.py')
proof = json.loads((HERE / 'authorship.json').read_text())
scene = next(scene for scene in bpy.data.scenes if scene.get('meal_variants'))
bpy.context.window.scene = scene
bpy.context.window.view_layer = scene.view_layers[0]
objects = {obj.name.removeprefix('S11 cucumber '): obj for obj in scene.objects if obj.name.startswith('S11 cucumber ')}
assert author.body_hash(objects) == proof['bodyGeometry'], 'Native body mesh/bone rest geometry differs'
checks = []
samples = 0
for aid in author.IDS:
    record = json.loads((HERE / 'export/source' / aid / 'rig.json').read_text())
    root = bpy.data.objects[record['groundRootObject']]
    collection = next(c for c in scene.collection.children if root in list(c.all_objects))
    asset = {'root': root, 'collection': collection}
    plane = bpy.data.objects[proof['edits'][aid]['foodPlane']]
    image = next(node for node in plane.data.materials[0].node_tree.nodes if node.type == 'TEX_IMAGE').image
    assert image.packed_file and hashlib.sha256(bytes(image.packed_file.data)).hexdigest() == proof['approvedFood']['sha256'], 'Held food is not the exact original ImageGen cucumber'
    expected = {(item['clip'], item['owner']): item['sha256'] for item in proof['edits'][aid]['unchangedActions']}
    for clip, clip_record in record['clips'].items():
        for target in clip_record['actions']:
            if (clip, target['ownerName']) in expected:
                assert author.action_hash(native, bpy.data.actions[target['action']]) == expected[(clip, target['ownerName'])], 'Native body/attachment action changed'
        for direction in ['N', 'E', 'S', 'W']:
            for frame in range(1, 13):
                native.apply_clip(asset, record, clip, frame=frame, direction=direction, scene=scene)
                target = next(target for target in clip_record['actions'] if target['ownerName'] == plane.name)
                visibility = next(curve for curve in native._fcurves(bpy.data.actions[target['action']]) if curve.data_path == 'hide_render')
                assert plane.hide_render == bool(round(visibility.evaluate(frame))), 'Held cucumber visibility differs from native load handoff'
                assert root.location.length < 1e-8 and max(abs(value - 1.25) for value in root.scale) < 1e-7, 'Root position or C125 anatomy scale changed'
                samples += 1
        checks.append({'asset': aid, 'clip': clip, 'foodVisibilityPreserved': True, 'bodyAndAttachmentActionsUnchanged': True})
result = {'passed': True, 'sourceBlendSha256': hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(), 'bodyGeometryUnchanged': True, 'approvedCucumberPackedBytesMatch': True, 'poseFacingSamples': samples, 'clips': checks}
(HERE / 'native-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print('CHEF_CUCUMBER_NATIVE_AUDIT ' + json.dumps(result))
