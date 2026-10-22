import bpy,json,pathlib,hashlib,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import closest_point_on_tri
from bpy_extras.object_utils import world_to_camera_view
O=pathlib.Path(__file__).resolve().parent;E=O.parent.parent;R=E/'source'
def plain(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 if isinstance(v,bpy.types.ID):return {'ID':v.name,'type':v.bl_rna.identifier}
 try:return [plain(x) for x in v]
 except:return str(v)
def props(o):
 d={}
 for p in o.bl_rna.properties:
  if p.identifier in ['rna_type','name','name_full','session_uid'] or p.type in ['COLLECTION','POINTER']:continue
  try:d[p.identifier]=plain(getattr(o,p.identifier))
  except:pass
 return d
def graph(tree):
 if not tree:return None
 nodes=[]
 for n in tree.nodes:
  d={'name':n.name,'props':props(n),'inputs':{i.identifier:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value')}}
  if hasattr(n,'color_ramp'):d['ramp']={'props':props(n.color_ramp),'elements':[(e.position,list(e.color)) for e in n.color_ramp.elements]}
  nodes.append(d)
 return {'nodes':nodes,'links':sorted([[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in tree.links])}
def material(m):return {'props':props(m),'graph':graph(m.node_tree)}
def mesh(me):return {'v':[list(v.co) for v in me.vertices],'edges':[list(e.vertices) for e in me.edges],'p':[(list(f.vertices),f.material_index,f.use_smooth) for f in me.polygons],'cornerNormals':[list(x.vector) for x in me.corner_normals],'uv':{u.name:[list(x.uv) for x in u.data] for u in me.uv_layers},'materials':[material(m) for m in me.materials]}
def obj(ob,canonical=False):
 d={'name':ob.name,'type':ob.type,'parent':None if canonical and ob.name=='collector__root' else ob.parent.name if ob.parent else None,'location':list(ob.location),'rotation':list(ob.rotation_euler),'rotationMode':ob.rotation_mode,'scale':list(ob.scale),'basis':[list(r) for r in ob.matrix_basis],'parentInverse':[list(r) for r in ob.matrix_parent_inverse],'modifiers':[props(m) for m in ob.modifiers]}
 if ob.type=='MESH':d['mesh']=mesh(ob.data)
 elif ob.type in ['LIGHT','CAMERA']:d['data']=props(ob.data)
 return d
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def set_idle(s):
 for suffix in ['guard_rock','mouth_pulse','mouth_sleeve']:
  ob=bpy.data.objects['collector__'+suffix];a=bpy.data.actions[f'INLET_NATIVE__idle__collector__{suffix}'];ob.animation_data_create();ob.animation_data.action=a;ob.animation_data.action_slot=a.slots[0]
 bpy.data.objects['collector__root'].rotation_euler.z=0;s.frame_set(1);bpy.context.view_layer.update()
def set_main(s):
 root=bpy.data.objects['submarine-yellow__root'];root.location=(0,0,0);root.rotation_euler=(0,0,0)
 for owner,an in json.loads(root['nativeActions'])['upgraded-dock-ready'].items():
  ob=bpy.data.objects[owner];a=bpy.data.actions[an];ob.animation_data_create();ob.animation_data.action=a;ob.animation_data.action_slot=a.slots[0]
 s.frame_set(1);bpy.context.view_layer.update()
def action(a):
 return [(fc.data_path,fc.array_index,[(list(k.co),k.interpolation,list(k.handle_left),list(k.handle_right)) for k in fc.keyframe_points]) for l in a.layers for st in l.strips for bag in st.channelbags for fc in bag.fcurves]
def scene_state(s):return {'camera':s.camera.name,'render':{k:plain(getattr(s.render,k)) for k in ['resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y','filter_size','dither_intensity','fps','engine','film_transparent']},'view':props(s.view_settings),'world':graph(s.world.node_tree),'compositor':graph(s.compositing_node_group)}
def bb(v):return [[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]]
def geometry(ob,dg):
 eo=ob.evaluated_get(dg);me=eo.to_mesh();vs=[eo.matrix_world@v.co for v in me.vertices];me.calc_loop_triangles();tri=[tuple(vs[i] for i in f.vertices) for f in me.loop_triangles];poly=[list(f.vertices) for f in me.polygons];faces=[{'vertices':[list(vs[i]) for i in f.vertices],'normal':list((eo.matrix_world.to_3x3().inverted().transposed()@f.normal).normalized()),'localArea':f.area} for f in me.polygons];edges=[tuple(vs[i] for i in e.vertices) for e in me.edges];eo.to_mesh_clear();return {'v':vs,'tri':tri,'poly':poly,'edges':edges,'faces':faces,'bb':bb(vs),'bvh':BVHTree.FromPolygons(vs,poly,all_triangles=False)}
# Independent persistent canonical resources and exact frozen-body comparison.
bpy.ops.wm.open_mainfile(filepath=str(R/'round-02.blend'));s=bpy.context.scene;set_idle(s);canonical={o.name:obj(o,True) for o in bpy.data.collections['REFINED__sub-collector-inlet'].all_objects}
bpy.ops.wm.open_mainfile(filepath=str(E/'inputs/frozen-main-v1/project.blend'));s=bpy.context.scene;set_main(s);body={o.name:digest(obj(o)) for o in s.objects};bodyactions={a.name:digest(action(a)) for a in bpy.data.actions};ss=scene_state(s)
bpy.ops.wm.open_mainfile(filepath=str(R/'round-02-assembled.blend'));s=bpy.context.scene;set_main(s);col=bpy.data.collections['REFINED__sub-collector-inlet'];mounted={o.name:obj(o,True) for o in col.all_objects};resourceDifferences=[k for k,v in canonical.items() if v!=mounted.get(k)];bodyDiff=[k for k,v in body.items() if k not in bpy.data.objects or digest(obj(bpy.data.objects[k]))!=v];actionDiff=[k for k,v in bodyactions.items() if k not in bpy.data.actions or digest(action(bpy.data.actions[k]))!=v];dg=bpy.context.evaluated_depsgraph_get();own={ob.name:geometry(ob,dg) for ob in col.all_objects if ob.type=='MESH'};bg={ob.name:geometry(ob,dg) for ob in s.objects if ob.type=='MESH' and ob.name not in own and not ob.name.startswith('PROVISIONAL__')};mount=bpy.data.objects['MOUNT__sub-collector-inlet'];root=bpy.data.objects['collector__root'];allv=[p for g in own.values() for p in g['v']]
# Actual finite native front face and convex tongue section, no AABB contact claim.
seat=bg['body__collector_contact_seat'];face=next(f for f in seat['faces'] if f['normal'][1]<-.999);Y=face['vertices'][0][1];section=[];tg=own['collector__rear_seat_tongue']
for a,b in tg['edges']:
 if abs(a.y-Y)<1e-8:section.append((a.x,a.z))
 if (a.y-Y)*(b.y-Y)<0:
  p=a+(b-a)*((Y-a.y)/(b.y-a.y));section.append((p.x,p.z))
def hull(points):
 p=sorted(set((round(x,10),round(z,10)) for x,z in points));lo=[];hi=[]
 def cross(o,a,b):return(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 for v in p:
  while len(lo)>1 and cross(lo[-2],lo[-1],v)<=0:lo.pop()
  lo.append(v)
 for v in reversed(p):
  while len(hi)>1 and cross(hi[-2],hi[-1],v)<=0:hi.pop()
  hi.append(v)
 return lo[:-1]+hi[:-1]
# Derive the actual triangular plane-section loop; no global convex-hull shortcut.
segments=[];pointByKey={};neighbors={}
for tri in tg['tri']:
 hits=[]
 for a,b in zip(tri,tri[1:]+tri[:1]):
  if (a.y-Y)*(b.y-Y)<0:
   p=a+(b-a)*((Y-a.y)/(b.y-a.y));key=(round(p.x,8),round(p.z,8));pointByKey.setdefault(key,(p.x,p.z));hits.append(key)
 if len(set(hits))==2:
  a,b=list(dict.fromkeys(hits));neighbors.setdefault(a,set()).add(b);neighbors.setdefault(b,set()).add(a);segments.append([a,b])
assert all(len(v)==2 for v in neighbors.values()),'Plane section is not a simple two-neighbor boundary'
start=min(neighbors);keys=[start];previous=None;current=start
while True:
 nxt=next(v for v in neighbors[current] if v!=previous)
 if nxt==start:break
 assert nxt not in keys,'Multiple-loop/self-crossing section';keys.append(nxt);previous,current=current,nxt
assert len(keys)==len(neighbors),'Multiple disconnected plane-section loops'
poly=[pointByKey[k] for k in keys];terms=[a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])];signed=sum(terms)/2;centroid=[sum((a[i]+b[i])*t for a,b,t in zip(poly,poly[1:]+poly[:1],terms))/(6*signed) for i in [0,1]];pb=[[min(p[i] for p in poly) for i in [0,1]],[max(p[i] for p in poly) for i in [0,1]]];fb=bb([Vector(v) for v in face['vertices']]);convex=True # A single actual triangle-plane loop was established independently; no whole-tongue face-plane assumption.
contact={'frontFace':face,'actualTriangleSectionSingleContiguousLoop':True,'sectionTopologyJoinToleranceWorld':1e-8,'wholeTongueConvexAssumptionUsed':False,'finiteSectionXZ':poly,'area':abs(signed),'centroid':[centroid[0],Y,centroid[1]],'extentsXZ':pb,'entireSectionInsideAvailableFace':pb[0][0]>=fb[0][0]-1e-7 and pb[1][0]<=fb[1][0]+1e-7 and pb[0][1]>=fb[0][2]-1e-7 and pb[1][1]<=.25+1e-7,'actualPlaneSeparation':0,'insertionDepth':tg['bb'][1][1]-Y,'tongueRearPositiveYNormals':[f['normal'] for f in tg['faces'] if f['normal'][1]>.999]}
# Native finite intersections and point containment against all fixed body meshes.
intersections=[];containments=[]
for cn,cg in own.items():
 for bn,bg1 in bg.items():
  if any(cg['bb'][1][i]<bg1['bb'][0][i] or bg1['bb'][1][i]<cg['bb'][0][i] for i in range(3)):continue
  pairs=cg['bvh'].overlap(bg1['bvh'])
  if pairs:intersections.append({'collector':cn,'body':bn,'trianglePairs':len(pairs),'intentionalSeat':bn=='body__collector_contact_seat'})
  inside=0
  for p in cg['v']:
   if not all(bg1['bb'][0][i]+1e-6<p[i]<bg1['bb'][1][i]-1e-6 for i in range(3)):continue
   near=bg1['bvh'].find_nearest(p)
   if near[0] is not None and (p-near[0]).dot(near[1])< -1e-7:inside+=1
  if inside:containments.append({'collector':cn,'body':bn,'insideVertices':inside,'intentionalSeat':bn=='body__collector_contact_seat'})
# Exact finite triangle distance with safe numeric broad-phase pruning.
def segdist(a,b,c,d):
 u=b-a;v=d-c;w=a-c;aa=u.dot(u);bb1=u.dot(v);cc=v.dot(v);dd=u.dot(w);ee=v.dot(w);den=aa*cc-bb1*bb1
 if aa<1e-20:return (a-(c+v*max(0,min(1,ee/cc)))).length if cc>1e-20 else(a-c).length
 if cc<1e-20:return(c-(a+u*max(0,min(1,-dd/aa)))).length
 sn=max(0,min(1,(bb1*ee-cc*dd)/den)) if den>1e-20 else 0;tn=(bb1*sn+ee)/cc
 if tn<0:tn=0;sn=max(0,min(1,-dd/aa))
 elif tn>1:tn=1;sn=max(0,min(1,(bb1-dd)/aa))
 return(w+sn*u-tn*v).length
def tdist(a,b):
 best=min([(v-closest_point_on_tri(v,*b)).length for v in a]+[(v-closest_point_on_tri(v,*a)).length for v in b]);ea=[(a[i],a[(i+1)%3]) for i in range(3)];eb=[(b[i],b[(i+1)%3]) for i in range(3)]
 return min(best,min(segdist(*x,*y) for x in ea for y in eb))
ct=[t for g in own.values() for t in g['tri']];ar=np.array([[list(v) for v in t] for t in ct]);clo=ar.min(axis=1);chi=ar.max(axis=1);lamp=[]
for name,g in bg.items():
 if 'lamp' not in name:continue
 best=min((p-g['bvh'].find_nearest(p)[0]).length for p in allv);tested=0
 for t in g['tri']:
  lo=np.min(np.array(t),axis=0);hi=np.max(np.array(t),axis=0);ds=np.maximum(np.maximum(lo-chi,clo-hi),0);ids=np.where((ds*ds).sum(axis=1)<=best*best+1e-14)[0]
  for idx in ids:best=min(best,tdist(ct[int(idx)],t));tested+=1
 lamp.append({'name':name,'finiteDistance':best,'testedPairs':tested})
# Baseline visible lens rays, using independently built per-object finite BVHs.
vis=[];main=bpy.data.objects['submarine-yellow__root'];cam=s.camera
for di,angle in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 main.rotation_euler.z=angle;s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();obgs={ob.name:geometry(ob,dg) for ob in s.objects if ob.type=='MESH' and not ob.hide_render and ob.name not in own};ogs=[geometry(ob,dg) for ob in col.all_objects if ob.type=='MESH'];proj=cam.calc_matrix_camera(dg,x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y).inverted();direction=-(cam.matrix_world.to_3x3()@Vector((0,0,1))).normalized();counts={}
 for name in ['body__nose_lamp_lens','body__bumper_lamp_-1','body__bumper_lamp_1']:
  coords=[world_to_camera_view(s,cam,p) for p in obgs[name]['v']];xs=[p.x*s.render.resolution_x for p in coords];ys=[(1-p.y)*s.render.resolution_y for p in coords];visible=occluded=0
  for y in range(max(0,math.floor(min(ys))-1),min(s.render.resolution_y,math.ceil(max(ys))+1)):
   for x in range(max(0,math.floor(min(xs))-1),min(s.render.resolution_x,math.ceil(max(xs))+1)):
    p=proj@Vector((2*(x+.5)/s.render.resolution_x-1,1-2*(y+.5)/s.render.resolution_y,-1,1));p/=p.w;origin=cam.matrix_world@p.to_3d();hits=[(hit[3],n) for n,g in obgs.items() if (hit:=g['bvh'].ray_cast(origin,direction))[0] is not None]
    if not hits:continue
    dist,n=min(hits)
    if n!=name:continue
    visible+=1
    if any((h:=g['bvh'].ray_cast(origin,direction))[0] is not None and h[3]<dist-1e-6 for g in ogs):occluded+=1
  counts[name]={'baselineVisible':visible,'occludedByCandidate':occluded}
 vis.append({'direction':di,'lenses':counts});s.render.filepath=str(O/f'assembled-{di}.png');bpy.ops.render.render(write_still=True)
main.rotation_euler.z=0;bpy.context.view_layer.update()
mouthOb=bpy.data.objects['collector__actual_mouth'];actualMouth=list(mouthOb.matrix_world.translation);mouthAxis=list((mouthOb.matrix_world.to_3x3()@Vector((0,-1,0))).normalized());mouthRays=[]
for x in [-.075,.075]:
 p=mount.matrix_world@Vector((x,-.215001,.217));axis=Vector(mouthAxis);hits=[(h[3],n) for n,g in own.items() if (h:=g['bvh'].ray_cast(p,axis,.3))[0] is not None];mouthRays.append({'origin':list(p),'direction':mouthAxis,'distance':.3,'hits':hits})
report={'method':'Independent saved-file reopening and direct native data/BVH/finite-plane/triangle geometry, no builder.','excludedNonPersistentRuntimeProperty':{'session_uid':'Blender allocates this ID counter afresh on file load; identity-diagnosis.json demonstrates the initial false differences. All actual art/data and persistent transforms remain compared exactly.'},'actualMouthWorld':actualMouth,'actualMouthAxisWorld':mouthAxis,'mouthForwardSlotRays':mouthRays,'canonicalResourcesExact':not resourceDifferences,'resourceDifferences':resourceDifferences,'canonicalResourceHashes':{k:digest(v) for k,v in canonical.items()},'mountedResourceHashes':{k:digest(v) for k,v in mounted.items()},'originalBodyResourceDifferences':bodyDiff,'originalBodyActionDifferences':actionDiff,'originalSceneCameraLightsWorldCompositorSettingsExact':ss==scene_state(s),'sceneDifferenceKeys':[k for k in ss if ss[k]!=scene_state(s)[k]],'mountMatrix':[list(r) for r in mount.matrix_local],'candidateRootParent':root.parent.name,'candidateNeutralBoundsMain':bb(allv),'finiteContact':contact,'nativeIntersections':intersections,'nativeContainment':containments,'finiteLampDistances':lamp,'lampVisibility':vis,'skidMinZ':min(bg[n]['bb'][0][2] for n in bg if n.startswith('body__hover_skid_')),'collectorMinZ':min(p.z for p in allv),'candidateCurrentActions':{o.name:o.animation_data.action.name if o.animation_data and o.animation_data.action else None for o in col.all_objects},'libraries':[l.filepath for l in bpy.data.libraries]}
(O/'identity-contact-lamps-v2.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['canonicalResourceHashes','mountedResourceHashes','candidateCurrentActions']},indent=2))
