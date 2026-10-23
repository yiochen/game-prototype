"""Evaluated guard/housing sweep plus exact continuous separating-surface proof."""
import bpy,pathlib,json,math,sys,importlib.util
sys.dont_write_bytecode=True
from mathutils import Vector
H=pathlib.Path(__file__).resolve().parent;E=H.parent;O=E/'candidates/round-02'
sp=importlib.util.spec_from_file_location('round02_native_audit_tools',H/'assemble-audit-02.py');T=importlib.util.module_from_spec(sp);sp.loader.exec_module(T);A=T.A
bpy.ops.wm.open_mainfile(filepath=str(H/'round-02.blend'));s=bpy.context.scene;col=bpy.data.collections['REFINED__sub-collector-inlet'];guard=bpy.data.objects['collector__guard_rock'];root=bpy.data.objects['collector__root']
A.apply_clip(s,col,'idle','S',1);dg=bpy.context.evaluated_depsgraph_get();moving=[o for o in col.all_objects if o.type=='MESH' and o.parent==guard];hinge=bpy.data.objects['collector__lower_guard_shaft'];fixed=[o for o in col.all_objects if o.type=='MESH' and o not in moving and o!=hinge]
local={o.name:[guard.matrix_world.inverted()@p for p in T.evaluated(o,dg)[0]] for o in moving};pivot=guard.location.copy();angles=[]
for f in range(1,14):A.apply_clip(s,col,'active','S',f);angles.append(float(guard.rotation_euler.x))
amin,amax=min(angles),max(angles)
def extrema(a,b):
 ts=[amin,amax];q=math.atan2(b,a)
 for n in range(-3,4):
  t=q+n*math.pi
  if amin<=t<=amax:ts.append(t)
 return [a*math.cos(t)+b*math.sin(t) for t in ts]
continuous=[]
for pts in local.values():
 for p in pts:
  yy=extrema(p.y,-p.z);zz=extrema(p.z,p.y)
  continuous.extend([Vector((pivot.x+p.x,pivot.y+min(yy),pivot.z+min(zz))),Vector((pivot.x+p.x,pivot.y+max(yy),pivot.z+max(zz)))])
guardBound=A.bounds(continuous);fixedPoints={o.name:[] for o in fixed};phases=[];distanceRecords=[];maxIntersections=0
for step in range(49):
 frame=1+step/4;A.apply_clip(s,col,'active','S',int(frame));s.frame_set(math.floor(frame),subframe=frame-math.floor(frame));bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();gt,_=T.tree(moving,dg);allg=[];guardTris=[]
 for o in moving:
  vs,ts,_=T.evaluated(o,dg);allg+=vs;guardTris+=ts
 contacts=[]
 for o in fixed:
  vs,ts,fs=T.evaluated(o,dg);fixedPoints[o.name]+=vs;ot,_=T.tree([o],dg);pairs=gt.overlap(ot)
  if pairs:contacts.append({'object':o.name,'surfacePairs':len(pairs)})
 maxIntersections=max(maxIntersections,sum(c['surfacePairs'] for c in contacts));ht,_=T.tree([hinge],dg)
 phases.append({'nativeFrame':frame,'guardRotationX':float(guard.rotation_euler.x),'guardBounds':A.bounds(allg),'housingSurfaceIntersections':contacts,'designedLowerShaftContactSurfacePairs':len(gt.overlap(ht)),'rootMatrix':[list(r) for r in root.matrix_world]})
 if step%2==0:
  for name in ['collector__mouth_surround','collector__hollow_enamel_shell','collector__dark_mouth']:
   vs,ts,_=T.evaluated(bpy.data.objects[name],dg);r=T.finite_distance(guardTris,ts);r.update(nativeFrame=frame,obstacle=name);distanceRecords.append(r)
separations=[]
for name,pts in fixedPoints.items():
 b=A.bounds(pts);opts=[]
 for i,axis in enumerate('XYZ'):
  opts.extend([{'axis':axis,'guardBeforeObstacle':True,'distance':b[0][i]-guardBound[1][i]},{'axis':axis,'guardBeforeObstacle':False,'distance':guardBound[0][i]-b[1][i]}])
 best=max(opts,key=lambda x:x['distance']);separations.append({'obstacle':name,'evaluatedActiveBounds':b,'continuousSeparatingPlaneLowerBound':best,'positiveSeparation':best['distance']>0})
report={'asset':'sub-collector-inlet','round':'round-02','source':'source/round-02.blend','sourceSHA256':A.sha(H/'round-02.blend'),'method':'Evaluate all runtime keys, closing13 and every quarterframe. BVH checks actual evaluated moving cage/bars against every nonhinge native mesh. Exact finite triangle distances against mouth surround, cyan shell and dark mouth at every half-frame. Separately, analytic extrema of every moving native vertex over full angle interval establish continuous bounds and positive separating planes from every nonhinge mesh; fixed/pulsing pieces have unchanged X/Y and native linear scaleZ, whose extrema occur at source keys.','guardAngleRangeRadians':[amin,amax],'unchangedFixedHingePivot':list(pivot),'movingParts':[o.name for o in moving],'designedHinge':{'object':hinge.name,'qualification':'Unchanged cross-shaft is the intentional rotational hinge inside the connected cage bottom rail. Its designed contact is listed separately, never used to waive a housing collision.'},'continuousGuardBounds':guardBound,'continuousNonhingeSeparation':separations,'allContinuousSeparatingPlanesPositive':all(x['positiveSeparation'] for x in separations),'phaseRecords':phases,'exactFiniteDistanceRecords':distanceRecords,'maximumNonhingeSurfaceIntersections':maxIntersections,'minimumMeasuredHousingFiniteDistance':min(x['minimumFiniteSurfaceDistance'] for x in distanceRecords),'facingCoverage':'Finite sweep is measured in canonicalS. All standalone facings apply the same rigid common-root yaw to all native surfaces, preserving the measured distances/intersections; all four native key/half-frame view exports are provided. No per-view movement or fitting.','neutralReservationAndMainSeat':'Neutral source geometry/transforms unchanged; verified independently in neutral round01/round02 identity and native assembly audit. No active-main mapping.','approval':False}
A.savej(O/'moving-part-clearance.json',report)
print(json.dumps({'phaseCount':len(phases),'finiteDistanceCount':len(distanceRecords),'maxSurfacePairs':maxIntersections,'allContinuousPlanesPositive':report['allContinuousSeparatingPlanesPositive'],'minFiniteDistance':report['minimumMeasuredHousingFiniteDistance'],'separatingPlanes':[{'object':r['obstacle'],**r['continuousSeparatingPlaneLowerBound']} for r in separations]},indent=2))
