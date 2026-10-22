import bpy, pathlib, json, hashlib, sys
sys.dont_write_bytecode = True
B = pathlib.Path(__file__).parent

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def value(x):
    try:
        return list(x)
    except TypeError:
        return x

def graph(m):
    nodes = list(m.node_tree.nodes)
    return {
        'nodes': [{'type': n.bl_idname, 'operation': getattr(n, 'operation', None),
                   'attribute': getattr(n, 'attribute_name', None),
                   'inputs': [(i.name, value(i.default_value)) for i in n.inputs if hasattr(i, 'default_value')]}
                  for n in nodes],
        'links': [(nodes.index(l.from_node), l.from_socket.name, nodes.index(l.to_node), l.to_socket.name)
                  for l in m.node_tree.links]
    }

def read(p):
    bpy.ops.wm.open_mainfile(filepath=str(p))
    s = bpy.context.scene
    root = bpy.data.objects['rock-shelf-middle__root']
    root.rotation_euler = (0, 0, 0)
    s.frame_set(1)
    for c in s.collection.children:
        c.hide_viewport = False
    for l in s.view_layers[0].layer_collection.children:
        l.exclude = False
        l.hide_viewport = False
    for o in s.objects:
        o.hide_set(False)
        o.hide_viewport = False
    s.view_layers[0].update()
    o = next(o for o in s.objects if o.type == 'MESH' and 'sculpted_core' in o.name)
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    verts = [list(ev.matrix_world @ v.co) for v in me.vertices]
    faces = [list(p.vertices) for p in me.polygons]
    normals = [list(n.vector) for n in me.corner_normals]
    albedo = [list(x.color) for x in me.color_attributes['rock_shelf_albedo'].data]
    domain = me.color_attributes['rock_shelf_albedo'].domain
    top_vertices = [i for i, v in enumerate(verts) if v[2] > .28 + 1e-6]
    top_faces = [p for p in me.polygons if all(verts[i][2] > .28 + 1e-6 for i in p.vertices)]
    top_loops = [i for p in top_faces for i in p.loop_indices]
    result = {'sha256': sha(p), 'vertices': verts, 'faces': faces, 'normals': normals,
              'albedo': albedo, 'albedoDomain': domain,
              'topVertices': top_vertices, 'topLoops': top_loops, 'topFaceCount': len(top_faces), 'topFaces': [list(p.vertices) for p in top_faces],
              'capGraph': graph(o.data.materials[1])}
    ev.to_mesh_clear()
    return result

old_path = B / 'resources/prior-source.blend'
new_path = B / 'resources/source.blend'
before = [sha(old_path), sha(new_path)]
a = read(old_path)
b = read(new_path)
same_topology = a['faces'] == b['faces'] and len(a['vertices']) == len(b['vertices'])
# Lower-body topology may improve; compare only the actual upper spatial subset.
assert a['topFaces'] == b['topFaces'], 'Actual selected upper face topology must correspond for indexed field comparison'
assert a['albedoDomain'] == b['albedoDomain'] == 'POINT'
assert a['topVertices'] == b['topVertices'] and a['topLoops'] == b['topLoops']

def residual(x, y, indices):
    return max((abs(x[i][k] - y[i][k]) for i in indices for k in range(len(x[i]))), default=0)

changed = [i for i in a['topVertices'] if a['vertices'][i] != b['vertices'][i]]
result = {
    'asset': 'rock-shelf-middle', 'round': 'round-03', 'method': 'Independent read-only native source reopen comparison; no source save, recipe or label-only comparison.',
    'sourceSHA256': before, 'actualEqualTopology': same_topology, 'coreVertices': len(a['vertices']),
    'coreFaces': [len(a['faces']), len(b['faces'])], 'newCoreVertices': len(b['vertices']), 'selection': 'All actual evaluated vertices strictly above native Z .28 plus float tolerance, and faces whose actual vertices meet that criterion; selected from geometry, not editor vertex-count assertions. Lower-body topology is free to change and is not forced equal.',
    'selectedTopVertices': len(a['topVertices']), 'selectedTopFaces': a['topFaceCount'],
    'topPositionMaxResidual': residual(a['vertices'], b['vertices'], a['topVertices']),
    'topAlbedoMaxResidual': residual(a['albedo'], b['albedo'], a['topVertices']),
    'topCornerNormalMaxResidual': residual(a['normals'], b['normals'], a['topLoops']),
    'changedSelectedTopPositionVertices': len(changed),
    'changedOldPositionBounds': [[min(a['vertices'][i][k] for i in changed) for k in range(3)], [max(a['vertices'][i][k] for i in changed) for k in range(3)]] if changed else None,
    'changedNewPositionBounds': [[min(b['vertices'][i][k] for i in changed) for k in range(3)], [max(b['vertices'][i][k] for i in changed) for k in range(3)]] if changed else None,
    'capGraphsEqual': a['capGraph'] == b['capGraph'],
    'capGraphs': [a['capGraph'], b['capGraph']],
    'sourceBytesUnchangedAfter': before == [sha(old_path), sha(new_path)],
    'meaning': 'Preservation audit only; aesthetic outcome still judged from current visible art. Exact crown identity is not a new obligation to preserve weak art.'
}
(B / 'evidence/independent-preservation-comparison.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'capGraphs'}, indent=2))
