import bpy,json
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent;s=bpy.context.scene;c=bpy.data.collections['S33_PROP_decor-background-wreck.001'];objs=list(c.all_objects)
def ad(x):
 a=getattr(x,'animation_data',None)
 return {'hasAnimationData':bool(a),'action':a.action.name if a and a.action else None,'nla':[{'track':t.name,'strips':[{'name':q.name,'action':q.action.name if q.action else None,'range':[q.frame_start,q.frame_end]} for q in t.strips]} for t in a.nla_tracks] if a else [],'drivers':[{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression} for f in a.drivers] if a else []}
mats=list(dict.fromkeys(x.material for o in objs for x in o.material_slots if x.material));seen=set();groups=[]
def group(g,role):
 if not g or g.name in seen:return
 seen.add(g.name);groups.append({'name':g.name,'role':role,'animation':ad(g),'nodeTypes':[n.type for n in g.nodes],'images':[{'name':n.image.name,'filepath':n.image.filepath,'packed':bool(n.image.packed_file)} for n in g.nodes if n.type=='TEX_IMAGE' and n.image]})
 for n in g.nodes:
  if n.type=='GROUP':group(n.node_tree,role+' nested')
for m in mats:group(m.node_tree,'owned material '+m.name)
group(s.world.node_tree,'scene world')
group(getattr(s,'compositing_node_group',None),'scene compositor')
meshes=[]
for o in objs:
 if o.type!='MESH':continue
 me=o.data;counts=Counter(tuple(sorted(e)) for f in me.polygons for e in f.edge_keys)
 meshes.append({'object':o.name,'meshData':me.name,'dataUsers':me.users,'animation':ad(me),'uvLayers':[u.name for u in me.uv_layers],'shapeKeys':ad(me.shape_keys) if me.shape_keys else None,'boundaries':sum(v==1 for v in counts.values()),'nonManifoldEdges':sum(v!=2 for v in counts.values()),'faceCount':len(me.polygons),'vertexCount':len(me.vertices),'materialOwnership':[{'material':sl.material.name,'objectUsers':[ob.name for ob in bpy.data.objects if any(q.material==sl.material for q in ob.material_slots)]} for sl in o.material_slots if sl.material],'activeModifiers':[{'name':m.name,'type':m.type,'nodeGroup':m.node_group.name if m.type=='NODES' and m.node_group else None} for m in o.modifiers]})
report={'asset':'decor-background-wreck','sceneAnimation':ad(s),'worldAnimation':ad(s.world),'cameraObjectAnimation':ad(s.camera),'cameraDataAnimation':ad(s.camera.data),'objects':[{'name':o.name,'animation':ad(o),'constraints':[{'name':a.name,'type':a.type} for a in o.constraints]} for o in objs],'materials':[{'name':m.name,'animation':ad(m),'linked':bool(m.library)} for m in mats],'nodeTrees':groups,'meshes':meshes,'ownedArmatures':[o.name for o in objs if o.type=='ARMATURE'],'externalLibraries':[l.filepath for l in bpy.data.libraries],'ownedImageDependencyCount':sum(len(g['images']) for g in groups if g['role'].startswith('owned')),'limits':'Unrelated packed dish images remain in untouched library backup, but are not reachable from this object. No new source saved.'}
(P/'temporal-resource-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'nodeTrees':len(groups),'ownedMeshCount':len(meshes),'ownedImageDependencyCount':report['ownedImageDependencyCount'],'allTemporalOwnersStatic':all(not x['animation']['hasAnimationData'] for x in report['objects']+report['materials']+groups+meshes)}))
