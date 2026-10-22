import runpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from collision import pair,tree
G=runpy.run_path(str(P/'physical_scene.py'));pose=G['pose'];geometry=G['geometry'];projected=G['projected'];solve=G['solve'];support=G['walking_support']();hc=G['hc'];ec=G['ec'];companions=G['companions'];records=[]
cases=[('approach',0,-2.25),('first-tread',0,-1.922),('second-tread',0,-1.762),('terminal-tread',0,-1.56),('transfer',0,-1.5),('front-deck',0,-1.32),('front-right-branch',.25,-1.25),('right-apron',.66,-1.1),('hut-front-approach',.66,-.85),('exterior-stop',.66,-.67)]
for cid,x,y in cases:
 pose(x,y,0);s=solve(projected(geometry(hc,True)),support);z=s['solvedRootZ'];pose(x,y,z);human=geometry(hc);blocks=[o for o in geometry(ec)if'continuous_loadbearing'not in o['name']]
 for c in companions.values():blocks+=geometry(c['collection'])
 trees={o['name']:tree(o)for o in blocks};checks=[]
 for ob in human:
  t=tree(ob)
  for b in blocks:
   r=pair(ob,b,t,trees[b['name']]);
   if r['bvhCandidatePairs']or r['containedActorVerticesBeyondTolerance']or r['containedObstacleVerticesBeyondTolerance']:checks.append(r)
 bad=[r for r in checks if r['actualTriangleIntersectionPairs']or r['containedActorVerticesBeyondTolerance']or r['containedObstacleVerticesBeyondTolerance']]
 records.append({'id':cid,'worldXY':[x,y],'rootZ':z,'support':s,'collisions':checks,'badMeshPairs':len(bad),'actualSourceRootScale':list(G['hr'].scale)});print('ROUTE_STUDY',cid,[x,y,z],'contact',[(p['contactArea'],p['fractionOfFlatSole'])for p in s['perShoe']],'BAD',[(r['actorMesh'],r['obstacleMesh'],r['actualTriangleIntersectionPairs'],r['maximumSampledContainmentDepth'])for r in bad],flush=True)
(G['O']/'study/route-study.json').write_text(json.dumps({'sourceHashes':G['sourceHashes'],'pose':'unchanged approved stand/frame12, actual published stand index11, native companions dock-ready/uncover frame12','scope':'Feasibility measured only; no art/source changes or approval. Collision tests use actual triangle intersections and containment, not AABBs alone.','records':records},indent=2))
