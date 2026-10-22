import bpy,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).resolve().parent
src=OUT/'resources/original-library.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33)
bpy.context.window.scene=sc
root=bpy.data.objects['rock-wall-corner__root.001']
col=next(c for c in sc.collection.children if root in list(c.all_objects))
for layer in sc.view_layers[0].layer_collection.children: layer.exclude=layer.collection!=col
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
root.rotation_euler.z=0;sc.frame_set(1);bpy.context.view_layer.update()
def val(v):
 try:return list(v)
 except:return v
materials={m for o in col.all_objects for m in o.data.materials if m} if False else {sl.material for o in col.all_objects if o.type=='MESH' for sl in o.material_slots if sl.material}
objects=[]; allpts=[]
for o in col.all_objects:
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':[list(r) for r in o.matrix_world],'dimensions':list(o.dimensions),'modifiers':[{ 'name':m.name,'type':m.type} for m in o.modifiers],'properties':{k:val(v) for k,v in o.items()},'actions':o.animation_data.action.name if o.animation_data and o.animation_data.action else None}
 if o.type=='MESH':
  pts=[o.matrix_world@v.co for v in o.data.vertices];allpts+=pts
  d.update(vertices=len(o.data.vertices),edges=len(o.data.edges),polygons=len(o.data.polygons),smoothPolygons=sum(p.use_smooth for p in o.data.polygons),materials=[sl.material.name if sl.material else None for sl in o.material_slots],bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],vertexCoordinates=[list(p) for p in pts],polygonVertices=[list(p.vertices) for p in o.data.polygons],polygonNormals=[list(p.normal) for p in o.data.polygons],uvLayers=list(o.data.uv_layers.keys()))
 objects.append(d)
matdata=[]
for m in materials:
 nodes=[]
 for n in m.node_tree.nodes:
  inp={}
  for p in n.inputs:
   try:inp[p.name]=val(p.default_value)
   except:pass
  nd={'name':n.name,'type':n.type,'inputs':inp}
  if n.type=='VALTORGB':nd['ramp']=[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]
  nodes.append(nd)
 matdata.append({'name':m.name,'nodes':nodes,'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links]})
tree=getattr(sc,'node_tree',None) or getattr(sc,'compositing_node_group',None)
audit={'source':str(src),'blenderVersion':bpy.app.version_string,'scene':sc.name,'collection':col.name,'root':root.name,'rootLocation':list(root.location),'rootScale':list(root.scale),'bounds':[[min(p[i] for p in allpts) for i in range(3)],[max(p[i] for p in allpts) for i in range(3)]],'objects':objects,'materials':matdata,'images':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file),'source':i.source} for i in bpy.data.images],'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'location':list(o.location),'rotation':list(o.rotation_euler),'size':o.data.size} for o in sc.objects if o.type=='LIGHT' and o.data.energy>0],'sceneEngine':sc.render.engine,'filterSize':sc.render.filter_size,'renderSamples':getattr(sc.eevee,'taa_render_samples',None),'compositor':{'nodes':[(n.name,n.type) for n in (tree.nodes if tree else [])],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in (tree.links if tree else [])]}}
(OUT/'own-source-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print('OWN_AUDIT',json.dumps({k:audit[k] for k in ['scene','collection','root','bounds','sceneEngine','filterSize','renderSamples']}))
