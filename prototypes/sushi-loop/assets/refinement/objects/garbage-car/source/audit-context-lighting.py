import bpy,json,pathlib,math,hashlib
from mathutils import Matrix
P=pathlib.Path(__file__).resolve().parent.parent;OUT=P/'candidates/round-01';sc=bpy.context.scene;placements=json.loads((OUT/'native-context-audit.json').read_text())['placements'];rows=[];groups=[];errors=[]
for place in placements:
 root=bpy.data.objects[place['root']];coll=root.users_collection[0];lights=[o for o in sc.objects if o.type=='LIGHT' and o.light_linking.receiver_collection==coll];group=[]
 for o in lights:
  local=root.matrix_world.inverted()@o.matrix_world
  row={'instanceRoot':root.name,'receiverCollection':coll.name,'light':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'shape':o.data.shape,'shadow':o.data.use_shadow,'matrixRelativeToRoot':[list(v) for v in local],'actualWorldMatrix':[list(v) for v in o.matrix_world],'receiverCollectionObjects':[x.name for x in coll.all_objects]};rows.append(row);group.append(row)
 group.sort(key=lambda x:(round(x['matrixRelativeToRoot'][0][3],3),round(x['matrixRelativeToRoot'][1][3],3),round(x['matrixRelativeToRoot'][2][3],3)));groups.append(group)
 if len(lights)!=5:errors.append('Each assembly must receive exactly five local lights')
for g in groups[1:]:
 for first,row in zip(groups[0],g):
  for k in ('type','energy','color','size','shape','shadow'):
   if first[k]!=row[k]:errors.append('Changed local rig setting '+k)
  delta=max(abs(first['matrixRelativeToRoot'][i][j]-row['matrixRelativeToRoot'][i][j]) for i in range(4) for j in range(4))
  if delta>1e-6:errors.append('Changed relative light transform '+str(delta))
for o in sc.objects:
 if o.type=='LIGHT' and o.light_linking.receiver_collection is None:errors.append('Unlinked additive light '+o.name)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
a={'status':'pass' if not errors else 'fail','errors':errors,'contextProjectSHA256':sha(P/'source/context-round01.blend'),'isolatedCandidateProjectSHA256':sha(P/'source/round-01.blend'),'isolatedCandidateBytesChangedByContext':False,'contextsUsingReceiverLinkedRig':['candidates/round-01/previews/native-repeated.png'],'retainedDistanceFalloffDiagnostic':'candidates/round-01/previews/native-repeated-draft01.png','lightingPolicy':'Native repeated context uses three translated copies of the exact same asset-local five-light capture rig, each receiver-linked only to its own independent assembly. Original isolated candidate source and capture rig remain unchanged. No per-facing/color/energy fitting and no cross-additive duplicate contribution. Independent exported-sprite consumer context uses exact captures separately.','lights':rows}
(OUT/'native-context-lighting-audit.json').write_text(json.dumps(a,indent=2));print(a['status'],a['errors'])
if errors:raise RuntimeError('Context lighting mismatch')
