import sys
sys.dont_write_bytecode = True
import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector

ROOT = Path("/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype")
OUT = ROOT / "prototypes/sushi-loop/assets/refinement/objects/safe-passage/source/initial-raw-probe-v1.json"
RAW = ROOT / "prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend"
EXPECTED = "b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6"
assert hashlib.sha256(RAW.read_bytes()).hexdigest() == EXPECTED
assert not OUT.exists(), "Do not replace initial evidence"


def val(v):
    if isinstance(v, (str, int, bool, float)) or v is None: return v
    if isinstance(v, bpy.types.ID): return {"id_name": v.name, "id_type": v.bl_rna.identifier}
    if isinstance(v, dict) or hasattr(v, "to_dict"):
        return {str(k): val(v[k]) for k in v.keys()}
    try: return [val(x) for x in v]
    except TypeError: return str(v)


def props(x): return {k: val(x[k]) for k in x.keys() if k != "_RNA_UI"}
def matrix(m): return [[float(x) for x in r] for r in m]
def bounds(points):
    if not points: return None
    return {"min": [min(p[i] for p in points) for i in range(3)], "max": [max(p[i] for p in points) for i in range(3)]}
def action_info(a):
    if a is None: return None
    result = {"name": a.name, "frame_range": val(a.frame_range), "custom_properties": props(a)}
    result["slots"] = [{"identifier": s.identifier, "target_id_type": s.target_id_type} for s in getattr(a, "slots", [])]
    layers = []
    for l in getattr(a, "layers", []):
        strips = []
        for s in l.strips:
            bags = []
            for bag in getattr(s, "channelbags", []):
                bags.append({"slot_handle": bag.slot_handle, "curves": [{"data_path": f.data_path, "array_index": f.array_index, "keyframes": [val(k.co) for k in f.keyframe_points]} for f in bag.fcurves]})
            strips.append({"type": s.type, "channelbags": bags})
        layers.append({"name": l.name, "strips": strips})
    result["layers"] = layers
    return result

def animation_info(x):
    a = x.animation_data
    if a is None: return None
    return {"action": action_info(a.action), "nla_tracks": [{"name": t.name, "mute": t.mute, "strips": [{"name": s.name, "frame_start": s.frame_start, "frame_end": s.frame_end, "action": action_info(s.action)} for s in t.strips]} for t in a.nla_tracks], "drivers": [{"data_path": f.data_path, "array_index": f.array_index, "expression": f.driver.expression} for f in a.drivers]}

scene = bpy.data.scenes["Sushi33 Native Library"]
col = bpy.data.collections["S33_PROP_safe-passage.001"]
root = bpy.data.objects["safe-passage__root.001"]
objects = sorted(col.all_objects, key=lambda x: x.name)
assert root in objects
bpy.context.window.scene = scene
vl = scene.view_layers[0]
bpy.context.window.view_layer = vl

paths = []
def find_paths(c, path):
    p = path + [c]
    if c == col: paths.append(p)
    for child in c.children: find_paths(child, p)
find_paths(scene.collection, [])
assert paths, "Own collection not in authorized scene"
before_col = [{"path": [c.name for c in p], "states": [{"name": c.name, "hide_render": c.hide_render, "hide_viewport": c.hide_viewport} for c in p]} for p in paths]
for p in paths:
    for c in p: c.hide_render = False; c.hide_viewport = False

def enable_layer(lc):
    hit = lc.collection == col
    child_hits = [enable_layer(c) for c in lc.children]
    if hit or any(child_hits):
        lc.exclude = False; lc.hide_viewport = False
        return True
    return False
enable_layer(vl.layer_collection)
before_objects = [{"name": o.name, "hide_render": o.hide_render, "hide_viewport": o.hide_viewport, "hide_set": o.hide_get(view_layer=vl)} for o in objects]
for o in objects:
    o.hide_render = False; o.hide_viewport = False; o.hide_set(False, view_layer=vl)
scene.frame_set(scene.frame_current)
vl.update()
dg = bpy.context.evaluated_depsgraph_get()
dg.update()
root_inv = root.evaluated_get(dg).matrix_world.inverted()

obj_reports=[]; all_root_points=[]; materials={}
for o in objects:
    eo=o.evaluated_get(dg)
    r={"name": o.name, "type": o.type, "users_collection": [c.name for c in o.users_collection], "parent": o.parent.name if o.parent else None, "parent_type": o.parent_type, "parent_bone": o.parent_bone, "location": val(o.location), "rotation_mode": o.rotation_mode, "rotation_euler": val(o.rotation_euler), "scale": val(o.scale), "matrix_world": matrix(eo.matrix_world), "matrix_parent_inverse": matrix(o.matrix_parent_inverse), "custom_properties": props(o), "animation": animation_info(o), "constraints": [{"name": c.name, "type": c.type, "influence": c.influence, "mute": c.mute} for c in o.constraints], "modifiers": [{"name": m.name, "type": m.type, "show_viewport": m.show_viewport, "show_render": m.show_render} for m in o.modifiers], "visibility_after": {"hide_render": o.hide_render, "hide_viewport": o.hide_viewport, "hide_set": o.hide_get(view_layer=vl), "visible_get": o.visible_get(view_layer=vl)}}
    if o.type == "MESH":
        mesh = o.data
        evmesh = eo.to_mesh()
        root_pts=[root_inv @ eo.matrix_world @ v.co for v in evmesh.vertices]
        world_pts=[eo.matrix_world @ v.co for v in evmesh.vertices]
        all_root_points += root_pts
        r["mesh"]={"data_name": mesh.name, "users": mesh.users, "vertices": len(mesh.vertices), "edges": len(mesh.edges), "polygons": len(mesh.polygons), "smooth_polygons": sum(p.use_smooth for p in mesh.polygons), "uv_layers": [u.name for u in mesh.uv_layers], "shape_keys": [k.name for k in mesh.shape_keys.key_blocks] if mesh.shape_keys else None, "evaluated_vertices": len(evmesh.vertices), "evaluated_polygons": len(evmesh.polygons), "evaluated_bounds_world": bounds(world_pts), "evaluated_bounds_root": bounds(root_pts), "vertices_local": [val(v.co) for v in mesh.vertices] if len(mesh.vertices)<=2000 else "omitted over 2000", "polygons_indices": [list(p.vertices) for p in mesh.polygons] if len(mesh.polygons)<=2000 else "omitted over 2000", "custom_properties": props(mesh), "animation": animation_info(mesh)}
        r["materials"]=[s.material.name if s.material else None for s in o.material_slots]
        r["material_polygon_counts"]={str(i): sum(p.material_index == i for p in mesh.polygons) for i in range(len(o.material_slots))}
        for slot in o.material_slots:
            mat=slot.material
            if mat is None or mat.name in materials: continue
            mr={"name": mat.name, "diffuse_color": val(mat.diffuse_color), "use_nodes": mat.use_nodes, "custom_properties": props(mat), "animation": animation_info(mat)}
            if mat.use_nodes:
                mr["nodes"]=[{"name": n.name, "type": n.type, "inputs": {i.name: val(i.default_value) for i in n.inputs if hasattr(i,"default_value") and not i.is_linked}} for n in mat.node_tree.nodes]
                mr["links"]=[{"from": l.from_node.name+"."+l.from_socket.name, "to": l.to_node.name+"."+l.to_socket.name} for l in mat.node_tree.links]
            materials[mat.name]=mr
        eo.to_mesh_clear()
    if o.type == "ARMATURE":
        r["pose"]=[{"name": b.name, "parent": b.parent.name if b.parent else None, "matrix": matrix(b.matrix), "custom_properties": props(b)} for b in o.pose.bones]
    obj_reports.append(r)

camera=scene.camera
report={"purpose": "Read-only independent initial inspection; no construction or capture locks inferred", "source": {"path": str(RAW), "sha256_before": EXPECTED, "sha256_after": hashlib.sha256(RAW.read_bytes()).hexdigest()}, "runtime": {"version": bpy.app.version_string, "binary": bpy.app.binary_path, "active_scene": bpy.context.scene.name, "active_view_layer": bpy.context.view_layer.name}, "scene": {"name": scene.name, "frame_current": scene.frame_current, "frame_start": scene.frame_start, "frame_end": scene.frame_end, "render_resolution": [scene.render.resolution_x, scene.render.resolution_y], "resolution_percentage": scene.render.resolution_percentage, "pixel_aspect": [scene.render.pixel_aspect_x, scene.render.pixel_aspect_y], "render_engine": scene.render.engine, "film_transparent": scene.render.film_transparent, "custom_properties": props(scene), "saved_scene_camera_observation_only": {"name": camera.name, "type": camera.data.type, "ortho_scale": camera.data.ortho_scale, "location": val(camera.location), "rotation_euler": val(camera.rotation_euler), "matrix_world": matrix(camera.evaluated_get(dg).matrix_world)} if camera else None}, "collection": {"name": col.name, "direct_objects": sorted(o.name for o in col.objects), "children": sorted(c.name for c in col.children), "custom_properties": props(col), "ancestry_before": before_col}, "objects_visibility_before": before_objects, "root": root.name, "evaluated_all_mesh_bounds_root": bounds(all_root_points), "objects": obj_reports, "materials": list(materials.values()), "not_performed": ["render", "model construction", "model save", "target generation", "live Blender access", "candidate assessment", "contract inference"]}
assert report["source"]["sha256_after"] == EXPECTED
with OUT.open("x") as f: json.dump(report,f,indent=2,sort_keys=True); f.write("\n")
print(json.dumps({"report": str(OUT), "report_bytes": OUT.stat().st_size, "report_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(), "object_count": len(objects), "mesh_count": sum(o.type=="MESH" for o in objects), "material_count": len(materials), "bounds_root": report["evaluated_all_mesh_bounds_root"]}))
