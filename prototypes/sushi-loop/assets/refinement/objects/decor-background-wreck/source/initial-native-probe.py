import bpy, json, hashlib, os
from mathutils import Vector

OUT = os.path.dirname(os.path.realpath(__file__))
COLLECTION = 'S33_PROP_decor-background-wreck.001'
col = bpy.data.collections[COLLECTION]
scene = bpy.context.scene
own = set(col.all_objects)

def matrix(m):
    return [[float(v) for v in row] for row in m]

def enable_layer(layer):
    layer.exclude = False
    layer.hide_viewport = False
    for child in layer.children:
        enable_layer(child)

# Visibility changes affect only this unsaved background process. Enabling all
# layer paths ensures parented evaluated matrices are current before measuring.
for c in bpy.data.collections:
    c.hide_viewport = False
for layer in scene.view_layers:
    enable_layer(layer.layer_collection)
for o in own:
    o.hide_set(False)
    o.hide_viewport = False
    o.hide_render = False
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
deps.update()

report = {
    'native_path': bpy.data.filepath,
    'native_sha256': hashlib.sha256(open(bpy.data.filepath, 'rb').read()).hexdigest(),
    'blender_version': bpy.app.version_string,
    'scene': scene.name,
    'collection': col.name,
    'root_expected': 'decor-background-wreck__root.001',
    'method': 'Unsaved background process; enable actual scene/view-layer collection paths and own objects; update depsgraph before reading evaluated parent transforms. No mesh, transform, material, or original project edits.',
    'capture_state': {
        'camera': scene.camera.name if scene.camera else None,
        'resolution': [scene.render.resolution_x, scene.render.resolution_y],
        'resolution_percentage': scene.render.resolution_percentage,
        'engine': scene.render.engine,
        'transparent': scene.render.film_transparent,
        'view_transform': scene.view_settings.view_transform,
        'look': scene.view_settings.look,
        'exposure': scene.view_settings.exposure,
        'gamma': scene.view_settings.gamma,
    },
    'objects': [], 'cameras': [], 'lights': [],
}
all_points = []
for o in sorted(own, key=lambda o:o.name):
    eo = o.evaluated_get(deps)
    item = {'name':o.name, 'type':o.type, 'parent':o.parent.name if o.parent else None,
            'location':list(o.location), 'rotation_euler':list(o.rotation_euler),
            'scale':list(o.scale), 'evaluated_matrix_world':matrix(eo.matrix_world),
            'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]}
    if o.type == 'MESH':
        mesh = eo.to_mesh()
        pts = [eo.matrix_world @ v.co for v in mesh.vertices]
        all_points.extend(pts)
        item.update({'vertices':len(mesh.vertices),'edges':len(mesh.edges), 'polygons':len(mesh.polygons),
                     'smooth_faces':sum(p.use_smooth for p in mesh.polygons),
                     'bounds_world':{'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]},
                     'material_slots':[]})
        for slot in o.material_slots:
            m = slot.material
            mi = {'name':m.name if m else None}
            if m:
                mi.update({'diffuse_color':list(m.diffuse_color),'use_nodes':m.use_nodes})
                if m.use_nodes:
                    mi['nodes'] = []
                    for n in m.node_tree.nodes:
                        ni = {'name':n.name,'type':n.type}
                        ni['inputs'] = {s.name: list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value') and not isinstance(s.default_value,bpy.types.ID)}
                        mi['nodes'].append(ni)
            item['material_slots'].append(mi)
        eo.to_mesh_clear()
    report['objects'].append(item)
if all_points:
    report['evaluated_bounds_world'] = {'min':[min(p[i] for p in all_points) for i in range(3)], 'max':[max(p[i] for p in all_points) for i in range(3)]}
for o in scene.objects:
    if o.type == 'CAMERA':
        report['cameras'].append({'name':o.name,'matrix_world':matrix(o.matrix_world),'type':o.data.type,'ortho_scale':o.data.ortho_scale,'lens':o.data.lens,'shift_x':o.data.shift_x,'shift_y':o.data.shift_y})
    if o.type == 'LIGHT':
        report['lights'].append({'name':o.name,'matrix_world':matrix(o.matrix_world),'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color)})

with open(os.path.join(OUT,'initial-native-probe.json'),'w') as f:
    json.dump(report,f,indent=2)
print('INITIAL_NATIVE_PROBE', json.dumps({'collection':col.name,'objects':len(own),'bounds':report.get('evaluated_bounds_world'),'capture':report['capture_state'],'cameras':report['cameras']},indent=2))
