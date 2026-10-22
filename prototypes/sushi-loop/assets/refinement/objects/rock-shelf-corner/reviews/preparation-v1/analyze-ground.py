import pathlib,json,math
P=pathlib.Path(__file__).resolve().parent;d=json.loads((P/'measured-original.json').read_text());ts=[[tuple(v[:2]) for v in t['vertices']] for t in d['finiteGroundTriangles']]
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def sub(a,b):return (a[0]-b[0],a[1]-b[1])
def inside(p):
 for a,b,c in ts:
  vs=[cross(sub(b,a),sub(p,a)),cross(sub(c,b),sub(p,b)),cross(sub(a,c),sub(p,c))]
  if min(vs)>=-1e-12 or max(vs)<=1e-12:return True
 return False
edges=[(t[k],t[(k+1)%3]) for t in ts for k in range(3)];segments={}
for a,b in edges:
 r=sub(b,a);rr=r[0]*r[0]+r[1]*r[1];cuts=[0.,1.]
 for c,d in edges:
  s=sub(d,c);den=cross(r,s)
  if abs(den)>1e-12:
   v=sub(c,a);t=cross(v,s)/den;u=cross(v,r)/den
   if -1e-10<=t<=1+1e-10 and -1e-10<=u<=1+1e-10:cuts.append(max(0,min(1,t)))
  elif abs(cross(sub(c,a),r))<1e-12:
   for v in [c,d]:
    t=(sub(v,a)[0]*r[0]+sub(v,a)[1]*r[1])/rr
    if 0<=t<=1:cuts.append(t)
 cuts=sorted(set(round(x,12) for x in cuts))
 for t,u in zip(cuts,cuts[1:]):
  if u-t<1e-10:continue
  aa=(a[0]+r[0]*t,a[1]+r[1]*t);bb=(a[0]+r[0]*u,a[1]+r[1]*u);v=sub(bb,aa);ln=math.hypot(*v);mid=((aa[0]+bb[0])/2,(aa[1]+bb[1])/2);eps=1e-7;left=(mid[0]-v[1]/ln*eps,mid[1]+v[0]/ln*eps);right=(mid[0]+v[1]/ln*eps,mid[1]-v[0]/ln*eps);il,ir=inside(left),inside(right)
  if il==ir:continue
  if not il:aa,bb=bb,aa
  key=lambda p:tuple(round(x,9) for x in p)
  segments[(key(aa),key(bb))]=(aa,bb)
paths=[]
while segments:
 _,(a,b)=segments.popitem();path=[a,b]
 while math.dist(path[-1],path[0])>1e-7:
  nxt=next((k for k,(aa,bb) in segments.items() if math.dist(aa,path[-1])<1e-7),None)
  if nxt is None:raise RuntimeError('unclosed ground union')
  aa,bb=segments.pop(nxt);path.append(bb)
 paths.append(path)
areas=[sum(cross(a,b) for a,b in zip(path,path[1:]))/2 for path in paths]
r={'method':'Exact original Blender tessellated z=0 triangle union boundary; segment arrangement and inside-union classification. No AABB/fullcell substitution.','outlineLoopsXY':paths,'signedAreas':areas,'unionArea':sum(areas),'sumTriangleArea':sum(abs(cross(sub(b,a),sub(c,a)))/2 for a,b,c in ts),'groundZ':0,'boundsXY':[[-.5,-.44999998807907104],[.44999998807907104,.5]],'note':'Interior overlap of the old swept ribbon is not a modeling requirement. Its finite ground-support union is the measured source footprint to preserve; editor may replace overlapping/folded source surfaces.'}
(P/'finite-ground-union.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
