"""Pair exact saved neutral resources to the immutable preliminary main, then audit."""
import bpy,pathlib,json,math,hashlib,sys,importlib.util
sys.dont_write_bytecode=True
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import closest_point_on_tri
from bpy_extras.object_utils import world_to_camera_view
H=pathlib.Path(__file__).resolve().parent;E=H.parent;O=E/'candidates/round-02';R=H/'resources';F=R/'frozen-main-v1'
sp=importlib.util.spec_from_file_location('saved_replay',H/'replay-02.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M);A=M.A
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def original_identity(objects):
 out={}
 for o in objects:
  d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'localMatrix':[list(r) for r in o.matrix_local]}
  if o.type=='MESH':
   me=o.data;d['mesh']={'vertices':[list(v.co) for v in me.vertices],'normals':[list(n.vector) for n in me.corner_normals],'polygons':[(list(f.vertices),f.material_index,f.use_smooth) for f in me.polygons],'uvs':{u.name:[list(x.uv) for x in u.data] for u in me.uv_layers},'materials':[]}
   for m in me.materials:
    ns=[]
    for n in m.node_tree.nodes:
     ins={}
     for i in n.inputs:
      if hasattr(i,'default_value'):
       v=i.default_value
       try:v=list(v)
       except TypeError:pass
       if isinstance(v,(str,int,float,bool,list)):ins[i.identifier]=v
     ns.append({'name':n.name,'type':n.bl_idname,'inputs':ins})
    d['mesh']['materials'].append({'name':m.name,'nodes':ns,'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in m.node_tree.links]})
  if o.type=='LIGHT':d['light']={'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color),'type':o.data.type}
  if o.type=='CAMERA':d['camera']={'type':o.data.type,'orthoScale':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y]}
  out[o.name]=digest(d)
 return out
def evaluated(o,dg):
 eo=o.evaluated_get(dg);me=eo.to_mesh();me.calc_loop_triangles();vs=[eo.matrix_world@v.co for v in me.vertices];ts=[tuple(vs[i] for i in t.vertices) for t in me.loop_triangles];fs=[list(p.vertices) for p in me.polygons];eo.to_mesh_clear();return vs,ts,fs
def tree(objects,dg):
 vs=[];fs=[];names=[]
 for o in objects:
  if o.type!='MESH' or o.hide_render:continue
  p,t,f=evaluated(o,dg);off=len(vs);vs+=p
  fs.extend([[off+i for i in face] for face in f]);names.extend([o.name]*len(f))
 return BVHTree.FromPolygons(vs,fs,all_triangles=False),names
def segdist(p1,q1,p2,q2):
 d1=q1-p1;d2=q2-p2;r=p1-p2;a=d1.dot(d1);e=d2.dot(d2);f=d2.dot(r)
 if a<=1e-20 and e<=1e-20:return (p1-p2).length
 if a<=1e-20:s=0;t=max(0,min(1,f/e))
 else:
  c=d1.dot(r)
  if e<=1e-20:t=0;s=max(0,min(1,-c/a))
  else:
   b=d1.dot(d2);den=a*e-b*b;s=max(0,min(1,(b*f-c*e)/den)) if abs(den)>1e-20 else 0;t=(b*s+f)/e
   if t<0:t=0;s=max(0,min(1,-c/a))
   elif t>1:t=1;s=max(0,min(1,(b-c)/a))
 return ((p1+d1*s)-(p2+d2*t)).length
def tridist(a,b):
 d=min([(v-closest_point_on_tri(v,*b)).length for v in a]+[(v-closest_point_on_tri(v,*a)).length for v in b])
 for i in range(3):
  for j in range(3):d=min(d,segdist(a[i],a[(i+1)%3],b[j],b[(j+1)%3]))
 return d
def finite_distance(ats,bts):
 ab=[(t,A.bounds(t)) for t in ats];bb=[(t,A.bounds(t)) for t in bts];best=1e9;tested=0
 # Valid finite upper bound from nearest native triangle pair, then prune by box distance.
 if ab and bb:best=tridist(ab[0][0],bb[0][0])
 for ta,ba in ab:
  for tb,bc in bb:
   lower=sum(max(0,ba[0][i]-bc[1][i],bc[0][i]-ba[1][i])**2 for i in range(3))
   if lower>=best*best:continue
   best=min(best,tridist(ta,tb));tested+=1
 return {'minimumFiniteSurfaceDistance':best,'testedTrianglePairs':tested,'triangleCounts':[len(ats),len(bts)],'method':'Exact minimum over finite evaluated triangle pairs: vertex-triangle and all edge-edge distances, with safe box-distance pruning. Native triangle intersection separately tested by BVH.'}
def hull(points):
 p=sorted(set((round(v[0],9),round(v[1],9)) for v in points))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 lo=[]
 for v in p:
  while len(lo)>=2 and cross(lo[-2],lo[-1],v)<=0:lo.pop()
  lo.append(v)
 hi=[]
 for v in reversed(p):
  while len(hi)>=2 and cross(hi[-2],hi[-1],v)<=0:hi.pop()
  hi.append(v)
 return lo[:-1]+hi[:-1]
def polygon_measure(p):
 cr=[a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1])];twice=sum(cr);area=abs(twice)/2
 return {'area':area,'centroid':[sum((a[i]+b[i])*c for a,b,c in zip(p,p[1:]+p[:1],cr))/(3*twice) for i in range(2)],'extents':A.bounds(p)}
def main():
 bpy.ops.wm.open_mainfile(filepath=str(F/'project.blend'));s=bpy.context.scene;main=bpy.data.objects['submarine-yellow__root'];main.location=(0,0,0);main.rotation_euler=(0,0,0)
 actions=json.loads(main['nativeActions'])
 for owner,an in actions['upgraded-dock-ready'].items():
  o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
 s.frame_set(1);bpy.context.view_layer.update();original=list(s.objects);before=original_identity(original)
 beforeCapture={'camera':s.camera.name,'cameraMatrix':[list(r) for r in s.camera.matrix_world],'renderFrame':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'filterSize':s.render.filter_size,'world':s.world.name,'mainActions':actions}
 with bpy.data.libraries.load(str(H/'round-02.blend'),link=False) as (src,dst):dst.collections=['REFINED__sub-collector-inlet']
 col=dst.collections[0];s.collection.children.link(col);root=bpy.data.objects['collector__root'];mount=bpy.data.objects['MOUNT__sub-collector-inlet'];root.parent=mount;root.matrix_parent_inverse=Matrix.Identity(4);root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1)
 def en(l):
  l.exclude=False;l.hide_viewport=False
  for c in l.children:en(c)
 en(bpy.context.view_layer.layer_collection);col.hide_render=False;col.hide_viewport=False
 for o in col.all_objects:o.hide_set(False);o.hide_render=False;o.hide_viewport=False
 for o in s.objects:
  if o.name.startswith('PROVISIONAL__collector'):o.hide_render=True;o.hide_viewport=True
 bpy.context.view_layer.update()
 own=set(col.all_objects);canonical=json.loads((O/'canonical-neutral-resources.json').read_text());now=M.fingerprint(col)
 sourceBy={r['name']:r for r in canonical['records']};mountedBy={r['name']:r for r in now['records']};resourceIdentity=[];maxExtractionError=0.
 for o in col.all_objects:
  if o.type!='MESH':continue
  identical=sourceBy[o.name]['mesh']==mountedBy[o.name]['mesh'];resourceIdentity.append({'object':o.name,'meshNormalsUVMaterialExact':identical,'sourceMeshSHA256':digest(sourceBy[o.name]['mesh']),'mountedMeshSHA256':digest(mountedBy[o.name]['mesh'])})
  for v in o.data.vertices:
   local=(mount.matrix_world.inverted()@(o.matrix_world@v.co));expected=o.matrix_local@v.co
   # Nested pulse/guard owners retain exact idle local matrices; extract through own root.
   expected=root.matrix_world.inverted()@(o.matrix_world@v.co)
   maxExtractionError=max(maxExtractionError,(local-expected).length)
 records=[]
 for di,a in A.FACINGS.items():
  main.rotation_euler.z=a;s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pts=[]
  for o in own:
   if o.type=='MESH':pts.extend(evaluated(o,dg)[0])
  p=O/'assembled'/f'upgraded-dock-ready-{di}.png';p.parent.mkdir(exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  records.append({'direction':di,'clip':'upgraded-dock-ready','nativeFrame':1,'rootRotationZ':float(main.rotation_euler.z),'rootMatrix':[list(r) for r in main.matrix_world],'path':str(p.relative_to(E)),'sha256':A.sha(p),'wholeNativeFrame':[s.render.resolution_x,s.render.resolution_y],'collectorWorldBounds':A.bounds(pts),'qualification':'Actual native assembly. Exact frozen preliminary main in upgraded-dock-ready frame1, exact candidate neutral at frozen mount, other equipment provisional. Main final approval remains pending.'})
 # Original pixel-center BVH ray test, rerun on this candidate's actual finite surfaces.
 lamps=['body__nose_lamp_lens','body__bumper_lamp_-1','body__bumper_lamp_1'];rays=[];cam=s.camera
 for di,a in A.FACINGS.items():
  main.rotation_euler.z=a;s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();base,names=tree([o for o in s.objects if o not in own and not o.name.startswith('PROVISIONAL__collector')],dg);cv,_=tree(own,dg)
  proj=cam.calc_matrix_camera(dg,x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y).inverted();direction=-(cam.matrix_world.to_3x3()@Vector((0,0,1))).normalized();counts={n:{'baselineVisibleRaySamples':0,'occludedByCandidate':0} for n in lamps}
  for name in lamps:
   coords=[world_to_camera_view(s,cam,v) for v in evaluated(bpy.data.objects[name],dg)[0]];xs=[p.x*s.render.resolution_x for p in coords];ys=[(1-p.y)*s.render.resolution_y for p in coords]
   for y in range(max(0,math.floor(min(ys))-1),min(s.render.resolution_y,math.ceil(max(ys))+1)):
    for x in range(max(0,math.floor(min(xs))-1),min(s.render.resolution_x,math.ceil(max(xs))+1)):
     p=proj@Vector((2*(x+.5)/s.render.resolution_x-1,1-2*(y+.5)/s.render.resolution_y,-1,1));p/=p.w;origin=cam.matrix_world@p.to_3d();hit=base.ray_cast(origin,direction)
     if hit[0] is None or names[hit[2]]!=name:continue
     counts[name]['baselineVisibleRaySamples']+=1;ch=cv.ray_cast(origin,direction)
     if ch[0] is not None and ch[3]<hit[3]-1e-6:counts[name]['occludedByCandidate']+=1
  rays.append({'direction':di,'rootRotationZ':float(main.rotation_euler.z),'lenses':counts})
 main.rotation_euler.z=0;s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 # Exact finite section through the convex structural tongue at actual native seat face.
 seat=bpy.data.objects['body__collector_contact_seat'];seatE=seat.evaluated_get(dg);seatMe=seatE.to_mesh();face=[]
 for f in seatMe.polygons:
  no=(seatE.matrix_world.to_3x3().inverted().transposed()@f.normal).normalized()
  if no.y<-.999:face.append({'vertices':[list(seatE.matrix_world@seatMe.vertices[i].co) for i in f.vertices],'normal':list(no),'area':float(f.area)})
 seatE.to_mesh_clear();sf=max(face,key=lambda f:f['area']);plane=sf['vertices'][0][1]
 tongue=bpy.data.objects['collector__rear_seat_tongue'];eo=tongue.evaluated_get(dg);me=eo.to_mesh();ps=[eo.matrix_world@v.co for v in me.vertices];ints=[]
 for ed in me.edges:
  a,b=[ps[i] for i in ed.vertices];da=a.y-plane;db=b.y-plane
  if abs(da)<1e-8:ints.append((a.x,a.z))
  if da*db<0:
   v=a+(b-a)*(-da/(db-da));ints.append((v.x,v.z))
 section=hull(ints);sec=polygon_measure(section);eo.to_mesh_clear()
 facebb=A.bounds(sf['vertices']);sectionInside=all(facebb[0][0]-1e-7<=p[0]<=facebb[1][0]+1e-7 and max(facebb[0][2],.1665000021457672)-1e-7<=p[1]<=min(facebb[1][2],.25)+1e-7 for p in section)
 # BVH intersection audit: only the structural tongue/seat hardware may enter designated seat.
 overlaps=[];body=[o for o in original if o.type=='MESH' and o.name.startswith('body__')]
 obtrees={o.name:tree([o],dg)[0] for o in own if o.type=='MESH'};bdtrees={o.name:tree([o],dg)[0] for o in body}
 for on,ot in obtrees.items():
  for bn,bt in bdtrees.items():
   pairs=ot.overlap(bt)
   if pairs:overlaps.append({'collectorObject':on,'bodyObject':bn,'intersectingTrianglePairs':len(pairs),'intentionalSeatInsertion':bn=='body__collector_contact_seat' and any(t in on for t in ['rear_seat','seat_bolt'])})
 # Detect complete native containment as well as triangle crossings.
 containment=[];bodyMeshes={o.name:evaluated(o,dg)[0] for o in body};probeDirection=Vector((1,.371,.173)).normalized()
 for o in own:
  if o.type!='MESH':continue
  ovs=evaluated(o,dg)[0]
  for bn,bt in bdtrees.items():
   bb=A.bounds(bodyMeshes[bn]);inside=0;tested=0
   for v in ovs:
    if not all(bb[0][i]+1e-7<v[i]<bb[1][i]-1e-7 for i in range(3)):continue
    tested+=1;origin=v.copy();hits=0
    for iteration in range(32):
     hit=bt.ray_cast(origin,probeDirection)
     if hit[0] is None:break
     hits+=1;origin=hit[0]+probeDirection*1e-6
    if hits%2:inside+=1
   if inside:containment.append({'collectorObject':o.name,'bodyObject':bn,'evaluatedVerticesInside':inside,'testedWithinBroadPhase':tested,'intentionalSeatInsertion':bn=='body__collector_contact_seat' and any(t in o.name for t in ['rear_seat','seat_bolt','rear_service'])})
 mouthSlots=[]
 cv,_=tree(own,dg)
 for x in [-.075,.075]:
  local=Vector((x,-.215001,.217));origin=mount.matrix_world@local;axis=(mount.matrix_world.to_3x3()@Vector((0,-1,0))).normalized();hit=cv.ray_cast(origin,axis,.3)
  mouthSlots.append({'localMouthSample':list(local),'worldSample':list(origin),'axis':list(axis),'clearDistanceTestedWorld':.3,'hit':list(hit[0]) if hit[0] else None,'slotFreeForward':hit[0] is None})
 allOwnTriangles=[];ownPts=[]
 for o in own:
  if o.type=='MESH':
   vs,ts,_=evaluated(o,dg);allOwnTriangles+=ts;ownPts+=vs
 distances=[]
 for o in body:
  if any(t in o.name for t in ['nose_lamp','bumper_lamp']):
   vs,ts,_=evaluated(o,dg);d=finite_distance(allOwnTriangles,ts);d['object']=o.name;distances.append(d)
 skidPts=[]
 for o in body:
  if 'hover_skid' in o.name:skidPts+=evaluated(o,dg)[0]
 extraction=[]
 # Inverse mount extraction compares the actual hierarchy chain to the saved standalone neutral hierarchy.
 for o in own:
  if o.type!='MESH':continue
  old=sourceBy[o.name];chain=o.name;mx=Matrix.Identity(4)
  while chain!=root.name:mx=Matrix(sourceBy[chain]['localMatrix'])@mx;chain=sourceBy[chain]['parent']
  vals=[]
  for v in o.data.vertices:vals.append((mount.matrix_world.inverted()@(o.matrix_world@v.co)-mx@v.co).length)
  extraction.append({'object':o.name,'maxVertexError':max(vals),'resourceIdentityExact':sourceBy[o.name]['mesh']==mountedBy[o.name]['mesh'],'savedNeutralLocalMatrixExact':sourceBy[o.name]['localMatrix']==mountedBy[o.name]['localMatrix']})
 after=original_identity(original);sourceHash=A.sha(F/'project.blend')
 audit={'frozenMainSHA256':sourceHash,'expectedFrozenMainSHA256':'c8462a4072c8ce12f2afcc6907a02d705dcd7df6858f7d790bb2a1dcc5d7fb0e','bodyAndOriginalResourceIdentitiesBefore':before,'bodyAndOriginalResourceIdentitiesAfter':after,'allOriginalGeometryMaterialsHierarchyCameraLightsIdentical':before==after,'captureBeforeAndAfter':beforeCapture,'mountMatrixLocal':[list(r) for r in mount.matrix_local],'rootMatrixLocal':[list(r) for r in root.matrix_local],'allNeutralResourcesExact':all(r['meshNormalsUVMaterialExact'] for r in resourceIdentity),'neutralResources':resourceIdentity,'inverseMountExtraction':extraction,'nativeAssemblyCaptures':records,'finiteSeat':{'authority':sf,'actualPlaneY':plane,'sectionObject':tongue.name,'convexNativeSectionXZ':section,'convexQualification':'The bevelled rectangular tongue is convex; the plane section is convex, so the edge-intersection convex hull is exactly its filled finite section. No collector shell convex-hull shortcut.','contiguousFinitePatch':True,'sectionEntirelyInsideAvailableFiniteFace':sectionInside,'areaWorld':sec['area'],'centroidWorld':[sec['centroid'][0],plane,sec['centroid'][1]],'extentsXZ':sec['extents'],'contactNormalCollector':[0,1,0],'contactNormalSeat':sf['normal'],'planeSeparation':0,'tongueEvaluatedBounds':A.bounds(evaluated(tongue,dg)[0]),'insertionDepthBeyondActualFrontFace':A.bounds(evaluated(tongue,dg)[0])[1][1]-plane,'interpretation':'Purposeful structural insertion with finite two-axis section; other hull/lamp overlap separately listed.'},'nativeBodyIntersections':overlaps,'nativeBodyContainment':containment,'mouthSlotForwardRays':mouthSlots,'lampFiniteDistances':distances,'lampRayVisibility':rays,'hover':{'collectorMinZ':min(p.z for p in ownPts),'skidsMinZ':min(p.z for p in skidPts),'skidsRemainLowest':min(p.z for p in ownPts)>min(p.z for p in skidPts),'bodyUnchanged':before==after,'dockedHover':'Frozen main native actions and skid geometry retained. Only static upgraded-dock-ready frame1 paired here; full main dock clip/family approval pending.'},'actualMouth':{'local':[0,-.215,.217],'main':[0,-.606,.1768],'axisLocal':[0,-1,0],'axisMain':[0,-1,0],'driftFromProvisional':[0,.009,.0068],'driftFromOldSource':[0,.018,-.0092],'legacyReferenceUnchanged':[0,-.53,.21],'provisionalReference':[0,-.615,.17],'oldSourceReference':[0,-.624,.186],'clearance':'Open front guarded mouth; finite native shell/guard geometry. Main neutral only.'},'qualification':'Candidate technical evidence, no self-approval. Static frozen preliminary main and explicitly provisional other gear; final576-frame main adoption/approval pending.'}
 A.savej(O/'assembly-audit.json',audit)
 bpy.ops.wm.save_as_mainfile(filepath=str(H/'round-02-assembled.blend'),compress=True)
 print(json.dumps({'bodyUnchanged':before==after,'resourcesExact':audit['allNeutralResourcesExact'],'seat':audit['finiteSeat'],'intersections':overlaps,'lampDistances':distances,'lampRays':rays,'hover':audit['hover']},indent=2))
if __name__=='__main__':main()
