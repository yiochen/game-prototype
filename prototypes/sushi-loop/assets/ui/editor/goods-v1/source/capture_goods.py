"""Editable UI merchandise cameras, authored and rendered via live Blender MCP.

Import this module in Blender, call build(repo), then render_one(art_id). It only
appends owned production collections, adds isolated scenes, and writes a library
containing those scenes. It never opens, replaces, or saves the user's main file.
"""
import bpy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from mathutils import Vector

SIZE = 384
ELEVATION = 35.0
AZIMUTH = 35.0
CAMERA_ID = 'goods-three-quarter-35'
COLLECTIONS = {
    'belt-straight-e': 'S33_FB_belt-straight-e.001',
    'stool-wood': 'S33_PROP_stool_wood.001',
    'plant-angular': 'S33_PROP_plant-angular',
    'crate-wood': 'S33_PROP_crate-wood',
    'barrel-wood': 'S33_PROP_barrel-wood',
    'floor-cream': 'S33_FB_floor-cream.001',
}
state = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def geometry_hash(collection):
    payload = []
    for obj in sorted(collection.all_objects, key=lambda o: o.name):
        if obj.type != 'MESH':
            continue
        payload.append({
            'source_object': obj.get('goods_source_object', obj.name),
            'matrix': [[round(v, 7) for v in row] for row in obj.matrix_world],
            'vertices': [[round(v, 7) for v in vertex.co] for vertex in obj.data.vertices],
            'polygons': [list(poly.vertices) for poly in obj.data.polygons],
        })
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def material_record(mat):
    return {
        'name': mat.name,
        'approved_revision': mat.get('s33FacetedRevision'),
        'refinement': mat.get('s33MaterialRefinement'),
        'floor_calibration': mat.get('s33FloorCalibrated'),
        'native_height_ramp': mat.get('lowerTone'),
        'principled': [{
            'roughness': node.inputs['Roughness'].default_value,
            'specular_ior_level': node.inputs['Specular IOR Level'].default_value,
            'metallic': node.inputs['Metallic'].default_value,
        } for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED'],
    }


def slab(collection, material):
    # UI presentation exception: a real .12-cell ceramic sample slab. World
    # floor geometry stays untouched. Its approved cream material is reused.
    vertices = [(x, y, z) for z in (0, .12) for y in (-.5, .5) for x in (-.5, .5)]
    faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4),
             (1, 3, 7, 5), (3, 2, 6, 7), (2, 0, 4, 6)]
    mesh = bpy.data.meshes.new('Editor goods cream slab mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new('Editor goods cream slab .12', mesh)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new('Small native ceramic bevel', 'BEVEL')
    bevel.width = .018
    bevel.segments = 1
    obj['goods_source_object'] = 'UI-only beveled cream slab'
    obj['ui_only_thickness'] = .12
    obj['production_floor_unchanged'] = True
    return obj


def build(repo):
    global state
    repo = Path(repo)
    base = repo / 'prototypes/sushi-loop'
    output = base / 'assets/ui/editor/goods-v1'
    production = base / 'assets/production/source/blender/sushi-loop-world-library.blend'
    native_base = production.parent
    previous = bpy.context.window.scene
    main_file = bpy.data.filepath
    dirty_before = bpy.data.is_dirty
    state = {'repo': repo, 'output': output, 'scenes': {}, 'records': {}}
    source_hash = sha(production)
    try:
        # Each appended collection has independent objects/material datablocks;
        # no object from the user's existing production scenes is mutated.
        with bpy.data.libraries.load(str(production), link=False) as (source, target):
            assert all(name in source.collections for name in COLLECTIONS.values())
            target.collections = list(COLLECTIONS.values())
        appended = dict(zip(COLLECTIONS, target.collections))
        style = load('s12_goods_approved_grade', native_base / 'catalog_style.py')
        lighting = load('s12_goods_approved_faceted', native_base / 'catalog_faceted.py')
        for art_id, source_collection in appended.items():
            source_objects = list(source_collection.all_objects)
            for obj in source_objects:
                obj['goods_source_object'] = obj.name
                # Static merchandising pose: saved geometry/transforms, no live
                # animation. Only appended owners are cleared.
                if obj.animation_data:
                    obj.animation_data_clear()
                if obj.parent is None:
                    obj.rotation_euler = (0, 0, 0)
                if obj.type == 'MESH':
                    for mat in obj.data.materials:
                        if mat and mat.use_nodes and mat.node_tree.animation_data:
                            mat.node_tree.animation_data_clear()
            scene = bpy.data.scenes.new('S12 editor goods ' + art_id)
            scene['project_role'] = 'UI merchandise only; ordinary 3/4 camera exception'
            scene['goods_art_id'] = art_id
            bpy.context.window.scene = scene
            collection = source_collection
            geometry_origin = 'Unmodified production mesh; static saved transforms, root facing S'
            if art_id == 'floor-cream':
                material = next(mat for obj in source_objects if obj.type == 'MESH'
                                and 'full_square' in obj.name for mat in obj.data.materials if mat)
                collection = bpy.data.collections.new('S12 UI-only thick cream tile')
                slab(collection, material)
                geometry_origin = 'UI-only .12-cell beveled slab, approved native floor cream material'
            scene.collection.children.link(collection)
            collection.hide_render = False
            collection.hide_viewport = False
            for obj in collection.all_objects:
                obj.hide_render = False
                obj.hide_viewport = False
                obj.hide_set(False)
            try:
                scene.render.engine = 'BLENDER_EEVEE'
            except TypeError as exc:
                raise RuntimeError('Available render engine identifiers: ' + str(exc))
            scene.eevee.taa_render_samples = 64
            scene.render.resolution_x = SIZE
            scene.render.resolution_y = SIZE
            scene.render.resolution_percentage = 100
            scene.render.pixel_aspect_x = 1
            scene.render.pixel_aspect_y = 1
            scene.render.film_transparent = True
            assert 'PNG' in [item.identifier for item in scene.render.image_settings.bl_rna.properties['file_format'].enum_items]
            scene.render.image_settings.file_format = 'PNG'
            scene.render.image_settings.color_mode = 'RGBA'
            scene.render.image_settings.color_depth = '8'
            scene.render.image_settings.compression = 100
            scene.render.dither_intensity = 0
            scene.view_settings.view_transform = 'Standard'
            scene.view_settings.look = 'None'
            scene.view_settings.exposure = 0
            scene.view_settings.gamma = 1
            scene.render.fps = 12
            scene.frame_set(1)
            bpy.context.view_layer.update()
            vertices = [obj.matrix_world @ vertex.co for obj in collection.all_objects
                        if obj.type == 'MESH' for vertex in obj.data.vertices]
            lower = Vector(tuple(min(p[i] for p in vertices) for i in range(3)))
            upper = Vector(tuple(max(p[i] for p in vertices) for i in range(3)))
            center = (lower + upper) / 2
            elevation = math.radians(ELEVATION)
            azimuth = math.radians(AZIMUTH)
            eye = Vector((math.sin(azimuth)*math.cos(elevation),
                          -math.cos(azimuth)*math.cos(elevation), math.sin(elevation)))
            camera_data = bpy.data.cameras.new('S12 goods 35-degree orthographic')
            camera_data.type = 'ORTHO'
            camera_data.sensor_fit = 'HORIZONTAL'
            camera = bpy.data.objects.new('S12 goods camera ' + art_id, camera_data)
            scene.collection.objects.link(camera)
            scene.camera = camera
            camera.rotation_euler = (-eye).to_track_quat('-Z', 'Y').to_euler()
            rotation = camera.rotation_euler.to_matrix()
            right, up = rotation @ Vector((1, 0, 0)), rotation @ Vector((0, 1, 0))
            screen = [(point.dot(right), point.dot(up)) for point in vertices]
            extents = [(min(p[i] for p in screen), max(p[i] for p in screen)) for i in (0, 1)]
            # Move the camera target to the center of the projected geometric
            # envelope. Framing is authored in 3D; raster art is never fitted.
            center += right*((sum(extents[0])/2)-center.dot(right))
            center += up*((sum(extents[1])/2)-center.dot(up))
            camera.location = center + eye * 10
            camera_data.ortho_scale = max(high-low for low, high in extents) / .82
            camera_data.shift_x = camera_data.shift_y = 0
            rig = lighting.ensure_lights(scene)
            style.ensure_compositor(scene)
            bpy.context.view_layer.update()
            materials = sorted({mat for obj in collection.all_objects if obj.type == 'MESH'
                                for mat in obj.data.materials if mat}, key=lambda m: m.name)
            camera_record = {
                'id': CAMERA_ID, 'projection': 'ordinary-orthographic-three-quarter',
                'elevation_degrees': ELEVATION, 'azimuth_degrees': AZIMUTH,
                'azimuth_convention': 'positive from front -Y toward right +X',
                'pixel_aspect': [1, 1], 'resolution': [SIZE, SIZE],
                'ortho_scale': camera_data.ortho_scale,
                'position': list(camera.location), 'target': list(center),
                'world_matrix': [list(row) for row in camera.matrix_world],
                'projection_matrix': [list(row) for row in camera.calc_matrix_camera(
                    bpy.context.evaluated_depsgraph_get(), x=SIZE, y=SIZE, scale_x=1, scale_y=1)],
            }
            record = {
                'art_id': art_id, 'scene': scene.name,
                'source_collection': COLLECTIONS[art_id],
                'native_collection': collection.name,
                'native_objects': [obj.name for obj in collection.all_objects],
                'geometry_origin': geometry_origin, 'geometry_sha256': geometry_hash(collection),
                'world_bounds': [list(lower), list(upper)], 'camera': camera_record,
                'lighting': rig, 'materials': [material_record(mat) for mat in materials],
                'contrast': {'factor': 1.35, 'space': 'sRGB', 'alpha': 'unchanged native render alpha'},
                'source_render': 'renders/' + art_id + '.png',
                'source_production_sha256': source_hash,
            }
            if art_id == 'floor-cream':
                record['floor_thickness'] = .12
                record['floor_bevel'] = .018
            state['scenes'][art_id] = scene
            state['records'][art_id] = record
        project = output / 'source/editor-goods.blend'
        project.parent.mkdir(parents=True, exist_ok=True)
        bpy.data.libraries.write(str(project), set(state['scenes'].values()), fake_user=True, compress=True)
        state['project'] = project
        state['production'] = production
        state['main_file'] = main_file
        state['previous_scene'] = previous.name
        state['dirty_before'] = dirty_before
        save_records()
        assert bpy.data.filepath == main_file
        assert sha(production) == source_hash
        return {'project': str(project), 'scenes': list(state['scenes']), 'production_unchanged': True}
    finally:
        bpy.context.window.scene = previous


def save_records():
    write(state['output'] / 'records/captures.json', {
        'schema_version': 1, 'method': 'Blender MCP native render',
        'main_file_preserved': bpy.data.filepath == state['main_file'],
        'original_scene_restored': bpy.context.window.scene.name == state['previous_scene'],
        'main_file_path': state['main_file'],
        'original_scene_name': state['previous_scene'],
        'main_file_dirty_before': state['dirty_before'],
        'production_blend': 'assets/production/source/blender/sushi-loop-world-library.blend',
        'production_blend_sha256': sha(state['production']),
        'blend': 'source/editor-goods.blend', 'blend_sha256': sha(state['project']),
        'recipe': 'source/capture_goods.py', 'recipe_sha256': sha(__file__),
        'sprites': state['records'],
    })


def render_one(art_id):
    scene = state['scenes'][art_id]
    previous = bpy.context.window.scene
    try:
        bpy.context.window.scene = scene
        destination = state['output'] / state['records'][art_id]['source_render']
        destination.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(destination)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        state['records'][art_id]['source_sha256'] = sha(destination)
        save_records()
        return {'art_id': art_id, 'image': str(destination), 'sha256': sha(destination)}
    finally:
        bpy.context.window.scene = previous


def save_project():
    # Call after all renders so each saved scene also remembers its output path.
    bpy.data.libraries.write(str(state['project']), set(state['scenes'].values()), fake_user=True, compress=True)
    save_records()
    return {'project': str(state['project']), 'sha256': sha(state['project'])}
