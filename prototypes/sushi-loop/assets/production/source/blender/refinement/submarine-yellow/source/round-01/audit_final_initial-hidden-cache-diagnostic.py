"""Saved-source geometry, inverse-neutral, envelope, hover and interface audit."""
import sys,runpy,itertools
sys.dont_write_bytecode=True
from pathlib import Path
globals().update(runpy.run_path(str(Path(__file__).parent/'native_common.py')))
from mathutils.bvhtree import BVHTree
F=runpy.run_path(str(H/'component_identity.py'));s,root,col=open_source();apply('upgraded-dock-ready')
components=json.loads(col['canonicalComponents']);meshes=[o for o in col.all_objects if o.type=='MESH'];cache={}
def cache_mesh(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();v=[p.co.copy() for p in me.vertices];f=[list(p.vertices) for p in me.polygons];e.to_mesh_clear();return v,f
for o in meshes:cache[o.name]=cache_mesh(o)
def geom(objs,hidden=False):
 pts=[];faces=[];per={}
 for o in objs:
  if o.type!='MESH' or (o.hide_render and not hidden):continue
  if o.name not in cache:cache[o.name]=cache_mesh(o)
  v,f=cache[o.name];p=[o.matrix_world@x for x in v];start=len(pts);pts+=p;faces += [[start+i for i in ff] for ff in f];per[o.name]=bounds(p)
 return pts,faces,per
# Re-extract at identity from actual saved assembly, compare signed resources and
# retain actual evaluated neutral points BEFORE remounting for motion invariance.
inverse=[];reference={}
for q in components:
 c=bpy.data.collections[q['collection']];cr=bpy.data.objects[q['root']];par=cr.parent;basis=cr.matrix_basis.copy();pinv=cr.matrix_parent_inverse.copy();cr.parent=None;cr.matrix_parent_inverse=Matrix.Identity(4);cr.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update()
 pref={'sub-hull-panels':('inputs/approved-equipment-preparation-v1/sub-hull-panels','candidates/round-01/neutral-resource-identity.json','panel_identity'),'sub-harpoon-mount':('inputs/approved-equipment-preparation-v1/sub-harpoon-mount','candidates/round-02/canonical-neutral-persistent-resources.json','harpoon_identity'),'sub-collector-inlet':('inputs/approved-canonical-equipment-v1/sub-collector-inlet','candidates/round-02/canonical-neutral-resources.json','collector_identity')}[q['asset']]
 signed=json.loads((R/'approved-inputs'/pref[0]/pref[1]).read_text());expected=signed if q['asset']=='sub-hull-panels' else signed['objects'] if q['asset']=='sub-harpoon-mount' else signed['records'];actual=F[pref[2]](c);assert actual==expected,q['asset']
 reference[q['asset']]={o.name:[o.matrix_world@p for p in cache[o.name][0]] for o in c.all_objects if o.type=='MESH'}
 cr.parent=par;cr.matrix_parent_inverse=pinv;cr.matrix_basis=basis;bpy.context.view_layer.update();inverse.append({'asset':q['asset'],'signedCanonicalResourceMatchAfterActualInverseExtraction':True,'neutralGeometrySHA256':hd({n:val(p) for n,p in reference[q['asset']].items()}),'rootMatrixBasis':val(cr.matrix_basis),'mountMatrix':val(par.matrix_local),'maximumMotionInverseVertexResidual':0})
# Exact finite contact-plane witnesses. Rectangular clipping measures actual
# planar polygon area within the frozen finite seat; no infinite plane proxy.
def clip_poly(p,axis,edge,greater):
 out=[]
 for a,b in zip(p,p[1:]+p[:1]):
  ia=(a[axis]>=edge if greater else a[axis]<=edge);ib=(b[axis]>=edge if greater else b[axis]<=edge)
  if ia:out.append(a)
  if ia!=ib:
   t=(edge-a[axis])/(b[axis]-a[axis]);out.append([a[j]+t*(b[j]-a[j]) for j in range(2)])
 return out
def area(p):return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1])))*.5 if p else 0
def plane_area(objs,axis,plane,rect):
 axes=[i for i in range(3) if i!=axis];total=0;witness=[]
 for o in objs:
  v,f=cache[o.name];p=[o.matrix_world@x for x in v]
  for face in f:
   if not all(abs(p[i][axis]-plane)<2e-6 for i in face):continue
   poly=[[p[i][a] for a in axes] for i in face]
   for k in range(2):poly=clip_poly(poly,k,rect[0][k],True) if poly else [];poly=clip_poly(poly,k,rect[1][k],False) if poly else []
   a=area(poly)
   if a>1e-10:total+=a;witness.append({'object':o.name,'area':a,'clippedPolygon':poly})
 return {'planeAxis':axis,'plane':plane,'finiteRectangle':rect,'summedActualCoplanarFaceAreaWithinSeat':total,'witnesses':witness}
contacts=[]
for q in components:
 objs=[bpy.data.objects[n] for n in q['meshNames']]
 if q['asset']=='sub-hull-panels':
  cc=[plane_area(objs,2,.65,[[x0,.028],[x1,.292]]) for x0,x1 in [(-.249,-.181),(.181,.249)]]
 elif q['asset']=='sub-harpoon-mount':cc=[plane_area(objs,2,.5685,[[.2695,-.1955],[.3505,-.0445]])]
 else:cc=[plane_area(objs,1,-.454,[[-.117,.1665],[.117,.2575]])]
 contacts.append({'asset':q['asset'],'finiteSeatContact':cc,'allSeatsHavePositiveMeasuredPlanarArea':all(c['summedActualCoplanarFaceAreaWithinSeat']>1e-6 for c in cc),'collectorIntentionalRearEngagement':'Rear bearing engages bracket; designed structural overlap is distinct from unrelated equipment clearance.' if q['asset']=='sub-collector-inlet' else None})
pts,ff,per=geom(meshes);mounts=json.loads((R/'proposed-mounts.json').read_text())['mounts'];reservation=[];gaps=[]
def sep(a,b):return max(max(a[0][i]-b[1][i],b[0][i]-a[1][i]) for i in range(3))
groups={'window':[o for o in meshes if any(k in o.name for k in ['port_flange','port_enamel','glass_gasket','convex_blue_glass','inner_gold_bead','port_fastener'])],'periscopeStatus':[o for o in meshes if 'periscope_' in o.name or 'status_' in o.name],'propeller':[o for o in meshes if 'propeller_' in o.name],'noseLamp':[o for o in meshes if 'nose_lamp_' in o.name or 'bumper_lamp' in o.name]}
partbounds={k:bounds(geom(o)[0]) for k,o in groups.items()};compbounds={}
for q in components:
 cr=bpy.data.objects[q['root']];p,_,_=geom([bpy.data.objects[n] for n in q['meshNames']]);local=[cr.matrix_world.inverted()@v for v in p];bb=bounds(local);cap=mounts[q['asset']]['localReservation'];bad=[i for i in range(3) if bb[0][i]<cap[0][i]-1e-6 or bb[1][i]>cap[1][i]+1e-6];compbounds[q['asset']]=bounds(p);reservation.append({'asset':q['asset'],'canonicalNeutralBounds':bb,'frozenReservation':cap,'violatingAxes':bad,'integratedBounds':bounds(p)});assert not bad
 # Split hull panels use actual side subsets to avoid false center-bridge AABBs.
 subsets=[p] if q['asset']!='sub-hull-panels' else [[v for v in p if v.x<0],[v for v in p if v.x>0]]
 gaps.append({'asset':q['asset'],'separatingAxisGapsByActualPart':[{'bounds':bounds(pp),'gaps':{k:sep(bounds(pp),b) for k,b in partbounds.items()}} for pp in subsets]})
for a,b in itertools.combinations(compbounds,2):gaps.append({'pair':[a,b],'separatingAxisGap':sep(compbounds[a],compbounds[b])})
# Geometry cache is permissible only for fixed mesh/modifier data. All actual
# motion owners act on transforms/visibility; no mesh/shape/material drivers.
static={'noShapeKeys':all(not o.data.shape_keys for o in meshes),'noMeshAnimation':all(not o.data.animation_data for o in meshes),'noAnimatedMaterialNodes':all(not m.animation_data and not m.node_tree.animation_data for o in meshes for m in o.data.materials),'noGeometryModifierAnimationChannels':all(not any('modifiers' in fc.data_path for a in bpy.data.actions for l in a.layers for st in l.strips for bag in st.channelbags for fc in bag.fcurves) for o in meshes)}
assert all(static.values()),static
phases=[];closures=[];viol=[]
for clip in json.loads(root['nativeActions']):
 for d,ang in DIRS.items():
  first=None
  for j in range(25):
   frame=1+j*.5;apply(clip,frame,d);p,_,parts=geom(meshes);canonical=[Matrix.Rotation(-ang,3,'Z')@v for v in p];bb=bounds(canonical);cap=.56 if 'dock-' in clip else .61;bad=bb[0][0]<-cap-1e-6 or bb[1][0]>cap+1e-6 or bb[0][1]<-.64-1e-6 or bb[1][1]>.68+1e-6 or bb[0][2]<.01-1e-6 or bb[1][2]>1.12+1e-6
   if bad:viol.append({'clip':clip,'direction':d,'frame':frame,'bounds':bb})
   lamp=bpy.data.objects['body__status_cyan_lens'];phases.append({'clip':clip,'direction':d,'frame':frame,'kind':'runtime' if j%2==0 and j<24 else 'closure' if j==24 else 'half','canonicalBounds':bb,'rootMatrix':val(root.matrix_world),'motionLocal':val(bpy.data.objects['submarine-yellow__body_motion'].matrix_local),'statusVisible':not lamp.hide_render,'statusScale':val(lamp.scale),'visibleMeshNames':sorted(parts)})
   # All exact-neutral component points follow body/mount rigid transforms.
   for inv,q in zip(inverse,components):
    cr=bpy.data.objects[q['root']];m=cr.matrix_world.inverted();er=0
    for n,expected in reference[q['asset']].items():
     ob=bpy.data.objects[n];local=[m@(ob.matrix_world@v) for v in cache[n][0]];er=max(er,max((a-b).length for a,b in zip(local,expected)))
    inv['maximumMotionInverseVertexResidual']=max(inv['maximumMotionInverseVertexResidual'],er)
   if j==0:first=p
   if j==24:closures.append({'clip':clip,'direction':d,'loop':not clip.endswith('impact'),'vertexCountSame':len(first)==len(p),'maximumEndpointVertexDelta':max((a-b).length for a,b in zip(first,p))})
  print('AUDIT',clip,d,flush=True)
save(O/'native-phase-audit.json',{'sourceSHA256':sha(H/'project.blend'),'phases':phases,'closures':closures,'violations':viol,'staticResourceCacheProof':static})
save(O/'native-interface-audit.json',{'sourceSHA256':sha(H/'project.blend'),'inverseNeutralIdentity':inverse,'contacts':contacts,'reservations':reservation,'clearances':gaps,'protectedBodyPartBounds':partbounds,'legacyReferences':{n:val(bpy.data.objects[n].location) for n in ['sub_harpoon','sub_collector']},'derivedNativeMouths':{o.name:{'local':val(o.location),'worldCanonicalS':None} for q in components for o in bpy.data.collections[q['collection']].all_objects if o.type=='EMPTY' and ('mouth' in o.name or 'muzzle' in o.name)}})
# Exact accepted support meshes, including nail apices and bevels.
companions={}
for key,file,cn,loc in [('floor','dock-floor-round-04.blend','WarmSoft_dock-floor',(0,0,0)),('hut','workshop-hut-round-01.blend','WarmSoft_workshop-hut',(.78,.35,.23))]:
 with bpy.data.libraries.load(str(R/file),link=False) as(src,dst):dst.collections=[cn]
 c=dst.collections[0];s.collection.children.link(c);c.hide_render=False;c.hide_viewport=False;rr=next(o for o in c.all_objects if o.type=='EMPTY' and o.parent is None);rr.location=loc;rr.rotation_euler=(0,0,0);bpy.context.view_layer.update();p,f,_=geom(c.all_objects);companions[key]={'points':p,'faces':f,'bounds':bounds(p),'bvh':BVHTree.FromPolygons(p,f,all_triangles=False),'sha256':sha(R/file)}
floor=companions['floor'];fb=floor['bvh'];hover=[];hut=[]
for clip in json.loads(root['nativeActions']):
 for d in DIRS:
  for j in range(25):
   frame=1+j*.5;apply(clip,frame,d,(-.70,-.42,.23));p,f,_=geom(meshes);bb=bounds(p);hut.append({'clip':clip,'direction':d,'frame':frame,'conservativeXGap':companions['hut']['bounds'][0][0]-bb[1][0]})
   if 'dock-' not in clip:continue
   sub=BVHTree.FromPolygons(p,f,all_triangles=False);gs=[];zs=[];nr=0
   for q in floor['points']:
    if not (bb[0][0]-1e-6<=q.x<=bb[1][0]+1e-6 and bb[0][1]-1e-6<=q.y<=bb[1][1]+1e-6):continue
    top,_,_,_=fb.ray_cast(Vector((q.x,q.y,2)),Vector((0,0,-1)),3)
    if top is None or abs(top.z-q.z)>1e-5:continue
    hit,_,_,_=sub.ray_cast(q+Vector((0,0,1e-6)),Vector((0,0,1)),2);nr+=1
    if hit is not None:gs.append((hit.z-q.z,val(hit),val(q),'actual-deck-vertex-up'));zs.append(q.z)
   for q in p:
    if q.z>.35:continue
    hit,_,_,_=fb.ray_cast(q+Vector((0,0,1e-7)),Vector((0,0,-1)),2);nr+=1
    if hit is not None:gs.append((q.z-hit.z,val(q),val(hit),'actual-underside-vertex-down'));zs.append(hit.z)
   g=min(gs);hover.append({'clip':clip,'direction':d,'frame':frame,'minimumVerticalGap':g[0],'underside':g[1],'deck':g[2],'witness':g[3],'supportSurfaceZRange':[min(zs),max(zs)],'bidirectionalRays':nr})
save(O/'native-hover-audit.json',{'sourceSHA256':sha(H/'project.blend'),'acceptedDockManifestSHA256':sha(R/'accepted-dock-manifest.json'),'fixedRoot':[-.70,-.42,.23],'allFourDirection400DockPhaseRecords':hover,'minimumGap':min(q['minimumVerticalGap'] for q in hover),'maximumGap':max(q['minimumVerticalGap'] for q in hover),'allInsideRequiredGap':all(.02<=q['minimumVerticalGap']<=.09 for q in hover),'hutAll1200PhaseRecords':hut,'minimumConservativeHutXGap':min(q['conservativeXGap'] for q in hut),'supportSources':{k:{'sha256':v['sha256'],'bounds':v['bounds']} for k,v in companions.items()},'method':'Actual evaluated frozen native meshes and exact accepted deck meshes cached in object-local coordinates; all changing matrices applied from saved actions. Bidirectional BVH rays from every actual top deck vertex including nail apices and low underside vertex, no support-plane proxy. Floor/hut fixed; all4 main rotations at fixed stated mainroot. Cover remains unapproved.'})
print('FINAL_AUDIT',len(phases),'violations',len(viol),'inverse',inverse,'contacts',[(q['asset'],q['allSeatsHavePositiveMeasuredPlanarArea']) for q in contacts],flush=True)
