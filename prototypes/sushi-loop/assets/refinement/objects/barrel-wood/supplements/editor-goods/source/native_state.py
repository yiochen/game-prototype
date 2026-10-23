"""Read-only full-state digests for exact approved barrel goods capture parity."""
import bpy,json,hashlib

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def value(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 if isinstance(v,bpy.types.ID):return {'id':v.name_full,'type':v.bl_rna.identifier}
 try:return [value(x) for x in v]
 except TypeError:return str(v)
def rna(obj,exclude=()):
 out={}
 for p in obj.bl_rna.properties:
  if p.identifier in ('rna_type','name','type',*exclude):continue
  try:
   v=getattr(obj,p.identifier)
   if p.type in ('BOOLEAN','INT','FLOAT','STRING','ENUM'):out[p.identifier]=value(v)
   elif p.type=='POINTER' and isinstance(v,bpy.types.ID):out[p.identifier]=value(v)
  except (AttributeError,TypeError,RuntimeError):pass
 return out
def graph(tree):
 if tree is None:return None
 return {'name':tree.name,'nodes':[{'name':n.name,'type':n.bl_idname,'rna':rna(n),'inputs':[{'id':i.identifier,'value':value(i.default_value)} for i in n.inputs if hasattr(i,'default_value')],'nestedGraph':graph(n.node_tree) if n.type=='GROUP' else None} for n in tree.nodes],'links':sorted([l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in tree.links)}
def state():
 s=bpy.context.scene;root=bpy.data.objects['barrel-wood__root'];c=bpy.data.collections['S33_PROP_barrel-wood'];bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();objects={};materials={};meshcount=0
 for o in sorted(c.all_objects,key=lambda o:o.name):
  r={'type':o.type,'parent':o.parent.name if o.parent else None,'basis':[list(x) for x in o.matrix_basis],'parentInverse':[list(x) for x in o.matrix_parent_inverse],'rna':rna(o),'custom':{k:value(v) for k,v in o.items()},'animation':{'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None}}
  if o.type=='MESH':
   meshcount+=1;me=o.data
   r['mesh']={'vertices':[list(v.co) for v in me.vertices],'edges':[list(e.vertices) for e in me.edges],'polygons':[(list(p.vertices),p.material_index,p.use_smooth) for p in me.polygons],'uvLayers':[{'name':u.name,'uv':[list(x.uv) for x in u.data]} for u in me.uv_layers],'attributes':[{'name':a.name,'type':a.data_type,'domain':a.domain,'data':[rna(x) for x in a.data]} for a in me.attributes],'cornerNormals':[list(n.vector) for n in me.corner_normals],'materials':[m.name for m in me.materials],'modifiers':[{'name':m.name,'type':m.type,'rna':rna(m)} for m in o.modifiers]}
   eo=o.evaluated_get(dg);ev=eo.to_mesh();r['evaluated']={'vertices':[list(eo.matrix_world@v.co) for v in ev.vertices],'faces':[list(p.vertices) for p in ev.polygons],'cornerNormals':[list(n.vector) for n in ev.corner_normals]};eo.to_mesh_clear()
   for m in me.materials:materials[m.name]={'rna':rna(m),'useNodes':m.use_nodes,'graph':graph(m.node_tree)}
  objects[o.name]=digest(r)
 lights=[{'name':o.name,'matrix':[list(r) for r in o.matrix_world],'rna':rna(o.data),'useNodes':o.data.use_nodes,'graph':graph(o.data.node_tree)} for o in sorted(s.objects,key=lambda o:o.name) if o.type=='LIGHT']
 pipeline={'render':rna(s.render,('resolution_x','resolution_y','pixel_aspect_x','pixel_aspect_y','filepath')),'cycles':rna(s.cycles),'view':rna(s.view_settings),'display':rna(s.display_settings),'sequencerColorspace':rna(s.sequencer_colorspace_settings),'sceneUseNodes':s.use_nodes,'compositor':graph(s.compositing_node_group),'world':{'rna':rna(s.world),'useNodes':s.world.use_nodes,'graph':graph(s.world.node_tree)},'imageSettings':rna(s.render.image_settings),'frame':[s.frame_start,s.frame_end,s.frame_current,s.frame_subframe],'viewLayers':[{'name':v.name,'rna':rna(v),'cycles':rna(v.cycles)} for v in s.view_layers]}
 sections={'objects':objects,'materials':materials,'lights':lights,'pipeline':pipeline}
 return {'scene':s.name,'root':root.name,'meshCount':meshcount,'sectionHashes':{k:digest(v) for k,v in sections.items()},'objectDigests':objects,'materialDigests':{k:digest(v) for k,v in materials.items()},'pipelineSummary':{'engine':s.render.engine,'cyclesSamples':s.cycles.samples,'sceneUseNodes':s.use_nodes,'useCompositing':s.render.use_compositing,'compositorNodeCount':len(s.compositing_node_group.nodes) if s.compositing_node_group else 0,'view':rna(s.view_settings),'frame':[s.frame_start,s.frame_end,s.frame_current],'resolutionPercentage':s.render.resolution_percentage},'dependencies':{'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE'],'libraries':[l.filepath for l in bpy.data.libraries]}}
def camera_record():
 s=bpy.context.scene;c=s.camera
 return {'object':c.name,'type':c.data.type,'world_matrix':[list(r) for r in c.matrix_world],'projection_matrix':[list(r) for r in c.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)],'ortho_scale':c.data.ortho_scale,'shift':[c.data.shift_x,c.data.shift_y],'resolution':[s.render.resolution_x,s.render.resolution_y],'resolutionPercentage':s.render.resolution_percentage,'pixel_aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]}
