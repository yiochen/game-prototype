import bpy, bmesh, json, os, sys
from mathutils import Vector

OUT = os.path.dirname(os.path.abspath(__file__))
def enable_layer(c):
    c.exclude = False
    c.hide_viewport = False
    for child in c.children: enable_layer(child)
enable_layer(bpy.context.view_layer.layer_collection)
for c in bpy.data.collections: c.hide_viewport = False
for o in bpy.data.objects:
    if o.name.startswith('wreck-middle'):
        o.hide_viewport = False
        o.hide_set(False)
bpy.context.view_layer.update()
def vec(v): return [float(x) for x in v]
def props(x):
    return {k: x[k] if isinstance(x[k], (str, int, float, bool)) else str(x[k]) for k in x.keys()}
objects = [o for o in bpy.data.objects if o.name.startswith('wreck-middle')]
report = {
    'blend': bpy.data.filepath, 'blender': bpy.app.version_string,
    'collections': [{'name': c.name, 'objects': [o.name for o in c.all_objects]} for c in bpy.data.collections if 'wreck-middle' in c.name],
    'scenes': [{'name': s.name, 'camera': s.camera.name if s.camera else None,
        'render': {k: getattr(s.render, k) for k in ['engine','resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y','film_transparent']},
        'world': s.world.name if s.world else None,
        'view': {k: getattr(s.view_settings,k) for k in ['view_transform','look','exposure','gamma']}}
        for s in bpy.data.scenes], 'objects': []}
deps = bpy.context.evaluated_depsgraph_get()
for o in objects:
    entry = {'name': o.name, 'type': o.type, 'parent': o.parent.name if o.parent else None,
        'matrix_world': [vec(r) for r in o.matrix_world], 'custom_properties': props(o),
        'location': vec(o.location), 'rotation_euler': vec(o.rotation_euler), 'scale': vec(o.scale),
        'modifiers': [{'name': m.name, 'type': m.type} for m in o.modifiers],
        'animation': {'action': o.animation_data.action.name if o.animation_data and o.animation_data.action else None},
        'constraints': [c.type for c in o.constraints]}
    if o.type == 'MESH':
        eo = o.evaluated_get(deps); me = eo.to_mesh(preserve_all_data_layers=True, depsgraph=deps)
        me.calc_loop_triangles()
        entry['mesh'] = {'vertices': [vec(eo.matrix_world @ v.co) for v in me.vertices],
            'edges': [list(e.vertices) for e in me.edges],
            'polygons': [{'vertices': list(p.vertices), 'normal_local': vec(p.normal), 'material': p.material_index, 'smooth': p.use_smooth,
                'loops': [{'vertex': me.loops[i].vertex_index, 'normal_local': vec(me.corner_normals[i].vector)} for i in p.loop_indices]} for p in me.polygons],
            'materials': [m.name if m else None for m in me.materials],
            'uv_layers': [u.name for u in me.uv_layers]}
        eo.to_mesh_clear()
    report['objects'].append(entry)
materials = {m for o in objects if o.type == 'MESH' for m in o.data.materials if m}
report['materials'] = []
for m in sorted(materials, key=lambda m:m.name):
    e = {'name':m.name, 'diffuse_color':vec(m.diffuse_color), 'use_nodes':m.use_nodes, 'properties':props(m)}
    if m.use_nodes:
        e['nodes'] = [{'name': n.name, 'type':n.type, 'operation':getattr(n,'operation',None),
            'blend_type':getattr(n,'blend_type',None), 'interpolation_type':getattr(n,'interpolation_type',None), 'clamp':getattr(n,'clamp',None),
            'ramp_interpolation':n.color_ramp.interpolation if hasattr(n,'color_ramp') else None,
            'inputs': [{'index': j, 'name': i.name, 'value': (vec(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value)} for j,i in enumerate(n.inputs) if hasattr(i,'default_value')],
            'color_ramp': [{'position': el.position, 'color':vec(el.color)} for el in n.color_ramp.elements] if hasattr(n,'color_ramp') else None}
            for n in m.node_tree.nodes]
        e['links'] = [[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links]
    report['materials'].append(e)
report['cameras'] = [{'name':o.name,'matrix_world':[vec(r) for r in o.matrix_world], 'type':o.data.type,
    'ortho_scale':o.data.ortho_scale, 'shift_x':o.data.shift_x,'shift_y':o.data.shift_y} for o in bpy.data.objects if o.type=='CAMERA']
report['lights'] = [{'name':o.name,'type':o.data.type,'location':vec(o.location),'energy':o.data.energy,'size':getattr(o.data,'size',None)} for o in bpy.data.objects if o.type=='LIGHT']
report['images'] = [{'name': i.name, 'filepath':i.filepath, 'packed':bool(i.packed_file)} for i in bpy.data.images]
report['actions'] = [a.name for a in bpy.data.actions if 'wreck' in a.name]
bm=bmesh.new()
for o in report['objects']:
    for v in o.get('mesh',{}).get('vertices',[]):bm.verts.new(v)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
bm.normal_update()
report['sourceOuterConvexHull']={'purpose':'Measured finite conservative outer envelope proposal, not source occupied solid or approved admissible interior volume.',
    'planes':[{'normal':vec(f.normal),'constant':-float(f.normal.dot(f.verts[0].co)),'polygon':[vec(v.co) for v in f.verts]} for f in bm.faces],
    'convention':'Inside if normal dot point + constant <= 1e-6 for every hull plane.'}
bm.free()
with open(os.path.join(OUT,'source-inspection.json'),'w') as f: json.dump(report,f,indent=2)
print('INSPECTED', len(objects), 'objects', [o.name for o in objects])
