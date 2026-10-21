"""Canonical read-only native parity for the approved plant, including its rig."""
import bpy, json, hashlib

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def value(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [value(x) for x in v]
 except TypeError:return str(v)
def rna(obj,exclude=()):
 out={}
 skip={'rna_type','name','type','session_uid','users','is_evaluated','is_runtime_data','is_editable','is_missing','is_library_indirect','use_fake_user'}|set(exclude)
 for p in obj.bl_rna.properties:
  if p.identifier in skip or p.type not in ('BOOLEAN','INT','FLOAT','STRING','ENUM'):continue
  try:out[p.identifier]=value(getattr(obj,p.identifier))
  except (AttributeError,TypeError,RuntimeError):pass
 return out
def graph(tree):
 if tree is None:return None
 nodes=[]
 for n in tree.nodes:
  item={'name':n.name,'type':n.bl_idname,'rna':rna(n),
        'inputs':[{'id':s.identifier,'name':s.name,'value':value(s.default_value)} for s in n.inputs if hasattr(s,'default_value')],
        'outputs':[{'id':s.identifier,'name':s.name,'value':value(s.default_value)} for s in n.outputs if hasattr(s,'default_value')]}
  if hasattr(n,'color_ramp'):
   c=n.color_ramp;item['colorRamp']={'mode':c.color_mode,'hueInterpolation':c.hue_interpolation,'interpolation':c.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in c.elements]}
  if hasattr(n,'node_tree') and n.node_tree:item['group']=graph(n.node_tree)
  if hasattr(n,'image') and n.image:item['image']=n.image.name
  nodes.append(item)
 return {'name':tree.name,'nodes':nodes,'links':sorted([l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in tree.links)}
def curves(action):
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:yield layer,strip,bag,fc
def all_actions():
 records=[]
 for a in sorted(bpy.data.actions,key=lambda a:a.name):
  record={'name':a.name,'rna':rna(a),'slots':[{'identifier':s.identifier,'targetIdType':s.target_id_type} for s in a.slots],'curves':[]}
  for layer,strip,bag,fc in curves(a):
   record['curves'].append({'layer':layer.name,'stripType':strip.type,'slotHandle':bag.slot_handle,
    'path':fc.data_path,'index':fc.array_index,'group':fc.group.name if fc.group else None,'rna':rna(fc),
    'modifiers':[{'type':m.type,'rna':rna(m)} for m in fc.modifiers],
    'keys':[{'co':list(k.co),'left':list(k.handle_left),'right':list(k.handle_right),
             'leftType':k.handle_left_type,'rightType':k.handle_right_type,'rna':rna(k)} for k in fc.keyframe_points]})
  records.append(record)
 return records
def normalize_static():
 s=bpy.context.scene;root=bpy.data.objects['plant-angular__root']
 assert list(root.location)==[0,0,0] and list(root.rotation_euler)==[0,0,0] and list(root.scale)==[1,1,1]
 normalized=[]
 for i in range(12):
  owner=bpy.data.objects['plant-angular__folded_leaf_%02d'%i].data.shape_keys
  action=bpy.data.actions['WARM_NATIVE__plant-angular__static__leaf_%02d'%i]
  slot=next(s for s in action.slots if s.identifier=='KEplant-angular__leaf_%02d__shape_keys'%i)
  owner.animation_data_create();owner.animation_data.action=action;owner.animation_data.action_slot=slot
  normalized.append({'owner':owner.name,'action':action.name,'slot':slot.identifier})
 s.frame_set(1);bpy.context.view_layer.update()
 for i in range(12):
  k=bpy.data.objects['plant-angular__folded_leaf_%02d'%i].data.shape_keys
  assert {x.name:x.value for x in k.key_blocks}=={'Basis':1.0,'Breeze X':0.0,'Breeze depth':0.0}
 return normalized
def ensure_visible():
 s=bpy.context.scene
 for c in bpy.data.collections:c.hide_render=False;c.hide_viewport=False
 def show(l):
  l.exclude=False;l.holdout=False;l.indirect_only=False
  for c in l.children:show(c)
 for v in s.view_layers:v.use=True;show(v.layer_collection)
 for o in s.objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update()
def state():
 s=bpy.context.scene;bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();objects=[];materials={}
 for o in sorted(s.objects,key=lambda o:o.name):
  if o.type=='CAMERA':continue
  rec={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,
       'matrixBasis':[list(r) for r in o.matrix_basis],'matrixWorld':[list(r) for r in o.matrix_world],
       'matrixParentInverse':[list(r) for r in o.matrix_parent_inverse],
       'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'hideGet':o.hide_get()}
  if o.type=='MESH':
   mesh=o.data
   rec.update({'vertices':[list(v.co) for v in mesh.vertices],'edges':[list(e.vertices) for e in mesh.edges],
    'polygons':[{'vertices':list(p.vertices),'material':p.material_index,'smooth':p.use_smooth} for p in mesh.polygons],
    'attributes':[{'name':a.name,'type':a.data_type,'domain':a.domain,'values':[rna(d) for d in a.data]} for a in mesh.attributes],
    'uvLayers':[{'name':u.name,'uv':[list(x.uv) for x in u.data]} for u in mesh.uv_layers],
    'materials':[m.name if m else None for m in mesh.materials],
    'modifiers':[{'name':m.name,'type':m.type,'rna':rna(m)} for m in o.modifiers]})
   if mesh.shape_keys:
    k=mesh.shape_keys;ad=k.animation_data
    rec['shapeKeys']={'name':k.name,'useRelative':k.use_relative,'evalTime':k.eval_time,
      'binding':{'action':ad.action.name if ad and ad.action else None,'slot':ad.action_slot.identifier if ad and ad.action_slot else None},
      'keys':[{'name':b.name,'value':b.value,'relativeKey':b.relative_key.name,'rna':rna(b),'vertices':[list(p.co) for p in b.data]} for b in k.key_blocks]}
   ev=o.evaluated_get(deps);me=ev.to_mesh()
   rec['evaluatedVertices']=[list(ev.matrix_world@v.co) for v in me.vertices]
   rec['evaluatedPolygons']=[list(p.vertices) for p in me.polygons]
   ev.to_mesh_clear()
   for m in mesh.materials:
    if m:materials[m.name]={'graph':graph(m.node_tree),'diffuseColor':list(m.diffuse_color),'rna':rna(m)}
  objects.append(rec)
 lights=[{'name':o.name,'matrix':[list(r) for r in o.matrix_world],'rna':rna(o.data),'graph':graph(o.data.node_tree) if o.data.use_nodes else None} for o in sorted(s.objects,key=lambda o:o.name) if o.type=='LIGHT']
 pipeline={'engine':s.render.engine,'cycles':rna(s.cycles),'view':rna(s.view_settings),'display':rna(s.display_settings),
  'render':rna(s.render,{'resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y','filepath'}),
  'imageSettings':rna(s.render.image_settings),'world':{'name':s.world.name,'rna':rna(s.world),'graph':graph(s.world.node_tree)},
  'compositor':graph(s.compositing_node_group)}
 sections={'objects':objects,'materials':materials,'lights':lights,'pipeline':pipeline,'actions':all_actions()}
 return {'scene':s.name,'frame':s.frame_current,'meshCount':sum(o['type']=='MESH' for o in objects),
  'sections':sections,'sectionHashes':{k:digest(v) for k,v in sections.items()},
  'dependencies':{'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file],
   'packedImages':[i.name for i in bpy.data.images if i.packed_file],'libraries':[l.filepath for l in bpy.data.libraries]}}
def camera_record():
 s=bpy.context.scene;c=s.camera
 return {'object':c.name,'type':c.data.type,'world_matrix':[list(r) for r in c.matrix_world],
  'projection_matrix':[list(r) for r in c.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)],
  'ortho_scale':c.data.ortho_scale,'shift':[c.data.shift_x,c.data.shift_y],
  'resolution':[s.render.resolution_x,s.render.resolution_y],'resolutionPercentage':s.render.resolution_percentage,
  'pixel_aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]}
