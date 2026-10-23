import bpy,json,pathlib,hashlib
from mathutils import Vector
OUT=pathlib.Path(__file__).parent
s=bpy.context.scene
for c in s.collection.children:c.hide_viewport=False
for l in s.view_layers[0].layer_collection.children:l.exclude=False;l.hide_viewport=False
for o in s.objects:o.hide_viewport=False;o.hide_set(False)
s.frame_set(1);s.view_layers[0].update()
def val(x):
 try:return list(x)
 except:return str(x)
def objrec(o):
 d={'name':o.name,'type':o.type,'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':[list(x) for x in o.matrix_world],'parent':o.parent.name if o.parent else None,'custom':{k:o[k] for k in o.keys()},'hideRender':o.hide_render,'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'materials':[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else []}
 if o.type=='MESH':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  d.update(vertices=[list(o.matrix_world@v.co) for v in me.vertices],polygons=[{'vertices':list(p.vertices),'normal':list(p.normal),'material':p.material_index,'smooth':p.use_smooth} for p in me.polygons],edges=[list(e.vertices) for e in me.edges],uvLayers=[u.name for u in me.uv_layers])
  ev.to_mesh_clear()
 if o.type=='CAMERA':d['camera']={'type':o.data.type,'orthoScale':o.data.ortho_scale,'shiftX':o.data.shift_x,'shiftY':o.data.shift_y}
 if o.type=='LIGHT':d['light']={'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None)}
 return d
cols=[c for c in bpy.data.collections if 'rock-shelf-middle' in c.name]
obs={o.name:o for c in cols for o in c.all_objects}
mats={m.name:m for o in obs.values() if o.type=='MESH' for m in o.data.materials if m}
rec={'blenderVersion':bpy.app.version_string,'scene':s.name,'collections':[{'name':c.name,'custom':{k:c[k] for k in c.keys()},'objects':[o.name for o in c.all_objects]} for c in cols],'objects':[objrec(o) for o in obs.values()],'cameras':[objrec(o) for o in bpy.data.objects if o.type=='CAMERA'],'lights':[objrec(o) for o in bpy.data.objects if o.type=='LIGHT'],'sceneCamera':s.camera.name if s.camera else None,'render':{'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'filmTransparent':s.render.film_transparent,'imageFormat':s.render.image_settings.file_format},'colorManagement':{'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'world':{'name':s.world.name,'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in s.world.node_tree.nodes] if s.world.use_nodes else None},'materials':[],'externalFiles':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'],'actions':[{'name':a.name,'users':a.users} for a in bpy.data.actions]}
for m in mats.values():
 rec['materials'].append({'name':m.name,'diffuseColor':list(m.diffuse_color),'useNodes':m.use_nodes,'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in m.node_tree.nodes] if m.use_nodes else [],'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocket':l.to_socket.name} for l in m.node_tree.links] if m.use_nodes else []})
(OUT/'native-initial-inspection.json').write_text(json.dumps(rec,indent=2,default=str))
print('SHELF COLLECTIONS',[(c.name,len(c.all_objects)) for c in cols]);print('SHELF OBJECTS',list(obs));print('CAMERAS',rec['cameras']);print('RENDER',rec['render'])
