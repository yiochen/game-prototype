import bpy,json,pathlib,hashlib
repo=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
base=repo/'prototypes/sushi-loop/assets/refinement/objects/belt-straight-e/supplements/editor-goods'
out=base/'reviews/round-01-inspection'
def value(v):
 if isinstance(v,(int,float,bool,str)) or v is None:return v
 try:return [value(x) for x in v]
 except:return str(v)
def rna(obj):
 result={}
 for prop in obj.bl_rna.properties:
  key=prop.identifier
  if key in ['rna_type','name','name_full'] or prop.type in ['POINTER','COLLECTION']:continue
  if prop.is_readonly:continue
  try:result[key]=value(getattr(obj,key))
  except:pass
 return result
def graph(tree):
 if tree is None:return None
 result={'nodes':[],'links':[]}
 for n in tree.nodes:
  node={'name':n.name,'type':n.bl_idname,'properties':rna(n),'inputs':[],'outputs':[]}
  for kind in ['inputs','outputs']:
   for s in getattr(n,kind):node[kind].append({'name':s.name,'identifier':s.identifier,'default':value(s.default_value) if hasattr(s,'default_value') else None})
  if hasattr(n,'color_ramp'):node['colorRamp']={'properties':rna(n.color_ramp),'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
  result['nodes'].append(node)
 result['nodes'].sort(key=lambda n:n['name'])
 for link in tree.links:result['links'].append([link.from_node.name,list(link.from_node.outputs).index(link.from_socket),link.to_node.name,list(link.to_node.inputs).index(link.to_socket)])
 result['links'].sort();return result
def collect():
 s=bpy.context.scene;bpy.context.view_layer.update();coll=bpy.data.collections['S33_FB_belt-straight-e.001'];dg=bpy.context.evaluated_depsgraph_get();objects=[];materials=set()
 for o in sorted(coll.all_objects,key=lambda o:o.name):
  record={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix':[list(row) for row in o.matrix_world],'hidden':[o.hide_render,o.hide_viewport],'modifiers':[rna(m) for m in o.modifiers]}
  if o.type=='MESH':
   record['vertices']=[list(v.co) for v in o.data.vertices];record['faces']=[list(p.vertices) for p in o.data.polygons];record['uv']={uv.name:[list(x.uv) for x in uv.data] for uv in o.data.uv_layers};record['materials']=[m.name for m in o.data.materials];materials.update(o.data.materials)
   ev=o.evaluated_get(dg);me=ev.to_mesh();record['evaluatedVertices']=[list(ev.matrix_world@v.co) for v in me.vertices];record['evaluatedFaces']=[list(p.vertices) for p in me.polygons];ev.to_mesh_clear()
  objects.append(record)
 mrecord={m.name:graph(m.node_tree) for m in sorted(materials,key=lambda m:m.name)}
 lights=[{'name':o.name,'matrix':[list(row) for row in o.matrix_world],'data':rna(o.data)} for o in sorted(s.objects,key=lambda o:o.name) if o.type=='LIGHT']
 render={'engine':s.render.engine,'device':s.cycles.device,'samples':s.cycles.samples,'pattern':s.cycles.sampling_pattern,'scrambling':s.cycles.scrambling_distance,'pixelFilter':s.cycles.pixel_filter_type,'filterWidth':s.cycles.filter_width,'denoising':s.cycles.use_denoising,'dither':s.render.dither_intensity,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'filmTransparent':s.render.film_transparent,'colorMode':s.render.image_settings.color_mode,'colorDepth':s.render.image_settings.color_depth}
 cam=s.camera;projection=cam.calc_matrix_camera(dg,x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)
 return {'objects':objects,'materials':mrecord,'lights':lights,'world':graph(s.world.node_tree),'compositor':graph(getattr(s,'compositing_node_group',None)),'render':render,'camera':{'matrix':[list(row) for row in cam.matrix_world],'projection':[list(row) for row in projection],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'resolution':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]},'pose':{'frame':s.frame_current,'rootRotation':list(bpy.data.objects['belt-straight-e__root.001'].rotation_euler),'intrinsicRotation':list(bpy.data.objects['belt-straight-e__orientation.001'].rotation_euler),'phase':bpy.data.materials['S33_belt-straight-e_moving_deck_native'].node_tree.nodes['Value'].outputs[0].default_value},'dependencies':{'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'source':i.source,'filepath':i.filepath} for i in bpy.data.images]}}
world=collect()
bpy.ops.wm.open_mainfile(filepath=str(base/'source/source.blend'))
candidate=collect()
parity={k:world[k]==candidate[k] for k in ['objects','materials','lights','world','compositor','render','pose']}
report={'worldProjectSHA256':hashlib.sha256((base/'inputs/approved-world-model.blend').read_bytes()).hexdigest(),'candidateProjectSHA256':hashlib.sha256((base/'source/source.blend').read_bytes()).hexdigest(),'parity':parity,'approvedWorld':world,'candidate':candidate}
(out/'independent-native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.context.scene.render.filepath=str(out/'independent-reopened-goods.png');bpy.ops.render.render(write_still=True)
print(json.dumps({'parity':parity,'pose':candidate['pose'],'camera':candidate['camera'],'dependencies':candidate['dependencies']},indent=2))
