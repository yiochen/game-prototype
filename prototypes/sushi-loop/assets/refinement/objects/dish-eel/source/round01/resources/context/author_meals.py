"""Run through Blender MCP. Derive meal-specific clips from approved native art.

Only held ImageGen food geometry/UV/visibility may change. Never save_mainfile,
modify approved collections, or load a different file into the user's session.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import struct
import sys
import bpy

HERE = Path(__file__).resolve().parent
PRODUCTION = HERE.parents[2]
HELPERS = PRODUCTION / 'source/blender'
BASE_BLEND = HELPERS / 'sushi-loop-world-library.blend'
FOOD = PRODUCTION / 'source/2d/generated/dish-salmon.png'
IDS = ['customer-rosa', 'customer-ellis', 'customer-samir', 'customer-june']
CLIPS = {'eat-salmon': 'eat', 'seated-wait-empty': 'seated_wait'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def body_hash(objects):
    result = {}
    for name, obj in objects.items():
        if obj.type == 'MESH' and obj.get('representation') != '2D ImageGen sprite, not modeled sushi':
            raw = b''.join(struct.pack('<3f', *vertex.co) for vertex in obj.data.vertices)
            raw += json.dumps([list(p.vertices) for p in obj.data.polygons]).encode()
            result[name] = hashlib.sha256(raw).hexdigest()
        elif obj.type == 'ARMATURE':
            result[name] = hashlib.sha256(json.dumps({b.name: [list(row) for row in b.matrix_local] for b in obj.data.bones}, sort_keys=True).encode()).hexdigest()
    return result


def action_hash(native, action):
    return hashlib.sha256(json.dumps([(curve.data_path, curve.array_index, [(list(k.co), k.interpolation) for k in curve.keyframe_points]) for curve in native._fcurves(action)], sort_keys=True).encode()).hexdigest()


def author():
    previous_scene = bpy.context.window.scene
    previous_file = bpy.data.filepath
    native = module('s10_meal_native', HELPERS / 'native_actions.py')
    runtime = module('s10_meal_runtime', HELPERS / 'capture_runtime.py')
    composition = module('s10_meal_composition', HELPERS / 'character_composition.py')
    originals = {aid: json.loads((PRODUCTION / 'source/records' / aid / 'rig.json').read_text()) for aid in IDS}
    action_names = sorted({t['action'] for record in originals.values() for clip in CLIPS.values() for t in record['clips'][clip]['actions']})
    with bpy.data.libraries.load(str(BASE_BLEND), link=False) as (available, loaded):
        object_names = [name for name in available.objects if any(name.startswith(aid.replace('-', '_') + '__') for aid in IDS)]
        collection_names = [name for name in available.collections if any(name.startswith('S33_CHARACTER_' + aid.replace('-', '_')) for aid in IDS)]
        assert len(collection_names) == 4, collection_names
        loaded.objects = list(object_names)
        loaded.collections = list(collection_names)
        loaded.actions = list(action_names)
    object_map = dict(zip(object_names, loaded.objects))
    action_map = dict(zip(action_names, loaded.actions))
    for name, obj in object_map.items():
        obj.name = 'S10 meal ' + name
    for name, action in action_map.items():
        action.name = 'S10 meal ' + name
    scene = bpy.data.scenes.new('S10 Starter Meal Variants')
    scene['source'] = 'native_actions.py'
    scene['issue'] = 33 # Existing capture worker selects a native export scene.
    scene['gameplay_issue'] = 10
    scene['meal_variants'] = True
    bpy.context.window.scene = scene
    bpy.context.window.view_layer = scene.view_layers[0]
    for collection in loaded.collections:
        collection.name = 'S10 meal ' + collection.name
        collection.hide_render = False
        collection.hide_viewport = False
        scene.collection.children.link(collection)
    source_body = body_hash(object_map)
    image = bpy.data.images.load(str(FOOD), check_existing=False)
    image.name = 'S10 approved ImageGen salmon'
    image.alpha_mode = 'STRAIGHT'
    image.pack()
    rectangle = composition._alpha_rectangle(image)
    x0, y0, x1, y1 = rectangle
    records, assets, edits = {}, {}, {}
    for aid in IDS:
        original = originals[aid]
        root = object_map[original['groundRootObject']]
        collection = next(c for c in loaded.collections if root in list(c.all_objects))
        plane = next(o for o in collection.all_objects if o.get('representation') == '2D ImageGen sprite, not modeled sushi')
        old_plane_name = next(name for name, obj in object_map.items() if obj == plane)
        plane.data = plane.data.copy()
        mat = plane.data.materials[0].copy()
        plane.data.materials[0] = mat
        texture = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE')
        texture.image = image
        native_scale = float(root.get('uniform_native_scale', 1.25))
        width = composition.SPRITE_WIDTH_CELLS / native_scale
        height = width * (y1 - y0) / (x1 - x0)
        vertices = [(-width/2, 0, 0), (width/2, 0, 0), (width/2, height, 0), (-width/2, height, 0)]
        assert len(plane.data.vertices) == 4
        for vertex, value in zip(plane.data.vertices, vertices):
            vertex.co = value
        uv = plane.data.uv_layers.active
        coords = [(x0/image.size[0], y0/image.size[1]), (x1/image.size[0], y0/image.size[1]), (x1/image.size[0], y1/image.size[1]), (x0/image.size[0], y1/image.size[1])]
        for polygon in plane.data.polygons:
            for index in polygon.loop_indices:
                uv.data[index].uv = coords[plane.data.loops[index].vertex_index]
        plane['source_image'] = str(FOOD)
        plane['source_sha256'] = sha(FOOD)
        plane['fixed_alpha_rectangle'] = json.dumps(rectangle)
        plane['meal_variant'] = 'salmon eating; no food while waiting'
        record = copy.deepcopy(original)
        record['groundRootObject'] = root.name
        record['clips'] = {}
        edit = {'foodPlane': plane.name, 'foodSourceSha256': sha(FOOD), 'foodAlphaRectangle': rectangle, 'unchangedActions': [], 'emptyVisibilityKeys': []}
        for variant, source_clip in CLIPS.items():
            action_record = copy.deepcopy(original['clips'][source_clip])
            for target in action_record['actions']:
                old_name = target['ownerName']
                target['ownerName'] = object_map[old_name].name
                action = action_map[target['action']]
                target['action'] = action.name
                before = action_hash(native, action)
                if variant == 'seated-wait-empty' and old_name == old_plane_name:
                    for curve in native._fcurves(action):
                        if curve.data_path in ['hide_render', 'hide_viewport']:
                            for key in curve.keyframe_points:
                                key.co.y = 1
                                key.handle_left.y = 1
                                key.handle_right.y = 1
                            edit['emptyVisibilityKeys'].append(curve.data_path)
                    assert edit['emptyVisibilityKeys'], 'No native visibility keys'
                else:
                    assert action_hash(native, action) == before
                    edit['unchangedActions'].append({'clip': variant, 'owner': target['ownerName'], 'sha256': before})
            record['clips'][variant] = action_record
        asset = json.loads((PRODUCTION / 'source/records' / aid / 'asset.json').read_text())
        asset['clips'] = {key: {'frames': 12, 'fps': 12, 'loop': True} for key in CLIPS}
        asset['directions'] = ['N', 'E', 'S', 'W']
        asset['variantSource'] = {'baseBlendSha256': sha(BASE_BLEND), 'approvedFoodSha256': sha(FOOD), 'edits': edit}
        write(HERE / 'export/source' / aid / 'asset.json', asset)
        write(HERE / 'export/source' / aid / 'rig.json', record)
        assets[aid] = {**asset, 'root': root, 'collection': collection}
        records[aid] = record
        edits[aid] = edit
    assert body_hash(object_map) == source_body, 'Body geometry/armature rest data changed'
    runtime.scene = lambda: scene
    runtime.SCENE_NAME = scene.name
    with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0]):
        camera = runtime.configure_camera('character-orthographic', (192, 320), (96, 248), 4)
        native.apply_clip(assets[IDS[0]], records[IDS[0]], 'eat-salmon', frame=5, direction='S', scene=scene)
    for aid, asset in assets.items():
        asset['collection'].hide_render = aid != IDS[0]
        asset['collection'].hide_viewport = aid != IDS[0]
    scene.view_layers[0].update()
    actions = set(action_map.values())
    owned = {o for asset in assets.values() for o in asset['collection'].all_objects}
    foreign = [o.name for o in scene.objects if o not in owned and o.type not in ['CAMERA', 'LIGHT']]
    assert not foreign, foreign
    blend = HERE / 'starter-meals.blend'
    bpy.data.libraries.write(str(blend), {scene, *actions}, fake_user=True, compress=True)
    write(HERE / 'export/source/native-actions/library-actions.json', {'version': 1, 'fps': 12, 'source': 'native_actions.py', 'assets': records})
    write(HERE / 'authorship.json', {
        'version': 1, 'issue': 10, 'userPrompt': 'Merge into main. Then continue on issue 10',
        'baseBlend': {'path': str(BASE_BLEND.relative_to(PRODUCTION.parent.parent)), 'sha256': sha(BASE_BLEND)},
        'derivativeBlend': {'file': blend.name, 'sha256': sha(blend)},
        'approvedFood': {'path': str(FOOD.relative_to(PRODUCTION.parent.parent)), 'sha256': sha(FOOD)},
        'authorScriptSha256': sha(__file__), 'bodyGeometryUnchanged': True, 'bodyGeometry': source_body,
        'camera': camera, 'edits': edits, 'ownedObjects': len(owned), 'foreignObjects': foreign,
        'captureContract': {'frameSize': [192, 320], 'root': [96, 248], 'sourceScale': 4, 'runtimeScale': 2, 'frames': 12, 'fps': 12, 'directions': ['N', 'E', 'S', 'W']},
        'changes': ['Use original approved ImageGen salmon cutout on native hand-attached alpha plane; fixed source rectangle and aspect', 'Hide only the held-food plane throughout seated waiting', 'Retain all native body, armature, pose, root, material and lighting data'],
        'userFilePreserved': bpy.data.filepath == previous_file,
    })
    globals()['STATE'] = {'scene': scene, 'previous_scene': previous_scene, 'assets': assets, 'records': records, 'native': native, 'runtime': runtime}
    return {'path': str(blend), 'sha256': sha(blend), 'objects': len(owned), 'bodyGeometryUnchanged': True, 'camera': camera, 'sourceScene': previous_scene.name}
