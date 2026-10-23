import bpy,json,pathlib
B=pathlib.Path(__file__).parents[1];s=bpy.context.scene;c=bpy.data.collections['decor-midground-coral refined'];rows=[]
for o in c.all_objects:
 if o.type!='MESH':continue
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();edges={tuple(sorted(x.vertices)):0 for x in me.edges}
 for p in me.polygons:
  for key in p.edge_keys:edges[tuple(sorted(key))]+=1
 rows.append({'owner':o.name,'vertices':len(me.vertices),'faces':len(me.polygons),'nonManifoldEdges':sum(v!=2 for v in edges.values()),'uvLayers':list(me.uv_layers.keys()),'customNormals':me.has_custom_normals,'flatFaces':sum(not p.use_smooth for p in me.polygons),'modifiers':[m.type for m in o.modifiers]});e.to_mesh_clear()
result={'actualCompositor':{'deprecatedSceneUseNodes':s.use_nodes,'renderUseCompositing':s.render.use_compositing,'compositingNodeGroup':s.compositing_node_group.name if s.compositing_node_group else None,'nodes':[]if not s.compositing_node_group else [{'name':n.name,'type':n.type}for n in s.compositing_node_group.nodes]},'evaluatedTopology':rows,'activeViewLayer':bpy.context.view_layer.name,'sceneObjects':[{'name':o.name,'type':o.type,'hideRender':o.hide_render}for o in s.objects]}
animationIDs=[]
for prop in bpy.data.bl_rna.properties:
 if prop.type!='COLLECTION':continue
 for owner in getattr(bpy.data,prop.identifier):
  ad=getattr(owner,'animation_data',None)
  if ad:animationIDs.append({'collection':prop.identifier,'owner':owner.name,'action':ad.action.name if ad.action else None,'drivers':len(ad.drivers),'nlaTracks':len(ad.nla_tracks)})
result['allIDAnimationOwners']=animationIDs
result['allActions']=[{'name':a.name,'users':a.users}for a in bpy.data.actions]
result['allImageResources']=[{'name':i.name,'source':i.source,'filepath':i.filepath}for i in bpy.data.images]
(B/'native-details.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['actualCompositor']));print('Nonmanifold total',sum(r['nonManifoldEdges']for r in rows))
