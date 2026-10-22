import sys, json, math
sys.dont_write_bytecode = True
from pathlib import Path
import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parents[1] / 'evidence' / 'original-native.json'
def rounded(v):
    return [round(float(x), 10) for x in v]
def props(o):
    return {k: str(o[k]) for k in o.keys()}
def node_data(m):
    if not m or not m.use_nodes:
        return None
    return {'nodes': [{'name': n.name, 'type': n.type, 'operation': getattr(n, 'operation', None), 'blend_type': getattr(n, 'blend_type', None), 'inputs': {s.name: rounded(s.default_value) if hasattr(s.default_value, '__len__') else str(s.default_value) for s in n.inputs if hasattr(s, 'default_value')}, 'colorRamp': [{'position': x.position, 'color': rounded(x.color)} for x in n.color_ramp.elements] if hasattr(n, 'color_ramp') else None} for n in m.node_tree.nodes], 'links': [[l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name] for l in m.node_tree.links]}
root = bpy.data.objects['reef-edge__root.001']
collections = list(root.users_collection)
scene = bpy.context.scene
for c in scene.collection.children:
    c.hide_render = c not in collections
    c.hide_viewport = c not in collections
for layer in scene.view_layers[0].layer_collection.children:
    layer.exclude = layer.collection not in collections
bpy.context.view_layer.update()
objects = sorted(set(o for c in collections for o in c.all_objects), key=lambda o:o.name)
if not objects:
    objects = sorted([o for o in bpy.data.objects if o.name.startswith('reef-edge__')], key=lambda o:o.name)
materials = {m for o in objects for m in getattr(o.data, 'materials', []) if m}
data = {'filepath': bpy.data.filepath, 'blenderVersion': bpy.app.version_string, 'collections': [{'name':c.name,'properties':props(c)} for c in collections], 'objects': [], 'materials': {m.name: {'diffuse_color':rounded(m.diffuse_color), 'nodes':node_data(m)} for m in materials}, 'scenes': []}
for o in objects:
    d = {'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':rounded(o.location),'rotation':rounded(o.rotation_euler),'scale':rounded(o.scale),'matrix_world':[rounded(r) for r in o.matrix_world],'properties':props(o),'hide_render':o.hide_render,'animation':str(o.animation_data),'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]}
    if o.type == 'MESH':
        d.update(vertices=[rounded(o.matrix_world @ v.co) for v in o.data.vertices], faces=[{'vertices':list(p.vertices),'normal':rounded(o.matrix_world.to_3x3() @ p.normal),'material_index':p.material_index,'smooth':p.use_smooth} for p in o.data.polygons], materials=[m.name if m else None for m in o.data.materials])
    data['objects'].append(d)
for s in bpy.data.scenes:
    data['scenes'].append({'name':s.name,'camera': {'name':s.camera.name, 'matrix_world':[rounded(r) for r in s.camera.matrix_world], 'type':s.camera.data.type,'ortho_scale':s.camera.data.ortho_scale,'shift_x':s.camera.data.shift_x,'shift_y':s.camera.data.shift_y} if s.camera else None, 'render':{'resolution':[s.render.resolution_x,s.render.resolution_y],'percentage':s.render.resolution_percentage,'pixel_aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'filter_size':s.render.filter_size,'engine':s.render.engine}, 'lights':[{'name':o.name,'position':rounded(o.matrix_world.translation),'type':o.data.type,'energy':o.data.energy,'size':getattr(o.data,'size',None)} for o in s.objects if o.type=='LIGHT'],'world':node_data(s.world) if s.world else None, 'colorManagement':{'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma}})
OUT.write_text(json.dumps(data, indent=2) + '\n')
print('INSPECTED', len(objects), 'objects', OUT)
