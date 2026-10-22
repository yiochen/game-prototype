import bpy,sys,math,json
sys.dont_write_bytecode=True
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parents[1]
def scalar(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return list(v)
 except TypeError:return str(v)
def matrec(m):
 rec={'name':m.name,'animationData':bool(m.animation_data),'nodeAnimationData':bool(m.node_tree.animation_data),'nodes':[],'links':[]}
 for n in m.node_tree.nodes:
  a={'name':n.name,'type':n.type,'inputs':{s.name:scalar(s.default_value) for s in n.inputs if hasattr(s,'default_value')}}
  for k in ['attribute_name','operation','interpolation_type','voronoi_dimensions','feature','normalize','blend_type']:
   if hasattr(n,k):a[k]=getattr(n,k)
  if hasattr(n,'color_ramp'):a['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
  rec['nodes'].append(a)
 rec['links']=[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links]
 return rec
s=bpy.context.scene;r=bpy.data.objects['rock-shelf-middle__root'];r.rotation_euler=(0,0,0);bpy.context.view_layer.update()
coll=r.users_collection[0];core=bpy.data.objects['rock-shelf-middle__sculpted_core'];m=core.data
out={'sourceSHA256':'3e6c7cbe865a918dbeec5faf1a48af540f6290e7afc41ef4c987162617199422','scene':s.name,'collection':coll.name,'rootMatrix':[list(row) for row in r.matrix_world],'objectActions':[],'materialActions':[],'shapeKeys':[],'objects':[],'endpoints':{},'materials':[matrec(mm) for mm in m.materials],'lights':[],'libraries':[l.filepath for l in bpy.data.libraries],'imageDependencies':[]}
allp=[]
for o in coll.all_objects:
 if o.animation_data:out['objectActions'].append(o.name)
 if o.type=='MESH':
  pts=[r.matrix_world.inverted()@o.matrix_world@v.co for v in o.data.vertices];allp+=pts
  out['objects'].append({'name':o.name,'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'vertices':len(pts),'faces':len(o.data.polygons),'modifiers':[mod.type for mod in o.modifiers],'uvLayers':list(o.data.uv_layers.keys()),'animationData':bool(o.animation_data)})
  if o.data.shape_keys:out['shapeKeys'].append(o.name)
  for mat in o.data.materials:
   if mat.animation_data or mat.node_tree.animation_data:out['materialActions'].append(mat.name)
   for n in mat.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image:out['imageDependencies'].append({'material':mat.name,'image':n.image.name,'path':n.image.filepath,'packed':bool(n.image.packed_file)})
attr=m.color_attributes['rock_shelf_albedo']
for label,sign in [('W',-1),('E',1)]:
 band=[]
 for poly in m.polygons:
  if all(sign*m.vertices[i].co.x>=.44-1e-6 for i in poly.vertices):
   band.append({'faceIndex':poly.index,'material':m.materials[poly.material_index].name,'geometricNormal':list(poly.normal),'smooth':poly.use_smooth,'corners':[{'vertex':m.loops[li].vertex_index,'position':list(m.vertices[m.loops[li].vertex_index].co),'normal':list(m.corner_normals[li].vector),'albedo':list(attr.data[m.loops[li].vertex_index].color)} for li in poly.loop_indices]})
 cap=[p for p in band if all(abs(c['position'][0]-sign*.5)<1e-6 for c in p['corners'])]
 out['endpoints'][label]={'planeX':sign*.5,'capFaces':cap,'bandFaces':band,'bandInterval':[sign*.5,sign*.44]}
out['bounds']=[[min(v[i] for v in allp) for i in range(3)],[max(v[i] for v in allp) for i in range(3)]]
for o in s.objects:
 if o.type=='LIGHT':out['lights'].append({'name':o.name,'type':o.data.type,'shape':o.data.shape,'location':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'useShadow':o.data.use_shadow,'color':list(o.data.color)})
c=s.camera
origin=world_to_camera_view(s,c,Vector((0,0,0)));out['capture']={'frame':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'filter':s.render.filter_size,'samples':s.eevee.taa_render_samples,'cameraWorldMatrix':[list(row) for row in c.matrix_world],'orthoScale':c.data.ortho_scale,'sensorFit':c.data.sensor_fit,'rootPixels':[origin.x*s.render.resolution_x,(1-origin.y)*s.render.resolution_y],'fps':s.render.fps,'frameRange':[s.frame_start,s.frame_end],'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'filmTransparent':s.render.film_transparent,'compositor':s.compositing_node_group.name,'worldBackgroundStrength':s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value}
# Field parity is inspected on the actual saved custom normals and point albedos.
def field_rows(end):
 rows=[]
 for p in out['endpoints'][end]['bandFaces']:
  if abs(p['geometricNormal'][0])>.9:continue
  for c in p['corners']:
   if abs(abs(c['position'][0])-.5)<1e-6:rows.append((tuple(round(v,7) for v in c['position'][1:]),tuple(round(v,7) for v in c['normal']),tuple(round(v,7) for v in c['albedo'])))
 return sorted(rows)
out['endpointVisibleBandParity']={'exactRounded7Places':field_rows('W')==field_rows('E'),'W':field_rows('W'),'E':field_rows('E')}
(P/'measurements/canonical-middle-native.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['bounds','objects','objectActions','materialActions','shapeKeys','imageDependencies','capture','lights','endpointVisibleBandParity']},indent=2))
