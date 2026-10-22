"""Independent original-native observation. Read-only, no candidate or render construction."""
import bpy, json, hashlib, datetime
from pathlib import Path
source = Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/backups/b1765262bfa897ad-sushi-loop-world-library.blend')
out = Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/wreck-middle/source/original-native-measurements.json')
bpy.ops.wm.open_mainfile(filepath=str(source))
matching = [c for c in bpy.data.collections if 'wreck' in c.name.lower() and 'middle' in c.name.lower()]
if len(matching) != 1:
    raise RuntimeError('Expected one own collection: ' + repr([c.name for c in matching]))
c = matching[0]
original_scene=bpy.context.scene
# The library scene excludes inactive assets. Instantiate only the unchanged own
# collection in an unsaved measurement scene so native parent transforms evaluate.
inspection_scene=bpy.data.scenes.new('wreck-middle read-only inspection')
inspection_scene.collection.children.link(c)
visibility_before={'collection_hide_viewport':c.hide_viewport, 'objects': {o.name:{'hide_viewport':o.hide_viewport,'hide_render':o.hide_render} for o in c.all_objects}}
c.hide_viewport=False
for o in c.all_objects:
    o.hide_viewport=False
    o.hide_set(False, view_layer=inspection_scene.view_layers[0])
bpy.context.window.scene=inspection_scene
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
objects = []
all_points=[]
for o in sorted(c.all_objects, key=lambda x:x.name):
    d = dict(name=o.name, type=o.type, parent=o.parent.name if o.parent else None, location=list(o.location), rotation_euler=list(o.rotation_euler), scale=list(o.scale), matrix_world=[list(row) for row in o.matrix_world], hide_render=o.hide_render, modifiers=[dict(name=m.name,type=m.type) for m in o.modifiers])
    if o.type == 'MESH':
        eo=o.evaluated_get(dg); me=eo.to_mesh()
        pts=[eo.matrix_world@v.co for v in me.vertices]
        d.update(vertices=len(o.data.vertices), edges=len(o.data.edges), polygons=len(o.data.polygons), evaluated_vertices=len(me.vertices), evaluated_polygons=len(me.polygons), smooth_polygon_count=sum(p.use_smooth for p in me.polygons), bounds={a:[min(p[i] for p in pts),max(p[i] for p in pts)] for i,a in enumerate('xyz')}, materials=[])
        for mat in o.data.materials:
            md=dict(name=mat.name, diffuse_color=list(mat.diffuse_color), use_nodes=mat.use_nodes)
            if mat.use_nodes:
                md['node_types']=[n.bl_idname for n in mat.node_tree.nodes]
                md['principled']=[{k: list(n.inputs[k].default_value) if hasattr(n.inputs[k].default_value,'__len__') else n.inputs[k].default_value for k in ['Base Color','Metallic','Roughness'] if k in n.inputs} for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED']
            d['materials'].append(md)
        all_points.extend([list(p) for p in pts]); eo.to_mesh_clear()
    objects.append(d)
scene=original_scene
result=dict(observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), source=str(source), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), blender_version=bpy.app.version_string, collection=c.name, collection_properties=dict(c.items()), visibility_before=visibility_before, object_count=len(objects), objects=objects, evaluated_collection_bounds={a:[min(p[i] for p in all_points),max(p[i] for p in all_points)] for i,a in enumerate('xyz')}, measurement_context='Unsaved temporary scene linking only the original collection; viewport visibility enabled only for dependency evaluation; no geometry/material/transform edits, render or source save', scene=dict(name=scene.name,camera=scene.camera.name if scene.camera else None, render_engine=scene.render.engine, resolution=[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage], pixel_aspect=[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],film_transparent=scene.render.film_transparent, frame=scene.frame_current))
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['objects','collection_properties']},indent=2))
print('Object names:', [o['name'] for o in objects])
