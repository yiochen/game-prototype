"""Own full-triangle contact, intersection and solid-containment audit of retained native extraction."""
import json,gzip,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_ray_tri
R=Path(__file__).resolve().parent
with gzip.open(R/'own-native-geometry.json.gz','rt')as f:g=json.load(f)
TOL=1e-5
# Independent Sutherland-Hodgman clipping and affine height comparison.
def area(p):return abs(sum(a[0]*b[1]-a[1]*b[0]for a,b in zip(p,p[1:]+p[:1])))*.5 if len(p)>2 else 0.
def cross(a,b,p):return(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def clip(poly,edge):
 a,b=edge;out=[]
 for p,q in zip(poly,poly[1:]+poly[:1]):
  dp,dq=cross(a,b,p),cross(a,b,q);ip,iq=dp>=-1e-12,dq>=-1e-12
  if ip:out.append(p)
  if ip!=iq:
   t=dp/(dp-dq);out.append([p[i]+t*(q[i]-p[i])for i in [0,1]])
 return out

def projected(obs,up=False):
 out=[]
 for o in obs:
  for idx,t in enumerate(o['triangles']):
   vs=[o['vertices'][i]for i in t];p,q,s=vs;det=cross(p,q,s)
   if abs(det)<1e-13 or (up and det<0):continue
   ax=((q[2]-p[2])*(s[1]-p[1])-(s[2]-p[2])*(q[1]-p[1]))/det;ay=((q[0]-p[0])*(s[2]-p[2])-(s[0]-p[0])*(q[2]-p[2]))/det;plane=[ax,ay,p[2]-ax*p[0]-ay*p[1]];xy=[v[:2]for v in vs]
   if det<0:xy.reverse()
   out.append({'owner':o['name'],'triangle':idx,'vertices':vs,'xy':xy,'plane':plane,'bbox':[min(v[0]for v in vs),min(v[1]for v in vs),max(v[0]for v in vs),max(v[1]for v in vs)]})
 return out

def shoe_test(shoes,support):
 tt=projected(shoes);ss=projected(support,True);over=[];ground=[];minGap=min(v[2]for o in shoes for v in o['vertices'])
 for t in tt:
  for s in ss:
   a,b=t['bbox'],s['bbox']
   if a[2]<b[0]or b[2]<a[0]or a[3]<b[1]or b[3]<a[1]:continue
   p=t['xy'][:]
   for edge in zip(s['xy'],s['xy'][1:]+s['xy'][:1]):
    p=clip(p,edge)
    if not p:break
   if area(p)<1e-14:continue
   plane=[t['plane'][i]-s['plane'][i]for i in range(3)];ds=[plane[0]*v[0]+plane[1]*v[1]+plane[2]for v in p];minGap=min(minGap,min(ds));over.append({'shoe':t['owner'],'shoeTriangle':t['triangle'],'support':s['owner'],'supportTriangle':s['triangle'],'polygon':p,'area':area(p),'actualGapRange':[min(ds),max(ds)]})
  if max(abs(v[2])for v in t['vertices'])<TOL:ground.append({'shoe':t['owner'],'triangle':t['triangle'],'polygon':t['xy'],'area':area(t['xy']),'support':'ground-Z0'})
 contact=[o for o in over if max(abs(d)for d in o['actualGapRange'])<TOL]+ground;per=[]
 for o in shoes:
  names=[t for t in tt if t['owner']==o['name']];minz=min(v[2]for v in o['vertices']);flat=sum(area(t['xy'])for t in names if max(abs(v[2]-minz)for v in t['vertices'])<TOL);co=[x for x in contact if x['shoe']==o['name']];pts=[v for c in co for v in c['polygon']];ar=sum(c['area']for c in co)
  per.append({'name':o['name'],'contactArea':ar,'actualFlatSoleArea':flat,'fractionOfActualFlatSole':ar/flat if flat else None,'patchBoundsXY':[[min(v[i]for v in pts)for i in [0,1]],[max(v[i]for v in pts)for i in[0,1]]]if pts else None})
 return {'minimumActualFullShoeGap':minGap,'maxPenetration':max(0,-minGap),'perShoe':per,'contactPatches':contact,'allFiniteOverlaps':over,'fullShoeTriangleCount':len(tt),'upwardNativeSupportTriangleCount':len(ss)}

def prepared(o):
 v=[Vector(p)for p in o['vertices']];return {'name':o['name'],'vertices':v,'triangles':o['triangles'],'bounds':[[min(p[i]for p in v)for i in range(3)],[max(p[i]for p in v)for i in range(3)]],'tree':BVHTree.FromPolygons(v,o['triangles'],all_triangles=True,epsilon=1e-9)}
def inside(p,obj):
 b=obj['bounds'];t=obj['tree']
 if not all(b[0][i]+TOL<p[i]<b[1][i]-TOL for i in range(3)):return False,None
 nn=t.find_nearest(p)
 if nn[0]is None or nn[3]<=TOL:return False,None
 votes=[]
 for d in [Vector((1,.341,.179)).normalized(),Vector((.191,1,.277)).normalized(),Vector((.387,.173,1)).normalized()]:
  q=p.copy();hits=0
  for _ in range(400):
   h,n,idx,dist=t.ray_cast(q,d,30)
   if h is None:break
   hits+=1;q=h+d*2e-6
  votes.append(hits%2)
 return sum(votes)>=2,nn[3]
def tri_intersections(a,b):
 out=[]
 for t,u in [(a,b),(b,a)]:
  for p,q in zip(t,t[1:]+t[:1]):
   edge=q-p
   if edge.length<1e-12:continue
   h=intersect_ray_tri(*u,edge,p,True)
   if h is not None and -1e-9<=(h-p).dot(edge)/edge.length_squared<=1+1e-9:out.append(h)
 # Coplanar projected overlap catches parallel face containment too.
 n=(a[1]-a[0]).cross(a[2]-a[0])
 if n.length>1e-12 and max(abs(n.normalized().dot(p-a[0]))for p in b)<1e-8:
  axis=max(range(3),key=lambda i:abs(n[i]));ids=[i for i in range(3)if i!=axis];p=[[v[i]for i in ids]for v in a];q=[[v[i]for i in ids]for v in b]
  if cross(*q)<0:q.reverse()
  for e in zip(q,q[1:]+q[:1]):
   p=clip(p,e)
   if not p:break
  if p:out.append(a[0]) # Existence only; exact projected witness retained separately via source triangles.
 return out

def collisions(a,b):
 ab,bb=a['bounds'],b['bounds'];sep=math.sqrt(sum(max(ab[0][i]-bb[1][i],bb[0][i]-ab[1][i],0)**2 for i in range(3)));r={'actor':a['name'],'obstacle':b['name'],'aabbDistanceLowerBound':sep}
 if sep>TOL:r['status']='separated-AABB';return r
 pairs=a['tree'].overlap(b['tree']);ints=[]
 for i,j in pairs:
  t=[a['vertices'][k]for k in a['triangles'][i]];u=[b['vertices'][k]for k in b['triangles'][j]];hit=tri_intersections(t,u)
  if hit:ints.append({'actorTriangle':i,'obstacleTriangle':j,'intersectionWitnesses':[list(v)for v in hit[:6]]})
 con=[]
 for label,ob,other in [('actor',a,b),('obstacle',b,a)]:
  for idx,v in enumerate(ob['vertices']):
   yes,depth=inside(v,other)
   if yes:con.append({'side':label,'vertex':idx,'depth':depth,'world':list(v)})
 r.update(status='intersecting'if ints or con else'clear-after-triangles-and-containment',bvhCandidatePairs=len(pairs),trueIntersectionPairs=len(ints),intersections=ints,containedBeyondTolerance=con)
 return r
records=[]
for rec in g['records']:
 d=rec['direction'];a={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d];rot=Matrix.Rotation(a,3,'Z');obstacles=[]
 for aid,obs in g['companionSourceFacingS'].items():
  for o in obs:obstacles.append({**o,'name':aid+'::'+o['name'],'vertices':[list(rot@Vector(p))for p in o['vertices']]})
 obstacles+=[o for o in rec['entry']if'continuous_loadbearing'not in o['name']]
 support=rec['floor']+[o for o in rec['entry']if'continuous_loadbearing'in o['name']]
 shoes=[o for o in rec['actor']if any(s in o['name'].lower()for s in ['shoe','sole','foot'])];test=shoe_test(shoes,support);preparedBlocks=[prepared(o)for o in obstacles];preparedSupport=[prepared(o)for o in support];checks=[]
 for ob in rec['actor']:
  p=prepared(ob);checks += [collisions(p,b)for b in preparedBlocks]
  if not any(s in ob['name'].lower()for s in ['shoe','sole','foot']):checks += [collisions(p,b)for b in preparedSupport]
 bad=[c for c in checks if c['status']=='intersecting'];out={'direction':d,'case':rec['case'],'actualRoot':rec['root'],'actualAuthoredScale':rec['authoredScale'],'support':test,'allBodyPairChecks':checks,'badPairs':bad};records.append(out)
 print('OWN_PHYSICAL',d,rec['case']['id'],'pen',test['maxPenetration'],'contacts',[(q['contactArea'],q['fractionOfActualFlatSole'])for q in test['perShoe']],'bad',[(q['actor'],q['obstacle'])for q in bad],flush=True)
report={'packetSHA256':g['packetSHA256'],'sourceHashes':g['sourcesBefore'],'toleranceWorld':TOL,'method':'Independent native extraction plus separately authored full shoe triangle/finite support clipping, affine extrema at every finite overlap vertex. Body tested via BVH candidate pairs, actual segment-triangle and coplanar projected intersection; both-way actual vertex containment with three-ray majority and nearest surface distance>1e-5. GroundZ0. AABB separation only excludes provably distant solids; it is not substituted for overlapping-pair proof.','records':records,'maxShoePenetration':max(r['support']['maxPenetration']for r in records),'minPerShoeContactArea':min(p['contactArea']for r in records for p in r['support']['perShoe']),'minPerShoeFlatSoleContactFraction':min(p['fractionOfActualFlatSole']for r in records for p in r['support']['perShoe']),'badPairs':sum(len(r['badPairs'])for r in records)}
with gzip.open(R/'own-physical-audit.json.gz','wt')as f:json.dump(report,f,separators=(',',':'))
summary={k:v for k,v in report.items()if k!='records'};summary['cases']=[{'direction':r['direction'],'id':r['case']['id'],'root':r['actualRoot'],'maximumPenetration':r['support']['maxPenetration'],'shoeContact':r['support']['perShoe'],'badPairs':len(r['badPairs']),'pairChecks':len(r['allBodyPairChecks'])}for r in records];(R/'own-physical-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
