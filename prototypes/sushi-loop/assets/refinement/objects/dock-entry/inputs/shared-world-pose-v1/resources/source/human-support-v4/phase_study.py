import runpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from collision import pair,tree
G=runpy.run_path(str(P/'physical_scene.py'));pose=G['pose'];geometry=G['geometry'];projected=G['projected'];solve=G['solve'];support=G['walking_support']();hc=G['hc'];ec=G['ec'];records=[]
blocks=[o for o in geometry(ec)if'continuous_loadbearing'not in o['name']];bt=[tree(b)for b in blocks]
for frame in range(1,13):
 for y in [-1.62,-1.56,-1.5,-1.46]:
  pose(0,y,0,clip='walk',frame=frame);s=solve(projected(geometry(hc,True)),support);z=s['solvedRootZ'];pose(0,y,z,clip='walk',frame=frame);checks=[]
  for ob in geometry(hc):
   t=tree(ob)
   for b,tb in zip(blocks,bt):
    r=pair(ob,b,t,tb)
    if r['actualTriangleIntersectionPairs']or r['containedActorVerticesBeyondTolerance']or r['containedObstacleVerticesBeyondTolerance']:checks.append(r)
  records.append({'xy':[0,y],'clip':'walk','sourceFrame':frame,'support':s,'blockerIntersections':checks});print('PHASE_STUDY',frame,y,z,[(p['contactArea'],p['fractionOfFlatSole'])for p in s['perShoe']],'BAD',[(r['actorMesh'],r['obstacleMesh'],r['actualTriangleIntersectionPairs'],r['maximumSampledContainmentDepth'])for r in checks],flush=True)
(G['O']/'study/walk-phases-gate-scan.json').write_text(json.dumps({'sourceHashes':G['sourceHashes'],'records':records,'scope':'Unchanged walk source pose phase study; not approval. Companion animation phases not evaluated by this cap-only scan.'},indent=2))
