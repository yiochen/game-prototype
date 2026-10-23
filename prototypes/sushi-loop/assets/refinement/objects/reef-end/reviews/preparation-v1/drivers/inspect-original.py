import sys
sys.dont_write_bytecode = True
import bpy, json, math
from pathlib import Path
from mathutils import Vector
OUT = Path(__file__).resolve().parents[1] / 'evidence' / 'original-native-evaluated.json'
source = Path(__file__).resolve().parents[5] / 'backups' / 'b1765262bfa897ad-sushi-loop-world-library.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
cols = [c for c in bpy.data.collections if c.name == 'S33_PROP_reef-end.001']
if len(cols) != 1:
    raise RuntimeError([(c.name, len(c.all_objects)) for c in bpy.data.collections if 'reef-end' in c.name])
col = cols[0]
for c in bpy.data.collections: c.hide_viewport = False
def enable_layers(lc):
    lc.exclude=False
    lc.hide_viewport=False
    for child in lc.children: enable_layers(child)
enable_layers(bpy.context.view_layer.layer_collection)
bpy.context.view_layer.update()
def val(x):
    if isinstance(x,(str,int,float,bool)) or x is None: return x
    try: return list(x)
    except: return str(x)
def material(m):
    return {'name':m.name,'diffuse_color':list(m.diffuse_color),'use_nodes':m.use_nodes,'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'props':{k:val(getattr(n,k)) for k in ('blend_type','operation') if hasattr(n,k)}} for n in m.node_tree.nodes] if m.node_tree else [],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links] if m.node_tree else []}
objs=[]
for o in col.all_objects:
    d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation_euler':list(o.rotation_euler),'scale':list(o.scale),'matrix_world':[list(r) for r in o.matrix_world],'hide_render':o.hide_render,'properties':{k:val(o[k]) for k in o.keys()},'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'animation':bool(o.animation_data)}
    if o.type=='MESH':
        verts=[list(o.matrix_world@v.co) for v in o.data.vertices]
        d.update(vertices_world=verts,faces=[list(p.vertices) for p in o.data.polygons],face_normals_local=[list(p.normal) for p in o.data.polygons],face_materials=[p.material_index for p in o.data.polygons],smooth=[p.use_smooth for p in o.data.polygons],materials=[m.name if m else None for m in o.data.materials],bounds_world=[[min(v[i] for v in verts),max(v[i] for v in verts)] for i in range(3)])
    objs.append(d)
scene=bpy.context.scene
report={'source':str(source),'blender_version':bpy.app.version_string,'collection':col.name,'collection_properties':{k:val(col[k]) for k in col.keys()},'objects':objs,'materials':[material(m) for m in {m for o in col.all_objects if o.type=='MESH' for m in o.data.materials if m}],'scene':{'name':scene.name,'camera':scene.camera.name if scene.camera else None,'engine':scene.render.engine,'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'pixel_aspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'filter_size':scene.render.filter_size,'film_transparent':scene.render.film_transparent},'cameras':[{'name':o.name,'matrix_world':[list(r) for r in o.matrix_world],'ortho_scale':o.data.ortho_scale,'shift_x':o.data.shift_x,'shift_y':o.data.shift_y} for o in bpy.data.objects if o.type=='CAMERA'],'actions':[a.name for a in bpy.data.actions]}
OUT.write_text(json.dumps(report,indent=2)+'\n')
print('WROTE',OUT)
print('OBJECTS',[(o['name'],o['type'],o.get('bounds_world')) for o in objs])
