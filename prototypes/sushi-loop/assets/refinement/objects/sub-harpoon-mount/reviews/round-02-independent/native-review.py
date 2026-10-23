"""Independent reopened source audit and representative replay. No builders or candidate mutations."""
import bpy,math,json,pathlib,hashlib,ast
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import closest_point_on_tri
from bpy_extras.object_utils import world_to_camera_view
R=pathlib.Path(__file__).resolve().parent;S=R/'resources';O=R/'native-replay';O.mkdir(exist_ok=True)
E=R.parents[1];C=E/'candidates/round-02'
def js(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mx(m):return [list(r) for r in m]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def value(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [value(x) for x in v]
 except:return str(v)
def nativeResource(o):
 d=o.data;d.calc_loop_triangles()
 mats=[]
 for m in d.materials:
  mats.append({'name':m.name,'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[(i.identifier,value(getattr(i,'default_value',None))) for i in n.inputs]} for n in m.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links]})
 return {'object':o.name,'mesh':d.name,'basis':mx(o.matrix_basis),'parentInverse':mx(o.matrix_parent_inverse),'parent':o.parent.name if o.parent else None,'vertices':[list(v.co) for v in d.vertices],'vertexNormals':[list(v.normal) for v in d.vertices],'cornerNormals':[list(n.vector) for n in d.corner_normals],'polygons':[(list(f.vertices),f.material_index,f.use_smooth,list(f.normal)) for f in d.polygons],'uvs':[(u.name,[list(v.uv) for v in u.data]) for u in d.uv_layers],'materials':mats,'modifiers':[(m.name,m.type) for m in o.modifiers]}
def surface(o):
 eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh();me.calc_loop_triangles();v=[eo.matrix_world@a.co for a in me.vertices];idx=[tuple(t.vertices) for t in me.loop_triangles];faces=[{'vertices':[list(v[i]) for i in f.vertices],'normal':list((eo.matrix_world.to_3x3().inverted().transposed()@f.normal).normalized())} for f in me.polygons];eo.to_mesh_clear();return {'vertices':v,'indices':idx,'triangles':[[v[i] for i in f] for f in idx],'tree':BVHTree.FromPolygons(v,idx,all_triangles=True,epsilon=0),'faces':faces}
def bb(v):return [[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]]
def inside(poly,p,tol=1e-8):
 z=[(poly[(i+1)%len(poly)][0]-a[0])*(p[1]-a[1])-(poly[(i+1)%len(poly)][1]-a[1])*(p[0]-a[0]) for i,a in enumerate(poly)];return min(z)>=-tol or max(z)<=tol
# Inspected standard exact vertex-face/edge-edge distance implementation from the
# hash-bound helper; only pure geometry definitions are loaded, never its authoring/audit body.
tree=ast.parse((S/'source/exact-native-audit.py').read_text());funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['segdist','tridist','exactdistance']];exec(compile(ast.Module(body=funcs,type_ignores=[]),str(S/'source/exact-native-audit.py'),'exec'))
bpy.ops.wm.open_mainfile(filepath=str(S/'project.blend'));sc=bpy.context.scene;root=bpy.data.objects['harpoon__root'];car=bpy.data.objects['harpoon__recoil_carriage'];coll=bpy.data.collections['CANONICAL__sub-harpoon-mount'];meshes=sorted([o for o in coll.all_objects if o.type=='MESH'],key=lambda o:o.name)
sc.frame_set(1);root.rotation_euler.z=0;bpy.context.view_layer.update();canonical={o.name:nativeResource(o) for o in meshes};neutral={o.name:mx(o.matrix_basis) for o in coll.all_objects};contract=json.loads((S/'native-contract.json').read_text());sourcecam=json.loads((S/'source-camera.json').read_text())
cam={'world':mx(sc.camera.matrix_world),'projection':mx(sc.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'frame':[sc.render.resolution_x,sc.render.resolution_y],'aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filterSize':sc.render.filter_size,'fps':sc.render.fps,'engine':sc.render.engine,'sensorFit':sc.camera.data.sensor_fit,'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'filmTransparent':sc.render.film_transparent,'lights':[{'name':o.name,'position':list(o.location),'color':list(o.data.color),'power':o.data.energy,'size':o.data.size,'type':o.data.type} for o in sc.objects if o.type=='LIGHT'],'imageDependencies':[{'name':i.name,'source':i.source,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.users and i.name!='Render Result']}
cam['worldMaxError']=max(abs(cam['world'][r][c]-sourcecam['camera']['worldMatrix'][r][c]) for r in range(4) for c in range(4));cam['projectionMaxError']=max(abs(cam['projection'][r][c]-sourcecam['camera']['projectionMatrix'][r][c]) for r in range(4) for c in range(4))
p=world_to_camera_view(sc,sc.camera,Vector((0,0,0)));cam['groundRootPixels']=[p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
phases=[];movingMatrices=[]
for f in range(1,13):
 sc.frame_set(f);bpy.context.view_layer.update();v=[root.matrix_world.inverted()@p for o in meshes for p in surface(o)['vertices']];st=[o.name for o in coll.all_objects if o!=root and o!=car and o.parent!=car and mx(o.matrix_basis)!=neutral[o.name]]
 phases.append({'sourceFrame':f,'deltaY':car.location.y,'nativeAction':car.animation_data.action.name if car.animation_data and car.animation_data.action else None,'bounds':bb(v),'insideReserve':all(-.18-1e-7<=p.x<=.18+1e-7 and -.62-1e-7<=p.y<=.62+1e-7 and -1e-7<=p.z<=.48+1e-7 for p in v),'staticBasisChanged':st,'mouthLocal':list(root.matrix_world.inverted()@bpy.data.objects['harpoon__actual_mouth'].matrix_world.translation)});movingMatrices.append(car.matrix_basis.copy())
action=car.animation_data.action;curves=[]
for layer in action.layers:
 for strip in layer.strips:
  for slot in action.slots:
   bag=strip.channelbag(slot)
   if bag:
    for fc in bag.fcurves:curves.append({'path':fc.data_path,'index':fc.array_index,'keys':[[*k.co] for k in fc.keyframe_points],'interpolation':[k.interpolation for k in fc.keyframe_points],'modifiers':[m.type for m in fc.modifiers],'extrapolation':fc.extrapolation})
replay=[]
for rep in [1,2]:
 if rep==2:
  bpy.ops.wm.open_mainfile(filepath=str(S/'project.blend'));sc=bpy.context.scene;root=bpy.data.objects['harpoon__root']
 for d,angle in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
  root.rotation_euler.z=angle
  for clip,f in [('idle',1),('active',1),('active',6),('active',12)]:
   sc.frame_set(f);bpy.context.view_layer.update();dst=O/f'repeat{rep}-{clip}-{d}-{f:02}.png';sc.render.filepath=str(dst);bpy.ops.render.render(write_still=True);replay.append({'repeat':rep,'clip':clip,'direction':d,'frame':f,'path':str(dst.relative_to(R)),'original':str((C/'native'/f'{clip}-{d}'/f'{f-1:03}.png').relative_to(E))})
js(R/'standalone-measurements.json',{'sourceSHA256':sha(S/'project.blend'),'camera':cam,'rootNeutralIdentity':neutral['harpoon__root'],'meshCount':len(canonical),'canonicalFingerprints':{n:digest(v) for n,v in canonical.items()},'phases':phases,'curves':curves,'exactPhaseDisplacementErrors':[phases[i]['deltaY']-contract['nativeMotion']['activeDeltaLocalYBySourceFrame'][i] for i in range(12)],'renders':replay})
# Reopen immutable main, establish untouched neutral native context, append exact own resources.
bpy.ops.wm.open_mainfile(filepath=str(S/'main.blend'));sc=bpy.context.scene;main=bpy.data.objects['submarine-yellow__root'];main.rotation_euler.z=0
for name,actionName in json.loads(main['nativeActions'])['upgraded-dock-ready'].items():
 o=bpy.data.objects[name];o.animation_data_create();a=bpy.data.actions[actionName];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
sc.frame_set(1);bpy.context.view_layer.update();body=[o for o in sc.objects if o.type=='MESH' and o.name.startswith('body__')];before={o.name:digest(nativeResource(o)) for o in body};mainbasis={o.name:mx(o.matrix_basis) for o in sc.objects};mainactions={o.name:o.animation_data.action.name if o.animation_data and o.animation_data.action else None for o in sc.objects};mcam=mx(sc.camera.matrix_world);mlights=[(o.name,list(o.location),o.data.energy,o.data.size) for o in sc.objects if o.type=='LIGHT']
for o in sc.objects:
 if o.name.startswith('PROVISIONAL__harpoon_'):o.hide_render=True;o.hide_viewport=True
with bpy.data.libraries.load(str(S/'project.blend'),link=False) as (src,dst):dst.collections=['CANONICAL__sub-harpoon-mount']
c=bpy.data.collections['CANONICAL__sub-harpoon-mount'];sc.collection.children.link(c);root=bpy.data.objects['harpoon__root'];car=bpy.data.objects['harpoon__recoil_carriage'];mount=bpy.data.objects['MOUNT__sub-harpoon-mount'];root.parent=mount;root.matrix_basis=Matrix.Identity(4);car.animation_data.action=None;car.matrix_basis=movingMatrices[0];bpy.context.view_layer.update();meshes=sorted([o for o in c.all_objects if o.type=='MESH'],key=lambda o:o.name)
identical={o.name:nativeResource(o)==canonical[o.name] for o in meshes};seat=surface(bpy.data.objects['body__harpoon_contact_seat']);foot=surface(bpy.data.objects['harpoon__bearing_foot']);seatfaces=[f for f in seat['faces'] if f['normal'][2]>.999];bear=[]
for face in foot['faces']:
 ps=[Vector(p) for p in face['vertices']];local=[root.matrix_world.inverted()@p for p in ps]
 if face['normal'][2]<-.999 and max(abs(p.z) for p in local)<1e-6:
  hits=[s for s in seatfaces if all(inside(s['vertices'],p) and abs(p.z-s['vertices'][0][2])<1e-5 for p in ps)];area=sum((ps[i]-ps[0]).cross(ps[i+1]-ps[0]).length/2 for i in range(1,len(ps)-1));bear.append({'worldVertices':[list(p) for p in ps],'localVertices':[list(p) for p in local],'footNormal':face['normal'],'fullyContainedInNativeFiniteFace':bool(hits),'areaWorld':area,'centroid':list(sum(ps,Vector())/len(ps)),'centerInside':inside([list(p) for p in ps],root.matrix_world@Vector((0,.343,0))),'planeMaxDistance':max(abs(p.z-seatfaces[0]['vertices'][0][2]) for p in ps)})
mainmeshes=[o for o in sc.objects if o.type=='MESH' and o not in meshes and not o.hide_render];mt={o.name:surface(o) for o in mainmeshes};hull=mt['body__hull'];focals=[o for o in mainmeshes if o.name.startswith('body__') and any(k in o.name for k in ['glass','port_','hatch','periscope'])];v=[];ix=[]
for o in focals:
 off=len(v);s=mt[o.name];v+=s['vertices'];ix += [tuple(i+off for i in tri) for tri in s['indices']]
focal={'vertices':v,'indices':ix,'triangles':[[v[i] for i in f] for f in ix],'tree':BVHTree.FromPolygons(v,ix,all_triangles=True,epsilon=0)}
cache={};allphases=[]
for i,M in enumerate(movingMatrices):
 car.matrix_basis=M;bpy.context.view_layer.update();intersections=[];ds=[]
 for o in meshes:
  A=surface(o)
  for n,T in mt.items():
   overlap=A['tree'].overlap(T['tree'])
   if overlap:intersections.append({'own':o.name,'main':n,'trianglePairs':len(overlap),'intendedSeat':o.name=='harpoon__bearing_foot' and n=='body__harpoon_contact_seat'})
  key=(o.name,i if o.parent==car else -1)
  if key not in cache:cache[key]={'hull':exactdistance(A,hull),'focal':exactdistance(A,focal)}
  ds.append({'own':o.name,**cache[key]})
 allphases.append({'frame':i+1,'deltaY':M[1][3],'intersections':intersections,'minimumHull':min(x['hull'] for x in ds),'hullClosest':min(ds,key=lambda x:x['hull']),'minimumFocal':min(x['focal'] for x in ds),'focalClosest':min(ds,key=lambda x:x['focal']),'mouthWorld':list(bpy.data.objects['harpoon__actual_mouth'].matrix_world.translation)});print('INDEPENDENT_PHASE',i+1,flush=True)
car.matrix_basis=movingMatrices[0];bpy.context.view_layer.update();mountedRenders=[]
for d,angle in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 main.rotation_euler.z=angle;bpy.context.view_layer.update();dst=O/f'mounted-neutral-{d}.png';sc.render.filepath=str(dst);bpy.ops.render.render(write_still=True);mountedRenders.append(str(dst.relative_to(R)))
main.rotation_euler.z=0;bpy.context.view_layer.update();after={o.name:digest(nativeResource(o)) for o in body};mouth=bpy.data.objects['harpoon__actual_mouth'];axis=mouth.matrix_world.to_3x3()@Vector((0,-1,0))
js(R/'mounted-measurements.json',{'frozenMainSHA256':sha(S/'main.blend'),'candidateSHA256':sha(S/'project.blend'),'mount':mx(mount.matrix_world),'rootBasis':mx(root.matrix_basis),'exactCanonicalResourcesByMesh':identical,'bodyResourcesUnchanged':before==after,'bodyBefore':before,'bodyAfter':after,'mainBasisUnchanged':all(mx(bpy.data.objects[n].matrix_basis)==v for n,v in mainbasis.items()),'mainActionAssignmentsUnchanged':all((bpy.data.objects[n].animation_data.action.name if bpy.data.objects[n].animation_data and bpy.data.objects[n].animation_data.action else None)==a for n,a in mainactions.items()),'cameraUnchanged':mx(sc.camera.matrix_world)==mcam,'lightsUnchanged':[(o.name,list(o.location),o.data.energy,o.data.size) for o in sc.objects if o.type=='LIGHT']==mlights,'seatFaces':seatfaces,'bearing':bear,'phases':allphases,'actualNeutralMouth':list(mouth.matrix_world.translation),'axisWorld':list(axis.normalized()),'legacy':list(bpy.data.objects['sub_harpoon'].location),'mountedRenders':mountedRenders,'distanceMethod':'Independent native data replay; inspected hash-bound pure exact triangle-distance helpers use vertex-face, edge-edge, BVH intersection and conservative centroid-sphere candidate ranges. All phases derive from actual saved native curves, not submitted matrices.'})
print('INDEPENDENT_NATIVE_COMPLETE',flush=True)
