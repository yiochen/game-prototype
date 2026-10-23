"""Bounded initial-only read-only inspection of the authorized raw asset.

Visibility and active-scene changes exist only in this background process.
This script does not render, construct geometry, or save a blend file.
"""
import bpy
import json
from pathlib import Path
from mathutils import Vector

OUTPUT = Path(__file__).with_name("initial-native-probe.json")
SCENE = "S33 Native Asset Library Export"
COLLECTION = "S33_CFX_attack-reef-fragments.001"
ROOT = "attack-reef-fragments__ground_root.001"

def vec(v):
    return [float(x) for x in v]

def mat(m):
    return [vec(row) for row in m]

def clean(v):
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if hasattr(v, "to_dict"):
        return {str(k): clean(x) for k, x in v.to_dict().items()}
    if hasattr(v, "to_list"):
        return clean(v.to_list())
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [clean(x) for x in v]
    try:
        return [clean(x) for x in v]
    except TypeError:
        return str(v)

def props(x):
    return {k: clean(x[k]) for k in x.keys() if k != "_RNA_UI"}

def local_pose(o):
    return {
        "location": vec(o.location), "rotation_mode": o.rotation_mode,
        "rotation_euler": vec(o.rotation_euler),
        "rotation_quaternion": vec(o.rotation_quaternion),
        "rotation_axis_angle": vec(o.rotation_axis_angle),
        "scale": vec(o.scale), "delta_location": vec(o.delta_location),
        "delta_rotation_euler": vec(o.delta_rotation_euler),
        "delta_scale": vec(o.delta_scale),
        "matrix_parent_inverse": mat(o.matrix_parent_inverse),
    }

def bounds(points):
    points = list(points)
    if not points:
        return None
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    return {"min": lo, "max": hi, "span": [hi[i] - lo[i] for i in range(3)]}

def curves(action):
    found = []
    try:
        found.extend(list(action.fcurves))
    except (AttributeError, RuntimeError):
        pass
    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            for bag in getattr(strip, "channelbags", []):
                found.extend(list(bag.fcurves))
    unique = {}
    for fc in found:
        unique[(fc.data_path, fc.array_index)] = {
            "data_path": fc.data_path, "array_index": fc.array_index,
            "keyframes": [{"co": vec(k.co), "interpolation": k.interpolation} for k in fc.keyframe_points],
            "modifiers": [m.type for m in fc.modifiers],
        }
    return list(unique.values())

def animation(o):
    ad = o.animation_data
    if ad is None:
        return None
    actions = {}
    if ad.action:
        actions[ad.action.name] = ad.action
    tracks = []
    for track in ad.nla_tracks:
        strips = []
        for s in track.strips:
            if s.action:
                actions[s.action.name] = s.action
            strips.append({"name": s.name, "action": s.action.name if s.action else None,
                           "frame_start": s.frame_start, "frame_end": s.frame_end,
                           "mute": s.mute, "influence": s.influence})
        tracks.append({"name": track.name, "mute": track.mute, "strips": strips})
    return {"active_action": ad.action.name if ad.action else None,
            "use_nla": ad.use_nla, "action_blend_type": ad.action_blend_type,
            "action_influence": ad.action_influence,
            "nla_tracks": tracks,
            "drivers": [{"data_path": d.data_path, "array_index": d.array_index,
                         "type": d.driver.type, "expression": d.driver.expression}
                        for d in ad.drivers],
            "actions": [{"name": a.name, "frame_range": vec(a.frame_range), "curves": curves(a)}
                        for a in actions.values()]}

scene = bpy.data.scenes.get(SCENE)
collection = bpy.data.collections.get(COLLECTION)
root = bpy.data.objects.get(ROOT)
assert scene is not None, SCENE
assert collection is not None, COLLECTION
assert root is not None, ROOT
assert root in list(collection.all_objects), "Root is outside own collection"
bpy.context.window.scene = scene
view_layer = scene.view_layers[0]
bpy.context.window.view_layer = view_layer
owned = sorted(collection.all_objects, key=lambda o: o.name)
owned_names = {o.name for o in owned}

def layer_paths(lc, path):
    here = path + [lc]
    results = [here] if lc.collection == collection else []
    for ch in lc.children:
        results.extend(layer_paths(ch, here))
    return results

paths = layer_paths(view_layer.layer_collection, [])
assert paths, "Own collection is outside selected actual scene/view layer"
raw_visibility = {
    "layers": [[{"name": x.name, "exclude": x.exclude, "hide_viewport": x.hide_viewport,
                 "collection_hide_render": x.collection.hide_render,
                 "collection_hide_viewport": x.collection.hide_viewport}
                for x in path] for path in paths],
    "objects": {o.name: {"hide_render": o.hide_render, "hide_viewport": o.hide_viewport,
                          "hide_set": o.hide_get(view_layer=view_layer)} for o in owned},
}
raw_local_poses = {o.name: local_pose(o) for o in owned}
for path in paths:
    for lc in path:
        lc.exclude = False
        lc.hide_viewport = False
        lc.collection.hide_render = False
        lc.collection.hide_viewport = False
for o in owned:
    o.hide_render = False
    o.hide_viewport = False
    o.hide_set(False, view_layer=view_layer)
scene.frame_set(scene.frame_current, subframe=scene.frame_subframe)
view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
depsgraph.update()
root_eval = root.evaluated_get(depsgraph)
root_inverse = root_eval.matrix_world.inverted_safe()
all_world_points = []
all_root_points = []
objects = []
for o in owned:
    ev = o.evaluated_get(depsgraph)
    entry = {"name": o.name, "type": o.type,
             "data": o.data.name if o.data else None,
             "collections": [c.name for c in o.users_collection],
             "parent": o.parent.name if o.parent else None,
             "parent_in_own_collection": o.parent.name in owned_names if o.parent else None,
             "parent_type": o.parent_type, "parent_bone": o.parent_bone,
             "children": [c.name for c in o.children],
             "custom_properties": props(o), "raw_local_pose": raw_local_poses[o.name],
             "updated_local_pose": local_pose(o),
             "evaluated_matrix_world": mat(ev.matrix_world),
             "evaluated_matrix_root_relative": mat(root_inverse @ ev.matrix_world),
             "visibility_after_enable": {"hide_render": o.hide_render, "hide_viewport": o.hide_viewport,
                                         "hide_set": o.hide_get(view_layer=view_layer),
                                         "visible_get": o.visible_get(view_layer=view_layer)},
             "modifiers": [{"name": m.name, "type": m.type,
                            "show_viewport": m.show_viewport, "show_render": m.show_render} for m in o.modifiers],
             "constraints": [{"name": c.name, "type": c.type, "mute": c.mute,
                              "influence": c.influence} for c in o.constraints],
             "animation": animation(o)}
    if o.type == "MESH":
        me = o.data
        edge_counts = [0] * len(me.edges)
        edge_index = {tuple(sorted(e.vertices)): i for i, e in enumerate(me.edges)}
        for p in me.polygons:
            for ek in p.edge_keys:
                edge_counts[edge_index[tuple(sorted(ek))]] += 1
        poly_sizes = {}
        for p in me.polygons:
            poly_sizes[str(len(p.vertices))] = poly_sizes.get(str(len(p.vertices)), 0) + 1
        eval_mesh = ev.to_mesh()
        wp = [ev.matrix_world @ v.co for v in eval_mesh.vertices]
        rp = [root_inverse @ p for p in wp]
        all_world_points.extend(wp)
        all_root_points.extend(rp)
        entry["mesh"] = {"vertices": len(me.vertices), "edges": len(me.edges),
                         "polygons": len(me.polygons), "polygon_sizes": poly_sizes,
                         "smooth_faces": sum(p.use_smooth for p in me.polygons),
                         "boundary_edges": sum(c == 1 for c in edge_counts),
                         "nonmanifold_edges": sum(c != 2 for c in edge_counts),
                         "local_bounds": bounds(v.co for v in me.vertices),
                         "evaluated_world_bounds": bounds(wp),
                         "evaluated_root_relative_bounds": bounds(rp),
                         "evaluated_vertices": len(eval_mesh.vertices),
                         "evaluated_polygons": len(eval_mesh.polygons),
                         "material_slots": [m.name if m else None for m in me.materials],
                         "face_material_index_counts": {str(i): sum(p.material_index == i for p in me.polygons)
                                                        for i in set(p.material_index for p in me.polygons)},
                         "uv_layers": [x.name for x in me.uv_layers],
                         "attributes": [{"name": a.name, "domain": a.domain, "data_type": a.data_type}
                                        for a in me.attributes],
                         "shape_keys": [k.name for k in me.shape_keys.key_blocks] if me.shape_keys else [],
                         "vertex_groups": [g.name for g in o.vertex_groups]}
        ev.to_mesh_clear()
    objects.append(entry)

materials = {}
for o in owned:
    for slot in o.material_slots:
        material = slot.material
        if material is None or material.name in materials:
            continue
        nodes = []
        links = []
        if material.use_nodes and material.node_tree:
            for n in material.node_tree.nodes:
                defaults = {}
                for sock in n.inputs:
                    if hasattr(sock, "default_value"):
                        defaults[sock.name] = clean(sock.default_value)
                nodes.append({"name": n.name, "type": n.bl_idname,
                              "inputs": defaults,
                              "image": {"name": n.image.name, "filepath": n.image.filepath,
                                        "packed": bool(n.image.packed_file)}
                                       if getattr(n, "image", None) else None})
            links = [{"from_node": l.from_node.name, "from_socket": l.from_socket.name,
                      "to_node": l.to_node.name, "to_socket": l.to_socket.name}
                     for l in material.node_tree.links]
        materials[material.name] = {"diffuse_color": vec(material.diffuse_color),
                                    "roughness": material.roughness, "metallic": material.metallic,
                                    "use_nodes": material.use_nodes, "nodes": nodes, "links": links,
                                    "animation": animation(material), "custom_properties": props(material)}

camera = scene.camera
camera_report = None
if camera:
    camera_report = {"name": camera.name, "type": camera.data.type,
                     "ortho_scale": camera.data.ortho_scale, "lens": camera.data.lens,
                     "shift_x": camera.data.shift_x, "shift_y": camera.data.shift_y,
                     "clip_start": camera.data.clip_start, "clip_end": camera.data.clip_end,
                     "matrix_world": mat(camera.evaluated_get(depsgraph).matrix_world)}
lights = [{"name": o.name, "type": o.data.type, "energy": o.data.energy,
           "color": vec(o.data.color), "matrix_world": mat(o.evaluated_get(depsgraph).matrix_world),
           "hide_render": o.hide_render, "hide_viewport": o.hide_viewport}
          for o in scene.objects if o.type == "LIGHT"]
report = {"scope": "initial-only raw read-only probe; no render, construction, or blend save",
          "source_path": bpy.data.filepath, "blender_version": bpy.app.version_string,
          "scene": scene.name, "view_layer": view_layer.name,
          "collection": collection.name, "root": root.name,
          "frame_current": scene.frame_current, "frame_subframe": scene.frame_subframe,
          "frame_start": scene.frame_start, "frame_end": scene.frame_end,
          "fps": scene.render.fps, "fps_base": scene.render.fps_base,
          "collection_custom_properties": props(collection),
          "raw_visibility": raw_visibility,
          "visibility_enabled_before_evaluated_measurements": True,
          "depsgraph_updated_before_evaluated_measurements": True,
          "objects": objects, "materials": materials,
          "evaluated_union_world_bounds": bounds(all_world_points),
          "evaluated_union_root_relative_bounds": bounds(all_root_points),
          "raw_scene_capture_settings": {
              "active_camera": camera_report, "resolution_x": scene.render.resolution_x,
              "resolution_y": scene.render.resolution_y,
              "resolution_percentage": scene.render.resolution_percentage,
              "pixel_aspect_x": scene.render.pixel_aspect_x,
              "pixel_aspect_y": scene.render.pixel_aspect_y,
              "film_transparent": scene.render.film_transparent,
              "engine": scene.render.engine, "view_transform": scene.view_settings.view_transform,
              "look": scene.view_settings.look, "exposure": scene.view_settings.exposure,
              "gamma": scene.view_settings.gamma,
              "world": scene.world.name if scene.world else None, "lights": lights},
          "limits": ["Raw scene settings are observations, not a frozen future capture contract.",
                     "No camera, size, envelope, or contact lock is inferred from target pixels.",
                     "Only own collection geometry, ownership, materials, and actions were inspected.",
                     "No other experiment brief, criteria, review, or preparation analysis was read."]}
payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
assert len(payload.encode()) < 100_000_000
with OUTPUT.open("x") as f:
    f.write(payload)
print("INITIAL_ONLY_PROBE_SAVED", str(OUTPUT), len(owned), "objects")
