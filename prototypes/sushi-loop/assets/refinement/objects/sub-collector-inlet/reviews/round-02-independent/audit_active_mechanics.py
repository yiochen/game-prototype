import bpy,pathlib,json,math,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=pathlib.Path(__file__).resolve().parent;E=O.parent.parent
# Reuse only independently authored finite native geometry/distance definitions.
defs=(O/'audit_identity_contact.py').read_text().split('# Independent persistent canonical')[0]
exec(compile(defs,str(O/'audit_identity_contact.py'),'exec'))
distdefs=(O/'audit_identity_contact.py').read_text().split('def segdist(')[1].split('\nct=')[0]
exec('def segdist('+distdefs)
bpy.ops.wm.open_mainfile(filepath=str(E/'source/round-02.blend'));s=bpy.context.scene;c=bpy.data.collections['REFINED__sub-collector-inlet'];root=bpy.data.objects['collector__root'];root.rotation_euler.z=0
def apply(fr):
 for suffix in ['guard_rock','mouth_pulse','mouth_sleeve']:
  ob=bpy.data.objects['collector__'+suffix];a=bpy.data.actions[f'INLET_NATIVE__active__collector__{suffix}'];ob.animation_data_create();ob.animation_data.action=a;ob.animation_data.action_slot=a.slots[0]
 s.frame_set(math.floor(fr),subframe=fr-math.floor(fr));bpy.context.view_layer.update()
guard=bpy.data.objects['collector__guard_rock'];moving=[o for o in c.all_objects if o.type=='MESH' and o.parent==guard];shaft=bpy.data.objects['collector__lower_guard_shaft'];fixed=[o for o in c.all_objects if o.type=='MESH' and o not in moving and o!=shaft]
env=json.loads((O/'continuous-envelope.json').read_text());bounds={p['name']:p['continuousBounds'] for p in env['parts']};gb=[[min(bounds[o.name][0][i] for o in moving) for i in range(3)],[max(bounds[o.name][1][i] for o in moving) for i in range(3)]];planes=[]
for o in fixed:
 b=bounds[o.name];gaps=[{'axis':i,'signedDirection':di,'lowerBound':b[0][i]-gb[1][i] if di==1 else gb[0][i]-b[1][i]} for i in range(3) for di in [-1,1]];planes.append({'fixed':o.name,**max(gaps,key=lambda x:x['lowerBound'])})
def finite(a,b):
 ar=np.array([[list(v) for v in t] for t in a['tri']]);lo=ar.min(1);hi=ar.max(1);best=min((p-b['bvh'].find_nearest(p)[0]).length for p in a['v']);n=0
 for t in b['tri']:
  x=np.array(t);d=np.maximum(np.maximum(x.min(0)-hi,lo-x.max(0)),0);ids=np.where((d*d).sum(1)<=best*best+1e-14)[0]
  for i in ids:best=min(best,tdist(a['tri'][int(i)],t));n+=1
 return {'distance':best,'testedTrianglePairs':n}
rows=[];distances=[];housing=['collector__mouth_surround','collector__hollow_enamel_shell','collector__dark_mouth']
for step in range(121):
 fr=1+step/10;apply(fr);dg=bpy.context.evaluated_depsgraph_get();mg={o.name:geometry(o,dg) for o in moving};fg={o.name:geometry(o,dg) for o in fixed};sg=geometry(shaft,dg);contacts=[]
 for n,g in mg.items():
  for n2,g2 in fg.items():
   if any(g['bb'][1][i]<g2['bb'][0][i] or g2['bb'][1][i]<g['bb'][0][i] for i in range(3)):continue
   ov=g['bvh'].overlap(g2['bvh'])
   if ov:contacts.append({'moving':n,'fixed':n2,'actualSurfaceIntersections':len(ov)})
 cage=mg['collector__guard_cage'];axis=shaft.matrix_world.translation.copy();ray=Vector((1,.371,.173)).normalized();origin=axis.copy();hits=0
 for j in range(64):
  h=cage['bvh'].ray_cast(origin,ray)
  if h[0] is None:break
  hits+=1;origin=h[0]+ray*1e-6
 inside=bool(hits%2);near=cage['bvh'].find_nearest(axis)
 rows.append({'frame':fr,'angle':guard.rotation_euler.x,'guardPosition':list(guard.location),'unintendedSurfaceContacts':contacts,'fixedShaftAxisInsideCage':inside,'shaftAxisInGuardLocal':list(guard.matrix_world.inverted()@axis),'shaftAxisDistanceToCageSurface':near[3],'intentionalShaftSurfacePairs':sum(len(g['bvh'].overlap(sg['bvh'])) for g in mg.values())})
 if step%5==0:
  ag={'v':[v for g in mg.values() for v in g['v']],'tri':[t for g in mg.values() for t in g['tri']]}
  for n in housing:distances.append({'frame':fr,'housing':n,**finite(ag,fg[n])})
# Derive actual central lower-rail section from triangle-plane intersections in cage-local space.
apply(1);dg=bpy.context.evaluated_depsgraph_get();g=geometry(bpy.data.objects['collector__guard_cage'],dg);inv=guard.matrix_world.inverted();segments=[]
for tri in g['tri']:
 tri=[inv@v for v in tri];hits=[]
 for a,b in zip(tri,tri[1:]+tri[:1]):
  if a.x*b.x<0:
   p=a+(b-a)*(-a.x/(b.x-a.x));hits.append((round(p.y,7),round(p.z,7)))
 if len(set(hits))==2:segments.append(list(dict.fromkeys(hits)))
neighbors={}
for a,b in segments:neighbors.setdefault(a,set()).add(b);neighbors.setdefault(b,set()).add(a)
loops=[];unseen=set(neighbors)
while unseen:
 start=min(unseen);loop=[start];prev=None;cur=start
 while True:
  nxt=next(v for v in neighbors[cur] if v!=prev)
  if nxt==start:break
  assert nxt not in loop;loop.append(nxt);prev,cur=cur,nxt
 unseen-=set(loop);loops.append(loop)
lower=min(loops,key=lambda loop:min(p[1] for p in loop));a0,a1=env['nativeChannelRanges'][guard.name];offset=shaft.location.y-guard.location.y
axisbox=[[offset*math.cos(a1),-offset*math.sin(a1)],[offset*math.cos(a0),-offset*math.sin(a0)]]
lb=[[min(p[i] for p in lower) for i in range(2)],[max(p[i] for p in lower) for i in range(2)]]
# All section edges collinear with one of the rectangle sides; prove whole axis box strictly inside finite slab.
sectionArea=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(lower,lower[1:]+lower[:1])))/2;isRectangle=all(any(abs(p[i]-lb[j][i])<2e-7 for i in [0,1] for j in [0,1]) for p in lower) and abs(sectionArea-(lb[1][0]-lb[0][0])*(lb[1][1]-lb[0][1]))<1e-9;margin=min(axisbox[0][i]-lb[0][i] for i in range(2));margin=min(margin,*[lb[1][i]-axisbox[1][i] for i in range(2)])
r={'method':'Own saved-source direct action assignment. Actual evaluated BVH at every 0.1frame 1..13. All moving cage and bars vs every other nonshaft mesh. Continuous analytic vertex envelopes independently derived from native channels supply positive separating planes at all real times, not just sample times. Exact finite triangle distance at every half-frame to three housing surfaces. Fixed shaft is intentional hinge; actual central native triangle-plane section and native parity rays assess its connection separately.','sourceSHA256':hashlib.sha256((E/'source/round-02.blend').read_bytes()).hexdigest(),'moving':[o.name for o in moving],'continuousGuardEnvelope':gb,'continuousSeparatingPlanes':planes,'continuousAllNonshaftSeparated':all(x['lowerBound']>0 for x in planes),'maximumUnintendedSurfacePairs':max(sum(x['actualSurfaceIntersections'] for x in r['unintendedSurfaceContacts']) for r in rows),'allSampledShaftAxisInside':all(r['fixedShaftAxisInsideCage'] for r in rows),'fixedShaftContinuousConnection':{'actualNativeLowerRailSectionYZ':lower,'rectangleSectionProven':isRectangle,'fixedShaftAxisBoxYZ':axisbox,'axisBoxInteriorMargin':margin,'finiteConnectedSectionAllTimes':isRectangle and margin>0,'axisEquation':['x=0','y=offset*cos(theta)','z=-offset*sin(theta)'],'offset':offset,'angleRange':[a0,a1]},'phases':rows,'finiteHousingDistances':distances,'minimumHousingDistance':min(x['distance'] for x in distances),'rigidYawQualification':'Same common-root rigid yaw preserves geometry distances and contact through all four facings. Independent visual coverage of all four remains separate.'}
(O/'active-mechanics.json').write_text(json.dumps(r,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['phases','finiteHousingDistances','continuousSeparatingPlanes']},indent=2))
