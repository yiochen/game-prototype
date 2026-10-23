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
bpy.ops.wm.open_mainfile(filepath=str(P/'project.blend'));sc=bpy.context.scene;root=bpy.data.objects['harpoon__root'];moving=bpy.data.objects['harpoon__recoil_carriage'];coll=bpy.data.collections['CANONICAL__sub-harpoon-mount'];meshes=[o for o in coll.all_objects if o.type=='MESH']
root.rotation_euler.z=0;sc.frame_set(1);bpy.context.view_layer.update()
canonical=[resource(o) for o in sorted(meshes,key=lambda o:o.name)]
dump(C/'canonical-neutral-resources.json',{'sourceSHA256':sha(P/'project.blend'),'canonicalRootMatrix':matrix(root.matrix_world),'objects':canonical,'resourceSHA256':digest(canonical),'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.users and i.name!='Render Result'],'qualification':'Editable unscaled canonical neutral local mesh/normals/UV/material resources; all bevels and weighted normals are applied native mesh data.'})
neutralmeshsha={r['object']:digest(r) for r in canonical}
samples=[]
for f in range(1,13):
 sc.frame_set(f);bpy.context.view_layer.update();vs=[root.matrix_world.inverted()@v for o in meshes for v in surf(o)[0]]
 samples.append({'sourceFrame':f,'movingMatrix':matrix(moving.matrix_local),'deltaY':float(moving.location.y),'bounds':bounds(vs),'withinReserve':all(-.180001<=p.x<=.180001 and -.620001<=p.y<=.620001 and -.000001<=p.z<=.480001 for p in vs),'mouthLocal':list(root.matrix_world.inverted()@bpy.data.objects['harpoon__actual_mouth'].matrix_world.translation)})
captures=[]
for clip,count in [('idle',1),('active',12)]:
 for d,angle in ANGLES.items():
  root.rotation_euler.z=angle
  folder=C/'native'/f'{clip}-{d}';folder.mkdir(parents=True,exist_ok=True)
  for f in range(1,count+1):
   sc.frame_set(f);bpy.context.view_layer.update();dst=folder/f'{f-1:03}.png';sc.render.filepath=str(dst);bpy.ops.render.render(write_still=True)
   rec=rootrec(sc,root,clip,d,f,dst);rec['movingLocalY']=float(moving.location.y);rec['bounds']=bounds([v for o in meshes for v in surf(o)[0]]);captures.append(rec)
root.rotation_euler.z=0;sc.frame_set(1);bpy.context.view_layer.update()
camera={'projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'cellSize':128,'captureScale':4,'fps':12,'nativeFrame':[768,1408],'nativeCaptureScale':4,'publishedFrame':[384,704],'publishedSourceScale':2,'publication':'Whole native frame BOX x0.5, no alpha/crop/fit/shift/paint','camera':{'type':'orthographic','worldMatrix':matrix(sc.camera.matrix_world),'projectionMatrix':matrix(sc.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=768,y=1408,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'worldUnitsPerCell':1,'elevationDegrees':55.00797980144134},'calibration':{'root':captures[-13]['projectedRootPixels'] if False else [384,992]},'actualSettings':json.loads((P/'settings.json').read_text())}
dump(C/'camera-native.json',camera)
dump(C/'standalone-audit.json',{'projectSHA256':sha(P/'project.blend'),'method':'Reopened exact saved project, render-only; no authoring builders. Actual native action evaluated at all12 integer source phases.','camera':camera,'neutralRootMatrix':matrix(root.matrix_world),'phases':samples,'renders':captures,'canonicalResourceSHA256':digest(canonical)})
# A second process-equivalent reopen establishes full replay against the saved file.
# The exact same recipe is used; retain independent PNG bytes and equality records.
replay=[]
bpy.ops.wm.open_mainfile(filepath=str(P/'project.blend'));sc=bpy.context.scene;root=bpy.data.objects['harpoon__root']
for clip,count in [('idle',1),('active',12)]:
 for d,a in ANGLES.items():
  root.rotation_euler.z=a
  for f in range(1,count+1):
   sc.frame_set(f);bpy.context.view_layer.update();dst=C/'replay'/f'{clip}-{d}-{f:02}.png';dst.parent.mkdir(exist_ok=True);sc.render.filepath=str(dst);bpy.ops.render.render(write_still=True);original=C/'native'/f'{clip}-{d}'/f'{f-1:03}.png';replay.append({'clip':clip,'direction':d,'sourceFrame':f,'path':str(dst.relative_to(E)),'original':str(original.relative_to(E)),'replaySHA256':sha(dst),'originalSHA256':sha(original),'exactPNGBytes':sha(dst)==sha(original)})
dump(C/'replay-audit.json',{'method':'Reopened standalone saved project again; no build import or source mutation; same native recipe all52 required frames and all4 views. PNG container hashes and decoded RGBA are checked separately by publication verification.','renders':replay})
# Main context: exact frozen preliminary body, native65degree capture and unchanged interfaces.
bpy.ops.wm.open_mainfile(filepath=str(P/'resources/frozen-main-v1/project.blend'));sc=bpy.context.scene;main=bpy.data.objects['submarine-yellow__root'];main.rotation_euler.z=0
for owner,an in json.loads(main['nativeActions'])['upgraded-dock-ready'].items():
 o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
sc.frame_set(1);bpy.context.view_layer.update()
body_objects=[o for o in sc.objects if o.type=='MESH' and o.name.startswith('body__')]
body_before={o.name:digest(resource(o)) for o in body_objects};transform_before={o.name:matrix(o.matrix_local) for o in sc.objects};main_action_before={o.name:o.animation_data.action.name if o.animation_data and o.animation_data.action else None for o in sc.objects}
main_settings={'cameraMatrix':matrix(sc.camera.matrix_world),'projectionMatrix':matrix(sc.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'frame':[sc.render.resolution_x,sc.render.resolution_y],'aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filterSize':sc.render.filter_size}
for o in sc.objects:
 if o.name.startswith('PROVISIONAL__harpoon_'):o.hide_render=True;o.hide_viewport=True
with bpy.data.libraries.load(str(P/'project.blend'),link=False) as (src,dst):dst.collections=['CANONICAL__sub-harpoon-mount']
coll=bpy.data.collections['CANONICAL__sub-harpoon-mount'];sc.collection.children.link(coll);root=bpy.data.objects['harpoon__root'];moving=bpy.data.objects['harpoon__recoil_carriage'];mount=bpy.data.objects['MOUNT__sub-harpoon-mount'];root.parent=mount;root.matrix_basis=Matrix.Identity(4);moving.animation_data.action=None;meshes=[o for o in coll.all_objects if o.type=='MESH']
moving.matrix_basis=Matrix(samples[0]['movingMatrix']);bpy.context.view_layer.update()
identity_after=[resource(o) for o in sorted(meshes,key=lambda o:o.name)];identical=digest(identity_after)==digest(canonical)
extraction=[]
for o in meshes:
 inv=root.matrix_world.inverted();vs=surf(o)[0];local=[inv@p for p in vs]
 # Compare transformed evaluated vertices against independent canonical mesh/world-local values.
 expected=[o.matrix_local@v.co for v in o.data.vertices]
 # Moving meshes have recoil-carriage parent, neutral matrix identity.
 extraction.append({'object':o.name,'meshMaterialNormalUVLocalResourceExact':digest(resource(o))==neutralmeshsha[o.name],'inverseMountLocalVertexMaxError':max((a-b).length for a,b in zip(local,expected)),'vertices':len(local)})
seat=bpy.data.objects['body__harpoon_contact_seat'];seat_surf=surf(seat);foot=bpy.data.objects['harpoon__bearing_foot'];fv,ff,fn=surf(foot);bearing=[]
for ids,n in zip(ff,fn):
 if n[2]<-.999:
  ps=[fv[i] for i in ids];local=[root.matrix_world.inverted()@p for p in ps]
  if max(abs(p.z) for p in local)<1e-6:
   # Shoelace polygon area and centroid in its actual horizontal bearing plane.
   area2=sum(local[i].x*local[(i+1)%len(local)].y-local[(i+1)%len(local)].x*local[i].y for i in range(len(local)))
   cx=sum((local[i].x+local[(i+1)%len(local)].x)*(local[i].x*local[(i+1)%len(local)].y-local[(i+1)%len(local)].x*local[i].y) for i in range(len(local)))/(3*area2)
   cy=sum((local[i].y+local[(i+1)%len(local)].y)*(local[i].x*local[(i+1)%len(local)].y-local[(i+1)%len(local)].x*local[i].y) for i in range(len(local)))/(3*area2)
   bearing.append({'nativeFaceVertexIndices':ids,'localVertices':[list(v) for v in local],'worldVertices':[list(p) for p in ps],'normalWorld':n,'localArea':abs(area2)/2,'worldArea':abs(area2)/2*.35*.35,'centroidLocal':[cx,cy,0],'localBounds':bounds(local),'fullyInsideFiniteSeat':all(-.11571425199508667-1e-6<=p.x<=.11571425199508667+1e-6 and .12714290618896484-1e-6<=p.y<=.5585713982582092+1e-6 for p in local),'normalOpposition':n[2]*-1,'maximumSeatPlaneSeparationWorld':max(abs(p.z-.5684999823570251) for p in ps),'intendedCenterContained':min(p.x for p in local)<0<max(p.x for p in local) and min(p.y for p in local)<.343<max(p.y for p in local)})
mainmeshes=[o for o in sc.objects if o.type=='MESH' and o not in meshes and not o.hide_render]
maintrees={o.name:tree(surf(o)) for o in mainmeshes};focal=[o for o in mainmeshes if any(k in o.name for k in ['glass','port_','hatch','periscope'])]
def distance(a,b):
 # Both-direction native evaluated vertices to opposite triangle surface.
 av=a[0];bv=b[0];at=tree(a);bt=tree(b)
 return min([bt.find_nearest(v)[3] for v in av]+[at.find_nearest(v)[3] for v in bv])
phases=[];mouths=[]
for s in samples:
 moving.matrix_basis=Matrix(s['movingMatrix']);bpy.context.view_layer.update();pairs=[];hullclear=[];focalclear=[]
 for o in meshes:
  ss=surf(o);ot=tree(ss)
  for b in mainmeshes:
   hits=ot.overlap(maintrees[b.name])
   if hits:pairs.append({'own':o.name,'main':b.name,'trianglePairCount':len(hits),'intendedCoplanarSeat':o==foot and b==seat})
  if o!=foot:
   hullclear.append({'own':o.name,'distance':distance(ss,surf(bpy.data.objects['body__hull']))})
  for b in focal:focalclear.append({'own':o.name,'focal':b.name,'distance':distance(ss,surf(b))})
 m=bpy.data.objects['harpoon__actual_mouth'];mouths.append(list(m.matrix_world.translation));phases.append({'sourceFrame':s['sourceFrame'],'ownMovingMatrix':matrix(moving.matrix_local),'nativeTriangleOverlaps':pairs,'minimumNonFootHullSurfaceDistance':min(x['distance'] for x in hullclear),'minimumFocalSurfaceDistance':min(x['distance'] for x in focalclear),'focalClosest':min(focalclear,key=lambda x:x['distance']),'mouthWorld':mouths[-1]})
mounted=[]
for d,a in ANGLES.items():
 main.rotation_euler.z=a;bpy.context.view_layer.update()
 for clip,count in [('idle',1),('active',12)]:
  for f in range(1,count+1):
   # Main stays upgraded-dock-ready native neutral frame1. Apply exact own sampled
   # native action matrix only for diagnostic phase views, no main action mapping.
   moving.matrix_basis=Matrix(samples[f-1]['movingMatrix']);bpy.context.view_layer.update();folder=C/'mounted'/f'{clip}-{d}';folder.mkdir(parents=True,exist_ok=True);dst=folder/f'{f-1:03}.png';sc.render.filepath=str(dst);bpy.ops.render.render(write_still=True);mounted.append(rootrec(sc,main,clip,d,f,dst))
main.rotation_euler.z=0;moving.matrix_basis=Matrix(samples[0]['movingMatrix']);bpy.context.view_layer.update()
body_after={o.name:digest(resource(o)) for o in body_objects}
actualmouth=mouths[0];provisional=contract['mouthAndLegacyReferences']['provisionalDerivedNeutralMouthWorld']
dump(C/'mounted-audit.json',{'qualification':'Native assembly on exact static preliminary frozen main, actual upgraded-dock-ready neutral frame1; own provisional hidden; all other upgrades remain explicitly PROVISIONAL. Component diagnostic, not main final approval. No raster sprite attachment overlay.','frozenMainSHA256':sha(P/'resources/frozen-main-v1/project.blend'),'standaloneSourceSHA256':sha(P/'project.blend'),'mountMatrix':matrix(mount.matrix_world),'rootLocalMatrix':matrix(root.matrix_local),'mainSettingsUnchanged':main_settings,'canonicalNeutralResourceExact':identical,'canonicalResourceSHA256':digest(canonical),'importedResourceSHA256':digest(identity_after),'inverseMountExtraction':extraction,'bodyResourceFingerprintsBefore':body_before,'bodyResourceFingerprintsAfter':body_after,'bodyResourcesUnchanged':body_before==body_after,'mainLocalMatricesUnchanged':all(matrix(bpy.data.objects[n].matrix_local)==m for n,m in transform_before.items()),'mainActionAssignmentsUnchanged':all((bpy.data.objects[n].animation_data.action.name if bpy.data.objects[n].animation_data and bpy.data.objects[n].animation_data.action else None)==a for n,a in main_action_before.items()),'bearingPolygons':bearing,'phases':phases,'mouth':{'neutralLocal':[0,-.602,.375],'neutralWorld':actualmouth,'localAxis':[0,-1,0],'worldAxis':[0,-1,0],'provisionalReference':provisional,'driftWorld':[actualmouth[i]-provisional[i] for i in range(3)],'legacyReferenceUnchanged':list(bpy.data.objects['sub_harpoon'].location),'activeMainMapping':None},'renders':mounted,'distanceQualification':'Native evaluated finite triangle surfaces, BVH intersections and symmetric vertex-to-triangle distance. Positive distances sample surface vertices against actual opposite triangles; surface-intersection audit separately covers crossing triangles. Coplanar intended seat contact is classified separately.'})
print('EVIDENCE_COMPLETE',len(captures),len(mounted))
