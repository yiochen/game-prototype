"""Portable read-only native parity records for the approved crate."""
import bpy,json,hashlib
from mathutils import Vector

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def value(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [value(x) for x in v]
 except TypeError:return str(v)
def rna(obj):
 out={}
 for p in obj.bl_rna.properties:
  if p.identifier in ('rna_type','name','type') or p.type not in ('BOOLEAN','INT','FLOAT','STRING','ENUM'):continue
  try:out[p.identifier]=value(getattr(obj,p.identifier))
  except (AttributeError,TypeError):pass
 return out
def graph(tree):
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'rna':rna(n),'inputs':[{'name':i.name,'value':value(i.default_value)} for i in n.inputs if hasattr(i,'default_value')]} for n in tree.nodes],'links':sorted([l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in tree.links)}
def state():
 scene=bpy.context.scene;root=bpy.data.objects['crate-wood__root'];collection=next(c for c in scene.collection.children if root.name in c.all_objects)
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();objects=[];materials={}
 for o in sorted(collection.all_objects,key=lambda x:x.name):
  rec={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixBasis':[list(r) for r in o.matrix_basis],'matrixParentInverse':[list(r) for r in o.matrix_parent_inverse],'hideRender':o.hide_render}
  if o.type=='MESH':
   rec.update(vertices=[list(v.co) for v in o.data.vertices],edges=[list(e.vertices) for e in o.data.edges],polygons=[{'vertices':list(p.vertices),'material':p.material_index,'smooth':p.use_smooth} for p in o.data.polygons],uvLayers=[{'name':u.name,'uv':[list(x.uv) for x in u.data]} for u in o.data.uv_layers],materials=[m.name for m in o.data.materials],modifiers=[{'name':m.name,'type':m.type,'rna':rna(m)} for m in o.modifiers])
   eo=o.evaluated_get(deps);me=eo.to_mesh();rec['evaluatedVertices']=[list(eo.matrix_world@v.co) for v in me.vertices];rec['evaluatedPolygons']=[list(p.vertices) for p in me.polygons];eo.to_mesh_clear()
   for m in o.data.materials:materials[m.name]={'graph':graph(m.node_tree),'diffuseColor':list(m.diffuse_color),'rna':rna(m)}
  objects.append(rec)
 lights=[{'name':o.name,'matrix':[list(r) for r in o.matrix_world],'rna':rna(o.data),'graph':graph(o.data.node_tree) if o.data.use_nodes else None} for o in sorted(scene.objects,key=lambda o:o.name) if o.type=='LIGHT']
 pipeline={'engine':scene.render.engine,'cycles':rna(scene.cycles),'view':rna(scene.view_settings),'display':rna(scene.display_settings),'useCompositing':scene.render.use_compositing,'compositor':graph(scene.compositing_node_group) if scene.compositing_node_group else None,'world':graph(scene.world.node_tree),'filmTransparent':scene.render.film_transparent,'dither':scene.render.dither_intensity,'imageSettings':rna(scene.render.image_settings)}
 sections={'objects':objects,'materials':materials,'lights':lights,'pipeline':pipeline}
 return {'scene':scene.name,'collection':collection.name,'root':root.name,'meshCount':sum(o['type']=='MESH' for o in objects),'sections':sections,'sectionHashes':{k:digest(v) for k,v in sections.items()},'dependencies':{'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE'],'libraries':[l.filepath for l in bpy.data.libraries]}}
def camera_record():
 s=bpy.context.scene;c=s.camera
 return {'object':c.name,'type':c.data.type,'world_matrix':[list(r) for r in c.matrix_world],'projection_matrix':[list(r) for r in c.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)],'ortho_scale':c.data.ortho_scale,'shift':[c.data.shift_x,c.data.shift_y],'resolution':[s.render.resolution_x,s.render.resolution_y],'resolutionPercentage':s.render.resolution_percentage,'pixel_aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]}
