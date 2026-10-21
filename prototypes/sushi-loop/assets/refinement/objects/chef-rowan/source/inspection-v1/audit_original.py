import bpy
import importlib.util
import json
import hashlib
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).parent
OBJ = OUT.parents[1]
ROOT = OBJ.parents[3]
rig = json.loads((OBJ/'inputs/source-rig.json').read_text())
native_path = ROOT/'assets/production/source/blender/revisions/d88e53edef8e7c73/native_actions.py'
spec = importlib.util.spec_from_file_location('original_native_actions', native_path)
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
source_scene = bpy.context.scene
collection = bpy.data.collections['S33_CHARACTER_chef_rowan.001']
root = bpy.data.objects[rig['groundRootObject']]
arm = bpy.data.objects[rig['armatures'][0]['object']]
source_camera = source_scene.camera
source_info = dict(camera=dict(name=source_camera.name, matrix=[list(r) for r in source_camera.matrix_world],
                               type=source_camera.data.type, ortho_scale=source_camera.data.ortho_scale,
                               shift_x=source_camera.data.shift_x, shift_y=source_camera.data.shift_y),
                   lights=[dict(name=o.name, type=o.data.type, energy=o.data.energy,
                                size=getattr(o.data,'size',None), position=list(o.location))
                           for o in source_scene.objects if o.type=='LIGHT'],
                   color_management=dict(view_transform=source_scene.view_settings.view_transform,
                                         look=source_scene.view_settings.look,
                                         exposure=source_scene.view_settings.exposure,
                                         gamma=source_scene.view_settings.gamma))
# Isolated active scene and full collection visibility precede all evaluation.
scene = bpy.data.scenes.new('Independent Rowan source inspection')
scene.collection.children.link(collection)
collection.hide_viewport = False
collection.hide_render = False
bpy.context.window.scene = scene
for layer in scene.view_layers:
    def visible(lc):
        lc.exclude = False
        lc.hide_viewport = False
        lc.collection.hide_viewport = False
        for child in lc.children:
            visible(child)
    visible(layer.layer_collection)
for obj in collection.all_objects:
    obj.hide_set(False)
    if obj.type == 'ARMATURE':
        obj.hide_viewport = False
        obj.hide_render = False
bpy.context.view_layer.update()
asset = dict(root=root, collection=collection, armature=arm)
food = next(o for o in collection.objects if o.type=='EMPTY' and o.name.endswith('__held_dish-salmon'))
utensil = next(o for o in collection.objects if o.name.endswith('__utensil'))

def bounds(obj, dg):
    eo = obj.evaluated_get(dg)
    mesh = eo.to_mesh()
    verts = [eo.matrix_world @ v.co for v in mesh.vertices]
    eo.to_mesh_clear()
    return [[min(v[i] for v in verts) for i in range(3)],
            [max(v[i] for v in verts) for i in range(3)]]

frames = []
for clip in rig['clips']:
    for direction in ['S','E','N','W']:
        for frame in range(1,13):
            native.apply_clip(asset, rig, clip, frame=frame, direction=direction, scene=scene)
            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()
            evaluated_arm = arm.evaluated_get(dg)
            object_bounds = {o.name:bounds(o,dg) for o in collection.objects
                             if o.type=='MESH' and not o.hide_render}
            character_bounds = [b for n,b in object_bounds.items()
                                if '__held_dish-' not in n and '__knife_' not in n]
            aggregate = [[min(b[0][i] for b in character_bounds) for i in range(3)],
                         [max(b[1][i] for b in character_bounds) for i in range(3)]]
            contacts = {}
            for side in ['L','R']:
                bone = evaluated_arm.pose.bones['hand_'+side]
                rest = evaluated_arm.data.bones['hand_'+side]
                point = rest.head_local + Vector((0,-.002,-.046))
                contacts['palm_'+side] = list(evaluated_arm.matrix_world @ bone.matrix @ rest.matrix_local.inverted() @ point)
                contacts['foot_'+side] = list(evaluated_arm.matrix_world @ evaluated_arm.pose.bones['foot_'+side].head)
            frames.append(dict(clip=clip, direction=direction, frame=frame, bounds=aggregate,
                               contacts=contacts, food_socket=list(food.evaluated_get(dg).matrix_world.translation),
                               food_plane_visible=not bpy.data.objects[food.name+'__image_plane'].hide_render,
                               utensil_socket=list(utensil.evaluated_get(dg).matrix_world.translation),
                               knife_visible=not bpy.data.objects[root.name+'__knife_blade'].hide_render,
                               object_bounds=object_bounds))
textures = []
for obj in collection.objects:
    if obj.type!='MESH': continue
    for material in obj.data.materials:
        if material and material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image:
                    im=node.image
                    row=dict(object=obj.name, material=material.name, image=im.name,
                             filepath=im.filepath, packed=bool(im.packed_file), size=list(im.size),
                             packed_sha256=hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None)
                    if row not in textures: textures.append(row)
data=dict(version=bpy.app.version_string, independent=True,
          scope='Original source only. No reviews or qualityCriteria read.',
          source=source_info, source_root_scale=list(root.scale),
          objects=len(collection.objects), meshes=sum(o.type=='MESH' for o in collection.objects),
          bones=[dict(name=b.name,parent=b.parent.name if b.parent else None,
                      head=list(b.head_local),tail=list(b.tail_local),deform=b.use_deform) for b in arm.data.bones],
          textures=textures, frames=frames,
          extent=[[min(f['bounds'][0][i] for f in frames) for i in range(3)],
                  [max(f['bounds'][1][i] for f in frames) for i in range(3)]])
(OUT/'native-action-audit.json').write_text(json.dumps(data,indent=2))
print(json.dumps({k:v for k,v in data.items() if k not in ['frames','bones','source']},indent=2))
for clip in rig['clips']:
    fs=[f for f in frames if f['clip']==clip and f['direction']=='S']
    print(clip, 'bounds', [[min(f['bounds'][0][i] for f in fs) for i in range(3)],
                           [max(f['bounds'][1][i] for f in fs) for i in range(3)]],
          'food visible',sum(f['food_plane_visible'] for f in fs),
          'knife visible',sum(f['knife_visible'] for f in fs),
          'food first/mid/last',[fs[i]['food_socket'] for i in [0,5,11]],
          'palmR first/mid/last',[fs[i]['contacts']['palm_R'] for i in [0,5,11]])
