import bpy
import json
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).with_name('native-probe.json')
COLLECTION = 'S33_PROP_wreck-end.001'
ROOT = 'wreck-end__root.001'

def vec(v):
    return [round(float(x), 8) for x in v]

def mat(m):
    return [vec(row) for row in m]

def bounds(points):
    pts = list(points)
    if not pts:
        return None
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return {'min': vec(lo), 'max': vec(hi), 'size': vec([hi[i]-lo[i] for i in range(3)])}

scene = bpy.context.scene
view_layer = bpy.context.view_layer
collection = bpy.data.collections[COLLECTION]
root = bpy.data.objects[ROOT]
members = list(collection.all_objects)
member_names = {o.name for o in members}
if root.name not in member_names:
    raise RuntimeError('Requested root is not in requested collection')

enabled_layer_paths = []
def enable_path(layer, path=()):
    chain = path + (layer,)
    found = layer.collection == collection
    child_found = False
    for child in layer.children:
        child_found = enable_path(child, chain) or child_found
    if found:
        for node in chain:
            enabled_layer_paths.append({'name': node.name, 'exclude_before': node.exclude, 'hide_viewport_before': node.hide_viewport})
            node.exclude = False
            node.hide_viewport = False
    return found or child_found

enable_path(view_layer.layer_collection)
if not enabled_layer_paths:
    raise RuntimeError('Requested collection not found in actual view layer')

collection_flags = []
def enable_collection(c):
    collection_flags.append({'name': c.name, 'hide_viewport_before': c.hide_viewport, 'hide_render_before': c.hide_render})
    c.hide_viewport = False
    c.hide_render = False
    for child in c.children:
        enable_collection(child)
enable_collection(collection)

object_flags = []
for obj in members:
    object_flags.append({'name': obj.name, 'hide_viewport_before': obj.hide_viewport, 'hide_render_before': obj.hide_render, 'hide_get_before': obj.hide_get(view_layer=view_layer)})
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False, view_layer=view_layer)

scene.frame_set(scene.frame_current)
view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
depsgraph.update()

objects = []
all_world_vertices = []
material_names = set()
for obj in sorted(members, key=lambda o: o.name):
    evaluated = obj.evaluated_get(depsgraph)
    record = {
        'name': obj.name, 'type': obj.type,
        'parent': obj.parent.name if obj.parent else None,
        'children': sorted(c.name for c in obj.children),
        'location': vec(obj.location), 'rotation_mode': obj.rotation_mode,
        'rotation_euler': vec(obj.rotation_euler), 'scale': vec(obj.scale),
        'matrix_world_evaluated': mat(evaluated.matrix_world),
        'dimensions_evaluated': vec(evaluated.dimensions),
        'matrix_parent_inverse': mat(obj.matrix_parent_inverse),
        'modifiers': [{'name': m.name, 'type': m.type, 'show_viewport': m.show_viewport, 'show_render': m.show_render,
                       **({'width': m.width, 'segments': m.segments, 'affect': m.affect} if m.type == 'BEVEL' else {})} for m in obj.modifiers],
        'constraints': [{'name': c.name, 'type': c.type, 'mute': c.mute} for c in obj.constraints],
        'materials': [s.material.name if s.material else None for s in obj.material_slots],
        'visible_in_view_layer_after_enable': obj.visible_get(view_layer=view_layer),
    }
    material_names.update(m for m in record['materials'] if m)
    if obj.type == 'MESH':
        mesh = obj.data
        evaluated_mesh = evaluated.to_mesh()
        try:
            pts = [evaluated.matrix_world @ v.co for v in evaluated_mesh.vertices]
            all_world_vertices.extend(pts)
            root_inv = root.evaluated_get(depsgraph).matrix_world.inverted()
            record['mesh'] = {
                'data_name': mesh.name, 'vertices': len(mesh.vertices), 'edges': len(mesh.edges), 'polygons': len(mesh.polygons),
                'smooth_polygons': sum(p.use_smooth for p in mesh.polygons),
                'evaluated_vertices': len(evaluated_mesh.vertices), 'evaluated_edges': len(evaluated_mesh.edges), 'evaluated_polygons': len(evaluated_mesh.polygons),
                'evaluated_world_bounds': bounds(pts),
                'evaluated_root_local_bounds': bounds(root_inv @ p for p in pts),
                'uv_layers': list(mesh.uv_layers.keys()),
            }
        finally:
            evaluated.to_mesh_clear()
    objects.append(record)

materials = []
for name in sorted(material_names):
    material = bpy.data.materials[name]
    nodes = []
    if material.use_nodes and material.node_tree:
        for node in material.node_tree.nodes:
            item = {'name': node.name, 'type': node.type}
            if node.type == 'BSDF_PRINCIPLED':
                item['inputs'] = {}
                for key in ('Base Color', 'Metallic', 'Roughness', 'IOR', 'Specular IOR Level', 'Coat Weight', 'Coat Roughness'):
                    if key in node.inputs:
                        value = node.inputs[key].default_value
                        item['inputs'][key] = vec(value) if hasattr(value, '__len__') else float(value)
            if node.type == 'TEX_IMAGE':
                item['image'] = node.image.name if node.image else None
                item['filepath'] = node.image.filepath if node.image else None
            nodes.append(item)
    materials.append({'name': name, 'diffuse_color': vec(material.diffuse_color), 'use_nodes': material.use_nodes,
                      'nodes': nodes, 'links': [{'from_node': l.from_node.name, 'from_socket': l.from_socket.name, 'to_node': l.to_node.name, 'to_socket': l.to_socket.name} for l in material.node_tree.links] if material.use_nodes and material.node_tree else []})

camera = scene.camera
native_camera = None
if camera:
    native_camera = {'name': camera.name, 'type': camera.data.type, 'ortho_scale': camera.data.ortho_scale,
                     'matrix_world': mat(camera.matrix_world), 'lens': camera.data.lens,
                     'shift_x': camera.data.shift_x, 'shift_y': camera.data.shift_y}

payload = {
    'kind': 'bounded_read_only_raw_native_probe', 'blender_version': bpy.app.version_string,
    'file': bpy.data.filepath, 'scene': scene.name, 'view_layer': view_layer.name,
    'requested_collection': COLLECTION, 'requested_root': ROOT,
    'procedure': ['load raw source without saving', 'enable requested actual scene/view-layer collection ancestry and own objects in memory', 'set current frame and update actual view layer and depsgraph', 'read evaluated own transforms and mesh vertices', 'write JSON only; no blend save'],
    'enabled_layer_paths': enabled_layer_paths, 'collection_flags_before': collection_flags, 'object_flags_before': object_flags,
    'root_evaluated_matrix_world': mat(root.evaluated_get(depsgraph).matrix_world),
    'evaluated_world_geometry_bounds': bounds(all_world_vertices),
    'evaluated_root_local_geometry_bounds': bounds(root.evaluated_get(depsgraph).matrix_world.inverted() @ p for p in all_world_vertices),
    'object_count': len(objects), 'mesh_object_count': sum(o['type'] == 'MESH' for o in objects),
    'objects': objects, 'materials': materials,
    'saved_scene_camera_observation_only': native_camera,
    'saved_scene_render_observation_only': {'engine': scene.render.engine, 'resolution_x': scene.render.resolution_x,
        'resolution_y': scene.render.resolution_y, 'resolution_percentage': scene.render.resolution_percentage,
        'pixel_aspect_x': scene.render.pixel_aspect_x, 'pixel_aspect_y': scene.render.pixel_aspect_y,
        'film_transparent': scene.render.film_transparent, 'view_transform': scene.view_settings.view_transform,
        'look': scene.view_settings.look, 'exposure': scene.view_settings.exposure, 'gamma': scene.view_settings.gamma},
    'constraint_status': 'observations only; no future camera, interface, registration, size or capture contract declared',
}
OUT.write_text(json.dumps(payload, indent=2) + '\n')
print(json.dumps({'probe_saved': str(OUT), 'own_objects': len(objects), 'own_meshes': payload['mesh_object_count'], 'geometry_bounds': payload['evaluated_root_local_geometry_bounds']}))
