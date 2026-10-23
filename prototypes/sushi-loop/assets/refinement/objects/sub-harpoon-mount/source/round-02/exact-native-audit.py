"""Reopen-only native capture, resource identity, finite-surface and main context audit.
No authoring builder imports. All output stays within this object.
"""
import bpy,json,pathlib,math,sys,hashlib
sys.dont_write_bytecode=True
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parent;E=P.parent.parent;C=E/'candidates/round-02';C.mkdir(exist_ok=True)
ANGLES={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
contract=json.loads((E/'inputs/root-native-contract.json').read_text())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def dump(p,x):pathlib.Path(p).write_text(json.dumps(x,indent=2)+'\n')
def val(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 try:return [val(v) for v in x]
 except:return str(x)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def matrix(x):return [list(r) for r in x]
def matrec(m):
 return {'name':m.name,'diffuse':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[{'identifier':i.identifier,'value':val(getattr(i,'default_value',None))} for i in n.inputs]} for n in m.node_tree.nodes],'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.identifier,'toNode':l.to_node.name,'toSocket':l.to_socket.identifier} for l in m.node_tree.links]}
def resource(o):
 d=o.data;d.calc_loop_triangles()
 return {'object':o.name,'mesh':d.name,'vertices':[list(v.co) for v in d.vertices],'vertexNormals':[list(v.normal) for v in d.vertices],'cornerNormals':[list(n.vector) for n in d.corner_normals],'polygons':[{'vertices':list(f.vertices),'material':f.material_index,'smooth':f.use_smooth,'normal':list(f.normal)} for f in d.polygons],'uvLayers':[{'name':u.name,'data':[list(v.uv) for v in u.data]} for u in d.uv_layers],'materials':[matrec(m) for m in d.materials if m],'matrixLocal':matrix(o.matrix_local),'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]}
def surf(o):
 eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh();vs=[eo.matrix_world@v.co for v in me.vertices];fs=[list(f.vertices) for f in me.polygons];normals=[list((eo.matrix_world.to_3x3().inverted().transposed()@f.normal).normalized()) for f in me.polygons];eo.to_mesh_clear();return vs,fs,normals
def tree(surface):return BVHTree.FromPolygons(surface[0],surface[1],all_triangles=False,epsilon=0)
def bounds(v):return [[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]]
def rootrec(sc,root,clip,d,f,path):
 q=world_to_camera_view(sc,sc.camera,root.matrix_world.translation)
 return {'clip':clip,'direction':d,'index':f-1,'sourceFrame':f,'path':str(path.relative_to(E)),'rootRotationZ':float(root.rotation_euler.z),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'actualRootMatrix':matrix(root.matrix_world),'projectedRootPixels':[q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y],'nativeSize':[sc.render.resolution_x,sc.render.resolution_y]}

from mathutils.geometry import closest_point_on_tri
# Fingerprint actual persistent local data. matrix_local is a computed inverse-
# parent product and exhibits1e-7 float roundoff after positive uniform mounting.
def persistent(o):
 r=resource(o);r.pop('matrixLocal');r['matrixBasis']=matrix(o.matrix_basis);r['parentInverse']=matrix(o.matrix_parent_inverse);r['parent']=o.parent.name if o.parent else None;return r
bpy.ops.wm.open_mainfile(filepath=str(P/'project.blend'));sc=bpy.context.scene;root=bpy.data.objects['harpoon__root'];sc.frame_set(1);bpy.context.view_layer.update();c=bpy.data.collections['CANONICAL__sub-harpoon-mount'];can={o.name:persistent(o) for o in c.all_objects if o.type=='MESH'}
canonical=[can[n] for n in sorted(can)]
dump(C/'canonical-neutral-persistent-resources.json',{'sourceSHA256':sha(P/'project.blend'),'objects':canonical,'resourceSHA256':digest(canonical),'definition':'Native saved mesh, vertex/corner/face normals, UVs, materials including node values/links, exact persistent matrix_basis/matrix_parent_inverse and parent ownership; excludes derived inverse-parent matrix_local float product.'})
bpy.ops.wm.open_mainfile(filepath=str(P/'resources/frozen-main-v1/project.blend'));sc=bpy.context.scene;main=bpy.data.objects['submarine-yellow__root'];main.rotation_euler.z=0
for owner,an in json.loads(main['nativeActions'])['upgraded-dock-ready'].items():
 o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
sc.frame_set(1);bpy.context.view_layer.update()
with bpy.data.libraries.load(str(P/'project.blend'),link=False) as (src,dst):dst.collections=['CANONICAL__sub-harpoon-mount']
c=bpy.data.collections['CANONICAL__sub-harpoon-mount'];sc.collection.children.link(c);root=bpy.data.objects['harpoon__root'];root.parent=bpy.data.objects['MOUNT__sub-harpoon-mount'];root.matrix_basis=Matrix.Identity(4);moving=bpy.data.objects['harpoon__recoil_carriage'];moving.animation_data.action=None;bpy.context.view_layer.update()
imported=[persistent(bpy.data.objects[n]) for n in sorted(can)]
identity={'canonicalSHA256':digest(canonical),'importedSHA256':digest(imported),'exactNeutralPersistentResourceIdentity':canonical==imported,'allObjects':[{'name':n,'exact':can[n]==persistent(bpy.data.objects[n])} for n in sorted(can)],'derivedMatrixLocalRoundoffExplanation':'The earlier mounted-audit canonicalNeutralResourceExact includes computed matrix_local under floating positive uniform parenting; its false value is a measurement-definition issue. Every stored local channel, mesh/normal/UV/material is exact here. Inverse-mount evaluated vertex maximum error is separately retained in mounted-audit.json. No resource editing was performed to resolve the audit.'}
dump(C/'canonical-neutral-identity.json',identity)
seat=bpy.data.objects['body__harpoon_contact_seat'];sv,sf,sn=surf(seat);foot=bpy.data.objects['harpoon__bearing_foot'];fv,ff,fn=surf(foot)
seatfaces=[{'vertices':[list(sv[i]) for i in ids],'normal':n} for ids,n in zip(sf,sn) if n[2]>.999]
def inside(poly,p,tol=1e-8):
 crosses=[]
 for i,a in enumerate(poly):
  b=poly[(i+1)%len(poly)];crosses.append((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))
 return all(v>=-tol for v in crosses) or all(v<=tol for v in crosses)
bearings=[]
for ids,n in zip(ff,fn):
 if n[2]<-.999:
  pts=[fv[i] for i in ids]
  local=[root.matrix_world.inverted()@p for p in pts]
  if max(abs(p.z) for p in local)>1e-6:continue
  seatface=next((f for f in seatfaces if all(inside(f['vertices'],p) and abs(p.z-f['vertices'][0][2])<1e-5 for p in pts)),None)
  bearings.append({'worldVertices':[list(p) for p in pts],'localVertices':[list(p) for p in local],'fullyContainedByActualEvaluatedNativeSeatPolygon':seatface is not None,'actualSeatFace':seatface,'footNormal':n,'areaWorld':sum((pts[i]-pts[0]).cross(pts[i+1]-pts[0]).length/2 for i in range(1,len(pts)-1)),'centroidWorld':list(sum(pts,Vector())/len(pts)),'intendedCenterWorld':list(root.matrix_world@Vector((0,.343,0))),'intendedCenterInsideBearing':inside([list(p) for p in pts],root.matrix_world@Vector((0,.343,0)))})
# Exact triangle-to-triangle native surface distances, including edge-edge minima.
def triangles(o):
 eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh();me.calc_loop_triangles();vs=[eo.matrix_world@v.co for v in me.vertices];ids=[tuple(t.vertices) for t in me.loop_triangles];eo.to_mesh_clear();return {'vertices':vs,'indices':ids,'triangles':[[vs[i] for i in ix] for ix in ids],'tree':BVHTree.FromPolygons(vs,ids,all_triangles=True,epsilon=0)}
def segdist(p1,q1,p2,q2):
 d1=q1-p1;d2=q2-p2;r=p1-p2;a=d1.dot(d1);e=d2.dot(d2);f=d2.dot(r)
 if a<=1e-20 and e<=1e-20:return r.length
 if a<=1e-20:s=0;t=max(0,min(1,f/e))
 else:
  cc=d1.dot(r)
  if e<=1e-20:t=0;s=max(0,min(1,-cc/a))
  else:
   b=d1.dot(d2);den=a*e-b*b;s=max(0,min(1,(b*f-cc*e)/den)) if abs(den)>1e-20 else 0;t=(b*s+f)/e
   if t<0:t=0;s=max(0,min(1,-cc/a))
   elif t>1:t=1;s=max(0,min(1,(b-cc)/a))
 return ((p1+d1*s)-(p2+d2*t)).length
def tridist(a,b):
 best=min([(p-closest_point_on_tri(p,*b)).length for p in a]+[(p-closest_point_on_tri(p,*a)).length for p in b])
 for i in range(3):
  for j in range(3):best=min(best,segdist(a[i],a[(i+1)%3],b[j],b[(j+1)%3]))
 return best
def exactdistance(A,B):
 if A['tree'].overlap(B['tree']):return 0
 best=min([B['tree'].find_nearest(v)[3] for v in A['vertices']]+[A['tree'].find_nearest(v)[3] for v in B['vertices']])
 for a in A['triangles']:
  center=sum(a,Vector())/3;radius=max((v-center).length for v in a)
  for hit in B['tree'].find_nearest_range(center,radius+best+1e-7):
   best=min(best,tridist(a,B['triangles'][hit[2]]))
 return best
meshes=[o for o in c.all_objects if o.type=='MESH'];hull=triangles(bpy.data.objects['body__hull']);focals=[o for o in sc.objects if o.type=='MESH' and o.name.startswith('body__') and any(k in o.name for k in ['glass','port_','hatch','periscope'])];ft={o.name:triangles(o) for o in focals}
vs=[];ix=[]
for n,t in ft.items():
 offset=len(vs);vs+=t['vertices'];ix += [tuple(i+offset for i in tri) for tri in t['indices']]
combined={'vertices':vs,'indices':ix,'triangles':[[vs[i] for i in tri] for tri in ix],'tree':BVHTree.FromPolygons(vs,ix,all_triangles=True,epsilon=0)}
cache={};phases=[]
samples=json.loads((C/'standalone-audit.json').read_text())['phases']
for sample in samples:
 moving.matrix_basis=Matrix(sample['movingMatrix']);bpy.context.view_layer.update();ds=[];hs=[]
 for o in meshes:
  key=(o.name,sample['sourceFrame'] if o.parent==moving else 0)
  if key not in cache:
   A=triangles(o);cache[key]={'hull':exactdistance(A,hull),'focal':{'combined actual focal surfaces':exactdistance(A,combined)}}
  v=cache[key];hs.append({'own':o.name,'distance':v['hull']});ds += [{'own':o.name,'focal':n,'distance':d} for n,d in v['focal'].items()]
 phases.append({'sourceFrame':sample['sourceFrame'],'minimumHullSurfaceDistance':min(x['distance'] for x in hs),'hullClosest':min(hs,key=lambda x:x['distance']),'minimumFocalSurfaceDistance':min(x['distance'] for x in ds),'focalClosest':min(ds,key=lambda x:x['distance']),'ownMovingMatrix':matrix(moving.matrix_basis)})
 print('EXACT_SURFACE_PHASE',sample['sourceFrame'],flush=True)
dump(C/'exact-native-surface-audit.json',{'nativeFrozenMainSHA256':sha(P/'resources/frozen-main-v1/project.blend'),'candidateSourceSHA256':sha(P/'project.blend'),'canonicalResourceIdentity':identity,'actualNativeSeatFaces':seatfaces,'bearingPolygons':bearings,'phases':phases,'distanceMethod':'Evaluated native triangles. Exact triangle-to-triangle Euclidean surface minima consider vertex-face and all9 edge-edge pairs. Conservative BVH triangle-centroid sphere range excludes only triangle pairs provably farther than current minimum. BVH intersection returns zero. Static distances cached with unchanged data; moving cohort sampled at all12 actual native action phases.','intersectionEvidence':'mounted-audit.json contains every own/main evaluated-surface intersection for all12 phases; only intended coplanar foot/seat contact remains.','approval':False})
print('EXACT_AUDIT_COMPLETE',identity['exactNeutralPersistentResourceIdentity'])
