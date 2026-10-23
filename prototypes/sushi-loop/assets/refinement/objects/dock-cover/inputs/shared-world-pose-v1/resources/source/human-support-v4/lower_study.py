import runpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from collision import pair,tree
G=runpy.run_path(str(P/'physical_scene.py'));pose=G['pose'];geometry=G['geometry'];projected=G['projected'];solve=G['solve'];hc=G['hc'];ec=G['ec'];support=G['walking_support']();blocks=geometry(ec);bt=[tree(b)for b in blocks];records=[]
for clip,frame in [('stand',12),('walk',4),('walk',7)]:
 for y in [-1.95,-1.942,-1.932,-1.927,-1.922,-1.79,-1.782,-1.772,-1.767,-1.762]:
  pose(0,y,0,clip=clip,frame=frame);s=solve(projected(geometry(hc,True)),support);z=s['solvedRootZ'];pose(0,y,z,clip=clip,frame=frame);checks=[]
  for ob in geometry(hc):
   if any(k in ob['name'].lower()for k in['shoe','sole','foot']):continue
   t=tree(ob)
   for b,tb in zip(blocks,bt):
    r=pair(ob,b,t,tb)
    if r['actualTriangleIntersectionPairs']or r['containedActorVerticesBeyondTolerance']or r['containedObstacleVerticesBeyondTolerance']:checks.append(r)
  records.append({'xy':[0,y],'clip':clip,'sourceFrame':frame,'support':s,'blockerIntersections':checks});print('LOWER',clip,frame,y,z,[(p['contactArea'],p['fractionOfFlatSole'])for p in s['perShoe']],'BAD',[(r['actorMesh'],r['obstacleMesh'],r['actualTriangleIntersectionPairs'],r['maximumSampledContainmentDepth'])for r in checks],flush=True)
(G['O']/'study/lower-body-stair-scan.json').write_text(json.dumps({'sourceHashes':G['sourceHashes'],'records':records,'scope':'Lower tread actual full nonshoe body/tread/post/cap feasibility; not approval.'},indent=2))
