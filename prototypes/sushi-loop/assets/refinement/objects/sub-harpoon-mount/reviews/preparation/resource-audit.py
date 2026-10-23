import bpy,json,pathlib,hashlib
P=pathlib.Path(__file__).resolve().parent;c=bpy.data.collections['S33_PROP_harpoon_mount.001'];bpy.context.view_layer.update()
def val(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 try:return [val(v) for v in x]
 except:return str(x)
materials=[];images=[]
for mat in {m for o in c.all_objects if o.type=='MESH' for m in o.data.materials if m}:
 nodes=[]
 for n in mat.node_tree.nodes:
  nodes.append({'name':n.name,'type':n.bl_idname,'label':n.label,'inputs':[{'name':i.name,'identifier':i.identifier,'value':val(getattr(i,'default_value',None))} for i in n.inputs],'image':n.image.name if hasattr(n,'image') and n.image else None})
  if hasattr(n,'image') and n.image:images.append({'name':n.image.name,'filepath':n.image.filepath,'packed':bool(n.image.packed_file)})
 materials.append({'name':mat.name,'nodes':nodes,'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.identifier,'toNode':l.to_node.name,'toSocket':l.to_socket.identifier} for l in mat.node_tree.links]})
mesh=[]
for o in c.all_objects:
 if o.type!='MESH':continue
 d=o.data;rec={'object':o.name,'vertices':[list(v.co) for v in d.vertices],'normals':[list(v.normal) for v in d.vertices],'polygons':[list(p.vertices) for p in d.polygons],'uvLayers':[{'name':u.name,'data':[list(v.uv) for v in u.data]} for u in d.uv_layers],'matrixLocal':[list(r) for r in o.matrix_local],'materialSlots':[m.name if m else None for m in d.materials]};rec['resourceDataSHA256']=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(',',':')).encode()).hexdigest();mesh.append(rec)
(P/'own-resource-closure.json').write_text(json.dumps({'nativeSourceSHA256':hashlib.sha256((P/'resources/own-original-library.blend').read_bytes()).hexdigest(),'materials':materials,'ownReachableImages':images,'ownMeshes':mesh,'closure':'All own reachable mesh/material/action data lives in saved source blend; own materials have no external image texture. Unrelated full-library packed images are not own material dependencies.'},indent=2)+'\n')
