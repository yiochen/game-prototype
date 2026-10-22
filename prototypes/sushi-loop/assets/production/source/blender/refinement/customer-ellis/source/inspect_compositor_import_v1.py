"""Read-only background Blender inspection; never saves or renders a source."""
import bpy,json,hashlib,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;MODE=sys.argv[sys.argv.index('--')+1]
rec=json.loads((HERE/'resources'/f'{MODE}-rig.json').read_text());root=bpy.data.objects[rec['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects)
def plain(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 if isinstance(v,bpy.types.ID):return {'idType':v.bl_rna.identifier,'name':v.name}
 try:return [plain(x) for x in v]
 except:return str(v)
def scalar_properties(value):
 out={}
 for p in value.bl_rna.properties:
  if p.identifier=='rna_type' or p.type not in ['BOOLEAN','INT','FLOAT','STRING','ENUM']:continue
  try:out[p.identifier]=plain(getattr(value,p.identifier))
  except Exception:pass
 return out
trees={}
def tree_record(tree):
 if tree is None:return None
 if tree.name in trees:return tree.name
 out={'name':tree.name,'type':tree.bl_idname,'nodes':[],'links':[]};trees[tree.name]=out
 for node in tree.nodes:
  record={'name':node.name,'type':node.bl_idname,'mute':node.mute,'properties':scalar_properties(node),'inputs':[{'name':s.name,'identifier':s.identifier,'type':s.bl_idname,'linked':s.is_linked,'defaultValue':plain(getattr(s,'default_value',None))} for s in node.inputs],'outputs':[{'name':s.name,'identifier':s.identifier,'type':s.bl_idname} for s in node.outputs]}
  if getattr(node,'node_tree',None):record['groupTree']=tree_record(node.node_tree)
  if getattr(node,'scene',None) is not None:record['sceneReference']=node.scene.name
  if getattr(node,'image',None) is not None:
   image=node.image;record['image']={'name':image.name,'packedSHA256':hashlib.sha256(bytes(image.packed_file.data)).hexdigest() if image.packed_file else None,'filepath':image.filepath}
  if getattr(node,'mapping',None) is not None and hasattr(node.mapping,'curves'):
   record['curveMapping']={'properties':scalar_properties(node.mapping),'curves':[[{'location':list(p.location),'handleType':p.handle_type} for p in c.points] for c in node.mapping.curves]}
  out['nodes'].append(record)
 for link in tree.links:out['links'].append({'fromNode':link.from_node.name,'fromSocket':link.from_socket.identifier,'toNode':link.to_node.name,'toSocket':link.to_socket.identifier,'valid':link.is_valid,'muted':getattr(link,'is_muted',False)})
 return tree.name
tree=getattr(sc,'compositing_node_group',None) or getattr(sc,'node_tree',None)
relevant={p.identifier:plain(getattr(sc.render,p.identifier)) for p in sc.render.bl_rna.properties if 'composit' in p.identifier or 'sequenc' in p.identifier or 'precision' in p.identifier}
report={'asset':'customer-ellis','mode':MODE,'kind':'read-only-native-compositor-inspection','source':str(Path(bpy.data.filepath)),'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'scene':sc.name,'rootObject':root.name,'sceneUseNodes':sc.use_nodes,'renderCompositingSettings':relevant,'activeCompositorTree':tree_record(tree),'compositorTrees':trees,'renderSettings':{'engine':sc.render.engine,'samples':sc.eevee.taa_render_samples,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'fps':sc.render.fps,'filmTransparent':sc.render.film_transparent,'imageColorMode':sc.render.image_settings.color_mode,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'operation':'No render; no source save; only this JSON written.'}
path=OBJ/'candidates/round-02/import-adapter-v1'/f'compositor-{MODE}.json';assert not path.exists();path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2)+'\n');print('COMPOSITOR_INSPECTION',MODE,report['sceneUseNodes'],relevant,report['activeCompositorTree'],len(trees),flush=True)
