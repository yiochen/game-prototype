"""Material-only identity proof binds immutable v5 technical gates to saved v6."""
import bpy,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parents[1];O=B/'candidates/round-01';R=H/'resources'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hd(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def vals(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [vals(x) for x in v]
 except:return str(v)
def graph(tree):
 if tree is None:return None
 ns=[]
 for n in tree.nodes:
  d={'name':n.name,'type':n.bl_idname,'inputs':{i.identifier:vals(i.default_value) for i in n.inputs if hasattr(i,'default_value')}}
  for k in ['operation','blend_type','use_clamp','distribution','subsurface_method','attribute_name','vector_type','convert_from','convert_to']:
   if hasattr(n,k):d[k]=vals(getattr(n,k))
  if hasattr(n,'color_ramp'):d['ramp']={'mode':n.color_ramp.color_mode,'interpolation':n.color_ramp.interpolation,'hue':n.color_ramp.hue_interpolation,'elements':[[e.position,vals(e.color)] for e in n.color_ramp.elements]}
  ns.append(d)
 return {'nodes':sorted(ns,key=lambda n:n['name']),'links':sorted([[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in tree.links]),'animated':bool(tree.animation_data)}
def modifiers(o):
 ret=[]
 for m in o.modifiers:
  d={'name':m.name,'type':m.type}
  for p in m.bl_rna.properties:
   if p.is_readonly or p.type not in ['BOOLEAN','INT','FLOAT','ENUM','STRING'] or p.identifier in ['name','type','rna_type']:continue
   try:d[p.identifier]=vals(getattr(m,p.identifier))
   except:pass
  ret.append(d)
 return ret

def snapshot(file):
 bpy.ops.wm.open_mainfile(filepath=str(file));s=bpy.context.scene;c=s.camera;col=bpy.data.collections['WarmSoft_submarine-yellow_stage1'];root=bpy.data.objects['submarine-yellow__root'];
 for owner,an in json.loads(root['nativeActions'])['dock-ready'].items():
  if owner not in bpy.data.objects:continue
  ob=bpy.data.objects[owner];ob.animation_data_create();ac=bpy.data.actions[an];ob.animation_data.action=ac
  if ac.slots:ob.animation_data.action_slot=ac.slots[0]
 root.location=(0,0,0);root.rotation_euler.z=0;s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 objects=[];meshes=[];slots={}
 for o in sorted((x for x in col.all_objects if x.name in body_names),key=lambda o:o.name):
  objects.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixLocal':vals(o.matrix_local),'parentInverse':vals(o.matrix_parent_inverse),'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'properties':{k:vals(v) for k,v in o.items()},'constraints':[x.type for x in o.constraints]})
  if o.type!='MESH':continue
  me=o.data;e=o.evaluated_get(dg);em=e.to_mesh();slots[o.name]=[m.name for m in me.materials]
  d={'object':o.name,'mesh':me.name,'vertices':[vals(v.co) for v in me.vertices],'edges':[vals(e.vertices) for e in me.edges],'polygons':[{'vertices':vals(p.vertices),'materialIndex':p.material_index,'smooth':p.use_smooth,'normal':vals(p.normal)} for p in me.polygons],'cornerNormals':[vals(n.vector) for n in me.corner_normals],'UV':{u.name:[vals(x.uv) for x in u.data] for u in me.uv_layers},'shapeKeys':me.shape_keys.name if me.shape_keys else None,'geometryAnimated':bool(me.animation_data),'modifiers':modifiers(o),'evaluatedVertices':[vals(v.co) for v in em.vertices],'evaluatedPolygons':[{'vertices':vals(p.vertices),'normal':vals(p.normal)} for p in em.polygons],'evaluatedCornerNormals':[vals(n.vector) for n in em.corner_normals]};e.to_mesh_clear();meshes.append(d)
 root=bpy.data.objects['submarine-yellow__root'];clips=json.loads(root['nativeActions']);actions=[]
 for clip,owners in clips.items():
  for owner,an in owners.items():
   a=bpy.data.actions[an];ch=[]
   for layer in a.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for f in bag.fcurves:ch.append({'path':f.data_path,'index':f.array_index,'extrapolation':f.extrapolation,'keys':[[vals(k.co),k.interpolation,vals(k.handle_left),vals(k.handle_right)] for k in f.keyframe_points]})
   actions.append({'clip':clip,'owner':owner,'action':an,'slots':[x.identifier for x in a.slots],'channels':ch})
 mats={m.name:{'graph':graph(m.node_tree),'roughness':m.roughness,'metallic':m.metallic,'diffuseColor':vals(m.diffuse_color),'animated':bool(m.animation_data)} for m in bpy.data.materials}
 scene={'cameraMatrix':vals(c.matrix_world),'cameraOrthoScale':c.data.ortho_scale,'shift':[c.data.shift_x,c.data.shift_y],'frame':[s.render.resolution_x,s.render.resolution_y],'percent':s.render.resolution_percentage,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'fps':s.render.fps,'engine':s.render.engine,'samples':s.eevee.taa_render_samples,'filterSize':s.render.filter_size,'filmTransparent':s.render.film_transparent,'colorManagement':[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma],'world':graph(s.world.node_tree),'lights':[{'name':o.name,'matrix':vals(o.matrix_world),'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'color':vals(o.data.color),'useShadow':o.data.use_shadow} for o in sorted(s.objects,key=lambda o:o.name) if o.type=='LIGHT']}
 return {'objects':objects,'meshes':meshes,'slots':slots,'actions':actions,'materials':mats,'scene':scene,'images':[{'name':x.name,'filepath':x.filepath,'source':x.source,'packed':bool(x.packed_file)} for x in bpy.data.images],'libraries':[x.filepath for x in bpy.data.libraries]}

bpy.ops.wm.open_mainfile(filepath=str(R/'frozen-body-v6.blend'))
body_names={o.name for o in bpy.data.collections['WarmSoft_submarine-yellow_stage1'].all_objects if not o.name.startswith('PROVISIONAL__')}
a=snapshot(R/'frozen-body-v6.blend');v=snapshot(H/'project.blend')
checks={
 'bodyHierarchyTransformsVisibilityPropertiesIdentical':a['objects']==v['objects'],
 'bodyBaseAndEvaluatedGeometryNormalsUVModifiersIdentical':a['meshes']==v['meshes'],
 'allFrozenNativeActionsOwnerBindingsTimingIdentical':a['actions']==v['actions'],
 'cameraLightsWorldFrameRenderSettingsIdentical':a['scene']==v['scene'],
 'allFrozenBodyMaterialSlotsIdentical':a['slots']==v['slots'],
 'everyFrozenMaterialGraphIdentical':all(v['materials'].get(k)==m for k,m in a['materials'].items()),
 'noExternalImageOrLinkedResourcesAdded':a['images']==v['images'] and a['libraries']==v['libraries']}
proof={'frozenBodySHA256':sha(R/'frozen-body-v6.blend'),'finalSourceSHA256':sha(H/'project.blend'),'bodyObjectNames':sorted(body_names),'checks':checks,'allIdentityGatesPass':all(checks.values()),'fingerprints':{k:{'frozen':hd(a[k]),'final':hd(v[k])} for k in ['objects','meshes','slots','actions','scene']},'frozenMaterialFingerprints':{k:hd(m) for k,m in a['materials'].items()},'note':'CanonicalS dock-ready frame1 applied from each saved source for like-for-like evaluation. Explicit PROVISIONAL geometry excluded; all frozen actions including archived visibility owners retained exactly. Main metadata including legacy reference coordinates unchanged. Canonical cohorts use new visibility actions only.'}
(O/'frozen-body-identity.json').write_text(json.dumps(proof,indent=2)+'\n')
print('FROZEN IDENTITY',checks)
assert all(checks.values()),checks
