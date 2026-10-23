import bpy,json,pathlib,collections,math
R=pathlib.Path(__file__).resolve().parent
report={'blend':bpy.data.filepath,'scene':bpy.context.scene.name,'meshObjects':[]}
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 me=o.data;row={'name':o.name,'vertices':len(me.vertices),'faces':len(me.polygons),'hiddenRender':o.hide_render,'materials':[m.name for m in me.materials if m],'attributes':[(a.name,a.domain,a.data_type) for a in me.attributes],'imageNodes':[n.image.name if n.image else None for m in me.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE']}
 if 'Unbroken' in o.name or 'Unbroken' in me.name:
  uses=collections.defaultdict(list)
  for f in me.polygons:
   for i in f.vertices:uses[i].append(f.index)
  planes={}
  for name,axis in [('incoming',1),('outgoing',0)]:
   shared=[]
   for v in me.vertices:
    if abs(v.co[axis]-.5)>1e-6:continue
    fids=uses[v.index];centers=[me.polygons[i].center[axis] for i in fids]
    if any(x<.5-1e-6 for x in centers) and any(x>.5+1e-6 for x in centers):shared.append({'vertex':v.index,'position':list(v.co),'faces':fids})
   planes[name]=shared
  row['nativeSharedJoinVertices']=planes;row['duplicatePositionCount']=len(me.vertices)-len({tuple(round(x,6) for x in v.co) for v in me.vertices})
 report['meshObjects'].append(row)
(R/'round01-assembly-independent.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([x for x in report['meshObjects'] if 'nativeSharedJoinVertices' in x]))
