"""Bounded, read-only inspection of the untouched decor-kelp source collection.

No scene, object, mesh, material or capture setting is changed or saved.
"""
import bpy
import json
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).with_name("original-collection-probe.json")
SCENE = "S33 Native Asset Library Export"
COLLECTION = "S33 production concept kelp-fan"
ROOT = "S33 production concept kelp-fan root"
scene = bpy.data.scenes.get(SCENE)
collection = bpy.data.collections.get(COLLECTION)
root = bpy.data.objects.get(ROOT)
assert scene is not None and collection is not None and root is not None

def rounded(v):
    return [round(float(x), 8) for x in v]

objects = []
all_points = []
depsgraph = bpy.context.evaluated_depsgraph_get()
for obj in sorted(collection.all_objects, key=lambda item: item.name):
    row = {
        "name": obj.name,
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "location": rounded(obj.location),
        "rotation_euler": rounded(obj.rotation_euler),
        "scale": rounded(obj.scale),
        "matrix_world": [rounded(r) for r in obj.matrix_world],
        "hide_render": obj.hide_render,
        "hide_viewport": obj.hide_viewport,
        "custom_properties": {key: str(obj[key]) for key in obj.keys()},
        "modifiers": [{"name": m.name, "type": m.type} for m in obj.modifiers],
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "animation_action": obj.animation_data.action.name if obj.animation_data and obj.animation_data.action else None,
        "constraints": [{"name": c.name, "type": c.type} for c in obj.constraints],
    }
    if obj.type == "MESH":
        mesh = obj.data
        evaluated = obj.evaluated_get(depsgraph)
        evaluated_mesh = evaluated.to_mesh()
        pts = [evaluated.matrix_world @ v.co for v in evaluated_mesh.vertices]
        all_points.extend(pts)
        row.update({
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "polygons": len(mesh.polygons),
            "smooth_polygons": sum(p.use_smooth for p in mesh.polygons),
            "uv_layers": [layer.name for layer in mesh.uv_layers],
            "shape_keys": [key.name for key in mesh.shape_keys.key_blocks] if mesh.shape_keys else [],
            "vertex_groups": [group.name for group in obj.vertex_groups],
            "evaluated_vertices": len(evaluated_mesh.vertices),
            "evaluated_world_bounds": {
                "minimum": [round(min(p[i] for p in pts), 8) for i in range(3)],
                "maximum": [round(max(p[i] for p in pts), 8) for i in range(3)],
            } if pts else None,
        })
        evaluated.to_mesh_clear()
    objects.append(row)

materials = []
used_names = sorted({name for row in objects for name in row["materials"] if name})
for name in used_names:
    mat = bpy.data.materials[name]
    materials.append({
        "name": name,
        "diffuse_color": rounded(mat.diffuse_color),
        "use_nodes": mat.use_nodes,
        "nodes": [{"name": node.name, "type": node.type} for node in mat.node_tree.nodes] if mat.node_tree else [],
    })

result = {
    "purpose": "Independent actual-original collection inspection only; no candidate construction or scene writes.",
    "blender_version": bpy.app.version_string,
    "input_filepath": bpy.data.filepath,
    "scene_identity": {"name": scene.name, "frame_current": scene.frame_current, "frame_start": scene.frame_start, "frame_end": scene.frame_end, "camera": scene.camera.name if scene.camera else None},
    "collection_identity": {"name": collection.name, "object_count": len(collection.all_objects)},
    "root_identity": {"name": root.name, "type": root.type, "in_collection": root.name in collection.all_objects, "location": rounded(root.location), "rotation_euler": rounded(root.rotation_euler), "scale": rounded(root.scale)},
    "collection_evaluated_world_bounds": {
        "minimum": [round(min(p[i] for p in all_points), 8) for i in range(3)],
        "maximum": [round(max(p[i] for p in all_points), 8) for i in range(3)],
    },
    "objects": objects,
    "materials": materials,
}
assert not OUT.exists(), "Preserve the first independent probe as immutable evidence"
OUT.write_text(json.dumps(result, indent=2) + "\n")
print("DECOR_KELP_ORIGINAL_PROBE", json.dumps({"scene": scene.name, "collection": collection.name, "root": root.name, "object_count": len(objects), "bounds": result["collection_evaluated_world_bounds"], "output": str(OUT)}))
