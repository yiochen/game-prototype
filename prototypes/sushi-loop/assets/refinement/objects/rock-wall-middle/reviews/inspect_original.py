import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
target=bpy.data.collections['S33_PROP_rock-wall-middle.001']
def layers(node):
    yield node
    for child in node.children: yield from layers(child)
for l in layers(bpy.context.view_layer.layer_collection): l.exclude=False
for l in bpy.context.view_layer.layer_collection.children: l.exclude=l.collection!=target
target.hide_viewport=False
target.hide_render=False
bpy.context.view_layer.update()
objects = [o for o in bpy.data.objects if 'rock-wall-middle' in o.name]
def vec(v): return [round(float(x), 9) for x in v]
def prop(o):
    return {k: o[k] for k in o.keys() if k != '_RNA_UI'}
def bounds(points):
    return {'min': [min(p[i] for p in points) for i in range(3)], 'max': [max(p[i] for p in points) for i in range(3)]} if points else None
report = {'sourceFile': bpy.data.filepath, 'sourceSHA256': hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(), 'scenes': [], 'objects': [], 'dependencies': {}}
for s in bpy.data.scenes:
    c = s.camera
    report['scenes'].append({'name': s.name, 'camera': c.name if c else None, 'cameraLocation': vec(c.location) if c else None, 'cameraRotationDegrees': vec([math.degrees(v) for v in c.rotation_euler]) if c else None, 'orthoScale': c.data.ortho_scale if c else None, 'resolution': [s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage], 'pixelAspect': [s.render.pixel_aspect_x, s.render.pixel_aspect_y], 'filmTransparent': s.render.film_transparent})
all_points=[]
for o in objects:
    points = [vec(o.matrix_world @ v.co) for v in o.data.vertices] if o.type == 'MESH' else []
    all_points += points
    item={'name': o.name, 'type': o.type, 'parent': o.parent.name if o.parent else None, 'collections': [c.name for c in o.users_collection], 'location': vec(o.location), 'rotationDegrees': vec([math.degrees(v) for v in o.rotation_euler]), 'scale': vec(o.scale), 'matrixWorld': [vec(r) for r in o.matrix_world], 'properties': prop(o), 'worldBounds': bounds(points), 'modifiers': [{'name': m.name, 'type': m.type} for m in o.modifiers]}
    if points:
        eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
        em=eo.to_mesh()
        evaluated_points=[vec(eo.matrix_world @ v.co) for v in em.vertices]
        item.update(vertices=len(points), polygons=len(o.data.polygons), evaluatedWorldBounds=bounds(evaluated_points), materials=[m.name if m else None for m in o.data.materials], endpointVertices={str(x): sorted([p for p in points if abs(p[0]-x)<1e-6]) for x in [-.5,.5]})
        eo.to_mesh_clear()
    report['objects'].append(item)
report['worldBounds']=bounds(all_points)
report['dependencies']['libraries']=[{'filepath': l.filepath} for l in bpy.data.libraries]
report['dependencies']['images']=[{'name': i.name, 'source': i.source, 'filepath': i.filepath, 'packed': bool(i.packed_file)} for i in bpy.data.images if i.source != 'GENERATED']
report['dependencies']['assetMaterialNodes']={}
for o in objects:
    if o.type != 'MESH': continue
    for mat in o.data.materials:
        if not mat or mat.name in report['dependencies']['assetMaterialNodes']: continue
        report['dependencies']['assetMaterialNodes'][mat.name]={'diffuseColor': vec(mat.diffuse_color), 'nodes': [{'name': n.name,'type': n.type,'image': n.image.name if n.type == 'TEX_IMAGE' and n.image else None} for n in mat.node_tree.nodes] if mat.node_tree else []}
(HERE/'original-native-audit.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
print('JUDGE_AUDIT', json.dumps({'objects':len(objects),'bounds':report['worldBounds'],'scenes':report['scenes']}))
