import sys
sys.dont_write_bytecode=True
import bpy,json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parents[1]
P=B.parents[2]/'reef-middle/source/round-02.blend'
assert hashlib.sha256(P.read_bytes()).hexdigest()=='51d515119c1a229f57f3b242fdf040b28ef00121692cb3d40d8821dab70ff3c5'
bpy.ops.wm.open_mainfile(filepath=str(P))
sc=bpy.context.scene
for c in bpy.data.collections:c.hide_viewport=False
def layers(l):
 l.exclude=False;l.hide_viewport=False
 for x in l.children:layers(x)
layers(bpy.context.view_layer.layer_collection)
bpy.context.view_layer.update()
def val(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 try:return list(x)
 except:return str(x)
def mat(m):
 ns=[]
 for n in m.node_tree.nodes:
  d={'name':n.name,'type':n.type,'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')}}
  if hasattr(n,'color_ramp'):d['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
  for k in ['operation','blend_type']:
   if hasattr(n,k):d[k]=getattr(n,k)
  ns.append(d)
 return {'name':m.name,'nodes':ns,'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links],'animation':bool(m.animation_data or m.node_tree.animation_data)}
dg=bpy.context.evaluated_depsgraph_get();geos=[]
for o in sc.objects:
 if o.type!='MESH' or o.hide_render:continue
 e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();verts=[list(e.matrix_world@v.co) for v in m.vertices];nt=e.matrix_world.to_3x3().inverted().transposed()
 d={'name':o.name,'vertices_world':verts,'faces':[list(p.vertices) for p in m.polygons],'face_materials':[p.material_index for p in m.polygons],'smooth':[p.use_smooth for p in m.polygons],'materials':[x.name for x in m.materials],'matrix_world':[list(r) for r in e.matrix_world],'meshUsers':o.data.users,'shapeKeys':bool(o.data.shape_keys),'animation':bool(o.animation_data or o.data.animation_data),'constraints':[x.type for x in o.constraints],'modifiers':[x.type for x in o.modifiers],'bounds':[[min(v[k] for v in verts),max(v[k] for v in verts)] for k in range(3)]}
 if 'continuous_core' in o.name:
  d['triangles']=[{'vertices':[verts[i] for i in t.vertices],'normal':list((nt@t.normal).normalized()),'cornerNormals':[list((nt@m.corner_normals[i].vector).normalized()) for i in t.loops],'material':m.materials[m.polygons[t.polygon_index].material_index].name} for t in m.loop_triangles]
 geos.append(d);e.to_mesh_clear()
lights=[{'name':o.name,'location':list(o.location),'matrix':[list(r) for r in o.matrix_world],'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'type':o.data.type} for o in sc.objects if o.type=='LIGHT' and not o.hide_render]
cam=sc.camera
r={'source':str(P),'sourceSHA256':hashlib.sha256(P.read_bytes()).hexdigest(),'geometry':geos,'materials':[mat(m) for m in bpy.data.materials],'lights':lights,'world':{'name':sc.world.name,'nodes':[{'type':n.type,'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in sc.world.node_tree.nodes]},'camera':{'matrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shiftX':cam.data.shift_x,'shiftY':cam.data.shift_y},'render':{'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filter':sc.render.filter_size,'fps':sc.render.fps,'filmTransparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'actions':[a.name for a in bpy.data.actions],'images':[i.name for i in bpy.data.images if i.source!='GENERATED'],'libraries':[l.filepath for l in bpy.data.libraries],'compositor':{'use_nodes':sc.use_nodes,'nodes':[{'name':n.name,'type':n.type} for n in sc.node_tree.nodes] if sc.node_tree else []}}
(B/'evidence/canonical-native.json').write_text(json.dumps(r,indent=2)+'\n')
print('canonical geometry count',len(geos));print('lights',lights);print('render',r['render']);print('core',[(g['name'],g['bounds'],len(g.get('triangles',[]))) for g in geos if 'continuous_core' in g['name']])
