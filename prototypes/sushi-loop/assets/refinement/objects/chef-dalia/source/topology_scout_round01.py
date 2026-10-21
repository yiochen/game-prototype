import bpy,json,sys
from pathlib import Path
P=Path(__file__).parent;BASE=P.parent;sys.path.insert(0,str(P));import native_actions_round01 as native
from audit_common_round01 import geometry
rig=json.loads((P/'rig-round01.json').read_text());recipe=json.loads((P/'recipe-round01.json').read_text());sc=bpy.data.scenes[recipe['scene']];bpy.context.window.scene=sc
coll=bpy.data.collections[recipe['collection']];root=bpy.data.objects[recipe['root']];arm=bpy.data.objects[recipe['armature']];asset={'collection':coll,'root':root,'armature':arm}
rows=[];topo={};bad=[]
for c in rig['clips']:
 for d in ['N','E','S','W']:
  for f in range(1,13):
   native.apply_clip(asset,rig,c,f,d,sc);dg=bpy.context.evaluated_depsgraph_get();row={}
   for o in coll.all_objects:
    if o.type!='MESH':continue
    g=geometry(o,dg);row[o.name]=g
    key=(g['vertices'],g['edges'],g['polygons']);prior=topo.setdefault(o.name,key)
    if key!=prior or g['zeroAreaPolygons'] or g['nonfiniteVertices'] or g['nonfiniteNormals']:bad.append({'clip':c,'direction':d,'index':f-1,'object':o.name,'geometry':g})
   rows.append({'clip':c,'direction':d,'index':f-1,'geometry':row})
result={'ok':not bad,'frameCount':len(rows),'topologyInvariantPerObject':topo,'failures':bad,'frames':rows}
(BASE/'candidates/round-01/topology-scout.json').write_text(json.dumps(result,separators=(',',':')))
print('TOPOLOGY_SCOUT',result['ok'],len(rows),len(bad),bad[:3])
if bad:raise RuntimeError('Fix topology before full render')
