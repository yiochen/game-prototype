"""Finite evaluated triangle surfaces. Bounds prune pairs only; no bounds-based verdict."""
import bpy,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def geometry(col):
 dg=bpy.context.evaluated_depsgraph_get();rows=[]
 for ob in col.all_objects:
  if ob.type!='MESH' or ob.hide_render or not ob.visible_camera:continue
  e=ob.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();v=[e.matrix_world@q.co for q in m.vertices];t=[tuple(x.vertices)for x in m.loop_triangles]
  rows.append({'name':ob.name,'vertices':v,'triangles':t,'bounds':[[min(q[i]for q in v)for i in range(3)],[max(q[i]for q in v)for i in range(3)]]});e.to_mesh_clear()
 return rows
def surface(rows,up):
 out=[]
 for ob in rows:
  for ti,ids in enumerate(ob['triangles']):
   v=[ob['vertices'][i]for i in ids];a,b,c=v;det=(b.x-a.x)*(c.y-a.y)-(c.x-a.x)*(b.y-a.y)
   if abs(det)<1e-12 or (det>0)!=up:continue
   ax=((b.z-a.z)*(c.y-a.y)-(c.z-a.z)*(b.y-a.y))/det;ay=((b.x-a.x)*(c.z-a.z)-(c.x-a.x)*(b.z-a.z))/det;az=a.z-ax*a.x-ay*a.y;xy=[(q.x,q.y)for q in v]
   if det<0:xy.reverse()
   out.append({'owner':ob['name'],'triangle':ti,'xy':xy,'plane':(ax,ay,az),'xyz':[tuple(q)for q in v],'bbox':(min(q.x for q in v),min(q.y for q in v),max(q.x for q in v),max(q.y for q in v))})
 return out
def clip(p,a,b):
 out=[];side=lambda q:(b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0])
 for u,v in zip(p,p[1:]+p[:1]):
  du,dv=side(u),side(v);iu,iv=du>=0,dv>=0
  if iu:out.append(u)
  if iu!=iv:
   t=du/(du-dv);out.append((u[0]+t*(v[0]-u[0]),u[1]+t*(v[1]-u[1])))
 return out
def area(p):return abs(sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(p,p[1:]+p[:1])))/2 if len(p)>2 else 0
def z_at(t,p):
 a,b,c=t['xyz'];det=(b[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(b[1]-a[1]);u=((p[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(p[1]-a[1]))/det;v=((b[0]-a[0])*(p[1]-a[1])-(p[0]-a[0])*(b[1]-a[1]))/det
 return a[2]+u*(b[2]-a[2])+v*(c[2]-a[2])
S=.2
def bins(b):
 return[(x,y)for x in range(math.floor(b[0]/S),math.floor(b[2]/S)+1)for y in range(math.floor(b[1]/S),math.floor(b[3]/S)+1)]
def finite_gap(lower,upper,contact=False):
 index={}
 for i,t in enumerate(upper):
  for k in bins(t['bbox']):index.setdefault(k,[]).append(i)
 best=None;maximum=None;count=0;covered=0.;patches=[]
 for t in lower:
  candidates={i for k in bins(t['bbox'])for i in index.get(k,[])};a=t['bbox']
  for i in candidates:
   s=upper[i];b=s['bbox']
   if a[2]<b[0]or b[2]<a[0]or a[3]<b[1]or b[3]<a[1]:continue
   p=t['xy'][:]
   for v,w in zip(s['xy'],s['xy'][1:]+s['xy'][:1]):
    p=clip(p,v,w)
    if not p:break
   ar=area(p)
   if ar<1e-12:continue
   g=[z_at(t,q)-z_at(s,q)for q in p];count+=1
   r={'lower':t['owner'],'lowerTriangle':t['triangle'],'upper':s['owner'],'upperTriangle':s['triangle'],'polygonXY':p,'area':ar,'gapRange':[min(g),max(g)]}
   if best is None or min(g)<best['gapRange'][0]:best=r
   if maximum is None or max(g)>maximum:maximum=max(g)
   if contact and max(abs(z)for z in g)<=1e-5:covered+=ar;patches.append(r)
 return{'finiteOverlapPolygonCount':count,'minimumGapWorld':best['gapRange'][0]if best else None,'maximumGapWorld':maximum,'limitingFinitePolygon':best,'contactArea':covered if contact else None,'nativeFiniteContactPolygons':patches if contact else None}
def bvh(rows):
 vs=[];ts=[];owners=[]
 for r in rows:
  off=len(vs);vs+=r['vertices'];ts +=[tuple(off+i for i in t)for t in r['triangles']];owners +=[r['name']]*len(r['triangles'])
 return BVHTree.FromPolygons(vs,ts,all_triangles=True,epsilon=1e-9),owners
