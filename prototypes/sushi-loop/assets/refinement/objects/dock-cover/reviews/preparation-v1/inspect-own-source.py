import bpy,json,hashlib,pathlib,math
from mathutils import Vector
BASE=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
OUT=BASE/'prototypes/sushi-loop/assets/refinement/objects/dock-cover/reviews/preparation-v1'
def plain(x):
 try:return list(x)
 except:return str(x)
root=bpy.data.objects.get('dock-cover__ground_root')
if not root:
 root=next((o for o in bpy.data.objects if o.get('production_id')=='dock-cover' or o.get('asset_id')=='dock-cover'),None)
col=next(c for c in bpy.data.collections if root in list(c.all_objects))
objs=list(col.all_objects)
def bounds(o):
 pts=[o.matrix_world@v.co for v in o.data.vertices] if o.type=='MESH' else []
 return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]] if pts else None
r={'source':str(bpy.data.filepath),'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'blender':bpy.app.version_string,'activeScene':bpy.context.scene.name,'activeCamera':bpy.context.scene.camera.name if bpy.context.scene.camera else None,'scenes':[{'name':s.name,'properties':dict(s.items()),'camera':s.camera.name if s.camera else None,'children':[c.name for c in s.collection.children]} for s in bpy.data.scenes],'root':{'name':root.name,'location':list(root.location),'rotation':list(root.rotation_euler),'scale':list(root.scale),'matrixWorld':[list(a) for a in root.matrix_world],'properties':dict(root.items())},'collection':{'name':col.name,'hideRender':col.hide_render,'hideViewport':col.hide_viewport},'objects':[],'materials':[],'resources':[]}
for o in objs:
 r['objects'].append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'boundsWorld':bounds(o),'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'visibleCamera':o.visible_camera,'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'constraints':[{'name':c.name,'type':c.type} for c in o.constraints],'mesh':{'vertices':len(o.data.vertices),'edges':len(o.data.edges),'polygons':len(o.data.polygons),'uvLayers':[u.name for u in o.data.uv_layers],'shapeKeys':o.data.shape_keys.name if o.data.shape_keys else None,'materials':[m.name if m else None for m in o.data.materials]} if o.type=='MESH' else None,'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None})
mats={m for o in objs if o.type=='MESH' for m in o.data.materials if m}
for m in mats:
 r['materials'].append({'name':m.name,'diffuseColor':list(m.diffuse_color),'surfaceRenderMethod':getattr(m,'surface_render_method',None),'useNodes':m.use_nodes,'nodes':[{'name':n.name,'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'inputs':{s.name:plain(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value') and not s.is_linked}} for n in m.node_tree.nodes] if m.use_nodes else [],'links':[{'from':l.from_node.name+':'+l.from_socket.name,'to':l.to_node.name+':'+l.to_socket.name} for l in m.node_tree.links] if m.use_nodes else []})
for im in bpy.data.images:
 if any(n.type=='TEX_IMAGE' and n.image==im for m in mats if m.use_nodes for n in m.node_tree.nodes):r['resources'].append({'type':'image','name':im.name,'filepath':im.filepath,'packed':bool(im.packed_file),'source':im.source,'size':list(im.size)})
r['libraries']=[{'name':l.name,'filepath':l.filepath,'exists':pathlib.Path(bpy.path.abspath(l.filepath)).exists()} for l in bpy.data.libraries]
(OUT/'own-source-inventory.json').write_text(json.dumps(r,indent=2,default=str)+'\n')
print(json.dumps({'root':r['root'],'collection':r['collection'],'objects':len(objs),'meshes':sum(o.type=='MESH' for o in objs),'materials':len(mats),'resources':r['resources'],'scenes':[{'name':s['name'],'camera':s['camera']} for s in r['scenes']]}))
