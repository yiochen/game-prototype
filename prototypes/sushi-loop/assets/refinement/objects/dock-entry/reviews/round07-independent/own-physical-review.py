import bpy,runpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_ray_tri
OUT=Path(__file__).resolve().parent;B=OUT/'resources/repo/prototypes/sushi-loop/assets/refinement/objects/dock-entry';HELP=B/'source/human-reference-round07/cohort_scene_entry.py';ns=runpy.run_path(str(HELP));scene=ns['sc'];getgeom=ns['geometry'];pose=ns['pose'];SN=ns['snapshots'];hr=ns['hr'];ec=ns['ec'];fc=ns['fc'];hc=ns['hc'];PLAN=json.loads((B/'inputs/shared-world-pose-v1/plan.json').read_text());H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();EPS=1e-5
rawdir=OUT/'physical-records';rawdir.mkdir(exist_ok=True);renderdir=OUT/'native-human-replay';renderdir.mkdir(exist_ok=True)
def area(poly):return abs(sum(p[0]*q[1]-q[0]*p[1]for p,q in zip(poly,poly[1:]+poly[:1])))/2 if len(poly)>2 else 0

def project(obs,up=False,bottom=False):
 res=[]
 for o in obs:
  for idx,f in enumerate(o['triangles']):
   v=[tuple(o['vertices'][i])for i in f];dx1=v[1][0]-v[0][0];dy1=v[1][1]-v[0][1];dz1=v[1][2]-v[0][2];dx2=v[2][0]-v[0][0];dy2=v[2][1]-v[0][1];dz2=v[2][2]-v[0][2];det=dx1*dy2-dx2*dy1
   if abs(det)<1e-12 or (up and det<=0) or (bottom and det>=0):continue
   ax=(dz1*dy2-dz2*dy1)/det;ay=(dx1*dz2-dx2*dz1)/det;plane=(ax,ay,v[0][2]-ax*v[0][0]-ay*v[0][1]);xy=[(q[0],q[1])for q in v]
   if det<0:xy.reverse()
   res.append({'owner':o['name'],'tri':idx,'v':[list(p)for p in v],'xy':xy,'plane':plane,'bbox':(min(p[0] for p in v),min(p[1] for p in v),max(p[0] for p in v),max(p[1] for p in v))})
 return res

def overlap(poly,clip):
 for a,b in zip(clip,clip[1:]+clip[:1]):
  if not poly:break
  out=[]
  for p,q in zip(poly,poly[1:]+poly[:1]):
   d=(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]);e=(b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0]);inside=d>=0
   if inside:out.append(p)
   if inside!=(e>=0):
    f=d/(d-e);out.append((p[0]+f*(q[0]-p[0]),p[1]+f*(q[1]-p[1])))
  poly=out
 return poly

def support_check(shoes,surfaces):
 shoeproj=project(shoes);supports=project(surfaces,up=True);maxpen=max(-v[2]for t in shoeproj for v in t['v']);contacts={o['name']:[] for o in shoes};tested=0;worst=None
 for a in shoeproj:
  ab=a['bbox']
  for b in supports:
   bb=b['bbox']
   if ab[2]<bb[0]or bb[2]<ab[0]or ab[3]<bb[1]or bb[3]<ab[1]:continue
   poly=overlap(a['xy'][:],b['xy']);ar=area(poly)
   if ar<1e-14:continue
   tested+=1;diff=[sum((b['plane'][i]-a['plane'][i])*p[i]for i in [0,1])+b['plane'][2]-a['plane'][2]for p in poly];high=max(diff)
   if high>maxpen:maxpen=high;worst={'shoe':a['owner'],'shoeTriangle':a['tri'],'support':b['owner'],'supportTriangle':b['tri'],'polygonXY':poly,'residualRange':[min(diff),high]}
   if max(abs(x)for x in diff)<=EPS:contacts[a['owner']].append({'support':b['owner'],'shoeTriangle':a['tri'],'supportTriangle':b['tri'],'polygonXY':poly,'area':ar,'residualRange':[min(diff),high]})
  if max(abs(v[2])for v in a['v'])<=EPS:contacts[a['owner']].append({'support':'ground0','shoeTriangle':a['tri'],'polygonXY':a['xy'],'area':area(a['xy']),'residualRange':[min(v[2]for v in a['v']),max(v[2]for v in a['v'])]})
 summary=[]
 for o in shoes:
  low=min(v.z for v in o['vertices']);flat=0
  for f in o['triangles']:
   v=[o['vertices'][i]for i in f]
   if max(abs(vv.z-low)for vv in v)<=EPS :flat+=area([(vv.x,vv.y)for vv in v])
  total=sum(c['area']for c in contacts[o['name']]);pts=[p for c in contacts[o['name']]for p in c['polygonXY']];summary.append({'shoe':o['name'],'lowestVisibleSoleZ':low,'flatSoleArea':flat,'contactArea':total,'flatSoleContactFraction':total/flat if flat else None,'contactBounds':[[min(p[i]for p in pts),max(p[i]for p in pts)]for i in [0,1]]if pts else None,'contactPatches':contacts[o['name']]})
 return {'maximumFullShoePenetration':max(0,maxpen),'testedFiniteTriangleOverlapPolygons':tested,'worstWitness':worst,'shoes':summary}

def tree(o):return BVHTree.FromPolygons(o['vertices'],o['triangles'],all_triangles=True,epsilon=1e-9)
def inside(p,t,bb):
 if not all(bb[0][i]+EPS<p[i]<bb[1][i]-EPS for i in range(3)):return False
 near=t.find_nearest(p)
 if near[0] is None or near[3]<=EPS:return False
 votes=[]
 for ray in [(1,.173,.411),(.237,1,-.301),(-.187,.321,1)]:
  d=Vector(ray).normalized();v=p.copy();count=0
  for _ in range(100):
   q,_,_,_=t.ray_cast(v,d,20)
   if q is None:break
   count+=1;v=q+d*2e-6
  votes.append(count%2)
 return sum(votes)>=2

def segment(p,q,tri):
 d=q-p
 if d.length<1e-10:return False
 hit=intersect_ray_tri(*tri,d,p,True)
 return hit is not None and -1e-8<=(hit-p).dot(d)/d.length_squared<=1+1e-8

def collision(a,b,ta,tb):
 if any(a['bounds'][1][i]<b['bounds'][0][i]-EPS or b['bounds'][1][i]<a['bounds'][0][i]-EPS for i in range(3)):return None
 crosses=0;witness=[]
 for i,j in ta.overlap(tb):
  av=[a['vertices'][v]for v in a['triangles'][i]];bv=[b['vertices'][v]for v in b['triangles'][j]]
  if any(segment(p,q,bv)for p,q in zip(av,av[1:]+av[:1]))or any(segment(p,q,av)for p,q in zip(bv,bv[1:]+bv[:1])):
   crosses+=1
   if len(witness)<3:witness.append([i,j])
 ca=sum(inside(v,tb,b['bounds'])for v in a['vertices']);cb=sum(inside(v,ta,a['bounds'])for v in b['vertices'])
 return {'actor':a['name'],'obstacle':b['name'],'crossingTrianglePairs':crosses,'containedActorVerticesBeyondTolerance':ca,'containedObstacleVerticesBeyondTolerance':cb,'witnessPairs':witness}

def matstate(ob):
 values=[]
 for m in ob.data.materials:
  if m and m.use_nodes:
   for n in m.node_tree.nodes:
    for s in n.inputs:
     if not hasattr(s,'default_value'):continue
     v=s.default_value
     if isinstance(v,(float,int,bool,str)):v=v
     else:
      try:v=list(v)
      except:v=str(type(v))
     values.append([m.name,n.name,s.identifier,v])
 return HJSON(values)
def HJSON(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
pose(0,-2.25,0,'S','stand',12);bpy.context.view_layer.update();baseline={};parity=[]
for audit in ns['snapshotAudit']:
 for row in audit['objects']:
  cp=bpy.data.objects[row['snapshotObject']];v=[list(cp.matrix_world@p.co)for p in cp.data.vertices];baseline[cp.name]={'v':v,'mat':matstate(cp)};parity.append({'object':cp.name,'sourceFrame12VertexSHA256':hashlib.sha256(json.dumps([tuple(p)for p in v],separators=(',',':')).encode()).hexdigest(),'declaredSourceParitySHA256':row['worldVertexSHA256'],'sourceSnapshotMatches':hashlib.sha256(json.dumps([tuple(p)for p in v],separators=(',',':')).encode()).hexdigest()==row['worldVertexSHA256']})
# Independently measure all36 physical stances; contact polygons canonicalized only through rigid rotations, never refitted.
records=[];renders=[];cam=scene.camera;scene.render.resolution_x=1536;scene.render.resolution_y=1536;cam.data.ortho_scale=6;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
from bpy_extras.object_utils import world_to_camera_view
def pix(v):
 p=world_to_camera_view(scene,cam,Vector(v));return Vector((p.x*768,(1-p.y)*768))
b=pix((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=pix((0,0,0)).y-b.y;cam.data.shift_y=(440-b.y)/dy;bpy.context.view_layer.update()
for d,ang in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 for idx,c in enumerate(PLAN['cases']):
  x,y=c['sourceFacingXY'];z=c['solvedRootZ'];pose(x,y,z,d,c['actorClip'],c['nativeFrame']);bpy.context.view_layer.update();actor=getgeom(hc);shoes=[o for o in actor if 'distinct cocoa shoe' in o['name']];load=getgeom(fc)+[o for o in getgeom(ec)if'continuous_loadbearing'in o['name']];support=support_check(shoes,load);obstacles=[o for o in getgeom(ec)if'continuous_loadbearing'not in o['name']]
  for q in SN.values():obstacles+=getgeom(q['collection'])
  obsTrees={o['name']:tree(o)for o in obstacles+load};checks=[]
  for a in actor:
   at=tree(a);blocks=obstacles+([]if'distinct cocoa shoe'in a['name']else load)
   for bb in blocks:
    r=collision(a,bb,at,obsTrees[bb['name']])
    if r is not None:checks.append(r)
  bad=[r for r in checks if r['crossingTrianglePairs']or r['containedActorVerticesBeyondTolerance']or r['containedObstacleVerticesBeyondTolerance']];rotation=Matrix.Rotation(ang,4,'Z');drift=0;matstable=True
  for name,base in baseline.items():
   cp=bpy.data.objects[name];actual=[cp.matrix_world@v.co for v in cp.data.vertices];expected=[rotation@Vector(v)for v in base['v']];drift=max(drift,max((a-b).length for a,b in zip(actual,expected)));matstable &=matstate(cp)==base['mat']
  r={'direction':d,'case':c,'actualRootMatrix':[list(row)for row in hr.matrix_world],'actualRootScale':list(hr.scale),'support':support,'nearMeshChecks':checks,'badPairs':bad,'cohortMaximumVertexDrift':drift,'cohortMaterialsUnchanged':matstable};f=rawdir/f'{d}-{idx}.json';f.write_text(json.dumps(r,indent=2)+'\n');records.append({'direction':d,'caseId':c['id'],'path':str(f.relative_to(OUT)),'sha256':H(f),'maximumPenetration':support['maximumFullShoePenetration'],'contactAreas':[s['contactArea']for s in support['shoes']],'contactFractions':[s['flatSoleContactFraction']for s in support['shoes']],'badPairs':len(bad),'cohortDrift':drift,'materialsStable':matstable})
  if idx in [1,3,8]:
   for fixture in ['current','approved-additional'] if idx==8 else ['current']:
    SN['workshop-hut']['collection'].hide_render=fixture!='current';SN['approved-workshop-hut']['collection'].hide_render=fixture=='current';out=renderdir/f'{d}-{idx}-{fixture}.png';scene.render.filepath=str(out);bpy.ops.render.render(write_still=True);renders.append({'direction':d,'index':idx,'fixture':fixture,'path':str(out.relative_to(OUT)),'sha256':H(out)})
  print('OWN07',d,idx,'pen',support['maximumFullShoePenetration'],'fractions',[s['flatSoleContactFraction']for s in support['shoes']],'bad',len(bad),'cohort',drift,matstable,flush=True)
summary={'candidatePacketSHA256':'5e4a1c313176fc0e0474474a0fbc800b3ddd321d9c4076e71da39620a617ba70','planSHA256':H(B/'inputs/shared-world-pose-v1/plan.json'),'method':'Retained native scene/cohort loader; independent complete triangle projected-overlap plane extrema for shoe nonpenetration and finite contact, independent mathutils segment/triangle checks plus three-ray containment beyond1e-5 for full-body/obstacles. All36 actual poses evaluated; no per-facing support solve. Current and separately labeled approved-hut fixture obstacles both checked. Own selected native replays saved.','snapshotSourceParity':parity,'records':records,'renders':renders,'scope':'Nine discrete stances, not locomotion/door traversal/future family approval'};(OUT/'own-physical-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
