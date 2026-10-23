import bpy
import json
import hashlib
from pathlib import Path

SOURCE = Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend')
EXPECTED = 'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
assert Path(bpy.data.filepath) == SOURCE
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
root = bpy.data.objects['creature-eel__ground_root.003']
arm = bpy.data.objects['creature-eel__armature.003']
body = bpy.data.objects['creature-eel__continuous_body.003']
coll = bpy.data.collections['S33_CFX_creature-eel.003']
record = json.loads(root['native_action_record'])
assert record['assetId'] == 'creature-eel'
def matrix(m):
    return [list(r) for r in m]
def bones():
    return [{'name': b.name, 'rotation_mode': b.rotation_mode,
             'rotation_euler': list(b.rotation_euler), 'rotation_quaternion': list(b.rotation_quaternion),
             'location': list(b.location), 'scale': list(b.scale),
             'matrix_basis': matrix(b.matrix_basis)} for b in arm.pose.bones]
def enable(layer):
    found = layer.collection == coll
    for child in layer.children:
        found = enable(child) or found
    if found:
        layer.exclude = False
        layer.hide_viewport = False
        layer.collection.hide_viewport = False
    return found
assert enable(bpy.context.view_layer.layer_collection)
for o in coll.all_objects:
    o.hide_viewport = False
    o.hide_render = False
    o.hide_set(False)
bpy.context.view_layer.update()
saved_pose = bones()
actions = []
for clip, names in record['clips'].items():
    for name in names:
        a = bpy.data.actions.get(name)
        assert a is not None, name
        curves = []
        for layer in a.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for f in bag.fcurves:
                        curves.append({'slot_handle': bag.slot_handle, 'data_path': f.data_path,
                                       'array_index': f.array_index,
                                       'keyframes': [{'co': list(k.co), 'interpolation': k.interpolation}
                                                     for k in f.keyframe_points]})
        actions.append({'clip': clip, 'name': name, 'frame_range': list(a.frame_range),
                        'slots': [{'identifier': s.identifier, 'handle': s.handle,
                                   'target_id_type': s.target_id_type} for s in a.slots],
                        'fcurves': curves})

# Native action evaluation in memory only: exact saved action slots, no bone mode
# corrections or geometry changes. This tests what the raw saved project does.
samples = []
for item in actions:
    a = bpy.data.actions[item['name']]
    arm.animation_data_create()
    arm.animation_data.action = a
    if len(a.slots) == 1:
        arm.animation_data.action_slot = a.slots[0]
    for frame in [1, 4, 12]:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        ev = body.evaluated_get(dg)
        me = ev.to_mesh()
        coords = [ev.matrix_world @ v.co for v in me.vertices]
        bb = {'world_min': [min(v[i] for v in coords) for i in range(3)],
              'world_max': [max(v[i] for v in coords) for i in range(3)]}
        ev.to_mesh_clear()
        ear = arm.evaluated_get(dg)
        samples.append({'clip': item['clip'], 'frame': frame,
                        'root_location': list(root.location), 'root_rotation_euler': list(root.rotation_euler),
                        'body_bounds': bb, 'pose_properties': bones(),
                        'evaluated_bones': [{'name': b.name, 'head_world': list(ear.matrix_world @ b.head),
                                             'tail_world': list(ear.matrix_world @ b.tail),
                                             'matrix': matrix(b.matrix)} for b in ear.pose.bones]})

result = {'scope': 'Untouched raw eel BODY actions/rig inspection. Memory-only exact native action assignment and frames 1,4,12. No mode corrections, model edits, save, or render.',
          'source_path': str(SOURCE), 'source_sha256': EXPECTED,
          'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'blender_version': bpy.app.version_string, 'armature_pose_position': arm.data.pose_position,
          'saved_bone_pose_properties': saved_pose, 'native_action_record': record,
          'root_socket_properties': json.loads(root['sockets']),
          'actions': actions, 'samples': samples}
output = Path(__file__).with_suffix('.json')
output.write_text(json.dumps(result, indent=2) + '\n')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
print(json.dumps({'output': str(output), 'actions': len(actions), 'samples': len(samples),
                  'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))
