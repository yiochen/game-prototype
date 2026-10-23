"""Source-exact physical scene and finite-support helpers. No model/source writes."""
import bpy,math,json,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
B=Path(__file__).resolve().parents[2];O=B/'candidates/round-05';H=B/'source/resources/approved-human-v3';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
F=B/'source/round-04.blend';E=B/'inputs/paired-native/dock-entry-round-06.blend';A=H/'customer-rosa-approved.blend';ORIG=B/'source/resources/original-library.blend'
assert sha(F)=='94b509984dc442547602f32feada987c5119e3b9031eb1bd65a6a07769880418';assert sha(E)=='22bd2b05201567c22d9dabcf767a3daf0639342e5522c43900ff4b777f5f3b37';assert sha(A)=='a6fe68fa07f3930c3d8e88ae6df992fefe447a9ef18935e322daf6f4bbc28253'
bpy.ops.wm.open_mainfile(filepath=str(F));sc=bpy.context.scene;fc=bpy.data.collections['WarmSoft_dock-floor'];fr=bpy.data.objects['dock-floor__root'];fr.rotation_euler=(0,0,0)
with bpy.data.libraries.load(str(E),link=False)as(a,b):b.collections=['S33_PROP_dock-entry']
ec=b.collections[0];sc.collection.children.link(ec);ec.hide_render=False;ec.hide_viewport=False;er=bpy.data.objects['dock-entry__root'];er.location=(0,-1.5,0)
rig=json.loads((H/'rig.json').read_text())
with bpy.data.libraries.load(str(A),link=False)as(a,b):b.collections=a.collections;b.actions=sorted({t['action'] for clip in ['stand','walk'] for t in rig['clips'][clip]['actions']})
for c in b.collections:sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
hr=bpy.data.objects[rig['groundRootObject']];hc=next(c for c in b.collections if hr in list(c.all_objects))
spec=importlib.util.spec_from_file_location('v4_native_actions',H/'native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
companions={}
with bpy.data.libraries.load(str(ORIG),link=False)as(a,b):
 b.collections=['S33_PROP_workshop-hut.001','S33_PROP_submarine_base.001','S33_PROP_dock-cover.001'];b.actions=[n for n in a.actions if any(t in n for t in ['submarine-yellow','dock-cover'])]
for aid,c,p in zip(['workshop-hut','submarine-yellow','dock-cover'],b.collections,[(.78,.35,.23),(-.7,-.42,.23),(0,0,.23)]):
 sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
 for ob in c.all_objects:ob.hide_viewport=False;ob.hide_set(False)
 root=next(o for o in c.objects if o.type=='EMPTY' and o.parent is None);root.location=p;root.rotation_euler=(0,0,0);companions[aid]={'root':root,'collection':c,'rootSource':p}
for aid,clip in [('submarine-yellow','dock-ready'),('dock-cover','uncover')]:
 r=json.loads((B/'source/resources/family-rigs'/f'{aid}.json').read_text());native.apply_clip(companions[aid],r,clip,12,'S',sc)
def pose(x=0,y=0,z=0,d='S',clip='stand',frame=12):
 a={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d];R=Matrix.Rotation(a,3,'Z');native.apply_clip({'root':hr,'collection':hc},rig,clip,frame,d,sc)
 for ob,p in [(fr,(0,0,0)),(er,(0,-1.5,0))]+[(q['root'],q['rootSource']) for q in companions.values()]:ob.rotation_euler.z=a;ob.location=R@Vector(p)
 hr.location=R@Vector((x,y,z));hr.rotation_euler.z=a;assert all(abs(s-1.25)<1e-9 for s in hr.scale);bpy.context.view_layer.update()
pose()
def geometry(col,shoe=False):
 dg=bpy.context.evaluated_depsgraph_get();out=[]
 for ob in col.all_objects:
  if ob.type!='MESH' or ob.hide_render or(shoe and not any(s in ob.name.lower()for s in ['shoe','sole','foot'])):continue
  e=ob.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();v=[e.matrix_world@p.co for p in m.vertices];f=[tuple(t.vertices)for t in m.loop_triangles];out.append({'name':ob.name,'vertices':v,'triangles':f,'matrix':[list(r)for r in e.matrix_world],'bounds':[[min(p[i]for p in v)for i in range(3)],[max(p[i]for p in v)for i in range(3)]]});e.to_mesh_clear()
 return out
def projected(g,upward=False):
 out=[]
 for ob in g:
  for idx,ids in enumerate(ob['triangles']):
   p=[tuple(ob['vertices'][i])for i in ids];det=(p[1][0]-p[0][0])*(p[2][1]-p[0][1])-(p[2][0]-p[0][0])*(p[1][1]-p[0][1])
   if abs(det)<1e-13 or(upward and det<0):continue
   ax=((p[1][2]-p[0][2])*(p[2][1]-p[0][1])-(p[2][2]-p[0][2])*(p[1][1]-p[0][1]))/det;ay=((p[1][0]-p[0][0])*(p[2][2]-p[0][2])-(p[2][0]-p[0][0])*(p[1][2]-p[0][2]))/det;az=p[0][2]-ax*p[0][0]-ay*p[0][1];xy=[q[:2]for q in p]
   if det<0:xy.reverse()
   out.append({'owner':ob['name'],'triangle':idx,'xy':xy,'plane':(ax,ay,az),'bbox':(min(q[0]for q in p),min(q[1]for q in p),max(q[0]for q in p),max(q[1]for q in p)),'vertices':p})
 return out
def signedarea(p):return sum(a[0]*b[1]-a[1]*b[0]for a,b in zip(p,p[1:]+p[:1]))/2 if len(p)>2 else 0
def area(p):return abs(signedarea(p))
def centroid(p):
 s=signedarea(p)
 if abs(s)<1e-15:return None
 return[sum((a[i]+b[i])*(a[0]*b[1]-a[1]*b[0])for a,b in zip(p,p[1:]+p[:1]))/(6*s)for i in [0,1]]
def clip(poly,a,b):
 out=[];cross=lambda p:(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
 for p,q in zip(poly,poly[1:]+poly[:1]):
  dp,dq=cross(p),cross(q);ip,iq=dp>=-1e-12,dq>=-1e-12
  if ip:out.append(p)
  if ip!=iq:
   t=dp/(dp-dq);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
 return out
def hull(points):
 ps=sorted(set(points));cross=lambda a,b,c:(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);lo=[];hi=[]
 for p in ps:
  while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
  lo.append(p)
 for p in reversed(ps):
  while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
  hi.append(p)
 return lo[:-1]+hi[:-1]
def solve(shoes,support):
 maxD=max(0,max(-v[2]for t in shoes for v in t['vertices']));over=[]
 for t in shoes:
  a=t['bbox']
  for s in support:
   b=s['bbox']
   if a[2]<b[0]or b[2]<a[0]or a[3]<b[1]or b[3]<a[1]:continue
   p=t['xy'][:]
   for v,w in zip(s['xy'],s['xy'][1:]+s['xy'][:1]):
    p=clip(p,v,w)
    if not p:break
   if len(p)<3 or area(p)<1e-14:continue
   plane=tuple(s['plane'][i]-t['plane'][i]for i in range(3));ds=[plane[0]*q[0]+plane[1]*q[1]+plane[2]for q in p];maxD=max(maxD,max(ds));over.append({'shoe':t['owner'],'shoeTriangle':t['triangle'],'support':s['owner'],'supportTriangle':s['triangle'],'polygonXY':p,'area':area(p),'centroid':centroid(p),'differenceRange':[min(ds),max(ds)],'shoePlane':t['plane'],'supportPlane':s['plane']})
 patches=[p for p in over if maxD-p['differenceRange'][0]<1e-5 and maxD-p['differenceRange'][1]<1e-5]
 ground=[]
 for t in shoes:
  if max(abs(v[2]+maxD)for v in t['vertices'])<1e-5:ground.append({'shoe':t['owner'],'shoeTriangle':t['triangle'],'support':'ground-Z0','polygonXY':t['xy'],'area':area(t['xy']),'centroid':centroid(t['xy'])})
 summary=[]
 for name in sorted(set(t['owner']for t in shoes)):
  ts=[t for t in shoes if t['owner']==name];minz=min(v[2]for t in ts for v in t['vertices']);flat=[t for t in ts if max(abs(v[2]-minz)for v in t['vertices'])<1e-5];base=sum(area(t['xy'])for t in flat);outline=hull([tuple(v[:2])for t in ts for v in t['vertices']]);pp=[p for p in patches+ground if p['shoe']==name];ar=sum(p['area']for p in pp);ps=[v for p in pp for v in p['polygonXY']];summary.append({'shoe':name,'flatSoleArea':base,'projectedFullShoeArea':area(outline),'contactArea':ar,'fractionOfFlatSole':ar/base if base else None,'fractionOfProjectedShoe':ar/area(outline),'contactCentroid':[sum(p['centroid'][i]*p['area']for p in pp)/ar for i in[0,1]]if ar else None,'contactBoundsXY':[[min(p[i]for p in ps)for i in[0,1]],[max(p[i]for p in ps)for i in[0,1]]]if ps else None,'contactConvexHull':hull(ps)if ps else[]})
 return{'solvedRootZ':maxD,'maxFullShoePenetrationAfterSolve':max(0,max((p['differenceRange'][1]-maxD for p in over),default=0)),'perShoe':summary,'nativeFinitePatches':patches,'groundFinitePatches':ground,'fullShoeOverlapPairs':len(over),'limitingIntersections':sorted(over,key=lambda p:p['differenceRange'][1],reverse=True)[:4]}
def walking_support():
 eg=[x for x in geometry(ec)if'continuous_loadbearing' in x['name']];return projected(geometry(fc)+eg,True)
sourceHashes={'floor':sha(F),'entry':sha(E),'approvedRosa':sha(A),'originalCompanions':sha(ORIG),'actorRig':sha(H/'rig.json'),'nativeActions':sha(H/'native_actions.py')}
