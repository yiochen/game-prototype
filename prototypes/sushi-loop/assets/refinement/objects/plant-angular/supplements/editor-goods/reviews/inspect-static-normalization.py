import bpy
import hashlib
import json
from pathlib import Path

output = Path(__file__).resolve().parent
scene = bpy.context.scene
source = Path(bpy.data.filepath)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def evaluated_meshes():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    result = {}
    for obj in scene.objects:
        if obj.type != 'MESH':
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        vertices = [list(evaluated.matrix_world @ vertex.co) for vertex in mesh.vertices]
        result[obj.name] = {"sha256": digest(vertices), "vertices": len(vertices)}
        evaluated.to_mesh_clear()
    return result

record = {"sourceSHA256": hashlib.sha256(source.read_bytes()).hexdigest(), "frameBefore": scene.frame_current, "actions": [], "before": [], "after": []}
record['evaluatedBefore'] = evaluated_meshes()
for action in bpy.data.actions:
    record['actions'].append({"name": action.name, "slots": [slot.identifier for slot in action.slots]})
for obj in scene.objects:
    if obj.type != 'MESH' or not obj.data.shape_keys:
        continue
    key = obj.data.shape_keys
    current = key.animation_data.action if key.animation_data else None
    record['before'].append({"owner": obj.name, "key": key.name, "action": current.name if current else None, "values": {kb.name: kb.value for kb in key.key_blocks}})
    suffix = obj.name.rsplit('_', 1)[1]
    name = f'WARM_NATIVE__plant-angular__static__leaf_{suffix}'
    action = bpy.data.actions.get(name)
    if action is None:
        raise RuntimeError(f'Missing native static action: {name}')
    key.animation_data_create()
    key.animation_data.action = action
    key.animation_data.action_slot = action.slots[0]
scene.frame_set(1)
bpy.context.view_layer.update()
for obj in scene.objects:
    if obj.type != 'MESH' or not obj.data.shape_keys:
        continue
    key = obj.data.shape_keys
    record['after'].append({"owner": obj.name, "key": key.name, "action": key.animation_data.action.name, "slot": key.animation_data.action_slot.identifier, "values": {kb.name: kb.value for kb in key.key_blocks}})
record['evaluatedStatic'] = evaluated_meshes()
record['allStaticKeyValuesZero'] = all(all(value == 0 for key, value in owner['values'].items() if key != 'Basis') for owner in record['after'])
record['rootMatrix'] = [list(row) for row in bpy.data.objects['plant-angular__root'].matrix_world]
record['frameAfter'] = scene.frame_current
(output / 'static-normalization-inspection.json').write_text(json.dumps(record, indent=2) + '\n')
scene.render.filepath = str(output / 'approved-source-static-view.png')
bpy.ops.render.render(write_still=True)
print('STATIC_NORMALIZATION_INSPECTED', len(record['after']), record['allStaticKeyValuesZero'])
