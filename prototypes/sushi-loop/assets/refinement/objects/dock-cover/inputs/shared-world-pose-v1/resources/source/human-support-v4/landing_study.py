import runpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from collision import pair,tree
G=runpy.run_path(str(P/'physical_scene.py'));pose=G['pose'];geometry=G['geometry'];projected=G['projected'];solve=G['solve'];support=G['walking_support']();hc=G['hc'];ec=G['ec'];records=[]
for y in [-1.66,-1.64,-1.62,-1.6,-1.58,-1.56,-1.54,-1.5,-1.46,-1.42]:
 pose(0,y,0,clip='walk',frame=12);s=solve(projected(geometry(hc,True)),support);z=s['solvedRootZ'];pose(0,y,z,clip='walk',frame=12);blocks=[o for o in geometry(ec)if'continuous_loadbearing'not in o['name']];checks=[]
 for ob in geometry(hc):
  t=tree(ob)
  for b in blocks:
   r=pair(ob,b,t,tree(b))
   if r['actualTriangleIntersectionPairs']or r['containedActorVerticesBeyondTolerance']or r['containedObstacleVerticesBeyondTolerance']:checks.append(r)
 records.append({'xy':[0,y],'clip':'walk','sourceFrame':12,'support':s,'blockerIntersections':checks});print('LANDING_STUDY',y,z,[(p['contactArea'],p['fractionOfFlatSole'])for p in s['perShoe']],'BAD',[(r['actorMesh'],r['obstacleMesh'],r['actualTriangleIntersectionPairs'],r['maximumSampledContainmentDepth'])for r in checks],flush=True)
(G['O']/'study/walk12-landing-scan.json').write_text(json.dumps({'sourceHashes':G['sourceHashes'],'records':records,'scope':'Unchanged walk12sourcepose study; not approval.'},indent=2))
