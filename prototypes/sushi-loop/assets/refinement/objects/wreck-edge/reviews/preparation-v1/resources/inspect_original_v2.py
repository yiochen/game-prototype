import bpy, json, hashlib, sys, math
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
OUT = BASE.parent / 'original-native-inspection-v2.json'
root = bpy.data.objects.get('wreck-edge__root.001')
assert root is not None
sc = next(sc for sc in bpy.data.scenes if sc.get('source')=='native_actions.py')
bpy.context.window.scene = sc
for c in bpy.data.collections:
    if root.name in c.all_objects: c.hide_render=False; c.hide_viewport=False
def visible(lc):
    lc.exclude=False;lc.hide_viewport=False
    for child in lc.children: visible(child)
visible(sc.view_layers[0].layer_collection)
root.rotation_euler=(0,0,0)
sc.frame_set(1)
bpy.context.view_layer.update()
owned = [root] + list(root.children_recursive)
inv = root.matrix_world.inverted()
def safe(v):
    if isinstance(v, (str, int, float, bool)) or v is None: return v
    try: return [safe(x) for x in v]
    except: return str(v)
def props(o): return {k:safe(o[k]) for k in o.keys()}
def tree(nt):
    if nt is None: return None
    return {'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'blend_type':getattr(n,'blend_type',None),'inputs':{i.name:safe(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'ramp': [{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements] if hasattr(n,'color_ramp') else None} for n in nt.nodes], 'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in nt.links]}
objects=[]
for ob in owned:
    item={'name':ob.name,'type':ob.type,'parent':ob.parent.name if ob.parent else None,'matrixWorld':[list(r) for r in ob.matrix_world], 'matrixRoot':[list(r) for r in inv@ob.matrix_world], 'properties':props(ob),'hide_render':ob.hide_render,'location':list(ob.location),'rotation':list(ob.rotation_euler),'scale':list(ob.scale),'matrixBasis':[list(r) for r in ob.matrix_basis],'animationData': bool(ob.animation_data),'modifiers':[{'name':m.name,'type':m.type} for m in ob.modifiers], 'constraints':[c.type for c in ob.constraints]}
    if ob.type=='MESH':
        vs=[list(inv@ob.matrix_world@v.co) for v in ob.data.vertices]
        item.update(vertices=vs, polygons=[{'vertices':list(p.vertices),'material_index':p.material_index,'normal':list(p.normal),'smooth':p.use_smooth} for p in ob.data.polygons], materials=[m.name if m else None for m in ob.data.materials],bounds={'min':[min(v[i] for v in vs) for i in range(3)],'max':[max(v[i] for v in vs) for i in range(3)]})
    objects.append(item)
mats={m for ob in owned if ob.type=='MESH' for m in ob.data.materials if m}
scenes=[]
for sc in bpy.data.scenes:
    scenes.append({'name':sc.name,'properties':props(sc),'frame':sc.frame_current,'world':sc.world.name if sc.world else None,'worldTree':tree(sc.world.node_tree) if sc.world else None,'render':{'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filmTransparent':sc.render.film_transparent,'filterSize':sc.render.filter_size,'fps':sc.render.fps},'camera':{'name':sc.camera.name,'matrixWorld':[list(r) for r in sc.camera.matrix_world],'type':sc.camera.data.type,'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y]} if sc.camera else None,'compositor':tree(sc.node_tree) if hasattr(sc,'node_tree') else None})
output={'asset':'wreck-edge','source':str(bpy.data.filepath),'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'root':root.name,'rootProperties':props(root),'collections':[{'name':c.name,'properties':props(c),'objects':[o.name for o in c.all_objects]} for c in bpy.data.collections if root.name in c.all_objects], 'objects':objects,'materials':[{'name':m.name,'users':m.users,'diffuseColor':list(m.diffuse_color),'useNodes':m.use_nodes,'properties':props(m),'tree':tree(m.node_tree)} for m in sorted(mats,key=lambda x:x.name)],'images':[{'name':i.name,'filepath':i.filepath,'source':i.source,'packed':bool(i.packed_file),'users':i.users} for i in bpy.data.images if i.users],'libraries':[{'name':l.name,'filepath':l.filepath} for l in bpy.data.libraries], 'scenes':scenes,'actions':[{'name':a.name,'users':a.users} for a in bpy.data.actions if a.users and any(ob.animation_data and ob.animation_data.action==a for ob in owned)]}
OUT.write_text(json.dumps(output,indent=2)+'\n')
print('WRECK_EDGE_ORIGINAL_INSPECTED',len(owned),OUT)
