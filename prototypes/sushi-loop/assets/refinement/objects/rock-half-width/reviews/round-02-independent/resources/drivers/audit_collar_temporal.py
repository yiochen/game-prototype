import bpy,json,math
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[2];root=bpy.data.objects['rock-half-width__root.001'];body=bpy.data.objects['rock-half-width__relief_core'];m=body.data
section=json.loads((B/'resources/root-native-contract.json').read_text())['nativeContract']['functionalInterfaces']['finiteSectionYZ'];edges=list(zip(section,section[1:]+section[:1]))
def distance(p,a,b):
 p,a,b=Vector(p),Vector(a),Vector(b);v=b-a;t=max(0,min(1,(p-a).dot(v)/v.length_squared));return (p-(a+t*v)).length
collars=[v for v in m.vertices if abs(v.co.x)>=.42-1e-6];residual=max(min(distance([v.co.y,v.co.z],a,b) for a,b in edges) for v in collars)
planes={}
for x in [-.5,-.46,-.42,.42,.46,.5]:planes[str(x)]=sorted({(round(v.co.y,7),round(v.co.z,7)) for v in m.vertices if abs(v.co.x-x)<1e-6})
attrs=m.attributes['collar_weight'];allOne=all(abs(attrs.data[v.index].value-1)<1e-7 for v in collars)
ids=[];seen=set()
def add(x):
 if x and x.as_pointer() not in seen:seen.add(x.as_pointer());ids.append(x)
for x in bpy.data.objects:add(x);add(x.data)
for x in bpy.data.materials:add(x);add(x.node_tree)
for x in bpy.data.node_groups:add(x)
for x in bpy.data.worlds:add(x);add(x.node_tree)
for x in bpy.data.scenes:add(x)
records=[]
for x in ids:
 if hasattr(x,'animation_data'):
  a=x.animation_data;records.append({'name':x.name,'type':type(x).__name__,'action':a.action.name if a and a.action else None,'drivers':[{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression} for f in a.drivers] if a else [],'NLA':[t.name for t in a.nla_tracks] if a else []})
result={'pathBase':'object root','source':'reviews/round-02-independent/resources/candidate.blend','actualFullCollars':{'vertexCount':len(collars),'allActualWeightsOne':allOne,'maxBoundaryDistanceFromFrozenSixPointSection':residual,'sectionYZSetsByActualX':planes,'allSixActualRingSetsMatch':all(v==planes['-0.5'] for v in planes.values()),'method':'Actual mesh coordinates at all six authored collar ring planes, full vertex-distance check to finite frozen section, actual POINT weights. Linear polygon faces preserve the source extrusion within the full.08 collars; no profile inferred from name.'},'temporalChannels':records,'noActualActionsDriversNLA':all(not r['action'] and not r['drivers'] and not r['NLA'] for r in records),'staticFrames':[bpy.context.scene.frame_start,bpy.context.scene.frame_end],'fps':bpy.context.scene.render.fps,'opacity':'Actual active material is an opaque emission surface; no transparent shader, mask or removed cap. Actual saved graph and matching field measured separately in independent-native-inspection.json.'}
(B/'evidence/collar-temporal-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'fullCollarVertexCount':len(collars),'maxProfileDistance':residual,'sixRingSetsMatch':result['actualFullCollars']['allSixActualRingSetsMatch'],'allWeightsOne':allOne,'actualTemporalIDs':len(records),'noActionsDriversNLA':result['noActualActionsDriversNLA']}))
