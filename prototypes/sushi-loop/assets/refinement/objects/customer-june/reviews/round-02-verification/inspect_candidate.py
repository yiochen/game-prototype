import bpy,json,hashlib,sys
sys.dont_write_bytecode=True
from pathlib import Path
P=Path(__file__).parent
mode='runtime' if 'runtime' in bpy.data.filepath else 'main'
sc=next(s for s in bpy.data.scenes if any('customer_june' in o.name for o in s.objects));bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
col=next(c for c in sc.collection.children if any('customer_june__armature' in o.name for o in c.all_objects))
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
col.hide_viewport=False;col.hide_render=False;bpy.context.view_layer.update()
def scalar(v):
 if isinstance(v,(str,int,float,bool)):return v
 try:return [scalar(x) for x in v]
 except:return str(v)
def graph(tree):
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'image':getattr(n,'image',None).name if getattr(n,'image',None) else None,'inputs':{s.name:scalar(s.default_value) for s in n.inputs if hasattr(s,'default_value') and not s.is_linked}} for n in tree.nodes],'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in tree.links]}
cam=sc.camera
out={'file':bpy.data.filepath,'scene':sc.name,'collection':col.name,'render':{'engine':sc.render.engine,'size':[sc.render.resolution_x,sc.render.resolution_y],'percent':sc.render.resolution_percentage,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'fps':sc.render.fps,'filmTransparent':sc.render.film_transparent,'view':[sc.view_settings.view_transform,sc.view_settings.look,sc.view_settings.exposure,sc.view_settings.gamma]},'camera':{'name':cam.name,'type':cam.data.type,'worldMatrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'sensorFit':cam.data.sensor_fit,'constraints':[(c.type,c.mute) for c in cam.constraints],'drivers':[(f.data_path,f.driver.expression) for f in cam.animation_data.drivers] if cam.animation_data else []},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':getattr(o.data,'size',None),'world':[list(r) for r in o.matrix_world],'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT'],'world':graph(sc.world.node_tree) if sc.world and sc.world.use_nodes else None,'compositor':graph(sc.compositing_node_group) if getattr(sc,'compositing_node_group',None) else graph(sc.node_tree) if getattr(sc,'node_tree',None) else None,'objects':[],'materials':[],'images':[]}
materials=set()
for o in col.all_objects:
 r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix':[list(r) for r in o.matrix_world],'hideRender':o.hide_render,'modifiers':[(m.name,m.type,m.show_render,m.show_viewport) for m in o.modifiers]}
 if o.type=='MESH':
  r.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),smoothPolygons=sum(p.use_smooth for p in o.data.polygons),materials=[m.name for m in o.data.materials if m],zeroWeightVertices=[v.index for v in o.data.vertices if o.get('weighted_character_geometry') and sum(g.weight for g in v.groups)<.999],nonfiniteVertices=[v.index for v in o.data.vertices if not all(__import__('math').isfinite(c) for c in v.co)])
  materials.update(m for m in o.data.materials if m)
 out['objects'].append(r)
for m in materials:
 out['materials'].append({'name':m.name,'nodes':graph(m.node_tree) if m.use_nodes else None})
 for n in m.node_tree.nodes if m.use_nodes else []:
  if n.type=='TEX_IMAGE' and n.image:
   i=n.image;out['images'].append({'name':i.name,'path':i.filepath,'packed':i.packed_file is not None,'packedSHA256':hashlib.sha256(bytes(i.packed_file.data)).hexdigest() if i.packed_file else None,'size':list(i.size)})
(P/(mode+'-scene-inspection.json')).write_text(json.dumps(out,indent=2)+'\n');print(mode,sc.name,col.name,'objects',len(out['objects']),'materials',len(materials),'camera',out['camera'],'render',out['render'])
