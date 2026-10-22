import bpy,runpy,json,hashlib
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;B=O/'resources/repo/prototypes/sushi-loop/assets/refinement/objects/dock-entry';G=runpy.run_path(str(B/'source/human-reference-round07/cohort_scene_entry.py'));G['pose'](0,-2.25,0,'S','stand',12);rows=[]
def state(ob):
 out=[]
 for m in ob.data.materials:
  if not m:continue
  d={'roughness':m.roughness,'metallic':m.metallic,'diffuse':list(m.diffuse_color),'nodes':[]}
  if m.use_nodes:
   for n in m.node_tree.nodes:
    ss=[]
    for s in n.inputs:
     if hasattr(s,'default_value'):
      x=s.default_value
      if not isinstance(x,(float,int,str,bool)):
       try:x=list(x)
       except:x=str(type(x))
      ss.append([s.identifier,x])
    d['nodes'].append([n.name,n.type,ss])
  out.append(d)
 return out
for group in G['snapshotAudit']:
 col=bpy.data.collections[group['sourceCollection']];col.hide_viewport=False;bpy.context.view_layer.update()
 for r in group['objects']:
  src=bpy.data.objects[r['sourceObject']];cp=bpy.data.objects[r['snapshotObject']];ev=src.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=[ev.matrix_world@v.co for v in me.vertices];b=[cp.matrix_world@v.co for v in cp.data.vertices];err=max((v-w).length for v,w in zip(a,b));ev.to_mesh_clear();rows.append({'sourceObject':src.name,'snapshotObject':cp.name,'vertexCounts':[len(a),len(b)],'maxWorldVertexError':err,'materialChannelsExactlyEqual':state(src)==state(cp),'nativeFrame':group['nativeFrame']})
r={'candidatePacketSHA256':'5e4a1c313176fc0e0474474a0fbc800b3ddd321d9c4076e71da39620a617ba70','method':'Independent actual source evaluated vertices/matrices and material socket values versus frozen memory snapshots at source frame12, not a declared hash comparison. Original collections enabled for correct dependency-graph evaluation.','rows':rows};(O/'own-cohort-source-parity.json').write_text(json.dumps(r,indent=2)+'\n');print('OWN_COHORT',len(rows),max(x['maxWorldVertexError']for x in rows),all(x['materialChannelsExactlyEqual']for x in rows))
