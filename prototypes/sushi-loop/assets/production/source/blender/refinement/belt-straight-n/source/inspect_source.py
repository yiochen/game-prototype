import bpy,json,pathlib
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parents[1]
b=json.load(open(P/'brief.json')); project=(P/b['source']['project']).resolve()
bpy.ops.wm.open_mainfile(filepath=str(project))
cols=[c for c in bpy.data.collections if 'belt-straight-n' in c.name]
print('MATCHCOLS',[(c.name,len(c.all_objects)) for c in cols])
for c in cols:
 print('COL',c.name)
 for o in c.all_objects:
  print('OBJ',o.name,o.type,'parent',o.parent.name if o.parent else None,'loc',list(o.location),'rot',list(o.rotation_euler),'scale',list(o.scale),'data',o.data.name if o.data else None)
scene=bpy.data.scenes.new('InspectionIsolated'); bpy.context.window.scene=scene
c=cols[0]; scene.collection.children.link(c); c.hide_viewport=False; c.hide_render=False
for o in c.all_objects:
 o.hide_viewport=False; o.hide_render=False; o.hide_set(False); o.update_tag()
scene.frame_set(1); bpy.context.view_layer.update(); dep=bpy.context.evaluated_depsgraph_get(); dep.update()
out={'project':str(project),'collection':c.name,'objects':[]}
for o in c.all_objects:
 r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix':[list(x) for x in o.matrix_world],'properties':dict(o.items())}
 if o.type=='MESH':
  ev=o.evaluated_get(dep); vs=[ev.matrix_world@v.co for v in ev.data.vertices]; r['bounds']=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
  r['vertexCount']=len(ev.data.vertices);r['polygons']=len(ev.data.polygons);r['vertices']=[list(v.co) for v in o.data.vertices];r['faces']=[list(p.vertices) for p in o.data.polygons];r['uv']=[list(x.uv) for x in o.data.uv_layers.active.data] if o.data.uv_layers.active else None
  r['materials']=[]
  for m in o.data.materials:
   mr={'name':m.name,'nodes':[],'links':[]}
   if m.use_nodes:
    for n in m.node_tree.nodes:
     nr={'name':n.name,'type':n.bl_idname,'inputs':{},'outputs':{}}
     for s in n.inputs:
      if hasattr(s,'default_value'):
       try:nr['inputs'][s.name]=list(s.default_value)
       except:nr['inputs'][s.name]=s.default_value
     for s in n.outputs:
      if hasattr(s,'default_value'):
       try:nr['outputs'][s.name]=list(s.default_value)
       except:nr['outputs'][s.name]=s.default_value
     mr['nodes'].append(nr)
    mr['links']=[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links]
   r['materials'].append(mr)
 out['objects'].append(r)
print('BOUNDS',[(o['name'],o.get('bounds')) for o in out['objects']])
(P/'source'/'source-inspection.json').write_text(json.dumps(out,indent=2,default=str))
