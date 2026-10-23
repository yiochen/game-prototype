import bpy,pathlib,json,math
from mathutils import Vector
B=pathlib.Path(__file__).parent.parent;col=bpy.data.collections['S33 production concept pink-coral.001'];root=bpy.data.objects['S33 production concept pink-coral root.001']
def anim(d):
 ad=getattr(d,'animation_data',None)
 return {'activeAction':ad.action.name if ad and ad.action else None,'nla':[{'name':t.name,'mute':t.mute,'strips':[{'name':s.name,'action':s.action.name if s.action else None,'frameStart':s.frame_start,'frameEnd':s.frame_end} for s in t.strips]} for t in ad.nla_tracks] if ad else [],'drivers':[{'path':x.data_path,'arrayIndex':x.array_index,'expression':x.driver.expression} for x in ad.drivers] if ad else []}
report={'root':{'name':root.name,'location':list(root.location),'scale':list(root.scale),'rotation':list(root.rotation_euler)},'objects':[],'materials':[],'images':[]}
for o in col.all_objects:
 row={'name':o.name,'parent':o.parent.name if o.parent else None,'objectOrigin':list(o.location),'scale':list(o.scale),'rotationMode':o.rotation_mode,'animation':anim(o),'constraints':[c.type for c in o.constraints],'modifiers':[m.type for m in o.modifiers]}
 if o.type=='MESH':
  me=o.data;edges={tuple(sorted(e.vertices)):0 for e in me.edges}
  for p in me.polygons:
   vv=list(p.vertices)
   for a,b in zip(vv,vv[1:]+vv[:1]):edges[tuple(sorted((a,b)))]+=1
  row.update({'mesh':me.name,'users':me.users,'vertices':len(me.vertices),'edges':len(me.edges),'polygons':len(me.polygons),'boundaryEdges':sum(n==1 for n in edges.values()),'nonmanifoldEdges':sum(n!=2 for n in edges.values()),'flatFaces':sum(not p.use_smooth for p in me.polygons),'uvLayers':list(me.uv_layers.keys()),'hasCustomNormals':me.has_custom_normals,'shapeKeys':None if not me.shape_keys else list(me.shape_keys.key_blocks.keys()),'meshAnimation':anim(me),'materials':[{'name':m.name,'users':m.users} for m in me.materials if m]})
  if o.get('studyRole')=='body':row['finiteGroundContactPolygons']=[{'normal':list(p.normal),'vertices':[list(me.vertices[i].co) for i in p.vertices]} for p in me.polygons if all(abs(me.vertices[i].co.z)<1e-6 for i in p.vertices)]
  else:row['finiteTubeBottomRing']=[list(v.co) for v in me.vertices[:12]];row['finiteTubeTopRimOuter']=[list(v.co) for v in me.vertices[36:48]];row['finiteTubeTopRimInner']=[list(v.co) for v in me.vertices[48:60]]
 report['objects'].append(row)
for m in set(m for o in col.all_objects if o.type=='MESH' for m in o.data.materials if m):
 report['materials'].append({'name':m.name,'users':m.users,'materialAnimation':anim(m),'nodeAnimation':anim(m.node_tree),'imageNodes':[],'groupNodes':[{'name':n.node_tree.name,'library':n.node_tree.library.filepath if n.node_tree.library else None} for n in m.node_tree.nodes if n.type=='GROUP']})
(B/'functional-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print('Functional source metadata and actual finite polygons saved')
