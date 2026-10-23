import bpy, hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
P = Path(__file__).resolve().parents[1]
S = Path(bpy.data.filepath)
before = hashlib.sha256(S.read_bytes()).hexdigest()
assert before == '7e32d44911b1fd044fe7f64ef6033f9cfccd5d0ec1c23fc9a46c4497bbb63ae7'
coll = bpy.data.collections['S33_CFX_creature-fish.001']
arm = bpy.data.objects['creature-fish__armature.001']
def curves(action):
    seen = set()
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    if curve.as_pointer() not in seen:
                        seen.add(curve.as_pointer())
                        yield curve
def value(v):
    if isinstance(v, (int, float, str, bool)): return v
    try: return list(v)
    except TypeError: return str(v)
actions = []
for a in sorted(bpy.data.actions, key=lambda a:a.name):
    cs = list(curves(a))
    actions.append({'action':a.name, 'fakeUser':a.use_fake_user,
                    'range':list(a.frame_range),
                    'curves':[{'dataPath':c.data_path, 'arrayIndex':c.array_index,
                               'keyCount':len(c.keyframe_points),
                               'samples':{str(f):c.evaluate(f) for f in [1,4,7,10,12,13,24]}}
                              for c in cs]})
materials = sorted({s.material for o in coll.all_objects if o.type=='MESH'
                    for s in o.material_slots if s.material}, key=lambda m:m.name)
record = {'sourceSHA256':before, 'blender':bpy.app.version_string,
          'buildHash':bpy.app.build_hash.decode(),
          'objectRotationMode':arm.rotation_mode,
          'boneRotationModes':{b.name:b.rotation_mode for b in arm.pose.bones},
          'actions':actions,
          'materials':[{'name':m.name, 'nodes':[{'name':n.name, 'type':n.type,
                           'unlinkedInputs':{i.name:value(i.default_value) for i in n.inputs
                                             if hasattr(i,'default_value') and not i.is_linked}}
                          for n in m.node_tree.nodes],
                        'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name]
                                 for l in m.node_tree.links]} for m in materials],
          'method':'Read raw saved action channels, modes and native node graphs only. No retarget, edit, evaluation override, render or save. Actual evaluated body response is separately measured in independent-native-evidence.json.'}
assert len(actions)==11 and all(a['fakeUser'] for a in actions)
assert all(m=='XYZ' for m in record['boneRotationModes'].values())
for a in actions:
    pose=[c for c in a['curves'] if c['dataPath'].startswith('pose.bones[')]
    assert pose and all(c['dataPath'].endswith('rotation_euler') for c in pose)
record['sourceSHA256After']=hashlib.sha256(S.read_bytes()).hexdigest()
assert record['sourceSHA256After']==before
(P/'native-channel-material-audit.json').write_text(json.dumps(record,indent=2)+'\n')
print('CHANNEL_MATERIAL_AUDIT_COMPLETE',len(actions),len(materials),before)
