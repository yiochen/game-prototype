import bpy, json, hashlib, datetime
from pathlib import Path
from mathutils import Vector
out=Path(__file__).parent/'initial-native-probe.json'
raw=Path(bpy.data.filepath)
collection_name='S33 production concept cobalt-shelf.001'
root_name='S33 production concept cobalt-shelf root.001'
col=bpy.data.collections.get(collection_name)
assert col is not None, collection_name
root=bpy.data.objects.get(root_name)
assert root is not None, root_name
scene=bpy.context.scene
vl=bpy.context.view_layer
# Saved hidden transforms may be stale. Expose the real collection and descendants
# transiently in the active scene/view layer, then evaluate before measurements.
if col.name not in scene.collection.children.keys() and not any(o in scene.objects[:] for o in col.all_objects):
    scene.collection.children.link(col)
objects=list(col.all_objects)
original_visibility={o.name:{'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'hide_get':o.hide_get()} for o in objects}
col.hide_render=False
col.hide_viewport=False
for o in objects:
    o.hide_render=False
    o.hide_viewport=False
    o.hide_set(False)
def expose_layer(lc, ancestor=False):
    is_own=(lc.collection==col)
    has_own=is_own or any(c.collection==col for c in lc.children_recursive) if hasattr(lc,'children_recursive') else False
    # Traverse paths, setting only ancestors and own subtree via returned containment.
    contains=is_own
    for c in lc.children:
        contains=expose_layer(c,ancestor or is_own) or contains
    if contains or ancestor:
        lc.exclude=False
        lc.hide_viewport=False
        lc.collection.hide_viewport=False
        lc.collection.hide_render=False
    return contains
expose_layer(vl.layer_collection)
vl.update()
dg=bpy.context.evaluated_depsgraph_get()
dg.update()
def vector(v): return [float(x) for x in v]
def matrix(m): return [[float(x) for x in row] for row in m]
def bbox(coords):
    return {'min':[min(v[i] for v in coords) for i in range(3)],'max':[max(v[i] for v in coords) for i in range(3)]} if coords else None
observations=[]
all_points=[]
materials={}
for o in sorted(objects,key=lambda o:o.name):
    ev=o.evaluated_get(dg)
    rec={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location_local':vector(o.location),'rotation_euler_local':vector(o.rotation_euler),'scale_local':vector(o.scale),'matrix_world_evaluated':matrix(ev.matrix_world),'dimensions_evaluated':vector(ev.dimensions),'visibility_before_transient_enable':original_visibility[o.name],'visible_after_enable':o.visible_get(),'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]}
    if o.type=='MESH':
        mesh=ev.to_mesh()
        pts=[ev.matrix_world@v.co for v in mesh.vertices]
        all_points+=pts
        rec['evaluated_mesh']={'vertices':len(mesh.vertices),'edges':len(mesh.edges),'polygons':len(mesh.polygons),'polygon_vertex_counts':sorted(set(len(p.vertices) for p in mesh.polygons)),'smooth_polygon_count':sum(p.use_smooth for p in mesh.polygons),'world_bounds':bbox(pts),'material_slots':[m.name if m else None for m in o.data.materials],'uv_layers':[u.name for u in mesh.uv_layers]}
        ev.to_mesh_clear()
        for m in o.data.materials:
            if m and m.name not in materials:
                md={'name':m.name,'diffuse_color':vector(m.diffuse_color),'use_nodes':m.use_nodes,'nodes':[]}
                if m.use_nodes:
                    for n in m.node_tree.nodes:
                        nd={'name':n.name,'type':n.type,'inputs':{}}
                        for i in n.inputs:
                            if not i.is_linked and hasattr(i,'default_value'):
                                val=i.default_value
                                if isinstance(val,(float,int,str,bool)): nd['inputs'][i.name]=val
                                elif hasattr(val,'__iter__'):
                                    try: nd['inputs'][i.name]=vector(val)
                                    except TypeError: pass
                        md['nodes'].append(nd)
                    md['links']=[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in m.node_tree.links]
                materials[m.name]=md
    observations.append(rec)
cam=scene.camera
camera=None
if cam:
    camera={'name':cam.name,'type':cam.data.type,'matrix_world':matrix(cam.matrix_world),'ortho_scale':cam.data.ortho_scale,'lens':cam.data.lens,'shift_x':cam.data.shift_x,'shift_y':cam.data.shift_y,'clip_start':cam.data.clip_start,'clip_end':cam.data.clip_end}
report={'phase':'independent_initial_raw_native_inspection_only','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw_path':str(raw),'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'probe_path':str(Path(__file__)),'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'scene':scene.name,'view_layer':vl.name,'actual_collection':col.name,'actual_root':root.name,'root_in_collection':root in objects,'collection_object_count':len(objects),'object_records':observations,'aggregate_evaluated_mesh_world_bounds':bbox(all_points),'materials':materials,'scene_capture_observation':{'active_camera':camera,'engine':scene.render.engine,'resolution_x':scene.render.resolution_x,'resolution_y':scene.render.resolution_y,'resolution_percentage':scene.render.resolution_percentage,'pixel_aspect_x':scene.render.pixel_aspect_x,'pixel_aspect_y':scene.render.pixel_aspect_y,'film_transparent':scene.render.film_transparent,'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma},'mutation_scope':'Only unsaved visibility toggles needed for correct evaluated transforms; no data construction, native save or production write.'}
with out.open('x') as f: json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'output':str(out),'collection':col.name,'root':root.name,'object_count':len(objects),'bounds':report['aggregate_evaluated_mesh_world_bounds'],'raw_sha256':report['raw_sha256']},indent=2))
