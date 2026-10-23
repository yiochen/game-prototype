import bpy, json, hashlib, math
from pathlib import Path
from mathutils import Vector
RAW = Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend')
OUT = Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/portal-entry/source/initial-native-probe.json')
assert hashlib.sha256(RAW.read_bytes()).hexdigest() == 'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
assert Path(bpy.data.filepath).resolve() == RAW.resolve()
scene = bpy.data.scenes['S33 Native Asset Library Export']
coll = bpy.data.collections['S33_PROP_portal_rim.003']
root = bpy.data.objects['portal_rim__root.003']
own = sorted(coll.all_objects, key=lambda o:o.name)
assert root in own

def value(v):
    if v is None or isinstance(v,(str,int,float,bool)): return v
    if isinstance(v,dict): return {str(k):value(x) for k,x in v.items()}
    if hasattr(v,'to_list'): return value(v.to_list())
    if hasattr(v,'keys'): return {str(k):value(v[k]) for k in v.keys()}
    try: return [value(x) for x in v]
    except TypeError: return str(v)
def props(x): return {str(k):value(x[k]) for k in x.keys()}
def matrix(m): return [[float(x) for x in row] for row in m]
def vec(v): return [float(x) for x in v]
def bounds(points):
    pp=list(points)
    return {'min':[min(p[i] for p in pp) for i in range(3)],'max':[max(p[i] for p in pp) for i in range(3)]} if pp else None
def animation(x):
    a=getattr(x,'animation_data',None)
    if not a: return None
    action=a.action
    return {'action':action.name if action else None,'action_frame_range':vec(action.frame_range) if action else None,'action_slots':[{'identifier':s.identifier,'target_id_type':s.target_id_type} for s in action.slots] if action else [],'nla_tracks':[{'name':t.name,'strips':[{'name':s.name,'action':s.action.name if s.action else None,'frame_start':s.frame_start,'frame_end':s.frame_end} for s in t.strips]} for t in a.nla_tracks],'drivers':[{'data_path':f.data_path,'array_index':f.array_index,'expression':f.driver.expression,'type':f.driver.type} for f in a.drivers]}
def cpath(c,target,path):
    if c == target: return path+[c]
    for ch in c.children:
        p=cpath(ch,target,path+[c])
        if p: return p
    return None
cp=cpath(scene.collection,coll,[])
assert cp, 'Own collection not linked to named scene'
vl=scene.view_layers[0]
if bpy.context.window:
    bpy.context.window.scene=scene
    bpy.context.window.view_layer=vl

def lpath(c,target,path):
    if c.collection == target: return path+[c]
    for ch in c.children:
        p=lpath(ch,target,path+[c])
        if p: return p
    return None
lp=lpath(vl.layer_collection,coll,[])
assert lp
before={'context_scene':bpy.context.scene.name,'view_layer':vl.name,'collection_path':[{'name':c.name,'hide_render':c.hide_render,'hide_viewport':c.hide_viewport} for c in cp],'layer_collection_path':[{'name':c.name,'exclude':c.exclude,'hide_viewport':c.hide_viewport,'holdout':c.holdout,'indirect_only':c.indirect_only} for c in lp],'objects':[{'name':o.name,'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'hide_set':o.hide_get(view_layer=vl)} for o in own]}
for c in cp:
    c.hide_render=False
    c.hide_viewport=False
for c in lp:
    c.exclude=False
    c.hide_viewport=False
    c.holdout=False
    c.indirect_only=False
for o in own:
    o.hide_render=False
    o.hide_viewport=False
    o.hide_set(False,view_layer=vl)
vl.update()
with bpy.context.temp_override(scene=scene,view_layer=vl):
    dg=bpy.context.evaluated_depsgraph_get()
    dg.update()
    entries=[]
    all_world=[]
    for o in own:
        e=o.evaluated_get(dg)
        d={'name':o.name,'type':o.type,'data_name':o.data.name if o.data else None,'data_users':o.data.users if o.data else None,'object_library':o.library.filepath if o.library else None,'data_library':o.data.library.filepath if o.data and o.data.library else None,'collections':[c.name for c in o.users_collection],'parent':o.parent.name if o.parent else None,'parent_type':o.parent_type,'children':[c.name for c in o.children],'location':vec(o.location),'rotation_mode':o.rotation_mode,'rotation_euler':vec(o.rotation_euler),'rotation_quaternion':vec(o.rotation_quaternion),'scale':vec(o.scale),'matrix_parent_inverse':matrix(o.matrix_parent_inverse),'matrix_world_evaluated':matrix(e.matrix_world),'custom_properties':props(o),'animation':animation(o),'visible_get':o.visible_get(view_layer=vl),'modifiers':[{'name':m.name,'type':m.type,'show_viewport':m.show_viewport,'show_render':m.show_render} for m in o.modifiers],'constraints':[{'name':c.name,'type':c.type,'influence':c.influence} for c in o.constraints]}
        if o.type=='MESH':
            me=e.to_mesh()
            pts=[e.matrix_world@v.co for v in me.vertices]
            all_world.extend(pts)
            d['mesh']={'vertices':len(o.data.vertices),'edges':len(o.data.edges),'polygons':len(o.data.polygons),'evaluated_vertices':len(me.vertices),'evaluated_edges':len(me.edges),'evaluated_polygons':len(me.polygons),'smooth_polygons':sum(p.use_smooth for p in o.data.polygons),'local_bounds':bounds(v.co for v in o.data.vertices),'evaluated_world_bounds':bounds(pts),'polygon_material_indices':sorted(set(p.material_index for p in o.data.polygons)),'uv_layers':[u.name for u in o.data.uv_layers],'attributes':[{'name':a.name,'data_type':a.data_type,'domain':a.domain} for a in o.data.attributes],'animation':animation(o.data),'shape_keys':o.data.shape_keys.name if o.data.shape_keys else None}
            d['material_slots']=[m.material.name if m.material else None for m in o.material_slots]
            e.to_mesh_clear()
        entries.append(d)
materials=sorted({m.material for o in own for m in o.material_slots if m.material},key=lambda m:m.name)
mat_entries=[]
for m in materials:
    md={'name':m.name,'users':m.users,'library':m.library.filepath if m.library else None,'diffuse_color':vec(m.diffuse_color),'metallic':m.metallic,'roughness':m.roughness,'use_nodes':m.use_nodes,'custom_properties':props(m),'animation':animation(m)}
    if m.use_nodes:
        nt=m.node_tree
        md['nodes']=[{'name':n.name,'type':n.type,'bl_idname':n.bl_idname,'inputs':{i.name:value(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'image':{'name':n.image.name,'filepath':n.image.filepath,'source':n.image.source,'packed':bool(n.image.packed_file)} if n.type=='TEX_IMAGE' and n.image else None} for n in nt.nodes]
        md['links']=[{'from_node':l.from_node.name,'from_socket':l.from_socket.name,'to_node':l.to_node.name,'to_socket':l.to_socket.name} for l in nt.links]
        md['node_tree_animation']=animation(nt)
    mat_entries.append(md)
cam=scene.camera
result={'scope':'Raw read-only inspection only; visibility changes are in background process memory, with no scene/model saves, renders, or construction. Other assets not inspected.','blender_version':bpy.app.version_string,'raw_file':str(RAW),'raw_sha256':hashlib.sha256(RAW.read_bytes()).hexdigest(),'scene':scene.name,'raw_frame_current':scene.frame_current,'raw_frame_subframe':scene.frame_subframe,'raw_frame_start':scene.frame_start,'raw_frame_end':scene.frame_end,'view_layer':vl.name,'collection':coll.name,'collection_custom_properties':props(coll),'collection_children':[c.name for c in coll.children],'root':root.name,'visibility_before':before,'visibility_after':{'collection_path':[{'name':c.name,'hide_render':c.hide_render,'hide_viewport':c.hide_viewport} for c in cp],'layer_collection_path':[{'name':c.name,'exclude':c.exclude,'hide_viewport':c.hide_viewport,'holdout':c.holdout,'indirect_only':c.indirect_only} for c in lp],'objects':[{'name':o.name,'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'hide_set':o.hide_get(view_layer=vl),'visible_get':o.visible_get(view_layer=vl)} for o in own]},'evaluated_geometry_world_bounds':bounds(all_world),'object_count':len(own),'objects':entries,'materials':mat_entries,'raw_camera':{'name':cam.name,'type':cam.data.type,'location':vec(cam.location),'rotation_euler':vec(cam.rotation_euler),'matrix_world':matrix(cam.matrix_world),'ortho_scale':cam.data.ortho_scale if cam.data.type=='ORTHO' else None,'lens':cam.data.lens,'shift_x':cam.data.shift_x,'shift_y':cam.data.shift_y,'clip_start':cam.data.clip_start,'clip_end':cam.data.clip_end} if cam else None,'raw_render':{'resolution_x':scene.render.resolution_x,'resolution_y':scene.render.resolution_y,'resolution_percentage':scene.render.resolution_percentage,'pixel_aspect_x':scene.render.pixel_aspect_x,'pixel_aspect_y':scene.render.pixel_aspect_y,'film_transparent':scene.render.film_transparent,'engine':scene.render.engine},'capture_contract_status':'Raw observations only, not a construction freeze or future camera/size/contact requirement.'}
with OUT.open('x') as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps({'output':str(OUT),'bytes':OUT.stat().st_size,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'object_count':len(own),'material_count':len(materials),'bounds':result['evaluated_geometry_world_bounds']}))
