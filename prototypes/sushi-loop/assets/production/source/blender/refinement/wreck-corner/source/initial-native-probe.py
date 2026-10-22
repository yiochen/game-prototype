import bpy, json, hashlib, os
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).parent
COLLECTION="S33_PROP_wreck-corner.001"
ROOT="wreck-corner__root.001"

def vec(v): return [round(float(x),9) for x in v]
def mat(m): return [vec(row) for row in m]
def val(v):
    if isinstance(v,(str,bool,int,float)) or v is None: return v
    try: return [val(x) for x in v]
    except: return str(v)
def props(o): return {k:val(o[k]) for k in o.keys()}
def coll_paths(c,target,path=None):
    path=(path or [])+[c]
    if c==target: return [path]
    return [p for child in c.children for p in coll_paths(child,target,path)]
def layer_paths(c,target,path=None):
    path=(path or [])+[c]
    if c.collection==target: return [path]
    return [p for child in c.children for p in layer_paths(child,target,path)]
def bounds(points):
    if not points: return None
    return {"min":[min(p[i] for p in points) for i in range(3)],"max":[max(p[i] for p in points) for i in range(3)],"extent":[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]}

c=bpy.data.collections.get(COLLECTION)
r=bpy.data.objects.get(ROOT)
assert c and r, "Authorized original collection/root missing"
objects=sorted(c.all_objects,key=lambda o:o.name)
assert r in objects
scenes=[s for s in bpy.data.scenes if coll_paths(s.collection,c)]
assert scenes, "Own collection not linked to any scene"
s=bpy.context.scene if bpy.context.scene in scenes else scenes[0]
bpy.context.window.scene=s
v=bpy.context.view_layer
raw={o.name:{"hide_viewport":o.hide_viewport,"hide_render":o.hide_render,"hide_set":o.hide_get(view_layer=v) if o.name in v.objects else None,"matrix_world":mat(o.matrix_world),"matrix_local":mat(o.matrix_local),"matrix_parent_inverse":mat(o.matrix_parent_inverse)} for o in objects}
activation=[]
for p in coll_paths(s.collection,c):
    for q in p:
        activation.append({"kind":"collection","name":q.name,"saved_hide_viewport":q.hide_viewport,"saved_hide_render":q.hide_render})
        q.hide_viewport=False
        q.hide_render=False
for p in layer_paths(v.layer_collection,c):
    for q in p:
        activation.append({"kind":"layer_collection","name":q.name,"saved_exclude":q.exclude,"saved_hide_viewport":q.hide_viewport})
        q.exclude=False
        q.hide_viewport=False
for o in objects:
    o.hide_viewport=False
    o.hide_render=False
    if o.name in v.objects: o.hide_set(False,view_layer=v)
v.update()
deps=bpy.context.evaluated_depsgraph_get()
deps.update()
allpoints=[]
root_inv=r.matrix_world.inverted()
record=[]
materials={}
for o in objects:
    ev=o.evaluated_get(deps)
    d={"name":o.name,"type":o.type,"parent":o.parent.name if o.parent else None,"raw_saved_state":raw[o.name],"post_activation_matrix_world":mat(o.matrix_world),"evaluated_matrix_world":mat(ev.matrix_world),"location":vec(o.location),"rotation_mode":o.rotation_mode,"rotation_euler":vec(o.rotation_euler),"scale":vec(o.scale),"dimensions":vec(ev.dimensions),"properties":props(o),"constraints":[{"type":x.type,"name":x.name,"mute":x.mute} for x in o.constraints],"modifiers":[{"type":x.type,"name":x.name,"show_viewport":x.show_viewport,"show_render":x.show_render} for x in o.modifiers],"materials":[slot.material.name if slot.material else None for slot in o.material_slots]}
    if o.type=="MESH":
        me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
        points=[ev.matrix_world @ x.co for x in me.vertices]
        rp=[root_inv @ p for p in points]
        d["mesh"]={"data_name":o.data.name,"base_vertices":len(o.data.vertices),"base_edges":len(o.data.edges),"base_polygons":len(o.data.polygons),"evaluated_vertices":len(me.vertices),"evaluated_edges":len(me.edges),"evaluated_polygons":len(me.polygons),"world_bounds":bounds(points),"root_local_bounds":bounds(rp),"flat_polygons":sum(not p.use_smooth for p in me.polygons),"smooth_polygons":sum(p.use_smooth for p in me.polygons),"uv_layers":[u.name for u in me.uv_layers],"material_polygon_counts":{str(i):sum(p.material_index==i for p in me.polygons) for i in range(max(1,len(me.materials)))}}
        allpoints.extend(points)
        ev.to_mesh_clear()
    for slot in o.material_slots:
        m=slot.material
        if not m or m.name in materials: continue
        md={"name":m.name,"diffuse_color":vec(m.diffuse_color),"use_nodes":m.use_nodes,"properties":props(m),"nodes":[],"links":[]}
        if m.use_nodes:
            for n in m.node_tree.nodes:
                nd={"name":n.name,"type":n.bl_idname}
                if n.bl_idname=="ShaderNodeBsdfPrincipled":
                    nd["inputs"]={k:val(n.inputs[k].default_value) for k in ["Base Color","Metallic","Roughness","IOR","Specular IOR Level","Coat Weight","Coat Roughness","Emission Color","Emission Strength","Alpha"] if k in n.inputs}
                if hasattr(n,"image") and n.image:
                    im=n.image
                    nd["image"]={"name":im.name,"filepath":im.filepath,"source":im.source,"packed":bool(im.packed_file),"size":list(im.size)}
                md["nodes"].append(nd)
            md["links"]=[{"from_node":l.from_node.name,"from_socket":l.from_socket.name,"to_node":l.to_node.name,"to_socket":l.to_socket.name} for l in m.node_tree.links]
        materials[m.name]=md
    record.append(d)
cam=s.camera
camera=None
if cam:
    camera={"name":cam.name,"type":cam.data.type,"matrix_world":mat(cam.matrix_world),"location":vec(cam.location),"rotation_euler":vec(cam.rotation_euler),"ortho_scale":cam.data.ortho_scale,"lens":cam.data.lens,"shift_x":cam.data.shift_x,"shift_y":cam.data.shift_y,"clip_start":cam.data.clip_start,"clip_end":cam.data.clip_end,"properties":props(cam)}
lights=[]
for o in s.objects:
    if o.type=="LIGHT": lights.append({"name":o.name,"type":o.data.type,"color":vec(o.data.color),"energy":o.data.energy,"matrix_world":mat(o.matrix_world),"hide_viewport":o.hide_viewport,"hide_render":o.hide_render,"size":getattr(o.data,"size",None)})
data={"schema":"independent-original-native-probe-v1","scope":"Bounded read-only original probe. In-memory visibility activation only; no geometry/material/camera edits; no project save or render.","blender_version":bpy.app.version_string,"blender_build_hash":bpy.app.build_hash.decode(),"native_path":bpy.data.filepath,"native_sha256":hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),"collection":c.name,"root":r.name,"collection_properties":props(c),"scene":s.name,"view_layer":v.name,"linked_scene_names":[q.name for q in scenes],"activation":activation,"object_count":len(objects),"objects":record,"world_bounds":bounds(allpoints),"root_local_bounds":bounds([root_inv @ p for p in allpoints]),"materials":list(materials.values()),"scene_capture_observations_only":{"camera":camera,"render":{"engine":s.render.engine,"resolution_x":s.render.resolution_x,"resolution_y":s.render.resolution_y,"resolution_percentage":s.render.resolution_percentage,"pixel_aspect_x":s.render.pixel_aspect_x,"pixel_aspect_y":s.render.pixel_aspect_y,"film_transparent":s.render.film_transparent,"image_file_format":s.render.image_settings.file_format,"image_color_mode":s.render.image_settings.color_mode},"view_settings":{"view_transform":s.view_settings.view_transform,"look":s.view_settings.look,"exposure":s.view_settings.exposure,"gamma":s.view_settings.gamma},"world_name":s.world.name if s.world else None,"lights":lights},"external_libraries":[{"name":l.name,"filepath":l.filepath} for l in bpy.data.libraries],"no_native_save":True}
out=OUT/"initial-native-probe.json"
assert not out.exists(), "Refuse overwrite"
out.write_text(json.dumps(data,indent=2)+"\n")
print(json.dumps({"probe":str(out),"objects":len(objects),"root_matrix_world":mat(r.matrix_world),"world_bounds":data["world_bounds"],"root_local_bounds":data["root_local_bounds"],"scene":s.name,"view_layer":v.name,"material_names":list(materials)}))
