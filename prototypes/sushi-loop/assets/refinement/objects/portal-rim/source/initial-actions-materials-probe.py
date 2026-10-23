import bpy
import hashlib
import json
import math
from pathlib import Path

BASE = Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
RAW = BASE / 'prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'
OUT = BASE / 'prototypes/sushi-loop/assets/refinement/objects/portal-rim/source/raw-initial-actions-materials.json'
COLLECTION = 'S33_PROP_portal_rim.002'
ROOT = 'portal_rim__root.002'

def value(v):
    if isinstance(v, (int, float, bool, str)):
        return v
    try:
        return list(v)
    except Exception:
        return str(v)

def curve(f):
    return {'data_path': f.data_path, 'array_index': f.array_index,
        'extrapolation': f.extrapolation,
        'keyframes': [{'co': list(k.co), 'interpolation': k.interpolation} for k in f.keyframe_points],
        'modifiers': [{'type': m.type} for m in f.modifiers]}

record = json.loads(bpy.data.objects[ROOT]['native_action_record'])
actions = []
for name in record['clips']['idle']:
    a = bpy.data.actions[name]
    entry = {'name': a.name, 'frame_range': list(a.frame_range), 'users': a.users, 'fake_user': a.use_fake_user,
        'slots': [{'identifier': s.identifier, 'target_id_type': s.target_id_type} for s in a.slots],
        'layers': []}
    for layer in a.layers:
        item = {'name': layer.name, 'strips': []}
        for strip in layer.strips:
            s = {'type': strip.type, 'channelbags': []}
            if hasattr(strip, 'channelbags'):
                for bag in strip.channelbags:
                    s['channelbags'].append({'slot_handle': bag.slot_handle, 'fcurves': [curve(f) for f in bag.fcurves]})
            item['strips'].append(s)
        entry['layers'].append(item)
    actions.append(entry)

objects = []
materials = {}
for o in bpy.data.collections[COLLECTION].all_objects:
    if o.type != 'MESH':
        continue
    item = {'name': o.name, 'modifiers': []}
    for m in o.modifiers:
        d = {'name': m.name, 'type': m.type}
        if m.type == 'BEVEL':
            d.update({'width': m.width, 'segments': m.segments, 'limit_method': m.limit_method, 'affect': m.affect})
        item['modifiers'].append(d)
    if 'ring' in o.name:
        item['local_z_bands'] = sorted({round(v.co.z, 7) for v in o.data.vertices})
        item['local_radial_bands'] = sorted({round(math.hypot(v.co.x, v.co.y), 6) for v in o.data.vertices})
        item['distinct_major_angles'] = len({round(math.atan2(v.co.y, v.co.x), 5) for v in o.data.vertices})
    objects.append(item)
    for slot in o.material_slots:
        m = slot.material
        if not m or m.name in materials:
            continue
        d = {'name': m.name, 'active_surface_links': [], 'node_details': []}
        for l in m.node_tree.links:
            if l.to_node.type == 'OUTPUT_MATERIAL' and l.to_socket.name == 'Surface':
                d['active_surface_links'].append({'node': l.from_node.name, 'type': l.from_node.bl_idname})
        for n in m.node_tree.nodes:
            nd = {'name': n.name, 'type': n.bl_idname,
                'inputs': [{'name': s.name, 'identifier': s.identifier, 'enabled': s.enabled, 'is_linked': s.is_linked, 'default_value': value(s.default_value)} for s in n.inputs if hasattr(s, 'default_value')]}
            for attr in ['operation', 'blend_type', 'interpolation_type', 'data_type', 'clamp', 'use_clamp']:
                if hasattr(n, attr):
                    nd[attr] = value(getattr(n, attr))
            if hasattr(n, 'color_ramp'):
                nd['ramp'] = {'interpolation': n.color_ramp.interpolation, 'elements': [{'position': e.position, 'color': list(e.color)} for e in n.color_ramp.elements]}
            d['node_details'].append(nd)
        materials[m.name] = d

payload = {'raw_source': str(RAW), 'source_sha256': hashlib.sha256(RAW.read_bytes()).hexdigest(), 'native_record': record,
    'actions': actions, 'geometry_details': objects, 'material_details': list(materials.values()),
    'scope': 'Read only own raw action, mesh primitive and material datablocks. No action application, geometry edit, render or model save.'}
OUT.write_text(json.dumps(payload, indent=2) + '\n')
print(json.dumps({'output': str(OUT), 'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(), 'actions': len(actions)}))
