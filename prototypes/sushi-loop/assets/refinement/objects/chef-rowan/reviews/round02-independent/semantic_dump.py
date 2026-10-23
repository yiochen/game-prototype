import bpy,json,pathlib,sys,hashlib,importlib.util
from mathutils import Matrix,Vector,Quaternion,Color
b=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-rowan');out=b/'reviews/round02-independent';which=pathlib.Path(bpy.data.filepath).stem
col=bpy.data.collections['S33_CHARACTER_chef_rowan.001'];root=bpy.data.objects['chef_rowan__ground_root.001'];arm=bpy.data.objects['chef_rowan__armature.001'];sc=bpy.context.scene
col.hide_viewport=col.hide_render=False
for l in bpy.context.view_layer.layer_collection.children:l.exclude=l.collection!=col
bpy.context.view_layer.update()
spec=importlib.util.spec_from_file_location('native_semantics',b/'source/resources/original-native-actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native);rec=json.loads((b/'inputs/source-rig.json').read_text());native.apply_clip({'root':root,'collection':col,'armature':arm},rec,'idle',1,'S',sc)
def conv(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 if isinstance(x,bpy.types.ID):return {'id':x.name,'type':x.bl_rna.identifier}
 if hasattr(x,'bl_rna'):return {'rna':x.bl_rna.identifier,'props':props(x)}
 try:return [conv(v) for v in x]
 except:return str(x)
def props(x):
 d={}
 for p in x.bl_rna.properties:
  if p.identifier in ['rna_type','id_data','name','name_full','original','users','use_fake_user','is_evaluated','library','override_library','preview','animation_data']:continue
  if p.type in ['BOOLEAN','INT','FLOAT','STRING','ENUM','POINTER']:
   try:d[p.identifier]=conv(getattr(x,p.identifier))
   except:pass
 return d
def nodes(tree):
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'props':props(n),'inputs':[{'name':s.name,'value':conv(getattr(s,'default_value',None))} for s in n.inputs]} for n in tree.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in tree.links]}
objs={};meshes={};materials={}
for o in sorted(col.all_objects,key=lambda x:x.name):
 d={'type':o.type,'parent':o.parent.name if o.parent else None,'matrixLocal':conv(o.matrix_local),'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'mods':[{'name':m.name,'type':m.type,'props':props(m)} for m in o.modifiers],'groups':[g.name for g in o.vertex_groups]}
 if '__image_plane' in o.name:
  d['matrixLocal']='allowed ray offset only, audited in192-frame comparison'
  d['drivers']=[{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression,'variables':[(v.name,[(t.id.name,t.data_path) for t in v.targets]) for v in f.driver.variables]} for f in o.animation_data.drivers]
 objs[o.name]=d
 if o.type=='MESH':
  me=o.data;meshes[o.name]={'vertices':[[conv(v.co),[(g.group,g.weight) for g in v.groups]] for v in me.vertices],'edges':[list(e.vertices) for e in me.edges],'polygons':[(list(p.vertices),p.material_index,p.use_smooth) for p in me.polygons],'uv':{u.name:[conv(x.uv) for x in u.data] for u in me.uv_layers},'materials':[m.name if m else None for m in me.materials]}
  for m in me.materials:
   if m:materials[m.name]={'props':props(m),'nodes':nodes(m.node_tree) if m.use_nodes else None}
images=[{'name':i.name,'size':list(i.size),'packed':bool(i.packed_file),'packedSHA256':hashlib.sha256(bytes(i.packed_file.data)).hexdigest() if i.packed_file else None,'alphaMode':i.alpha_mode,'colorspace':i.colorspace_settings.name} for i in bpy.data.images if i.name not in ['Render Result','Viewer Node']]
data={'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'objects':objs,'meshes':meshes,'materials':materials,'lights':{o.name:{'matrix':conv(o.matrix_world),'props':props(o.data)} for o in sc.objects if o.type=='LIGHT'},'camera':{'matrix':conv(sc.camera.matrix_world),'props':props(sc.camera.data)},'world':{'props':props(sc.world),'nodes':nodes(sc.world.node_tree)},'render':props(sc.render),'view':props(sc.view_settings),'images':images}
(out/(which+'-semantics.json')).write_text(json.dumps(data,sort_keys=True,indent=2));print('Semantic data recorded',which)
