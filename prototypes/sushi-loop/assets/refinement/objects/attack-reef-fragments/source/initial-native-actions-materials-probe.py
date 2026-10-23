"""Read only own unassigned saved actions and own shader settings; no render/save."""
import bpy
import json
from pathlib import Path

COLLECTION = "S33_CFX_attack-reef-fragments.001"
ROOT = "attack-reef-fragments__ground_root.001"
OUTPUT = Path(__file__).with_name("initial-native-actions-materials-probe.json")

def value(v):
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    try:
        return [value(x) for x in v]
    except TypeError:
        return str(v)

def curve(fc):
    return {"data_path": fc.data_path, "array_index": fc.array_index,
            "keyframes": [{"co": value(k.co), "interpolation": k.interpolation,
                           "handle_left": value(k.handle_left), "handle_right": value(k.handle_right)}
                          for k in fc.keyframe_points],
            "modifiers": [m.type for m in fc.modifiers]}

root = bpy.data.objects[ROOT]
record = json.loads(root["native_action_record"])
names = sorted({name for clip in record["clips"].values() for name in clip})
actions = []
for name in names:
    a = bpy.data.actions.get(name)
    if a is None:
        actions.append({"name": name, "present": False})
        continue
    layers = []
    for layer in a.layers:
        strips = []
        for strip in layer.strips:
            bags = []
            for bag in strip.channelbags:
                bags.append({"slot_handle": bag.slot_handle, "curves": [curve(fc) for fc in bag.fcurves]})
            strips.append({"type": strip.type, "channelbags": bags})
        layers.append({"name": layer.name, "strips": strips})
    legacy = []
    try:
        legacy = [curve(fc) for fc in a.fcurves]
    except (AttributeError, RuntimeError):
        pass
    actions.append({"name": name, "present": True, "users": a.users,
                    "use_fake_user": a.use_fake_user, "frame_range": value(a.frame_range),
                    "slots": [{"identifier": s.identifier, "handle": s.handle, "target_id_type": s.target_id_type}
                              for s in a.slots],
                    "legacy_curves": legacy, "layers": layers})

materials = {}
for o in bpy.data.collections[COLLECTION].all_objects:
    for slot in o.material_slots:
        m = slot.material
        if m is None or m.name in materials:
            continue
        nodes = []
        for n in m.node_tree.nodes:
            data = {"name": n.name, "type": n.bl_idname,
                    "input_sockets": [{"name": s.name, "identifier": s.identifier, "linked": s.is_linked,
                                       "default": value(s.default_value)} for s in n.inputs
                                      if hasattr(s, "default_value")]}
            for attr in ("operation", "blend_type", "data_type", "interpolation_type", "clamp", "use_clamp"):
                if hasattr(n, attr):
                    data[attr] = value(getattr(n, attr))
            if hasattr(n, "color_ramp"):
                ramp = n.color_ramp
                data["color_ramp"] = {"interpolation": ramp.interpolation, "color_mode": ramp.color_mode,
                                      "hue_interpolation": ramp.hue_interpolation,
                                      "elements": [{"position": e.position, "color": value(e.color)} for e in ramp.elements]}
            nodes.append(data)
        materials[m.name] = nodes

report = {"scope": "initial-only own raw saved action and material data; no model/capture edits",
          "source_path": bpy.data.filepath, "blender_version": bpy.app.version_string,
          "native_action_record": record, "actions": actions, "materials": materials,
          "important_distinction": "Own mesh objects have no assigned active action at saved frame 4; saved actions below are raw library datablocks referenced by the own root property."}
payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
assert len(payload.encode()) < 100_000_000
with OUTPUT.open("x") as f:
    f.write(payload)
print("INITIAL_ONLY_ACTIONS_MATERIALS_PROBE_SAVED", str(OUTPUT), len(actions), "recorded actions")
