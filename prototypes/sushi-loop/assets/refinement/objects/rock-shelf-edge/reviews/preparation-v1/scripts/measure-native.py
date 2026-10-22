import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent
label=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'original'
asset='rock-shelf-edge' if label=='original' else 'rock-shelf-middle'
coll=next(c for c in bpy.data.collections if asset in c.name and any(o.type=='MESH' for o in c.all_objects))
sc=bpy.context.scene
for c in sc.collection.children:c.hide_render=(c!=coll)
for c in bpy.data.collections:c.hide_viewport=False
def enable_layer(lc):
 lc.exclude=False;lc.hide_viewport=False
 for child in lc.children:enable_layer(child)
enable_layer(bpy.context.view_layer.layer_collection)
coll.hide_render=coll.hide_viewport=False
root=next(o for o in coll.all_objects if o.type=='EMPTY' and '__root' in o.name)
root.rotation_euler.z=0
for o in coll.all_objects:o.hide_viewport=False;o.hide_set(False);o.update_tag(refresh={'OBJECT'})
sc.frame_set(1);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();inv=root.matrix_world.inverted()
report={'asset':asset,'label':label,'sourceBlend':bpy.data.filepath,'blender':bpy.app.version_string,'collection':coll.name,'root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'objects':[],'materials':{},'bounds':None,'groundVertices':[],'ports':{}}
allcoords=[]
def val(v):
 try:return list(v)
 except:return v
def mat_record(m):
 d={'name':m.name,'diffuse':list(m.diffuse_color),'nodes':[],'links':[]}
 if not m.use_nodes:return d
 for n in m.node_tree.nodes:
  nr={'name':n.name,'type':n.type,'inputs':[{'name':i.name,'index':ix,'value':val(i.default_value)} for ix,i in enumerate(n.inputs) if hasattr(i,'default_value')]}
  for k in ['operation','attribute_name','blend_type','interpolation_type','voronoi_dimensions','feature','normalize','clamp']:
   if hasattr(n,k):nr[k]=getattr(n,k)
  if n.type=='VALTORGB':nr['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
  d['nodes'].append(nr)
 d['links']=[{'from':[l.from_node.name,l.from_socket.name,list(l.from_node.outputs).index(l.from_socket)],'to':[l.to_node.name,l.to_socket.name,list(l.to_node.inputs).index(l.to_socket)]} for l in m.node_tree.links]
 return d
for o in coll.all_objects:
 od={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'animation':bool(o.animation_data and (o.animation_data.action or o.animation_data.drivers)),'hideRender':o.hide_render}
 if o.type=='ARMATURE':od['armatureBones']=[b.name for b in o.data.bones]
 if o.type!='MESH':report['objects'].append(od);continue
 eo=o.evaluated_get(dg);mesh=eo.to_mesh();mat=inv@eo.matrix_world
 coords=[mat@v.co for v in mesh.vertices];allcoords+=coords
 od.update(vertices=len(coords),polygons=len(mesh.polygons),bounds=[[min(v[k] for v in coords) for k in range(3)],[max(v[k] for v in coords) for k in range(3)]],shapeKeys=bool(o.data.shape_keys),modifiers=[{'name':m.name,'type':m.type} for m in o.modifiers],materials=[m.name for m in mesh.materials],materialAnimation=[])
 for m in mesh.materials:
  report['materials'][m.name]=mat_record(m)
  od['materialAnimation'].append({'name':m.name,'material':bool(m.animation_data and (m.animation_data.action or m.animation_data.drivers)),'nodes':bool(m.node_tree and m.node_tree.animation_data and (m.node_tree.animation_data.action or m.node_tree.animation_data.drivers))})
 report['groundVertices'] += [list(v) for v in coords if abs(v.z)<1e-7]
 endpoint={}
 color=mesh.color_attributes.get('rock_shelf_albedo')
 ns=mesh.corner_normals
 for port,x in [('W',-.5),('E',.5)]:
  faces=[]
  for p in mesh.polygons:
   touches=any(abs(coords[vi].x-x)<1e-6 for vi in p.vertices)
   if not touches:continue
   faces.append({'polygon':p.index,'cap':all(abs(coords[vi].x-x)<1e-6 for vi in p.vertices),'faceNormal':list(p.normal),'material':mesh.materials[p.material_index].name if mesh.materials else None,'smooth':p.use_smooth,'corners':[{'vertex':mesh.loops[li].vertex_index,'position':list(coords[mesh.loops[li].vertex_index]),'normal':list(ns[li].vector),'albedo':list(color.data[mesh.loops[li].vertex_index].color) if color and color.domain=='POINT' else None} for li in p.loop_indices]})
  if faces:endpoint[port]=faces
 od['endpointFaces']=endpoint
 report['objects'].append(od);eo.to_mesh_clear()
report['bounds']=[[min(v[k] for v in allcoords) for k in range(3)],[max(v[k] for v in allcoords) for k in range(3)]]
report['groundBounds']=[[min(v[k] for v in report['groundVertices']) for k in range(3)],[max(v[k] for v in report['groundVertices']) for k in range(3)]]
report['savedScene']={'frame':sc.frame_current,'fps':sc.render.fps,'range':[sc.frame_start,sc.frame_end],'camera':sc.camera.name if sc.camera else None,'cameraMatrix':[list(r) for r in sc.camera.matrix_world] if sc.camera else None,'render':{'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filterSize':sc.render.filter_size,'samples':sc.eevee.taa_render_samples,'engine':sc.render.engine},'lights':[{'name':o.name,'position':list(o.location),'type':o.data.type,'energy':o.data.energy,'size':getattr(o.data,'size',None),'useShadow':o.data.use_shadow,'rotation':list(o.rotation_euler)} for o in sc.objects if o.type=='LIGHT'],'worldStrength':sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value if sc.world and sc.world.use_nodes else None}
(BASE/(label+'-native-measurements.json')).write_text(json.dumps(report,indent=2,default=str)+'\n')
print(json.dumps({'asset':asset,'bounds':report['bounds'],'groundBounds':report['groundBounds'],'objects':[{'name':o['name'],'bounds':o.get('bounds'),'portFaces':{p:len(fs) for p,fs in o.get('endpointFaces',{}).items()}} for o in report['objects']],'savedRender':report['savedScene']['render']},indent=2))
