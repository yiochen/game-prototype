import bpy,json,hashlib,sys
from pathlib import Path
P=Path(__file__).resolve().parent;OBJ=P.parents[1];MODE=sys.argv[sys.argv.index('--')+1]
record=json.loads((OBJ/('inputs/source-rig.json' if MODE=='main' else 'inputs/runtime-variants/export/source/customer-ellis/rig.json')).read_text());root=bpy.data.objects[record['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects);coll=next(c for c in sc.collection.children if root.name in c.all_objects)
def val(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 try:return [val(x) for x in v]
 except:return str(v)
def norm(s):return s.replace('S10 meal ','') if isinstance(s,str) else s
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def props(o,skip=[]):
 out={}
 for p in o.bl_rna.properties:
  if p.identifier in ['rna_type']+skip or p.is_readonly or p.type in ['COLLECTION','POINTER']:continue
  try:out[p.identifier]=val(getattr(o,p.identifier))
  except:pass
 return out
def tree(t):
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'mute':n.mute,'properties':props(n),'inputs':[{'name':i.name,'linked':i.is_linked,'default':val(i.default_value) if hasattr(i,'default_value') else None} for i in n.inputs],'image':{'name':n.image.name,'packedSHA256':hashlib.sha256(bytes(n.image.packed_file.data)).hexdigest(),'size':list(n.image.size)} if n.type=='TEX_IMAGE' and n.image and n.image.packed_file else None} for n in t.nodes], 'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in t.links]}
mats={m for o in coll.all_objects if o.type=='MESH' for m in o.data.materials if m}
materials={m.name:{'properties':props(m),'tree':tree(m.node_tree) if m.use_nodes else None} for m in mats}
body={}
for o in coll.all_objects:
 if o.type!='MESH' or o.get('representation') or '__knife_' in o.name:continue
 geometry={'vertices':[list(v.co) for v in o.data.vertices],'polygons':[list(f.vertices) for f in o.data.polygons],'smooth':[f.use_smooth for f in o.data.polygons]}
 weights=[[[norm(o.vertex_groups[g.group].name),g.weight] for g in v.groups] for v in o.data.vertices]
 modifiers=[{'type':m.type,'properties':props(m,skip=['name']),'object':norm(getattr(getattr(m,'object',None),'name',None))} for m in o.modifiers]
 body[norm(o.name)]={'geometrySHA256':digest(geometry),'weightsSHA256':digest(weights),'vertexCount':len(o.data.vertices),'polygonCount':len(o.data.polygons),'modifiers':modifiers,'transform':{'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'parentInverse':[list(r) for r in o.matrix_parent_inverse]},'materials':[m.name if m else None for m in o.data.materials]}
comp=getattr(sc,'compositing_node_group',None) or getattr(sc,'node_tree',None)
out={'source':bpy.data.filepath,'sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'mode':MODE,'body':body,'materials':materials,'lights':[{'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'matrix':[list(r) for r in o.matrix_world],'size':o.data.size} for o in sc.objects if o.type=='LIGHT'],'render':props(sc.render),'view':props(sc.view_settings),'sceneUseNodes':sc.use_nodes,'compositor':tree(comp) if comp else None,'images':[{'name':im.name,'packedSHA256':hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None} for im in bpy.data.images]}
food=next(o for o in coll.all_objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi');mat=food.data.materials[0]
out['foodFlags']={'plane':food.name,'visible_shadow':food.visible_shadow,'surface_render_method':mat.surface_render_method,'use_transparency_overlap':mat.use_transparency_overlap,'use_transparent_shadow':mat.use_transparent_shadow}
(P/(MODE+'-inventory.json')).write_text(json.dumps(out,indent=2)+'\n');print('INVENTORY_DONE',MODE,len(body),out['foodFlags'])
