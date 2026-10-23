import bpy,json,sys,hashlib
from pathlib import Path
P=Path(__file__).parent;sys.path.insert(0,str(P));import native_actions_round02 as native
sc=bpy.data.scenes.get('Lena warm soft round02') or bpy.data.scenes['Lena warm soft round01'];bpy.context.window.scene=sc;coll=bpy.data.collections['S33_CHARACTER_chef_lena.002'];root=bpy.data.objects['chef_lena__ground_root.002'];arm=bpy.data.objects['chef_lena__armature.002'];rig=json.loads((P/'rig-round02.json').read_text());asset={'collection':coll,'root':root,'armature':arm};native.apply_clip(asset,rig,'idle',1,'S',sc)
def value(x):
 if isinstance(x,(str,bool,float,int)) or x is None:return x
 try:return [float(a) for a in x]
 except:return str(type(x))
def tree(t):
 return {'nodes': [{'name':n.name,'type':n.type,'inputs':[[s.name,value(s.default_value)] for s in n.inputs if hasattr(s,'default_value')],'image':getattr(getattr(n,'image',None),'name',None)} for n in sorted(t.nodes,key=lambda n:n.name)],'links':sorted((l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in t.links)}
objects=[];mats={}
for o in sorted(sc.objects,key=lambda o:o.name):
 row={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'basis':[list(r) for r in o.matrix_basis],'parentInverse':[list(r) for r in o.matrix_parent_inverse],'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'drivers':[]}
 if o.animation_data:
  for d in o.animation_data.drivers:row['drivers'].append({'path':d.data_path,'index':d.array_index,'expression':d.driver.expression,'variables':[(v.name,[(t.id.name,t.data_path) for t in v.targets]) for v in d.driver.variables]})
 if o.type=='MESH':
  row['vertices']=[list(v.co) for v in o.data.vertices];row['polygons']=[list(p.vertices) for p in o.data.polygons];row['polyMaterials']=[p.material_index for p in o.data.polygons];row['groups']=[g.name for g in o.vertex_groups];row['weights']=[[(g.group,g.weight) for g in v.groups] for v in o.data.vertices];row['materials']=[m.name for m in o.data.materials];row['modifiers']=[(m.type,getattr(getattr(m,'object',None),'name',None)) for m in o.modifiers]
  for m in o.data.materials:
   if m.use_nodes:mats[m.name]=tree(m.node_tree)
 if o.type=='ARMATURE':row['rest']={b.name:[list(r) for r in b.matrix_local] for b in o.data.bones}
 if o.type=='LIGHT':row['light']={'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)}
 if o.type=='CAMERA':row['camera']={'type':o.data.type,'orthoScale':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y],'sensorFit':o.data.sensor_fit}
 objects.append(row)
actions={}
for config in rig['clips'].values():
 for t in config['actions']:
  a=bpy.data.actions[t['action']];actions[a.name]=[{'dataPath':fc.data_path,'index':fc.array_index,'keys':[(list(k.co),k.interpolation,list(k.handle_left),list(k.handle_right)) for k in fc.keyframe_points]} for fc in native._fcurves(a)]
x={'objects':objects,'materials':mats,'actions':actions,'world':tree(sc.world.node_tree),'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'denoise':sc.cycles.use_denoising,'filter':sc.cycles.pixel_filter_type,'filterSize':sc.render.filter_size,'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'view':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure},'images':[(im.name,hashlib.sha256(im.packed_file.data).hexdigest()) for im in bpy.data.images if im.packed_file]}
blob=json.dumps(x,sort_keys=True,separators=(',',':')).encode();name=sys.argv[sys.argv.index('--')+1];(P/('fingerprint-'+name+'.json')).write_text(json.dumps({'dataSHA256':hashlib.sha256(blob).hexdigest(),'blendSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scope':'All native scene object topology/coordinates/weights/transforms/material nodes/lighting/camera/render settings, full24 cohort action curves/rest bones/packed images; UI and serialization metadata excluded','objectCount':len(objects),'objectHashes':{o['name']:hashlib.sha256(json.dumps(o,sort_keys=True).encode()).hexdigest() for o in objects},'materialHashes':{n:hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest() for n,v in mats.items()},'actionHashes':{n:hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest() for n,v in actions.items()},'worldHash':hashlib.sha256(json.dumps(x['world'],sort_keys=True).encode()).hexdigest(),'renderHash':hashlib.sha256(json.dumps(x['render'],sort_keys=True).encode()).hexdigest()},indent=2));print('FINGERPRINT',name,hashlib.sha256(blob).hexdigest())
