import bpy,runpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;g=runpy.run_path(str(R/'audit-human-and-profile-v2.py'));sc=g['sc'];hr=g['hr'];hc=g['hc'];rig=g['rig'];native=g['native'];path=g['path']
def triangles(col,shoe=False):
 dg=bpy.context.evaluated_depsgraph_get();out=[]
 for o in col.all_objects:
  if o.type!='MESH' or o.hide_render or (shoe and not any(s in o.name.lower() for s in ['shoe','sole','foot'])):continue
  e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();v=[e.matrix_world@p.co for p in m.vertices]
  for t in m.loop_triangles:
   p=[tuple(v[i]) for i in t.vertices];det=(p[1][0]-p[0][0])*(p[2][1]-p[0][1])-(p[1][1]-p[0][1])*(p[2][0]-p[0][0])
   if abs(det)<1e-13:continue
   if not shoe and det<0:continue
   ax=((p[1][2]-p[0][2])*(p[2][1]-p[0][1])-(p[2][2]-p[0][2])*(p[1][1]-p[0][1]))/det;ay=((p[1][0]-p[0][0])*(p[2][2]-p[0][2])-(p[2][0]-p[0][0])*(p[1][2]-p[0][2]))/det;az=p[0][2]-ax*p[0][0]-ay*p[0][1];xy=[(q[0],q[1]) for q in p]
   if det<0:xy.reverse()
   out.append({'owner':o.name,'nativeTriangle':t.index,'xy':xy,'plane':(ax,ay,az),'bbox':(min(q[0] for q in p),min(q[1] for q in p),max(q[0] for q in p),max(q[1] for q in p)),'vertices':p})
  e.to_mesh_clear()
 return out
def area(p):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1])))/2 if len(p)>=3 else 0
def clip(poly,edge):
 a,b=edge;out=[]
 def side(p):return(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
 for p,q in zip(poly,poly[1:]+poly[:1]):
  dp,dq=side(p),side(q);ip,iq=dp>=-1e-12,dq>=-1e-12
  if ip:out.append(p)
  if ip!=iq:
   t=dp/(dp-dq);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
 return out
sup=triangles(bpy.data.collections['WarmSoft_dock-floor'])+triangles(g['ec']);records=[]
cases=[{'id':f'original-{i}','frame':i+1,'root':p} for i,p in enumerate(path)]+[{'id':'feasibility-ground-approach','frame':1,'root':[0,-2.16,0]},{'id':'feasibility-third-pose-finite-contact','frame':3,'root':[0,-1.73,.1466666667]},{'id':'feasibility-first-tread-native-world-path','frame':1,'root':[0,-2.0,0]},{'id':'feasibility-second-tread-native-world-path','frame':2,'root':[0,-1.80,0]},{'id':'feasibility-terminal-tread-native-world-path','frame':3,'root':[0,-1.62,0]}]
for case in cases:
 native.apply_clip({'root':hr,'collection':hc},rig,'walk',case['frame'],'S',sc);hr.location=case['root'];hr.rotation_euler=(0,0,0);bpy.context.view_layer.update();foot=triangles(hc,True);over=[];maxD=max(-v[2] for t in foot for v in t['vertices'])
 for t in foot:
  a=t['bbox']
  for s in sup:
   b=s['bbox']
   if a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1]:continue
   p=t['xy'][:]
   for e in zip(s['xy'],s['xy'][1:]+s['xy'][:1]):
    p=clip(p,e)
    if not p:break
   if len(p)<3 or area(p)<1e-14:continue
   plane=tuple(s['plane'][i]-t['plane'][i] for i in range(3));ds=[plane[0]*q[0]+plane[1]*q[1]+plane[2] for q in p];m=max(ds);maxD=max(maxD,m);over.append({'shoe':t['owner'],'support':s['owner'],'shoeTriangle':t['nativeTriangle'],'supportTriangle':s['nativeTriangle'],'intersectionXY':p,'differenceRange':[min(ds),max(ds)],'area':area(p),'planeDifference':plane})
 # Planar finite contact area after exact minimal rigid lift. No source pose is changed/published.
 patches=[x for x in over if maxD-x['differenceRange'][0]<1e-5 and maxD-x['differenceRange'][1]<1e-5]
 # Ground contact covers true coplanar lowest shoe triangles when lift leaves them atZ0.
 groundPatches=[]
 for t in foot:
  zs=[v[2]+maxD for v in t['vertices']]
  if max(abs(z) for z in zs)<1e-5:groundPatches.append({'shoe':t['owner'],'nativeTriangle':t['nativeTriangle'],'area':area(t['xy'])})
 records.append({'case':case,'minimalRigidLiftWorld':maxD,'derivedRootWorldZ':case['root'][2]+maxD,'contactAreaOnNativeSupport':sum(x['area'] for x in patches),'contactAreaOnGroundDiagnostic':sum(x['area'] for x in groundPatches),'finiteContactPatches':patches,'groundPatches':groundPatches,'activeLimitingIntersections':sorted(over,key=lambda x:x['differenceRange'][1],reverse=True)[:5],'method':'Exact 2D triangle-overlap clipping with linearly interpolated actual3D shoe and upward support surfaces. Max(supportZ-shoeZ) over overlap vertices is minimal rigid worldZ lift. Finite coplanar contact patch areas use1e-5world tolerance. Ground outside native support isZ0. Report is feasibility only; no candidate/frame/character source edited.'})
report={'candidatePacketSHA256':'205ed0c5916ae2a063423879d771351b4a52999391671f4f6f483c402921378d','sourceHashes':g['report']['sourceHashes'],'supportTriangleCount':len(sup),'records':records,'limits':['The explicitly labeled alternative XY cases are explicitly labeled mathematical feasibility diagnostics, not reviewed candidate evidence or per-view sprite corrections. Any chosen new worldpath must be common to all facings, native and actual unchanged sprite presentation.','Positive finite area alone is not automatic usability approval. Inspect visible stability/overhang and recheck body/post/cap clearance under the actual chosen root law.','This analysis does not make the supplied original traversal pass; new source-independent context/physical evidence must be supplied and reviewed.']}
(R/'own-rigid-support-law-feasibility-v2.json').write_text(json.dumps(report,indent=2)+'\n');print('RIGID_SUPPORT_LAW',json.dumps([{'id':r['case']['id'],'lift':r['minimalRigidLiftWorld'],'rootZ':r['derivedRootWorldZ'],'nativeContactArea':r['contactAreaOnNativeSupport'],'groundContactArea':r['contactAreaOnGroundDiagnostic']} for r in records]))
