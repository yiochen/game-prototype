"""Own independent initial read-only inspection. Never saves or renders Blender data."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).with_suffix('.json')
SCENE_NAME = 'S33 Native Asset Library Export'
COLLECTION_NAME = 'S33_CFX_creature-fish.001'
ROOT_NAME = 'creature-fish__ground_root.001'

def simple(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, 'to_list'):
        return value.to_list()
    if hasattr(value, 'items'):
        return {str(k): simple(v) for k,v in value.items()}
    try:
        return [simple(v) for v in value]
    except TypeError:
        return str(value)

def props(data):
    return {k: simple(data[k]) for k in data.keys() if k != '_RNA_UI'}

def vec(value):
    return [round(float(v), 8) for v in value]

def matrix(value):
    return [vec(row) for row in value]

scene = bpy.data.scenes[SCENE_NAME]
collection = bpy.data.collections[COLLECTION_NAME]
bpy.context.window.scene = scene

ancestry = []
def find_path(node, wanted, path):
    if node == wanted:
        return path + [node]
    for child in node.children:
        found = find_path(child, wanted, path + [node])
        if found:
            return found
    return None

path = find_path(scene.collection, collection, [])
if not path:
    raise RuntimeError('Authorized collection is not in actual named scene')
original_visibility = {}
for col in path:
    original_visibility[col.name] = {'hide_viewport': col.hide_viewport, 'hide_render': col.hide_render}
    col.hide_viewport = False
    col.hide_render = False
own = list(collection.all_objects)
for obj in own:
    original_visibility[obj.name] = {'hide_viewport': obj.hide_viewport, 'hide_render': obj.hide_render, 'hide_get': obj.hide_get()}
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)

view_layer = scene.view_layers[0]
bpy.context.window.view_layer = view_layer
layer_path = find_path(view_layer.layer_collection, next((x for x in []), None), []) if False else None
enabled_layer_paths = []
def enable_own_layer(node, names):
    if node.collection in path or node.collection == collection:
        enabled_layer_paths.append({'name': node.name, 'exclude_before': node.exclude, 'hide_viewport_before': node.hide_viewport})
        node.exclude = False
        node.hide_viewport = False
    for child in node.children:
        enable_own_layer(child, names)
enable_own_layer(view_layer.layer_collection, set(c.name for c in path))
view_layer.update()
scene.frame_set(scene.frame_current)
bpy.context.evaluated_depsgraph_get().update()
depsgraph = bpy.context.evaluated_depsgraph_get()

object_rows = []
materials = {}
for obj in sorted(own, key=lambda x: x.name):
    ev = obj.evaluated_get(depsgraph)
    row = {
        'name': obj.name, 'type': obj.type, 'parent': obj.parent.name if obj.parent else None,
        'parent_type': obj.parent_type, 'parent_bone': obj.parent_bone,
        'collections': [c.name for c in obj.users_collection],
        'location': vec(obj.location), 'rotation_mode': obj.rotation_mode,
        'rotation_euler': vec(obj.rotation_euler), 'scale': vec(obj.scale),
        'matrix_local': matrix(obj.matrix_local), 'matrix_world_evaluated': matrix(ev.matrix_world),
        'custom_properties': props(obj),
        'modifiers': [{'name': m.name, 'type':m.type, 'object':getattr(getattr(m,'object',None),'name',None),
                       'show_viewport':m.show_viewport,'show_render':m.show_render} for m in obj.modifiers],
        'constraints': [{'name':c.name,'type':c.type,'target':getattr(getattr(c,'target',None),'name',None)} for c in obj.constraints],
        'action': obj.animation_data.action.name if obj.animation_data and obj.animation_data.action else None,
        'action_slot': getattr(getattr(obj.animation_data, 'action_slot', None), 'identifier', None) if obj.animation_data else None,
        'nla_tracks': [{'name':tr.name,'mute':tr.mute,'strips':[{'name':s.name,'action':s.action.name if s.action else None,
                      'frame_start':s.frame_start,'frame_end':s.frame_end} for s in tr.strips]} for tr in obj.animation_data.nla_tracks] if obj.animation_data else [],
    }
    if obj.type == 'MESH':
        mesh = obj.data
        evaluated_mesh = ev.to_mesh()
        points = [ev.matrix_world @ v.co for v in evaluated_mesh.vertices]
        row['mesh'] = {'data':mesh.name,'vertices':len(mesh.vertices),'edges':len(mesh.edges),'polygons':len(mesh.polygons),
                       'triangles_calculated':sum(len(p.vertices)-2 for p in mesh.polygons),
                       'smooth_polygons':sum(p.use_smooth for p in mesh.polygons),'uv_layers':list(mesh.uv_layers.keys()),
                       'attributes':[{'name':a.name,'data_type':a.data_type,'domain':a.domain} for a in mesh.attributes],
                       'shape_keys':list(mesh.shape_keys.key_blocks.keys()) if mesh.shape_keys else [],
                       'vertex_groups':[{'name':g.name,'vertices':sum(any(a.group==g.index for a in v.groups) for v in mesh.vertices)} for g in obj.vertex_groups],
                       'evaluated_vertices':len(evaluated_mesh.vertices),
                       'evaluated_world_bounds':{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]} if points else None}
        ev.to_mesh_clear()
        row['materials'] = [s.material.name if s.material else None for s in obj.material_slots]
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or mat.name in materials:
                continue
            materials[mat.name] = {
                'diffuse_color':vec(mat.diffuse_color), 'use_nodes':mat.use_nodes,
                'roughness':mat.roughness, 'metallic':mat.metallic, 'custom_properties':props(mat),
                'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:simple(i.default_value) for i in n.inputs if hasattr(i,'default_value') and not i.is_linked},
                         'image':getattr(getattr(n,'image',None),'name',None)} for n in mat.node_tree.nodes] if mat.node_tree else [],
                'links':[{'from':l.from_node.name+':'+l.from_socket.name,'to':l.to_node.name+':'+l.to_socket.name} for l in mat.node_tree.links] if mat.node_tree else []}
    if obj.type == 'ARMATURE':
        row['armature'] = {'data':obj.data.name,'pose_position':obj.data.pose_position,
            'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head_local':vec(b.head_local),'tail_local':vec(b.tail_local),
                      'use_deform':b.use_deform,'custom_properties':props(b)} for b in obj.data.bones],
            'pose_bones':[{'name':b.name,'rotation_mode':b.rotation_mode,'location':vec(b.location),'rotation_euler':vec(b.rotation_euler),
                          'rotation_quaternion':vec(b.rotation_quaternion),'scale':vec(b.scale),'custom_properties':props(b),
                          'constraints':[{'name':c.name,'type':c.type,'target':getattr(getattr(c,'target',None),'name',None)} for c in b.constraints]} for b in obj.pose.bones]}
    object_rows.append(row)

def fcurve_rows(action):
    rows = []
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag = strip.channelbag(slot, ensure=False)
                if not bag:
                    continue
                for fc in bag.fcurves:
                    rows.append({'slot':slot.identifier,'data_path':fc.data_path,'array_index':fc.array_index,
                                 'keys':[{'co':vec(p.co),'interpolation':p.interpolation} for p in fc.keyframe_points]})
    return rows

actions=[]
assigned = {r['action'] for r in object_rows if r['action']}
for action in bpy.data.actions:
    if 'creature-fish' not in action.name and action.name not in assigned:
        continue
    actions.append({'name':action.name,'frame_range':vec(action.frame_range),'use_fake_user':action.use_fake_user,
                    'slots':[{'identifier':s.identifier,'target_id_type':s.target_id_type} for s in action.slots],
                    'custom_properties':props(action),'fcurves':fcurve_rows(action)})

camera = scene.camera
result = {
    'scope':'Authorized own creature-fish BODY collection only; initial read-only background inspection; no render/save/candidate/geometry/material/pose tuning.',
    'blender':{'version':bpy.app.version_string,'build_hash':bpy.app.build_hash.decode()},
    'source_file':bpy.data.filepath,'actual_scene':scene.name,'actual_view_layer':view_layer.name,
    'scene_frame_current':scene.frame_current,'scene_frame_range':[scene.frame_start,scene.frame_end],
    'collection':{'name':collection.name,'custom_properties':props(collection),'ancestry':[c.name for c in path],
                  'direct_object_count':len(collection.objects),'recursive_object_count':len(own),'children':[c.name for c in collection.children]},
    'temporary_inspection_visibility_before':original_visibility,'temporarily_enabled_layer_paths':enabled_layer_paths,
    'dependency_graph_updated_before_measurements':True,
    'scene_render_settings_observed_not_frozen_contract':{'engine':scene.render.engine,'resolution_x':scene.render.resolution_x,'resolution_y':scene.render.resolution_y,
        'resolution_percentage':scene.render.resolution_percentage,'film_transparent':scene.render.film_transparent,'fps':scene.render.fps,'pixel_aspect_x':scene.render.pixel_aspect_x,'pixel_aspect_y':scene.render.pixel_aspect_y},
    'active_scene_camera_observed_not_frozen_contract':{'name':camera.name,'type':camera.data.type,'ortho_scale':camera.data.ortho_scale,
        'matrix_world':matrix(camera.matrix_world)} if camera else None,
    'objects':object_rows,'materials':materials,'own_related_actions':actions,
}
with OUT.open('x') as f:
    json.dump(result, f, indent=2, sort_keys=True)
print('INITIAL_NATIVE_PROBE_OUTPUT', OUT)
print('COUNTS', len(object_rows), len(materials), len(actions))
