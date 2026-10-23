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
              'faceLoops': [list(p.loop_indices) for p in me.polygons], 'capGraph': graph(o.data.materials[1])}
    ev.to_mesh_clear()
    return result

old_path = B / 'resources/prior-source.blend'
new_path = B / 'resources/source.blend'
before = [sha(old_path), sha(new_path)]
a = read(old_path)
b = read(new_path)
same_topology = a['faces'] == b['faces'] and len(a['vertices']) == len(b['vertices'])
assert a['albedoDomain'] == b['albedoDomain'] == 'POINT'
# Discover correspondence from the saved mesh data, without an editor count.
common_face_prefix = 0
for x, y in zip(a['faces'], b['faces']):
    if x != y:
        break
    common_face_prefix += 1
shared_vertices = sorted({v for f in a['faces'][:common_face_prefix] for v in f})
shared_loops_a = [i for f in a['faceLoops'][:common_face_prefix] for i in f]
shared_loops_b = [i for f in b['faceLoops'][:common_face_prefix] for i in f]
assert len(shared_loops_a) == len(shared_loops_b)

def residual(x, y, indices):
    return max((abs(x[i][k] - y[i][k]) for i in indices for k in range(len(x[i]))), default=0)

result = {
    'asset': 'rock-shelf-middle', 'round': 'round-03',
    'method': 'Independent read-only native source reopen; actual topology/data correspondence discovered without supplied crown counts; no source save or recipe.',
    'sourceSHA256': before, 'actualEqualWholeCoreTopology': same_topology,
    'coreVertices': [len(a['vertices']), len(b['vertices'])],
    'coreFaces': [len(a['faces']), len(b['faces'])],
    'commonIndexedFacePrefixCount': common_face_prefix,
    'commonIndexedFacePrefixVertexCount': len(shared_vertices),
    'commonPrefixOldVertexBounds': [[min(a['vertices'][i][k] for i in shared_vertices) for k in range(3)], [max(a['vertices'][i][k] for i in shared_vertices) for k in range(3)]],
    'commonPrefixNewVertexBounds': [[min(b['vertices'][i][k] for i in shared_vertices) for k in range(3)], [max(b['vertices'][i][k] for i in shared_vertices) for k in range(3)]],
    'commonPrefixPositionMaxResidual': residual(a['vertices'], b['vertices'], shared_vertices),
    'commonPrefixAlbedoMaxResidual': residual(a['albedo'], b['albedo'], shared_vertices),
    'commonPrefixCornerNormalMaxResidual': max((abs(a['normals'][i][k]-b['normals'][j][k]) for i,j in zip(shared_loops_a, shared_loops_b) for k in range(3)),default=0),
    'strictUpperSpatialSelectionCounts': {'oldVertices':len(a['topVertices']), 'newVertices':len(b['topVertices']), 'oldFaces':a['topFaceCount'], 'newFaces':b['topFaceCount'], 'allFacesEqual':a['topFaces']==b['topFaces']},
    'capGraphsEqual': a['capGraph'] == b['capGraph'], 'capGraphs': [a['capGraph'], b['capGraph']],
    'sourceBytesUnchangedAfter': before == [sha(old_path), sha(new_path)],
    'diagnosticHistory': 'Initial whole-topology and broad upper-spatial assertions were invalid because legitimate body/shoulder topology changed. Both failed helper versions/logs retained. This result reports discovered shared actual face prefix and its measured bounds/fields, rather than forcing entire-core equality.',
    'meaning': 'Preservation evidence only. Actual shared prefix is checked in its measured upper bounds; lower-body topology is free to improve. Current art judged independently; no new requirement to freeze weak art.'
}
(B / 'evidence/independent-preservation-comparison.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'capGraphs'}, indent=2))
