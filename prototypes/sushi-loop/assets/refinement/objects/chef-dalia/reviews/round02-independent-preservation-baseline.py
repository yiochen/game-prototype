import bpy,pathlib,json,hashlib,importlib.util
b=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-dalia');r=b/'reviews';record=json.loads((b/'inputs/source-rig.json').read_text());root=bpy.data.objects[record['groundRootObject']];col=min([c for c in bpy.data.collections if root in list(c.all_objects)],key=lambda c:len(c.all_objects));plane=bpy.data.objects[root.name+'__held_dish-salmon__image_plane'];spec=importlib.util.spec_from_file_location('dalia_food_original_native',b/'source/native_actions_round01.py');na=importlib.util.module_from_spec(spec);spec.loader.exec_module(na)
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def h(v):return hashlib.sha256(canon(v)).hexdigest()
def val(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 try:return list(v)
 except:return str(v)
def tree(t):
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[{'name':s.name,'index':i,'value':val(s.default_value)} for i,s in enumerate(n.inputs) if hasattr(s,'default_value')],'outputs':[{'name':s.name,'index':i,'value':val(s.default_value)} for i,s in enumerate(n.outputs) if hasattr(s,'default_value')],'image':n.image.name if getattr(n,'image',None) else None,'operation':getattr(n,'operation',None),'blendType':getattr(n,'blend_type',None),'interpolation':getattr(n,'interpolation',None),'extension':getattr(n,'extension',None),'projection':getattr(n,'projection',None)} for n in t.nodes],'links':[{'fromNode':l.from_node.name,'fromIndex':list(l.from_node.outputs).index(l.from_socket),'toNode':l.to_node.name,'toIndex':list(l.to_node.inputs).index(l.to_socket)} for l in t.links]}
meshes={};transforms={};materials={}
for o in col.all_objects:
 transforms[o.name]={'type':o.type,'parent':o.parent.name if o.parent else None,'matrixBasis':[list(z) for z in o.matrix_basis],'matrixParentInverse':[list(z) for z in o.matrix_parent_inverse],'hideRender':o.hide_render,'modifiers':[{k:val(getattr(m,k,None)) for k in ['name','type','show_render','show_viewport','vertex_group','invert_vertex_group','use_vertex_groups','use_bone_envelopes','use_deform_preserve_volume']} | {'target':getattr(m,'object',None).name if getattr(m,'object',None) else None} for m in o.modifiers]}
 if o.type=='MESH':
  if o!=plane:
   data={'vertices':[list(v.co) for v in o.data.vertices],'edges':[list(e.vertices) for e in o.data.edges],'polygons':[list(p.vertices) for p in o.data.polygons],'polygonSmooth':[p.use_smooth for p in o.data.polygons],'polygonMaterialIndices':[p.material_index for p in o.data.polygons],'uvLayers':{uv.name:[list(q.uv) for q in uv.data] for uv in o.data.uv_layers},'materials':[m.name if m else None for m in o.data.materials]}
   weights={'groupNames':[g.name for g in o.vertex_groups],'vertices':[[[g.group,g.weight] for g in v.groups] for v in o.data.vertices]};meshes[o.name]={'geometrySHA256':h(data),'weightsSHA256':h(weights),'vertices':len(o.data.vertices),'edges':len(o.data.edges),'polygons':len(o.data.polygons)}
  for m in o.data.materials:
   if m and m.name not in materials:
    desc={'useNodes':m.use_nodes,'diffuseColor':list(m.diffuse_color),'surfaceRenderMethod':getattr(m,'surface_render_method',None),'useTransparentShadow':getattr(m,'use_transparent_shadow',None),'nodeTree':tree(m.node_tree) if m.use_nodes else None};materials[m.name]={'SHA256':h(desc),'description':desc,'foodShader':o==plane}
arm=bpy.data.objects[record['armatures'][0]['object']];bones={z.name:{'parent':z.parent.name if z.parent else None,'matrixLocal':[list(v) for v in z.matrix_local],'headLocal':list(z.head_local),'tailLocal':list(z.tail_local),'useDeform':z.use_deform} for z in arm.data.bones};actions={}
for clip,c in record['clips'].items():
 for target in c['actions']:
  name=target['action'];a=bpy.data.actions[name]
  curves=[{'path':f.data_path,'index':f.array_index,'extrapolation':f.extrapolation,'keys':[{'co':list(k.co),'interpolation':k.interpolation,'leftType':k.handle_left_type,'rightType':k.handle_right_type,'left':list(k.handle_left),'right':list(k.handle_right)} for k in f.keyframe_points]} for f in na._fcurves(a)];actions[name]={'SHA256':h(curves),'fcurves':len(curves),'keyframes':sum(len(f['keys']) for f in curves),'clip':clip}
result={'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'hashConvention':'SHA256 of JSON sort_keys=True,separators=(comma,colon),ensure_ascii=False; geometry/weights serialized by this saved script. Baseline describes native source data, not deterministic PNG bytes.','bodyAndKnifeMeshes':meshes,'bodyAndKnifeMeshCount':len(meshes),'boneRestSHA256':h(bones),'boneRest':bones,'actions':actions,'materials':materials,'sourceObjectTransforms':transforms,'excludedFromPhysicalGeometryLock':'Only held image plane local vertices/UV and permitted orthoray display-offset amplitude may change by frozen mapping; texture packed bytes replace with exact canonical artwork. All other native data locked.'}
(r/'round02-independent-preservation-baseline.json').write_text(json.dumps(result,indent=2)+'\n');print('BASELINE',len(meshes),'body/knife meshes',len(actions),'actions',len(materials),'materials')
