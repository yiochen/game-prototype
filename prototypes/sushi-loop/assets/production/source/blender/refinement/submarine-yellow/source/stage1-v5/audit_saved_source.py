"""Independent replay of saved stage1 bytes; no .blend writes, no final batch."""
import bpy,json,math,hashlib,itertools
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent;OBJ=HERE.parents[1];OUT=OBJ/'candidates/stage1-v5';RES=HERE/'resources'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):Path(p).write_text(json.dumps(d,indent=2,default=str)+'\n')
def vv(v):return [round(float(x),9) for x in v]
def bounds(v):return [[min(p[i] for p in v) for i in range(len(v[0]))],[max(p[i] for p in v) for i in range(len(v[0]))]]
bpy.ops.wm.open_mainfile(filepath=str(HERE/'submarine-stage1.blend'));sc=bpy.context.scene;col=bpy.data.collections['WarmSoft_submarine-yellow_stage1'];root=bpy.data.objects['submarine-yellow__root'];motion=bpy.data.objects['submarine-yellow__body_motion'];lamp=bpy.data.objects['body__status_cyan_lens'];cam=sc.camera
meshes=[o for o in col.all_objects if o.type=='MESH'];actions=json.loads(root['nativeActions']);dirs={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def apply(clip,frame):
 for owner,aname in actions[clip].items():
  o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[aname];o.animation_data.action=a
  if a.slots:o.animation_data.action_slot=a.slots[0]
 sc.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
def geom(objs):
 dg=bpy.context.evaluated_depsgraph_get();pts=[];faces=[];per={}
 for o in objs:
  if o.type!='MESH' or o.hide_render:continue
  e=o.evaluated_get(dg);me=e.to_mesh();op=[e.matrix_world@v.co for v in me.vertices];start=len(pts);pts+=op;faces += [[start+i for i in p.vertices] for p in me.polygons];per[o.name]=bounds(op);e.to_mesh_clear()
 return pts,faces,per
# Independently reload actual saved actions. Half frames follow piecewise linear keys.
phases=[];loop=[];viol=[];nativeactions=[]
for clip,owners in actions.items():
 for owner,name in owners.items():
  a=bpy.data.actions[name];channels=[]
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:channels.append({'dataPath':fc.data_path,'index':fc.array_index,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in fc.keyframe_points]})
  nativeactions.append({'clip':clip,'owner':owner,'action':name,'channels':channels})
 for d,ang in dirs.items():
  root.rotation_euler.z=ang;root.location=(0,0,0);inv=Matrix.Rotation(-ang,3,'Z');first=None
  for j in range(25):
   f=1+j*.5;apply(clip,f);pts,ff,per=geom(meshes);cp=[inv@p for p in pts];b=bounds(cp);cap=.56 if 'dock-' in clip else .61
   v=b[0][0]<-cap-1e-6 or b[1][0]>cap+1e-6 or b[0][1]<-.64-1e-6 or b[1][1]>.68+1e-6 or b[0][2]<.01-1e-6 or b[1][2]>1.12+1e-6
   if v:viol.append({'clip':clip,'direction':d,'frame':f,'bounds':b})
   phases.append({'clip':clip,'direction':d,'frame':f,'phase':'runtime' if j%2==0 and j<24 else 'closure' if j==24 else 'half','canonicalBounds':b,'rootMatrix':[vv(r) for r in root.matrix_world],'motionLocal':[vv(r) for r in motion.matrix_local],'statusVisible':not lamp.hide_render,'statusScale':vv(lamp.scale),'visibleMeshNames':list(per)})
   if j==0:first=[p.copy() for p in pts]
   if j==24:loop.append({'clip':clip,'direction':d,'loop':not clip.endswith('impact'),'maxVertexEndpointDelta':max((a-b).length for a,b in zip(first,pts)),'vertexCountSame':len(first)==len(pts)})
dump(OUT/'saved-action-phases.json',{'sourceSHA256':sha(HERE/'submarine-stage1.blend'),'phases':phases,'closures':loop,'violations':viol});dump(OUT/'saved-native-actions.json',nativeactions)
sourceclosure={'images':[{'name':i.name,'source':i.source,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries],'meshCount':len(meshes),'actionCount':len(nativeactions),'meshData':[{'name':o.name,'mesh':o.data.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'uvLayers':[u.name for u in o.data.uv_layers],'materialSlots':[m.name for m in o.data.materials],'modifiers':[m.type for m in o.modifiers]} for o in meshes]}
# Physical projected/native reservations and explicit contact/clearance accounting.
mounts=json.loads((OUT/'proposed-mounts.json').read_text())['mounts'];root.location=(0,0,0);root.rotation_euler.z=0;apply('upgraded-dock-ready',1);pts,ff,per=geom(meshes)
clearances={}
window=[bpy.data.objects[n] for n in per if any(k in n for k in ['port_flange','port_enamel','glass_gasket','convex_blue_glass','inner_gold_bead','port_fastener'])]
windowbb=bounds(geom(window)[0]);periscopebb=bounds(geom([bpy.data.objects[n] for n in per if 'periscope_' in n or 'status_' in n])[0]);propbb=bounds(geom([bpy.data.objects[n] for n in per if 'propeller_' in n])[0]);nosebb=bounds(geom([bpy.data.objects[n] for n in per if 'nose_lamp_' in n or 'bumper_lamp' in n])[0])
def corners(b):return [Vector(p) for p in itertools.product(*[(b[0][i],b[1][i]) for i in range(3)])]
for name,m in mounts.items():
 T=Matrix(m['matrixLocal']);boxworld=bounds([T@v for v in corners(m['localReservation'])]);m['integratedReservation']=boxworld
 cn=[o for o in meshes if o.name.startswith('PROVISIONAL__') and any(p.name==m['object'] for p in [o.parent,o.parent.parent if o.parent else None] if p)]
 pp,pf,pbounds=geom(cn);inv=T.inverted();m['provisionalLocalActualBounds']=bounds([inv@v for v in pp]);m['provisionalIntegratedActualBounds']=bounds(pp);m['provisionalMeshNames']=list(pbounds)
 m['provisionalReservationViolations']=[o for o in [i for i in range(3)] if m['provisionalLocalActualBounds'][0][o]<m['localReservation'][0][o]-1e-6 or m['provisionalLocalActualBounds'][1][o]>m['localReservation'][1][o]+1e-6]
 # Useful separating-axis gaps. A positive axis gap proves no geometry contact.
 def sep(a,b):return max(max(a[0][i]-b[1][i],b[0][i]-a[1][i]) for i in range(3))
 clearances[name]={'windowAxisGap':sep(boxworld,windowbb),'periscopeAxisGap':sep(boxworld,periscopebb),'propellerAxisGap':sep(boxworld,propbb),'noseLampAxisGap':sep(boxworld,nosebb),'note':'Positive disjoint axis proves separation. Negative AABB gaps for split panels require actual two-side regions below, not a collision assertion.'}
 if name=='sub-hull-panels':
  regs=[]
  for xs in [(-.52,-.34),(.34,.52)]:
   b=[(xs[0],-.30,0),(xs[1],.30,.16)];w=bounds([T@v for v in corners(b)]);regs.append({'local':b,'world':w,'windowGap':sep(w,windowbb),'periscopeGap':sep(w,periscopebb),'propellerGap':sep(w,propbb)})
  m['splitOccupiedReservations']=regs
# Contact points match actual evaluated named BODY seats, not legacy references.
seats={n:per[n] for n in per if 'contact_seat' in n or 'connected_pedestal' in n}
# Exact original standalone native source mesh proportions, registered camera distinct.
original={}
for aid,needle in [('sub-hull-panels','hull_panel'),('sub-harpoon-mount','harpoon_mount'),('sub-collector-inlet','collector_inlet')]:
 with bpy.data.libraries.load(str(RES/'original-library.blend'),link=False) as(src,dst):
  matches=[n for n in src.collections if needle in n.lower()];dst.collections=matches[:1]
 if not dst.collections:raise RuntimeError('Missing original component '+aid)
 c=dst.collections[0];sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False;r=next(o for o in c.all_objects if o.type=='EMPTY' and o.parent is None);r.location=(0,0,0);r.rotation_euler=(0,0,0)
 for o in c.all_objects:o.hide_render=False;o.hide_viewport=False
 bpy.context.view_layer.update();op,of,ops=geom(c.all_objects);original[aid]={'collection':c.name,'points':op,'bounds':bounds(op),'meshNames':list(ops)};c.hide_render=True
# Exact logical registered square camera basis; verify against supplied camera record.
# X128,Y-128,Z-89.6. Native2 published frame384x704, logical192x352/root96,248.
projection=[]
for aid,m in mounts.items():
 camera=json.loads((RES/(aid+'-camera.json')).read_text());asset=json.loads((RES/(aid+'-asset.json')).read_text());o=original[aid]
 actual=[]
 for name in m['provisionalMeshNames']:
  eo=bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh();actual.extend([Matrix(m['matrixLocal']).inverted()@(eo.matrix_world@v.co) for v in me.vertices]);eo.to_mesh_clear()
 basis={'X':camera['calibration']['unitX'][0]/camera['captureScale'],'Y':-camera['calibration']['unitDepth'][1]/camera['captureScale'],'Z':camera['calibration']['unitHeight'][1]/camera['captureScale']}
 pv={'originalSourceMesh':o['points'],'provisionalMesh':actual,'proposedReservationBox':corners(m['localReservation'])}
 values=[]
 for d,ang in dirs.items():
  R=Matrix.Rotation(ang,3,'Z')
  for kind,pts in pv.items():
   pp=[R@p for p in pts];xy=[(96+basis['X']*p.x,248+basis['Y']*p.y+basis['Z']*p.z) for p in pp];b=bounds(xy);values.append({'direction':d,'kind':kind,'logicalBounds':b,'logicalOccupiedSize':[b[1][i]-b[0][i] for i in range(2)],'insideFixedLogicalFrame':b[0][0]>=0 and b[1][0]<=192 and b[0][1]>=0 and b[1][1]<=352,'marginLogicalPixels':[b[0][0],192-b[1][0],b[0][1],352-b[1][1]]})
 projection.append({'asset':aid,'registrationIsUnchanged':True,'logicalFrame':[192,352],'logicalRoot':[96,248],'publishedNativeFrame':[384,704],'publishedSourceScale':2,'historicalSourceCameraCaptureScale':camera['captureScale'],'sourceCameraMatrix':camera['camera']['worldMatrix'],'sourcePixelAspect':camera['camera']['pixelAspect'],'logicalUnitBasis':{'X':[basis['X'],0],'Y':[0,basis['Y']],'Z':[0,basis['Z']]},'footprint':asset['footprint'],'nominalFunctionalHeight':asset['height'],'ownIdleActiveContract':asset['clips'],'sourceNativeMeshExtrema':o['bounds'],'provisionalNativeMeshExtrema':m['provisionalLocalActualBounds'],'reservationMeshCaps':m['localReservation'],'uniformIntegrationMatrix':m['matrixLocal'],'registrationVsMesh':'Frame/root/camera/pixelaspect/footprint/nominalheight/timing retained; redesigned mesh extrema are proposals, not metadata/root/camera resizing. Projection box is conservative envelope, actual provisional mesh is separately measured.','projection':values})
dump(OUT/'component-projection-feasibility.json',{'sourceSHA256':sha(HERE/'submarine-stage1.blend'),'originalSourceSHA256':sha(RES/'original-library.blend'),'projectionDifference':'Main65degree square pixels versus standalone55.00798degree pixelaspect1.22065556. Same physical geometry never implies identical raster pixels. No views fit individually.','components':projection,'tradeoffs':['Harpoon: .35uniform with shifted native frame centers the redesigned weapon inside every locked standalone facing. Proposed localXwidth .36 versus original .50base; narrower body attachment base is a disclosed native redesign, not an original-scale preservation claim. Overall cannon length remains readable; future independent component judges must assess actual art.','Hull panels become a matched pair of side armor pieces under a single standalone entry. New wider pair envelope retains all registered capture/nominal gameplay metadata.','Collector uses .4uniform to keep a useful standalone mouth while maintaining compact integrated clearance below the headlight.','All transforms stay PROPOSED until root freezes this source/mount handoff; no canonical component has been built or approved.']})
equipmentGaps={}
for a,b in itertools.combinations(mounts,2):
 x=mounts[a]['integratedReservation'];y=mounts[b]['integratedReservation'];equipmentGaps[a+'__'+b]=max(max(x[0][i]-y[1][i],y[0][i]-x[1][i]) for i in range(3))
dump(OUT/'mount-clearances.json',{'sourceSHA256':sha(HERE/'submarine-stage1.blend'),'mounts':mounts,'evaluatedBodyContactSeats':seats,'otherEquipmentSeparatingAxisGaps':equipmentGaps,'windowBounds':windowbb,'periscopeBounds':periscopebb,'propellerBounds':propbb,'noseLampBounds':nosebb,'separatingAxisClearances':clearances,'legacyDeclaredReferences':{k:vv(bpy.data.objects[k].location) for k in ['sub_harpoon','sub_collector']},'expectedStructuralContacts':'Equipment bases seat on named BODY pads/collectorrearbracket; intentional structural body/seat intersection is not an all-equipment airgap. Window/periscope/propeller and unrelated equipment must remain separated.'})
# Exact paired support geometry, now bidirectional ray sampling includes nail apices
# under solid undersides, not just submarine vertices that could miss a fixing.
companions={}
for key,file,colname,loc in [('floor','dock-floor-round-04.blend','WarmSoft_dock-floor',(0,0,0)),('hut','workshop-hut-round-01.blend','WarmSoft_workshop-hut',(.78,.35,.23))]:
 with bpy.data.libraries.load(str(RES/file),link=False) as(src,dst):
  if colname not in src.collections:colname=next(n for n in src.collections if key in n.lower())
  dst.collections=[colname]
 c=dst.collections[0];sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False;r=next(o for o in c.all_objects if o.type=='EMPTY' and o.parent is None);r.location=loc;r.rotation_euler=(0,0,0);bpy.context.view_layer.update();p,f,parts=geom(c.all_objects);companions[key]={'col':c,'root':r,'points':p,'faces':f,'bvh':BVHTree.FromPolygons(p,f,all_triangles=False),'sha256':sha(RES/file),'bounds':bounds(p)}
floor=companions['floor'];fb=floor['bvh'];root.location=(-.70,-.42,.23);root.rotation_euler.z=0
hover=[];hut=[]
for clip in actions:
 for j in range(25):
  apply(clip,1+j*.5);p,f,parts=geom(meshes);b=bounds(p);hut.append({'clip':clip,'frame':1+j*.5,'minXSeparation':companions['hut']['bounds'][0][0]-b[1][0]})
  if 'dock-' not in clip:continue
  sub=BVHTree.FromPolygons(p,f,all_triangles=False);gaps=[];supportz=[];nrays=0
  # Every floor vertex in projected occupied low solid bbox, including domed nails.
  for q in floor['points']:
   if not (b[0][0]-1e-6<=q.x<=b[1][0]+1e-6 and b[0][1]-1e-6<=q.y<=b[1][1]+1e-6):continue
   top,n,fi,dist=fb.ray_cast(Vector((q.x,q.y,2)),Vector((0,0,-1)),3)
   if top is None or abs(top.z-q.z)>1e-5:continue
   hit,n,fi,dist=sub.ray_cast(q+Vector((0,0,1e-6)),Vector((0,0,1)),2);nrays+=1
   if hit is not None:gaps.append((hit.z-q.z,list(hit),list(q),'deckvertex-up'));supportz.append(q.z)
  for q in p:
   if q.z>.35:continue
   hit,n,fi,dist=fb.ray_cast(q+Vector((0,0,1e-7)),Vector((0,0,-1)),2);nrays+=1
   if hit is not None:gaps.append((q.z-hit.z,list(q),list(hit),'undersidevertex-down'));supportz.append(hit.z)
  g=min(gaps,key=lambda x:x[0]);hover.append({'clip':clip,'frame':1+j*.5,'minimumVerticalGap':g[0],'undersidePoint':g[1],'deckPoint':g[2],'witness':g[3],'supportSurfaceZRange':[min(supportz),max(supportz)],'bidirectionalSupportRayCount':nrays})
summary={'sourceSHA256':sha(HERE/'submarine-stage1.blend'),'savedSourceReplayed':True,'runtimePhases':sum(p['phase']=='runtime' for p in phases),'halfPhases':sum(p['phase']=='half' for p in phases),'closurePhases':sum(p['phase']=='closure' for p in phases),'envelopeViolations':viol,'allLoopClosuresMaximumVertexDelta':max(r['maxVertexEndpointDelta'] for r in loop if r['loop']),'hover':{'minimum':min(h['minimumVerticalGap'] for h in hover),'maximum':max(h['minimumVerticalGap'] for h in hover),'records':hover,'method':'Actual saved native action evaluation at each runtime,half,closure, bidirectional support rays from actual low submarine vertices and top deck vertices (including all nailapices) within occupied XY. Both evaluated full meshes/BVH, exactfixed root[-.70,-.42,.23]. Reported support Z range measured; no broadplane proxy.'},'hut':{'minimumConservativeXGap':min(h['minXSeparation'] for h in hut),'all300Records':hut,'sourceSHA256':companions['hut']['sha256']},'sourceClosure':sourceclosure,'resourcesArePackedOrNative':not any(i.get('filepath') and not i.get('packed') for i in sourceclosure['images']) and not sourceclosure['libraries'],'originalSourceComponentCollections':{k:{j:v for j,v in o.items() if j!='points'} for k,o in original.items()},'representativeRendersOnly':'12 native representative body/provisional/family renders; no full576frame render run or finalapproval.'}
dump(OUT/'saved-source-audit.json',summary)
print('SAVED_SOURCE_AUDIT',json.dumps({k:summary[k] for k in ['sourceSHA256','runtimePhases','halfPhases','closurePhases','envelopeViolations','allLoopClosuresMaximumVertexDelta','resourcesArePackedOrNative']}));print('HOVER',summary['hover']['minimum'],summary['hover']['maximum'],'HUT',summary['hut']['minimumConservativeXGap']);print('RESERVATIONS',[(k,m['provisionalReservationViolations']) for k,m in mounts.items()])
