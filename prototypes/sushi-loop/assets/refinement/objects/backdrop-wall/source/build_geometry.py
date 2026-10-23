import bpy,math,json,hashlib
from mathutils import Matrix,Vector
from pathlib import Path
P=Path(__file__).resolve().parent.parent
SOURCE=(P/'../../backups/927a8a59e8d0f1e9-restaurant-backdrop-35.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
W=bpy.data.collections['S33_PROP_uniform35-wall-plain'];W.hide_render=False;W.hide_viewport=False
keep=set(W.all_objects)
# Isolate the authored wall. No unrelated geometry, textures or fixtures survive.
for o in list(bpy.data.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
sc=bpy.data.scenes.new('Warm Soft Backdrop Wall');bpy.context.window.scene=sc;sc.collection.children.link(W)
for s in list(bpy.data.scenes):
 if s!=sc:bpy.data.scenes.remove(s)
for c in list(bpy.data.collections):
 if c!=W:bpy.data.collections.remove(c)
for o in W.objects:o.hide_render=False;o.hide_viewport=False
root=bpy.data.objects['uniform35-wall-plain__root'];root.location=(0,0,0);root.rotation_euler=(0,0,0)
bpy.context.view_layer.update()
Z=1.0025131702423096
edits=[]
M=lambda n:bpy.data.materials['S33_uniform35_'+n]

def mesh_object(name,vs,fs,mat,parent=root):
 me=bpy.data.meshes.new(name+' mesh');me.from_pydata(vs,[],fs);me.update();me.materials.append(mat)
 ob=bpy.data.objects.new(name,me);W.objects.link(ob);ob.parent=parent;ob.scale.z=Z
 edits.append(name);return ob

def bevel(ob,width=.007,segments=4):
 b=ob.modifiers.new('Crafted rounded edges','BEVEL');b.width=width;b.segments=segments;b.harden_normals=True
 for f in ob.data.polygons:f.use_smooth=True
 n=ob.modifiers.new('Broad planar normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=50
 return ob

def box(name,x0,x1,y0,y1,z0,z1,mat,width=.006):
 vs=[(x,y,z) for z in [z0,z1] for y in [y0,y1] for x in [x0,x1]]
 fs=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
 return bevel(mesh_object(name,vs,fs,mat),width)

def rect_loop(x0,x1,z0,z1,y,chamfer=0):
 c=chamfer
 if c:return [(x0+c,y,z0),(x1-c,y,z0),(x1,y,z0+c),(x1,y,z1-c),(x1-c,y,z1),(x0+c,y,z1),(x0,y,z1-c),(x0,y,z0+c)]
 return [(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)]

# A single continuous frame with chamfered corners and stepped native depth.
# The complete detail remains inside x±.416 and within the existing projecting cap.
loops=[rect_loop(-.416,.416,.405,2.365,-.505,.035),rect_loop(-.407,.407,.414,2.356,-.532,.032),rect_loop(-.380,.380,.442,2.328,-.532,.025),rect_loop(-.372,.372,.450,2.320,-.505,.022)]
vs=sum(loops,[]);fs=[]
for k in range(len(loops)-1):
 for i in range(8):fs.append((k*8+i,k*8+(i+1)%8,(k+1)*8+(i+1)%8,(k+1)*8+i))
for i in range(8):fs.append((24+i,24+(i+1)%8,(i+1)%8,i))
frame=bevel(mesh_object('wall__continuous_chamfered_field_molding',vs,fs,M('goldwood')),.0035,3)
# The inner ochre field is only 9mm proud of its backing, with readable softened corners.
# No target plane or texture image is used; this is a native thin solid plaster panel.
loops=[rect_loop(-.372,.372,.450,2.320,-.503,.022),rect_loop(-.367,.367,.455,2.315,-.512,.020)]
vs=sum(loops,[]);fs=[]
for i in range(8):fs.append((i,(i+1)%8,8+(i+1)%8,8+i))
fs.append(tuple(range(8,16)));fs.append(tuple(reversed(range(8))))
panel=mesh_object('wall__plaster_inset_field',vs,fs,M('wall_wood'))
# The source baseboard is rebuilt with a real recessed center and intact outer seam faces.
base=bpy.data.objects['uniform35-wall-plain__baseboard_face']
old=base.data;base.data=bpy.data.meshes.new('wall__native_recessed_baseboard_mesh')
# Mesh is in world-shaped local coordinates, inheriting source Z scale only.
base.location=(0,0,0)
outer=rect_loop(-.5,.5,0,.34,-.5)
loops=[outer,rect_loop(-.418,.418,.045,.295,-.5),rect_loop(-.397,.397,.062,.278,-.488),rect_loop(-.370,.370,.083,.257,-.478)]
vs=sum(loops,[]);fs=[]
for k in range(3):
 for i in range(4):fs.append((k*4+i,k*4+(i+1)%4,(k+1)*4+(i+1)%4,(k+1)*4+i))
fs.append(tuple(range(12,16)))
back=rect_loop(-.5,.5,0,.34,0);vs+=back
fs += [(0,16,17,1),(1,17,18,2),(2,18,19,3),(3,19,16,0),(16,19,18,17)]
base.data.from_pydata(vs,[],fs);base.data.materials.append(M('wood'));base.data.materials.append(M('goldwood'));base.data.update()
for f in base.data.polygons:
 if f.index in range(4,8):f.material_index=1
edits.append(base.name)
# Paired carved corbels use curved native extrusions, well away from protected seams.
profile=[(-.505,2.135),(-.534,2.135),(-.543,2.180),(-.555,2.223),(-.573,2.265),(-.598,2.301),(-.631,2.332),(-.664,2.351),(-.664,2.424),(-.505,2.424)]
for side,cx in [('left',-.29),('right',.29)]:
 vs=[(x,y,z) for x in [cx-.042,cx+.042] for y,z in profile];n=len(profile)
 fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]
 for i in range(n):fs.append((i,(i+1)%n,n+(i+1)%n,n+i))
 bevel(mesh_object('wall__'+side+'_curved_eave_corbel',vs,fs,M('wood')),.007,4)
 box('wall__'+side+'_corbel_capital',cx-.057,cx+.057,-.665,-.495,2.404,2.466,M('goldwood'),.006)
# Retain four-per-unit roof cadence, original endpoints and slab thickness,
# but give each ceramic slab a gently convex native cross section.
for ob in list(W.objects):
 if ob.type!='MESH' or 'flat_roof_tile' not in ob.name:continue
 vv=[v.co.copy() for v in ob.data.vertices];xs=sorted(set(round(v.x,6) for v in vv));ys=sorted(set(round(v.y,6) for v in vv));x0,x1=xs[0],xs[-1];y0,y1=ys[0],ys[-1]
 # Sloped source profile, retaining its exact endpoint heights. Row/cadence unchanged.
 zhi0=max(v.z for v in vv if abs(v.y-y0)<1e-5);zhi1=max(v.z for v in vv if abs(v.y-y1)<1e-5)
 nx,ny=12,8;verts=[];faces=[]
 for lower in [False,True]:
  for j in range(ny+1):
   t=j/ny;y=y0+(y1-y0)*t;line=zhi0+(zhi1-zhi0)*t
   for i in range(nx+1):
    u=i/nx;x=x0+(x1-x0)*u
    # Crown is zero at each authored edge; maximum remains below source ridge envelope.
    crown=.008*math.sin(math.pi*u)**2*math.sin(math.pi*t)**2
    z=line+crown-(.045 if lower else 0)
    verts.append((x,y,z))
 stride=(nx+1)*(ny+1)
 for side in [0,1]:
  offset=side*stride
  for j in range(ny):
   for i in range(nx):
    a=offset+j*(nx+1)+i;f=(a,a+1,a+nx+2,a+nx+1);faces.append(tuple(reversed(f)) if side else f)
 outline=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
 for k,a in enumerate(outline):b=outline[(k+1)%len(outline)];faces.append((a,a+stride,b+stride,b))
 mats=list(ob.data.materials);me=bpy.data.meshes.new(ob.name+' curved ceramic mesh');me.from_pydata(verts,[],faces);me.update();ob.data=me
 for ma in mats:me.materials.append(ma)
 bevel(ob,.006,4);edits.append(ob.name)
# Camera is an equivalent narrow crop of the original camera, never fitted to the mesh.
ca=bpy.data.cameras.new('Registered Wall Camera');camera=bpy.data.objects.new('Registered Wall Camera',ca);sc.collection.objects.link(camera);sc.camera=camera
camera.matrix_world=Matrix(json.loads((P/'inputs/source-assetRecord.json').read_text())['camera']['camera']['worldMatrix'])
ca.type='ORTHO';ca.sensor_fit='HORIZONTAL';ca.ortho_scale=1.5;ca.shift_x=0;ca.shift_y=.8088066280
sc.render.resolution_x=576;sc.render.resolution_y=1344;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.fps=12
sc.render.engine='CYCLES'
bpy.context.view_layer.update()
# Remove unused linked resources. Retain only used materials and meshes.
for image in list(bpy.data.images):
 if not image.users:bpy.data.images.remove(image)
for _ in range(3):bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
bpy.ops.file.pack_all()
(P/'source/geometry-stage.json').write_text(json.dumps({'source':str(SOURCE),'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'nativeDesignChanges':edits,'protectedSeamPlanes':[-.5,.5],'detailMaxAbsoluteX':.418,'geometryOnlyWaitingForFamilySettings':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/geometry-stage.blend'))
print('GEOMETRY_STAGE_READY')
