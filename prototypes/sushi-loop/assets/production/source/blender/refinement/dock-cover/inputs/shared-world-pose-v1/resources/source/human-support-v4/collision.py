"""Native triangle-surface/containment evidence; no AABB-only collision verdict."""
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import math
EPS=1e-5

def tree(ob):return BVHTree.FromPolygons(ob['vertices'],ob['triangles'],all_triangles=True,epsilon=1e-9)
def bbox_intersect(a,b):return all(a[0][i]<=b[1][i]+EPS and b[0][i]<=a[1][i]+EPS for i in range(3))
def box_distance(a,b):return math.sqrt(sum(max(a[0][i]-b[1][i],b[0][i]-a[1][i],0)**2 for i in range(3)))
def segment_triangle(p,q,a,b,c):
 d=q-p;e1=b-a;e2=c-a;h=d.cross(e2);det=e1.dot(h)
 if abs(det)<1e-12:return None
 u=(p-a).dot(h)/det
 if u< -1e-9 or u>1+1e-9:return None
 z=(p-a).cross(e1);v=d.dot(z)/det
 if v< -1e-9 or u+v>1+1e-9:return None
 t=e2.dot(z)/det
 return p+d*t if -1e-9<=t<=1+1e-9 else None

def tri_hits(a,b):
 out=[]
 for t,u in [(a,b),(b,a)]:
  for p,q in zip(t,t[1:]+t[:1]):
   hit=segment_triangle(p,q,*u)
   if hit is not None and not any((hit-v).length<1e-8 for v in out):out.append(hit)
 # Parallel/coplanar pairs are handled by actual projected overlap clipping.
 n=(a[1]-a[0]).cross(a[2]-a[0])
 if n.length>1e-12 and max(abs(n.normalized().dot(p-a[0]))for p in b)<1e-7:
  ax=max(range(3),key=lambda i:abs(n[i]));ids=[i for i in range(3)if i!=ax];pa=[(p[ids[0]],p[ids[1]])for p in a];pb=[(p[ids[0]],p[ids[1]])for p in b];signed=lambda p:sum(x[0]*y[1]-x[1]*y[0]for x,y in zip(p,p[1:]+p[:1]))
  if signed(pb)<0:pb.reverse()
  poly=pa
  for p,q in zip(pb,pb[1:]+pb[:1]):
   new=[];side=lambda v:(q[0]-p[0])*(v[1]-p[1])-(q[1]-p[1])*(v[0]-p[0])
   for u,v in zip(poly,poly[1:]+poly[:1]):
    du,dv=side(u),side(v);iu,iv=du>=-1e-10,dv>=-1e-10
    if iu:new.append(u)
    if iu!=iv:
     f=du/(du-dv);new.append((u[0]+f*(v[0]-u[0]),u[1]+f*(v[1]-u[1])))
   poly=new
   if not poly:break
  for uv in poly:
   xyz=[0.,0.,0.];xyz[ids[0]]=uv[0];xyz[ids[1]]=uv[1];xyz[ax]=a[0][ax]-(n[ids[0]]*(xyz[ids[0]]-a[0][ids[0]])+n[ids[1]]*(xyz[ids[1]]-a[0][ids[1]]))/n[ax];v=Vector(xyz)
   if not any((v-q).length<1e-8 for q in out):out.append(v)
 return out

def inside(v,bvh,bounds):
 if not all(bounds[0][i]+EPS<v[i]<bounds[1][i]-EPS for i in range(3)):return False,0.
 near=bvh.find_nearest(v)
 if not near[0] or near[3]<=EPS:return False,near[3]or 0
 votes=[]
 for ray in [(1,.217,.391),(-.193,1,.337),(.283,-.149,1)]:
  d=Vector(ray).normalized();p=v.copy();count=0
  for _ in range(200):
   hit,n,idx,dist=bvh.ray_cast(p,d,20)
   if hit is None:break
   count+=1;p=hit+d*2e-6
  votes.append(count%2)
 return sum(votes)>=2,near[3]

def pair(a,b,ta=None,tb=None):
 ta=ta or tree(a);tb=tb or tree(b);bd=box_distance(a['bounds'],b['bounds']);r={'actorMesh':a['name'],'obstacleMesh':b['name'],'aabbSeparationLowerBound':bd,'bvhCandidatePairs':0,'actualTriangleIntersectionPairs':0,'containedActorVerticesBeyondTolerance':0,'containedObstacleVerticesBeyondTolerance':0,'maximumSampledContainmentDepth':0.,'intersectionWitnesses':[]}
 if not bbox_intersect(a['bounds'],b['bounds']):return r
 pairs=ta.overlap(tb);r['bvhCandidatePairs']=len(pairs)
 for i,j in pairs:
  av=[a['vertices'][k]for k in a['triangles'][i]];bv=[b['vertices'][k]for k in b['triangles'][j]];hits=tri_hits(av,bv)
  if hits:
   r['actualTriangleIntersectionPairs']+=1
   if len(r['intersectionWitnesses'])<8:r['intersectionWitnesses'].append({'actorTriangle':i,'obstacleTriangle':j,'points':[list(p)for p in hits]})
 for key,vertices,t,bounds in [('containedActorVerticesBeyondTolerance',a['vertices'],tb,b['bounds']),('containedObstacleVerticesBeyondTolerance',b['vertices'],ta,a['bounds'])]:
  for v in vertices:
   yes,depth=inside(v,t,bounds)
   if yes:r[key]+=1;r['maximumSampledContainmentDepth']=max(r['maximumSampledContainmentDepth'],depth)
 return r
