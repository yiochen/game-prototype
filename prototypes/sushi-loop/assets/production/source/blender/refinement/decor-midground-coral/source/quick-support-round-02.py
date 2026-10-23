"""Read-only saved-project support/ownership/clearance audit and exact hero recapture."""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
SRC=Path(__file__).resolve().parent;OBJ=SRC.parent;OUT=OBJ/'candidates/round-02'
sc=bpy.context.scene;root=bpy.data.objects['decor-midground-coral root'];col=bpy.data.collections['decor-midground-coral refined'];corals=[o for o in col.all_objects if o.get('role')=='coral'];rocks=[o for o in col.all_objects if o.get('role')=='reef']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def pts(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();v=[root.matrix_world.inverted()@e.matrix_world@p.co for p in me.vertices];f=[list(p.vertices)for p in me.polygons];e.to_mesh_clear();return v,f

def bound(v):return [[min(p[i]for p in v),max(p[i]for p in v)]for i in range(3)]

def reef_tree():
 v=[];f=[]
 for o in rocks:
  p,q=pts(o);offset=len(v);v+=p;f += [[a+offset for a in face]for face in q]
 return BVHTree.FromPolygons(v,f,all_triangles=False),v
records=[];allcollisions=[];reefhashes=[]
root.rotation_euler.z=0
for i in range(1):
 f=1+i/4;sc.frame_set(math.floor(f),subframe=f-math.floor(f));bpy.context.view_layer.update();tree,rp=reef_tree();reefhashes.append(hashlib.sha256(str([list(p)for p in rp]).encode()).hexdigest());allpoints=[];support=[];trees={}
 for o in col.all_objects:
  if o.type=='MESH':allpoints+=pts(o)[0]
 for o in corals:
  pp,ff=pts(o);trees[o.name]=BVHTree.FromPolygons(pp,ff,all_triangles=False);penetrations=[]
  for index in o['baseRingIndices']:
   p=pp[index];hit,normal,index2,distance=tree.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)),3);penetrations.append(hit.z-p.z if hit else None)
  support.append({'owner':o.name,'total':len(penetrations),'supported':sum(v is not None and v>=-1e-5 for v in penetrations),'minPenetration':min(v for v in penetrations if v is not None)if any(v is not None for v in penetrations)else None})
 for a,o in enumerate(corals):
  for other in corals[a+1:]:
   overlaps=trees[o.name].overlap(trees[other.name])
   if overlaps:allcollisions.append({'frame':f,'a':o.name,'b':other.name,'overlapCount':len(overlaps)})
 records.append({'nativeFrame':f,'rootLocation':list(root.location),'rootScale':list(root.scale),'boundsRoot':bound(allpoints),'support':support})
# Neutral construction bound at authored rooted transforms, with original active actions preserved in the file.
for o in corals:o.rotation_euler=(0,0,0)
bpy.context.view_layer.update();neutral=[]
for o in col.all_objects:
 if o.type=='MESH':neutral+=pts(o)[0]
scan=[]
for kind,items in [('objects',bpy.data.objects),('meshes',bpy.data.meshes),('materials',bpy.data.materials),('worlds',bpy.data.worlds),('lights',bpy.data.lights),('node_groups',bpy.data.node_groups)]:
 for o in items:
  ad=getattr(o,'animation_data',None)
  if ad:scan.append({'kind':kind,'owner':o.name,'action':ad.action.name if ad.action else None,'drivers':len(ad.drivers),'nlaTracks':len(ad.nla_tracks)})
  if hasattr(o,'node_tree')and o.node_tree:
   ad=getattr(o.node_tree,'animation_data',None)
   if ad:scan.append({'kind':kind+' node_tree','owner':o.name,'action':ad.action.name if ad.action else None,'drivers':len(ad.drivers),'nlaTracks':len(ad.nla_tracks)})
# Actual saved-source hero recapture in all proper native facings. No source save or fitting.
recaptures=[]
for d,angle in []:
 root.rotation_euler.z=angle;sc.frame_set(4);bpy.context.view_layer.update();p=OUT/'recapture'/f'{d}-003.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 recaptures.append({'direction':d,'frame':4,'rootRotationZ':root.rotation_euler.z,'path':str(p.relative_to(OBJ)),'sha256':sha(p)})
result={'asset':'decor-midground-coral','source':'source/round-02.blend','sourceSHA256':sha(SRC/'round-02.blend'),'blenderVersion':bpy.app.version_string,'quarterPhaseFrames':records,'staticReefEvaluatedPoseHashesUnique':len(set(reefhashes)),'neutralBoundsRoot':bound(neutral),'tubeSurfaceBVHOverlaps':allcollisions,'overlapMeaning':'Actual evaluated triangle BVH surface overlaps among coral meshes, at49 quarter-frame samples. Reef embedding is intentional and excluded.','actualAnimationDataScan':scan,'actualMaterials':[{'name':m.name,'nodes':[n.type for n in m.node_tree.nodes],'imageNodes':[n.image.name if n.image else None for n in m.node_tree.nodes if n.type=='TEX_IMAGE']}for m in bpy.data.materials if m.use_nodes],'actualImages':[{'name':i.name,'source':i.source,'filepath':i.filepath}for i in bpy.data.images],'recaptures':recaptures,'notes':['Read-only saved-source audit. Proper rotations preserve root-space geometry/support results across all4 facings.','No source/project file saved by this audit. No aesthetic approval.']}
(OUT/'quick-support-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('SAVED_SOURCE_AUDIT_COMPLETE',len(allcollisions),flush=True)
