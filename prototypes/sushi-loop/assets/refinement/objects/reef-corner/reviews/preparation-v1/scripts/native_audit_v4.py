import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
col=bpy.data.collections.get('reef-corner')
if not col:
    matches=[c for c in bpy.data.collections if 'reef-corner' in c.name]
    col=next((c for c in matches if any(o.type=='MESH' for o in c.all_objects)),None)
assert col, [c.name for c in bpy.data.collections if 'reef' in c.name]
root=next(o for o in col.all_objects if o.type=='EMPTY' and '__root' in o.name)
scene=next(sc for sc in bpy.data.scenes if root.name in sc.objects)
bpy.context.window.scene=scene
for c in bpy.data.collections:c.hide_viewport=False
def enable(lc):
    lc.exclude=False;lc.hide_viewport=False
    for c in lc.children:enable(c)
for vl in scene.view_layers:enable(vl.layer_collection)
for o in col.all_objects:o.hide_set(False)
scene.frame_set(1);bpy.context.view_layer.update()
inv=root.matrix_world.inverted()
def val(v):
    if hasattr(v,'to_list'):return v.to_list()
    try:return list(v) if not isinstance(v,(str,int,float,bool)) else v
    except:return str(v)
def props(o):return {k:val(o[k]) for k in o.keys()}
def matrec(m):
    return {'name':m.name,'diffuse':list(m.diffuse_color),'use_nodes':m.use_nodes,'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'inputs':{s.name:val(s.default_value) for s in n.inputs if hasattr(s,'default_value')}} for n in m.node_tree.nodes] if m.use_nodes else [],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links] if m.use_nodes else []}
meshes=[];allpts=[]
for o in col.all_objects:
    if o.type!='MESH':continue
    dg=bpy.context.evaluated_depsgraph_get();e=o.evaluated_get(dg);me=e.to_mesh()
    me.calc_loop_triangles()
    pts=[inv@(e.matrix_world@v.co) for v in me.vertices];allpts.extend(pts)
    meshes.append({'name':o.name,'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render,'location':list(o.location),'scale':list(o.scale),'rotation':list(o.rotation_euler),'props':props(o),'matrix_root_relative':[list(r) for r in inv@o.matrix_world],'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'verts':[list(v) for v in pts],'triangles':[{'v':list(t.vertices),'loops':list(t.loops),'polygon':t.polygon_index,'normal':list(t.normal),'cornerNormals':[list(me.corner_normals[i].vector) for i in t.loops],'material':t.material_index} for t in me.loop_triangles],'polygons':[{'v':list(f.vertices),'material':f.material_index,'normal':list((o.matrix_world.to_3x3()@f.normal).normalized()),'smooth':f.use_smooth} for f in me.polygons],'materials':[matrec(m) for m in me.materials if m],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]});e.to_mesh_clear()
scene=bpy.context.scene
out={'blender':bpy.app.version_string,'collection':col.name,'root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'rootProps':props(root),'meshCount':len(meshes),'bounds':[[min(v[i] for v in allpts) for i in range(3)],[max(v[i] for v in allpts) for i in range(3)]],'meshes':meshes,'savedCamera':{'name':scene.camera.name,'matrix':[list(r) for r in scene.camera.matrix_world],'ortho_scale':scene.camera.data.ortho_scale,'shift':[scene.camera.data.shift_x,scene.camera.data.shift_y],'angle':scene.camera.data.angle} if scene.camera else None,'render':{'engine':scene.render.engine,'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'filter':scene.render.filter_size,'film_transparent':scene.render.film_transparent},'lights':[{'name':o.name,'matrix':[list(r) for r in o.matrix_world],'energy':o.data.energy,'size':getattr(o.data,'size',None),'type':o.data.type} for o in scene.objects if o.type=='LIGHT'],'dependencies':{'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'path':x.filepath,'packed':bool(x.packed_file)} for x in bpy.data.images if x.source=='FILE']},'actions':[a.name for a in bpy.data.actions],'objectAnimation':[{'name':o.name,'animation':bool(o.animation_data),'constraints':[c.type for c in o.constraints]} for o in col.all_objects]}
(p/'evidence/original-native-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['blender','collection','root','rootProps','meshCount','bounds','savedCamera','render','dependencies','objectAnimation']},indent=2))
