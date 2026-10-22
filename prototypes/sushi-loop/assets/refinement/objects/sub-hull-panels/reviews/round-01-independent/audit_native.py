import sys
sys.dont_write_bytecode=True
import bpy,json,pathlib,math,hashlib
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
out=pathlib.Path(__file__).resolve().parent;res=out/'resources';(out/'native-replay').mkdir(exist_ok=True);(out/'mounted-replay').mkdir(exist_ok=True)
def plain(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 try:return [plain(x) for x in v]
 except:return str(v)
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def bb(p):return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
def mat(m):
 return {'diffuse':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[(s.name,plain(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],'attrs':{k:plain(getattr(n,k)) for k in ['operation','blend_type','distribution','subsurface_method','interpolation','extension','projection','vector_type','space','convert_from','convert_to'] if hasattr(n,k)}} for n in m.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links]}
def mesh(o,reference):
 dg=bpy.context.evaluated_depsgraph_get();eo=o.evaluated_get(dg);m=eo.to_mesh();M=reference.matrix_world.inverted()@eo.matrix_world;normM=M.to_3x3().inverted().transposed()
 v={'vertices':[list(M@v.co) for v in m.vertices],'polygons':[(list(p.vertices),p.material_index,p.use_smooth) for p in m.polygons],'normals':[list((normM@n.vector).normalized()) for n in m.corner_normals],'uv':{layer.name:[list(u.uv) for u in layer.data] for layer in m.uv_layers},'materials':[digest(mat(s.material)) for s in o.material_slots]};eo.to_mesh_clear();return v
sc=bpy.context.scene;root=bpy.data.objects['sub-hull-panels__root'];motion=bpy.data.objects['sub-hull-panels__motion'];actions=json.loads(root['nativeClipActions']);meshes=[o for o in root.children_recursive if o.type=='MESH']
def bind(clip,frame=1,d='S'):
 a=bpy.data.actions[actions[clip]];motion.animation_data.action=a;motion.animation_data.action_slot=a.slots[0];root.rotation_euler=(0,0,{'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d]);sc.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
bind('idle');canonical={o.name:mesh(o,root) for o in meshes};canonhash={k:digest(v) for k,v in canonical.items()};verts=[Vector(v) for data in canonical.values() for v in data['vertices']];bounds=bb(verts)
assert len(meshes)==20 and all(o.parent==motion for o in meshes);assert sc.render.filter_size==.5 and [sc.render.resolution_x,sc.render.resolution_y]==[768,1408]
for name,data in canonical.items():
 box=[[-.52,-.30,0],[-.34,.30,.16]] if name.startswith('panel_L') else [[.34,-.30,0],[.52,.30,.16]]
 assert all(box[0][i]-1e-6<=v[i]<=box[1][i]+1e-6 for v in data['vertices'] for i in range(3))
cam=sc.camera;dg=bpy.context.evaluated_depsgraph_get();camera={'worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(dg,x=768,y=1408,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'nativeFrame':[768,1408],'filterSize':sc.render.filter_size,'engine':sc.render.engine,'fps':sc.render.fps}
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return [p.x*768,(1-p.y)*1408]
camera['root']=px((0,0,0));camera['basis']={name:[v-a for v,a in zip(px(p),camera['root'])] for name,p in [('X',(1,0,0)),('depth',(0,-1,0)),('height',(0,0,1))]}
orig=json.loads((res/'original-camera.json').read_text());assert max(abs(camera['worldMatrix'][r][c]-orig['camera']['worldMatrix'][r][c]) for r in range(4) for c in range(4))<1e-6;assert max(abs(camera['projectionMatrix'][r][c]-orig['camera']['projectionMatrix'][r][c]) for r in range(4) for c in range(4))<1e-6
motionchecks=[]
for i in range(1201):
 f=1+i/100;bind('active',f);theta=math.tau*(f-1)/12;s=1+.015*math.sin(theta);b=.008*(1-math.cos(theta));err=max(abs(motion.scale[j]-s) for j in range(3));err=max(err,abs(motion.location.z-b));assert err<1e-7,(f,err)
 motionchecks.append({'frame':f,'scale':list(motion.scale),'location':list(motion.location),'minimumZ':bounds[0][2]*motion.scale.z+motion.location.z,'maximumZ':bounds[1][2]*motion.scale.z+motion.location.z,'errorVsFrozenLaw':err})
assert min(p['minimumZ'] for p in motionchecks)>=-1e-8
renders=[]
for d in 'NESW':
 for clip,frames in [('idle',[1]),('active',list(range(1,14)))]:
  for f in frames:
   bind(clip,f,d);path=out/'native-replay'/f'{clip}-{d}-{f:02}.png';sc.render.filepath=str(path)
   if not path.exists():bpy.ops.render.render(write_still=True)
   renders.append({'clip':clip,'direction':d,'frame':f,'path':str(path.relative_to(out))})
 for f in [2.5,5.5,8.5,11.5]:
  bind('active',f,d);path=out/'native-replay'/f'half-{d}-{f:04.1f}.png';sc.render.filepath=str(path)
  if not path.exists():bpy.ops.render.render(write_still=True)
  renders.append({'clip':'half','direction':d,'frame':f,'path':str(path.relative_to(out))})
# Reopen the exact frozen body; append ONLY the neutral native resource collection.
bpy.ops.wm.open_mainfile(filepath=str(res/'frozen-main.blend'));sc=bpy.context.scene;mainroot=bpy.data.objects['submarine-yellow__root'];mainactions=json.loads(mainroot['nativeActions'])
for owner,an in mainactions['upgraded-dock-ready'].items():
 o=bpy.data.objects[owner];a=bpy.data.actions[an];o.animation_data_create();o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
mainroot.rotation_euler=(0,0,0);sc.frame_set(1);bpy.context.view_layer.update()
body_before={o.name:digest(mesh(o,mainroot)) for o in sc.objects if o.type=='MESH' and o.name.startswith('body__')}
with bpy.data.libraries.load(str(res/'neutral.blend'),link=False) as (a,b):b.collections=['SUB_HULL_PANELS__neutral']
coll=b.collections[0];sc.collection.children.link(coll);neutralroot=next(o for o in coll.objects if o.name=='sub-hull-panels__root');mount=bpy.data.objects['MOUNT__sub-hull-panels'];neutralroot.parent=mount;neutralroot.matrix_parent_inverse=Matrix.Identity(4);neutralroot.matrix_basis=Matrix.Identity(4)
for o in coll.objects:
 if o.animation_data and o.animation_data.action:
  assert o.animation_data.action.name=='PANELS__idle_neutral','Neutral has a non-idle binding'
  o.animation_data_clear()
 o.hide_set(False);o.hide_render=False;o.hide_viewport=False
for o in sc.objects:
 if o.name.startswith('PROVISIONAL__panel'):o.animation_data_clear();o.hide_render=True
bpy.context.view_layer.update();neutralmeshes=[o for o in coll.objects if o.type=='MESH'];inverse={o.name:digest(mesh(o,neutralroot)) for o in neutralmeshes};assert inverse==canonhash,'Neutral resource mismatch'
assert body_before=={o.name:digest(mesh(o,mainroot)) for o in sc.objects if o.type=='MESH' and o.name.startswith('body__')}
expected=Matrix(((.5,0,0,0),(0,.5,0,.16),(0,0,.5,.65),(0,0,0,1)));assert max(abs(mount.matrix_local[r][c]-expected[r][c]) for r in range(4) for c in range(4))<1e-7

def worldgeom(o):
 eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=eo.to_mesh();m.calc_loop_triangles();p=[eo.matrix_world@v.co for v in m.vertices];polys=[list(f.vertices) for f in m.polygons];tri=[list(t.vertices) for t in m.loop_triangles];eo.to_mesh_clear();return p,polys,tri

def area_centroid(poly):
 s=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]));return abs(s)/2,[sum((a[i]+b[i])*(a[0]*b[1]-b[0]*a[1]) for a,b in zip(poly,poly[1:]+poly[:1]))/(3*s) for i in range(2)]
def cross(a,b,p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def clip_polygon(poly,seat):
 if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(seat,seat[1:]+seat[:1]))<0:seat=list(reversed(seat))
 for a,b in zip(seat,seat[1:]+seat[:1]):
  result=[]
  for u,v in zip(poly,poly[1:]+poly[:1]):
   cu,cv=cross(a,b,u),cross(a,b,v);iu,iv=cu>=-1e-12,cv>=-1e-12
   if iu:result.append(u)
   if iu!=iv:
    t=cu/(cu-cv);result.append([u[i]+t*(v[i]-u[i]) for i in range(2)])
  poly=result
  if not poly:break
 return poly
contacts=[]
for side,sign in [('L',-1),('R',1)]:
 seat=bpy.data.objects[f'body__panel_contact_seat_{sign}'];sp,sf,st=worldgeom(seat);face=next([sp[i] for i in f] for f in sf if (sp[f[1]]-sp[f[0]]).cross(sp[f[2]]-sp[f[0]]).normalized().z>.999);plane=face[0].z;seatpoly=[[v.x,v.y] for v in face];seat_area,_=area_centroid(seatpoly);base=bpy.data.objects[f'panel_{side}__seat_base'];bp,bf,bt=worldgeom(base);regions=[];normals=[];center=[sign*.215,.16]
 for inds in bt:
  pp=[bp[i] for i in inds];n=(pp[1]-pp[0]).cross(pp[2]-pp[0]).normalized()
  if n.z<-.999 and max(abs(v.z-plane) for v in pp)<1e-6:
   poly=clip_polygon([[v.x,v.y] for v in pp],seatpoly)
   if len(poly)>=3:
    area,centroid=area_centroid(poly)
    if area>1e-12:regions.append({'polygon':poly,'area':area,'centroid':centroid});normals.append(list(n))
 total=sum(r['area'] for r in regions);centroid=[sum(r['area']*r['centroid'][i] for r in regions)/total for i in range(2)];points=[p for r in regions for p in r['polygon']];inside=any(len(clip_polygon([[center[0]-1e-9,center[1]-1e-9],[center[0]+1e-9,center[1]-1e-9],[center[0],center[1]+1e-9]],r['polygon']))>=3 for r in regions)
 assert total>0 and inside
 contacts.append({'side':side,'clippedIntersectionArea':total,'availableSeatArea':seat_area,'coverage':total/seat_area,'centroid':centroid+[plane],'extents':[max(p[i] for p in points)-min(p[i] for p in points) for i in range(2)],'containsIntendedSeatCenter':inside,'seatCenter':center+[plane],'normal':normals[0],'planeSeparation':max(abs(v.z-plane) for v in bp if abs(v.z-plane)<1e-6),'actualClippedTriangleRegions':regions})
intersections=[];bodymeshes=[o for o in sc.objects if o.type=='MESH' and o.name.startswith('body__')];trees={o.name:BVHTree.FromPolygons(*worldgeom(o)[:2]) for o in bodymeshes}
for o in neutralmeshes:
 pp,ff,tt=worldgeom(o);tree=BVHTree.FromPolygons(pp,ff)
 for b in bodymeshes:
  pairs=tree.overlap(trees[b.name])
  if pairs:intersections.append({'candidate':o.name,'body':b.name,'pairs':len(pairs),'intentionalSeatContact':'seat_base' in o.name and 'panel_contact_seat' in b.name})
assert not any(not r['intentionalSeatContact'] for r in intersections),intersections
mounted=[]
for d,ang in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 mainroot.rotation_euler.z=ang;bpy.context.view_layer.update();p=out/'mounted-replay'/f'{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);mounted.append({'direction':d,'path':str(p.relative_to(out))})
record={'candidateSHA256':hashlib.sha256((res/'candidate.blend').read_bytes()).hexdigest(),'nativeCamera':camera,'meshIdentityDigests':canonhash,'nativeMeshes':len(meshes),'nativeNeutralBounds':bounds,'allMeshesInsideFrozenSideBoxes':True,'motionSamples':motionchecks,'motionMaximumLawError':max(p['errorVsFrozenLaw'] for p in motionchecks),'motionMinimumZ':min(p['minimumZ'] for p in motionchecks),'motionMaximumZ':max(p['maximumZ'] for p in motionchecks),'nativeRenders':renders,'neutralAndInverseMountMeshNormalUVMaterialIdentity':inverse==canonhash,'frozenBodyGeometryNormalsUVMaterialsUnchanged':True,'actualMount':[list(r) for r in mount.matrix_local],'finiteSeatContacts':contacts,'nativeBodySurfaceIntersections':intersections,'mountedRenders':mounted,'finalMainApproval':False}
(out/'native-independent-audit.json').write_text(json.dumps(record,indent=2));print('INDEPENDENT_AUDIT_COMPLETE',len(renders),len(contacts),len(intersections))
