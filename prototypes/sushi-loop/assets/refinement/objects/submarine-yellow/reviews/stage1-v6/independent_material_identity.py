import bpy,json,pathlib,hashlib
P=pathlib.Path(__file__).resolve().parent;SRC=P/'resources/source/stage1-v6';BASE=SRC/'resources/baseline-v5.blend';NEW=SRC/'submarine-stage1.blend'
def plain(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 if isinstance(v,bpy.types.ID):return {'idType':v.bl_rna.identifier,'name':v.name}
 try:return [plain(x) for x in v]
 except TypeError:return str(v)
def hd(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def props(x):
 d={}
 for p in x.bl_rna.properties:
  if p.identifier in {'rna_type'}:continue
  if p.type in {'BOOLEAN','INT','FLOAT','ENUM','STRING'}:
   try:d[p.identifier]=plain(getattr(x,p.identifier))
   except Exception:pass
 return d
def tree(t):
 if t is None:return None
 ns=[]
 for n in t.nodes:
  z={'name':n.name,'type':n.bl_idname,'settings':props(n),'inputs':[(a.identifier,plain(a.default_value)) for a in n.inputs if hasattr(a,'default_value')]}
  if hasattr(n,'color_ramp'):z['ramp']={'properties':props(n.color_ramp),'elements':[(e.position,plain(e.color)) for e in n.color_ramp.elements]}
  if hasattr(n,'node_tree') and n.node_tree:z['group']=tree(n.node_tree)
  ns.append(z)
 return {'nodes':sorted(ns,key=lambda a:a['name']),'links':sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links),'animation':bool(t.animation_data)}
def capture(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;col=bpy.data.collections['WarmSoft_submarine-yellow_stage1'];bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();objs=[];meshes=[];slots={};actions=[]
 for o in sorted(col.all_objects,key=lambda o:o.name):
  objs.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'parentInverse':plain(o.matrix_parent_inverse),'local':plain(o.matrix_local),'world':plain(o.matrix_world),'hide':(o.hide_render,o.hide_viewport),'custom':{k:plain(v) for k,v in o.items()},'constraints':[props(c) for c in o.constraints],'drivers':[(f.data_path,f.array_index) for f in o.animation_data.drivers] if o.animation_data else []})
  if o.type=='MESH':
   me=o.data;eo=o.evaluated_get(dg);ev=eo.to_mesh();slots[o.name]=[m.name for m in me.materials];meshes.append({'object':o.name,'v':[plain(v.co) for v in me.vertices],'e':[plain(e.vertices) for e in me.edges],'p':[(plain(f.vertices),plain(f.normal),f.material_index,f.use_smooth) for f in me.polygons],'cornerNormals':[plain(n.vector) for n in me.corner_normals],'uv':{u.name:[plain(x.uv) for x in u.data] for u in me.uv_layers},'modifiers':[props(m) for m in o.modifiers],'shapeKeys':me.shape_keys.name if me.shape_keys else None,'dataAnimation':bool(me.animation_data),'evalV':[plain(v.co) for v in ev.vertices],'evalP':[(plain(f.vertices),plain(f.normal),f.material_index) for f in ev.polygons],'evalCornerNormals':[plain(n.vector) for n in ev.corner_normals]});eo.to_mesh_clear()
 reg=json.loads(bpy.data.objects['submarine-yellow__root']['nativeActions'])
 for clip,owners in sorted(reg.items()):
  for owner,name in sorted(owners.items()):
   a=bpy.data.actions[name];channels=[]
   for lay in a.layers:
    for strip in lay.strips:
     for bag in strip.channelbags:
      for f in bag.fcurves:channels.append({'path':f.data_path,'index':f.array_index,'extrapolation':f.extrapolation,'keys':[(plain(k.co),k.interpolation,plain(k.handle_left),plain(k.handle_right)) for k in f.keyframe_points],'modifiers':[props(m) for m in f.modifiers]})
   actions.append({'clip':clip,'owner':owner,'name':name,'slots':[s.identifier for s in a.slots],'channels':channels})
 mats={m.name:{'nodes':tree(m.node_tree),'surface':props(m),'animation':bool(m.animation_data)} for m in bpy.data.materials};cam=sc.camera
 scene={'camera':(plain(cam.matrix_world),props(cam.data)),'render':{k:getattr(sc.render,k) for k in ['resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y','fps','fps_base','engine','filter_size','film_transparent']},'samples':sc.eevee.taa_render_samples,'world':tree(sc.world.node_tree),'color':props(sc.view_settings),'lights':[(o.name,plain(o.matrix_world),props(o.data)) for o in sorted(sc.objects,key=lambda a:a.name) if o.type=='LIGHT']}
 return {'objects':objs,'meshes':meshes,'actions':actions,'slots':slots,'materials':mats,'scene':scene,'images':[(i.name,i.filepath,i.source,bool(i.packed_file)) for i in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries]}
a=capture(BASE);b=capture(NEW);keys=['objects','meshes','actions','scene','images','libraries'];checks={k:a[k]==b[k] for k in keys};changed=[k for k in a['slots'] if a['slots'][k]!=b['slots'].get(k)];added=sorted(set(b['materials'])-set(a['materials']));old={k:v==b['materials'].get(k) for k,v in a['materials'].items()};checks.update({'onlyGlassSlot':changed==['body__convex_blue_glass'],'oneNewMaterial':added==['Sub Native depth glass v6'],'originalMaterialsIdentical':all(old.values())})
mat=bpy.data.materials['Sub Native depth glass v6'];nodes=mat.node_tree.nodes;links=mat.node_tree.links;principled=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');checks.update({'nativeStaticShader':not mat.animation_data and not mat.node_tree.animation_data,'opaqueUnchanged':principled.inputs['Alpha'].default_value==1 and principled.inputs['Transmission Weight'].default_value==0,'noGeometryDisplacement':not principled.inputs['Normal'].is_linked and not output.inputs['Displacement'].is_linked,'noImageOrPlaneShader':not any(n.type in ['TEX_IMAGE','TEX_ENVIRONMENT','TEX_COORD','TEX_NOISE','TEX_WAVE','TEX_VORONOI'] for n in nodes)})
used_geometry=[(l.from_socket.name,l.to_node.type) for l in links if l.from_node.type=='NEW_GEOMETRY'];split=[(l.from_node.type,l.from_socket.name,l.to_node.name) for l in links if l.from_node.type=='SEPXYZ'];proof={'baselineSHA256':hashlib.sha256(BASE.read_bytes()).hexdigest(),'newSourceSHA256':hashlib.sha256(NEW.read_bytes()).hexdigest(),'checks':checks,'allPass':all(checks.values()),'changedSlots':changed,'addedMaterials':added,'originalMaterialEquality':old,'hashes':{k:{'v5':hd(a[k]),'v6':hd(b[k])} for k in keys},'glassGraph':tree(mat.node_tree),'glassGraphInputs':{'geometryOutputsUsed':used_geometry,'separatedComponentsUsed':split},'technicalReuse':'All independent native identity groups pass only if unchanged. Reuse exact v5 1200-phase, hover, finite seat and reservation/projection evidence; no new geometry/motion/opacity/displacement channels. Native static glass graph uses view angle and reflected incoming-ray elevation (world Z), with no horizontal X/Y azimuth branch.'}
(P/'independent-identity-and-glass.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'checks':checks,'allPass':proof['allPass'],'changedSlots':changed,'newMaterials':added},indent=2))
# One representative verifies the new static shader renders from saved source; no broad phase rerun.
sc=bpy.context.scene;root=bpy.data.objects['submarine-yellow__root'];reg=json.loads(root['nativeActions'])
for owner,an in reg['dock-ready'].items():
 o=bpy.data.objects[owner];o.animation_data_create();ac=bpy.data.actions[an];o.animation_data.action=ac;o.animation_data.action_slot=ac.slots[0]
root.location=(0,0,0);root.rotation_euler=(0,0,0);sc.frame_set(1);bpy.context.view_layer.update();sc.render.filepath=str(P/'independent-replay-dock-ready-S.png');bpy.ops.render.render(write_still=True)
