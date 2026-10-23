"""Supplement adopted discrete stances with exact translated body-triangle swept surfaces on flat exterior apron. No stair locomotion asserted."""
import runpy,sys,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from collision import pair,tree
G=runpy.run_path(str(P/'cohort_scene.py'));pose=G['pose'];geometry=G['geometry'];B=G['B'];O=G['O'];plan=json.loads((O/'shared-world-pose-plan.json').read_text());steps=plan['cases'][5:];records=[]
# The boundary of each original actor triangle translated along the full segment is
# a triangular prism (two triangle caps and three swept edge quads). Every actor
# surface point at every linear segment time lies inside/on one such prism.
def swept(ob,delta):
 vs=ob['vertices'];n=len(vs);vertices=vs+[v+delta for v in vs];faces=[]
 for a,b,c in ob['triangles']:
  faces.extend([(a,b,c),(c+n,b+n,a+n),(a,b,b+n),(a,b+n,a+n),(b,c,c+n),(b,c+n,b+n),(c,a,a+n),(c,a+n,c+n)])
 return{'name':ob['name']+'__translation_sweep','vertices':vertices,'triangles':faces,'bounds':[[min(v[i]for v in vertices)for i in range(3)],[max(v[i]for v in vertices)for i in range(3)]]}
for direction in ['N','E','S','W']:
 for a,b in zip(steps,steps[1:]):
  pose(*a['sourceFacingXY'],a['solvedRootZ'],direction,'stand',12);body=geometry(G['hc']);start=G['hr'].location.copy();pose(*b['sourceFacingXY'],b['solvedRootZ'],direction,'stand',12);delta=G['hr'].location-start
  blocks=[q for q in geometry(G['ec'])if'continuous_loadbearing'not in q['name']]
  for q in G['snapshots'].values():blocks+=geometry(q['collection'])
  bt=[tree(q)for q in blocks];checks=[];candidateCount=0
  for ob in body:
   sw=swept(ob,delta);st=tree(sw)
   for block,t in zip(blocks,bt):
    r=pair(sw,block,st,t)
    candidateCount+=r['bvhCandidatePairs']
    if r['bvhCandidatePairs']or r['containedActorVerticesBeyondTolerance']or r['containedObstacleVerticesBeyondTolerance']:checks.append(r)
  bad=[r for r in checks if r['actualTriangleIntersectionPairs']or r['containedActorVerticesBeyondTolerance']or r['containedObstacleVerticesBeyondTolerance']]
  records.append({'direction':direction,'start':a['id'],'end':b['id'],'actualWorldTranslation':list(delta),'pose':'unchanged stand12/published11','bodyMeshCount':len(body),'obstacleMeshCount':len(blocks),'meshPairsChecked':len(body)*len(blocks),'bvhCandidatePairs':candidateCount,'nearChecks':checks,'badPairs':bad});print('EXTERIOR_SWEEP',direction,a['id'],b['id'],'candidates',candidateCount,'bad',len(bad),flush=True)
j={'sharedPlanSHA256':G['sha'](O/'shared-world-pose-plan.json'),'sourceHashes':G['sourceHashes'],'scope':'Supplemental continuous geometric clearance of fixed stand12 body translated along only the three flat-deck exterior polyline segments. No continuous stair locomotion/action transition or door passage claim. Same adopted endpoints/Z; no new path or art.','method':'Each actual native actor triangle sweeps a triangular prism; exact prism boundary triangle/obstacle triangle intersection tests and strict containment probes. Static endpoint full-body nonintersection/containment already measured in adopted plan. All original b176 companions and separate approved Hut01 remain fixed in their actual native frame12 evaluated cohorts. AABBs only prune provably disjoint candidates.','toleranceWorld':1e-5,'records':records,'maximumBadPairs':max(len(r['badPairs'])for r in records)};(O/'exterior-body-sweep.json').write_text(json.dumps(j,indent=2));print('SWEEP_DONE',j['maximumBadPairs'])
