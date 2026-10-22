import bpy,pathlib,json,hashlib,math,sys
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent;s=bpy.context.scene;s.view_layers[0].update()
root=bpy.data.objects['rock-shelf-middle__root'];root.rotation_euler=(0,0,0);s.view_layers[0].update()
def value(v):
 if isinstance(v,(float,int,bool,str)):return v
 try:return list(v)
 except:return str(v)
def material(m):
 ns=[]
 for n in m.node_tree.nodes:
  r={'name':n.name,'type':n.type,'inputs':{i.identifier:value(i.default_value) for i in n.inputs if hasattr(i,'default_value')}}
  for k in ['attribute_name','operation','voronoi_dimensions','feature','interpolation_type','clamp']:
   if hasattr(n,k):r[k]=value(getattr(n,k))
  if n.type=='VALTORGB':r['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
  ns.append(r)
 return {'name':m.name,'nodes':ns,'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in m.node_tree.links]}
r={'project':bpy.data.filepath,'blenderVersion':bpy.app.version_string,'rootMatrix':[list(v) for v in root.matrix_world],'scene':s.name,'objects':[],'materials':[],'ports':{},'lights':[],'capture':{'frame':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'filterSize':s.render.filter_size,'samples':s.eevee.taa_render_samples,'cameraMatrix':[list(v) for v in s.camera.matrix_world],'orthoScale':s.camera.data.ortho_scale,'shift':[s.camera.data.shift_x,s.camera.data.shift_y]}}
for o in s.objects:
 if o.type=='LIGHT':r['lights'].append({'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'type':o.data.type,'energy':o.data.energy,'shape':o.data.shape,'size':o.data.size,'color':list(o.data.color),'shadow':o.data.use_shadow})
 if o.type!='MESH':continue
 m=o.data;pts=[o.matrix_world@v.co for v in m.vertices];r['objects'].append({'name':o.name,'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'vertices':len(pts),'polygons':len(m.polygons),'animation':bool(o.animation_data)})
 if 'sculpted_core' not in o.name:continue
 attrs=m.color_attributes['rock_shelf_albedo'];r['materials']=[material(mm) for mm in m.materials]
 for name,sign in [('W',-1),('E',1)]:
  fs=[]
  for f in m.polygons:
   xx=[m.vertices[v].co.x for v in f.vertices]
   if not all(sign*x>=.42-1e-6 for x in xx):continue
   fs.append({'polygon':f.index,'material':f.material_index,'smooth':f.use_smooth,'faceNormal':list(f.normal),'corners':[{'vertex':m.loops[k].vertex_index,'position':list(m.vertices[m.loops[k].vertex_index].co),'normal':list(m.corner_normals[k].vector),'albedo':list(attrs.data[m.loops[k].vertex_index].color)} for k in f.loop_indices]})
  r['ports'][name]={'cutPlaneX':sign*.5,'bandRangeX':sorted([sign*.5,sign*.42]),'faces':fs}
(P/'canonical-middle-field.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'ports':{k:{'faces':len(v['faces']),'cap':next(f for f in v['faces'] if f['material']==1)} for k,v in r['ports'].items()},'capture':r['capture'],'lights':r['lights']},indent=2))
