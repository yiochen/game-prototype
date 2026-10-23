import runpy,json,sys,math
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from collision import pair,tree
G=runpy.run_path(str(P/'cohort_scene.py'));pose=G['pose'];geometry=G['geometry'];projected=G['projected'];solve=G['solve'];hc=G['hc'];ec=G['ec'];fc=G['fc'];snaps=G['snapshots'];records=[]
cases=[('approach',0,-2.25,'stand',12),('first-tread',0,-1.945,'stand',12),('second-tread',0,-1.785,'stand',12),('terminal-tread',0,-1.56,'walk',7),('transfer',0,-1.50,'walk',7),('front-deck',0,-1.32,'stand',12),('front-right-branch',.25,-1.25,'stand',12),('right-apron',.66,-1.1,'stand',12),('exterior-stop',.66,-.85,'stand',12)]
solved={}
for cid,x,y,clip,frame in cases:
 pose(x,y,0,clip=clip,frame=frame);s=solve(projected(geometry(hc,True)),G['walking_support']());solved[cid]=s['solvedRootZ']
for d in ['N','E','S','W']:
 for cid,x,y,clip,frame in cases:
  z=solved[cid];pose(x,y,0,d,clip,frame);s=solve(projected(geometry(hc,True)),G['walking_support']());pose(x,y,z,d,clip,frame);placedShoeResidual=solve(projected(geometry(hc,True)),G['walking_support']())['solvedRootZ'];human=geometry(hc);blocks=[o for o in geometry(ec)if'continuous_loadbearing'not in o['name']]
  for q in snaps.values():blocks+=geometry(q['collection'])
  trees={o['name']:tree(o)for o in blocks};checks=[];bad=[]
  for ob in human:
   t=tree(ob)
   for b in blocks:
    r=pair(ob,b,t,trees[b['name']]);checks.append(r)
    if r['actualTriangleIntersectionPairs']or r['containedActorVerticesBeyondTolerance']or r['containedObstacleVerticesBeyondTolerance']:bad.append(r)
  # Full body against actual loadbearing floor/stairs. Intended shoe contact surfaces can intersect.
  supportBodies=geometry(fc)+[o for o in geometry(ec)if'continuous_loadbearing'in o['name']];supportChecks=[]
  for ob in human:
   if any(k in ob['name'].lower()for k in['shoe','sole','foot']):continue
   t=tree(ob)
   for b in supportBodies:
    r=pair(ob,b,t,tree(b));supportChecks.append(r)
    if r['actualTriangleIntersectionPairs']or r['containedActorVerticesBeyondTolerance']or r['containedObstacleVerticesBeyondTolerance']:bad.append(r)
  rec={'id':cid,'direction':d,'sourceFacingXY':[x,y],'worldRoot':list(G['hr'].location),'frozenRootZ':z,'actorClip':clip,'sourceNativeFrame':frame,'publishedClipIndex':frame-1,'actualAuthoredRootScale':list(G['hr'].scale),'fullSupport':s,'actualPlacedFullShoeRequiredLiftResidual':placedShoeResidual,'directionSolveDeltaFromFrozenZ':s['solvedRootZ']-z,'bodyObstacleChecks':checks,'nonShoeBodyLoadbearingChecks':supportChecks,'badMeshPairs':bad};records.append(rec)
  print('VERIFY',d,cid,clip,frame,'Z',z,'delta',s['solvedRootZ']-z,'contact',[(p['contactArea'],p['fractionOfFlatSole'])for p in s['perShoe']],'BAD',[(r['actorMesh'],r['obstacleMesh'],r['actualTriangleIntersectionPairs'],r['maximumSampledContainmentDepth'])for r in bad],flush=True)
out={'status':'measured feasibility; not approval','scope':'Representative static native source poses on one coherent exterior route. No continuous stair locomotion claim. Exact source materials, geometry, camera, scale unchanged. Companion frame12 snapshot exact parity verified in-memory; both original and approved hut separately checked.','sourceHashes':G['sourceHashes'],'snapshotParity':G['snapshotAudit'],'cases':[{'id':cid,'sourceFacingXY':[x,y],'solvedRootZ':solved[cid],'actorClip':clip,'nativeFrame':frame,'publishedClipIndex':frame-1}for cid,x,y,clip,frame in cases],'records':records,'maxUnintendedPairs':max(len(r['badMeshPairs'])for r in records)}
import gzip
with gzip.GzipFile(filename=str(G['O']/'study/shared-plan-feasibility-v2.json.gz'),mode='wb',mtime=0)as f:f.write(json.dumps(out,separators=(',',':')).encode())
