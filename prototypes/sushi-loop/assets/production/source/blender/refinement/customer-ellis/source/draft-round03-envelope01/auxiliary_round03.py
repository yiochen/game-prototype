"""Read-only native shader/deformation inventory and empirical repeat renders."""
import bpy,json,sys,hashlib,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;MODE=sys.argv[sys.argv.index('--')+1]
OUT=OBJ/'candidates/round-03/diagnostics';OUT.mkdir(parents=True,exist_ok=True)
rec=json.loads((HERE/'resources'/f'{MODE}-rig.json').read_text());root=bpy.data.objects[rec['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects)
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];coll=next(c for c in sc.collection.children if root.name in c.all_objects);asset={'root':root,'collection':coll}
spec=importlib.util.spec_from_file_location('native',HERE/'resources/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
def plain(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 try:return [plain(v) for v in x]
 except:return str(x)
def mat_record(m):
 tree=m.node_tree;nodes=list(tree.nodes)
 return {'blend':m.surface_render_method,'overlap':m.use_transparency_overlap,'transparentShadow':m.use_transparent_shadow,'diffuseColor':list(m.diffuse_color),'nodes':[{'type':n.bl_idname,'mute':n.mute,'operation':getattr(n,'operation',None),'inputs':[{'id':s.identifier,'value':plain(getattr(s,'default_value',None))} for s in n.inputs],'imageSHA256':hashlib.sha256(bytes(n.image.packed_file.data)).hexdigest() if getattr(n,'image',None) and n.image.packed_file else None} for n in nodes],'links':[[nodes.index(l.from_node),l.from_socket.identifier,nodes.index(l.to_node),l.to_socket.identifier] for l in tree.links]}
food=next(o for o in coll.all_objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi')
report={'asset':'customer-ellis','mode':MODE,'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'bodyShaders':{o.name.split('customer_ellis__')[-1]:[mat_record(m) for m in o.data.materials] for o in coll.all_objects if o.type=='MESH' and o!=food},'foodMaterial':mat_record(food.data.materials[0]),'foodShadow':food.visible_shadow,'objectGroupAssignments':{o.name.split('customer_ellis__')[-1]:{'groups':[g.name for g in o.vertex_groups],'allVerticesFullyHeadWeighted':all(len(v.groups)==1 and o.vertex_groups[v.groups[0].group].name=='head' and v.groups[0].weight==1 for v in o.data.vertices)} for o in coll.all_objects if o.type=='MESH' and any(s in o.name for s in ['swept_short_hair','glasses_arm_'])},'renders':[]}
sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100
for clip,direction,frame in ([('stand','S',5),('eat','E',12),('panic','N',7)] if MODE=='main' else [('eat-salmon','S',5)]):
 native.apply_clip(asset,rec,clip,frame,direction,sc)
 for repeat in range(2):
  path=OUT/(MODE+'-'+clip.replace('_','-')+'-'+direction+f'-repeat-{repeat}.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True,scene=sc.name)
  report['renders'].append({'clip':clip,'direction':direction,'frame':frame,'repeat':repeat,'path':str(path.relative_to(OBJ)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(OUT/(MODE+'-native-settings.json')).write_text(json.dumps(report,indent=2)+'\n')
print('ELLIS_AUXILIARY',MODE,flush=True)
