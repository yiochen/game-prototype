import bpy, math, json, hashlib, random, struct
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parents[1]; RES=BASE/'source/resources';OUT=BASE/'candidates/round-04';OUT.mkdir(parents=True,exist_ok=True)
DIR={'S':0,'E':90,'N':180,'W':-90};PROFILE=[(-.5,0),(.5,0),(.5,.67),(.45,1.04),(.31,1.15),(-.31,1.15),(-.45,1.04),(-.5,.67)]
def sm(x):x=max(0,min(1,x));return x*x*(3-2*x)
def mix(a,b,t):return a*(1-t)+b*t
def srgb(v):return ((v+.055)/1.055)**2.4 if v>.04045 else v/12.92
def color(z,cav,tone):
 h=sm(z/1.15);lo=(.14,.34,.59);mi=(.12,.47,.74);hi=(.24,.67,.87)
 bs=[mix(lo[i],mi[i],sm(h/.72)) for i in range(3)];bs=[mix(bs[i],hi[i],sm((h-.60)/.40)*.65) for i in range(3)]
 return tuple(srgb(max(0,min(1,c*(1-.34*cav)*(1+.055*tone)))) for c in bs)+(1,)
def top(t):
 t=abs(t)
 return 1.15 if t<=.31 else 1.15-(t-.31)/.14*.11 if t<=.45 else 1.04-(t-.45)/.05*.37
# Exact immutable canonical scene supplies material, lights, camera, capture, and measured boundary data.
bpy.ops.wm.open_mainfile(filepath=str(RES/'approved-middle/project.blend'));sc=bpy.context.scene;sc.name='Rock wall corner native refinement round 04';cam=sc.camera
mc=bpy.data.collections['rock-wall-middle__asset'];mr=bpy.data.objects['rock-wall-middle__root'];side=bpy.data.objects['rock-wall-middle__continuous_carved_stone'];NQ=279;NX=128
mat=side.data.materials[0]
# Actual stored corner normals, never reconstructed from expected filename rotations.
snorm={}
for lp in side.data.loops:snorm.setdefault(lp.vertex_index,Vector(side.data.corner_normals[lp.index].vector))
rings={}
for label,ix in [('W',0),('E',NX)]:
 rings[label]=[{'yz':tuple(side.data.vertices[ix*NQ+j].co[1:]),'color':tuple(side.data.color_attributes['stone_albedo'].data[ix*NQ+j].color),'normal':snorm[ix*NQ+j]} for j in range(NQ)]
def sample(y,z,label='E'):
 # Interpolation along the real eight-edge profile gives exact measured canonical boundary albedo/normal.
 rr=rings[label];best=None
 for j in range(len(rr)):
  a=rr[j];b=rr[(j+1)%len(rr)];ay,az=a['yz'];by,bz=b['yz'];dy,dz=by-ay,bz-az;den=dy*dy+dz*dz
  t=0 if den==0 else max(0,min(1,((y-ay)*dy+(z-az)*dz)/den));d=(y-ay-dy*t)**2+(z-az-dz*t)**2
  if best is None or d<best[0]:best=(d,a,b,t)
 _,a,b,t=best;c=tuple(mix(a['color'][i],b['color'][i],t) for i in range(4));n=(a['normal']*(1-t)+b['normal']*t).normalized();return c,n
# Clone canonical inward-relief native terminal surfaces at real W and N ports.
caps=[]
for name,source,rot in [('W','rock-wall-middle__W_connector_stone',0),('N','rock-wall-middle__E_connector_stone',90)]:
 ob=bpy.data.objects[source].copy();ob.data=ob.data.copy();ob.name='rock-wall-corner__'+name+'_native_connector';mc.objects.link(ob);ob.rotation_euler.z=math.radians(rot);caps.append(ob)
# New own collection/root, with no middle model left in the standalone source.
coll=bpy.data.collections.new('rock-wall-corner__asset');sc.collection.children.link(coll);root=bpy.data.objects.new('rock-wall-corner__root',None);coll.objects.link(root);root['assetId']='rock-wall-corner';root['cellSize']=128
for ob in caps:mc.objects.unlink(ob);coll.objects.link(ob);ob.parent=root
for ob in list(mc.objects):bpy.data.objects.remove(ob,do_unlink=True)
bpy.data.collections.remove(mc)
# One native cellular field follows the actual 3D surface around the crown, shoulder and exterior.
rng=random.Random(241022);sites=[]
for iz in range(5):
 for iy in range(3):
  for ix in range(3):sites.append((-.5+(ix+.5+rng.uniform(-.18,.18))/3,-.5+(iy+.5+rng.uniform(-.18,.18))/3,(iz+.5+rng.uniform(-.17,.17))/5*1.20,rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)))
def field3(p):
 x,y,z=p;near=[]
 for i,(sx,sy,sz,tone,sl,st,su) in enumerate(sites):
  dx=x-sx+.010*math.sin(z*7.3+sy*3);dy=y-sy+.010*math.sin(x*6.5+sz*4);dz=z-sz+.009*math.sin(y*7.1+sx*4)
  near.append((dx*dx+dy*dy+dz*dz*.94,i,dx,dy,dz))
 near.sort();a,b=near[:2];site=sites[a[1]];gap=(b[0]-a[0])/(2*math.sqrt(max(b[0],1e-8)));worn=sm(gap/.037)
 rel=min(0,-.034*(1-worn)+.065*(site[4]*a[2]+site[5]*a[3]+site[6]*a[4])*worn-.003)
 return rel,1-worn,site[3]
def roofheight(x,y):
 r=math.hypot(x+.5,.5-y)
 # Continue the actual canonical outer profile with its -7.4 tangent, rather than a raised square plateau.
 return top(.5-r) if r<=1 else .67*(1-min(1,max(0,(r-1)/(math.sqrt(2)-1))))**(7.4*(math.sqrt(2)-1)/.67)
def bevelS(x):return min(.042*sm((x+.5)/.18),.32*roofheight(x,-.5))
def bevelE(y):return min(.042*sm((.5-y)/.18),.32*roofheight(.5,y))
def roofmap(x,y):return (x-bevelE(y)*sm((x-.42)/.08),y+bevelS(x)*sm((-.42-y)/.08),roofheight(x,y))
# Canonical profile coordinates are explicitly retained at both real port boundaries.
coords=sorted(set(round(p['yz'][0],9) for p in rings['E'] if p['yz'][1]>=.6699999));coords2=[]
for t in coords:
 if not coords2 or abs(t-coords2[-1])>1e-7:coords2.append(t)
coords=sorted(set(coords2+[-.5+i/320 for i in range(321)]));L=len(coords);vs=[];fs=[];index={};boundary=[]
def vertex(v):
 k=tuple(round(float(t),9) for t in v)
 if k not in index:index[k]=len(vs);vs.append(tuple(v))
 return index[k]
def quad(a,b,c,d):
 ids=[a,b,c,d]
 ids=[v for i,v in enumerate(ids) if v!=ids[i-1]]
 if len(set(ids))>=3:fs.append(tuple(ids))
roofgrid=[]
for y in coords:roofgrid.append([vertex(roofmap(x,y)) for x in coords])
for iy in range(L-1):
 for ix in range(L-1):
  a,b,c,d=roofgrid[iy][ix],roofgrid[iy][ix+1],roofgrid[iy+1][ix+1],roofgrid[iy+1][ix]
  if ix==0 and iy==L-2:fs.extend([(a,b,d),(b,c,d)])
  else:quad(a,b,c,d)
# Real rounded geometry joins the exterior to the roof. Shared vertices eliminate separate shell normals/colors.
for face in ['S','E']:
 grid=[];NV=88;NB=6
 for iz in range(NV+NB+1):
  row=[]
  for u in coords:
   h=roofheight(u,-.5) if face=='S' else roofheight(.5,u);b=bevelS(u) if face=='S' else bevelE(u)
   if iz<=NV:
    z=(h-b)*iz/NV;x,y=(u,-.5) if face=='S' else (.5,u)
   else:
    ang=(iz-NV)/NB*math.pi/2;f=1-math.cos(ang);z=h-b+b*math.sin(ang)
    if face=='S':x=u-bevelE(-.5+b)*sm((u-.42)/.08)*f;y=-.5+b*f
    else:x=.5-b*f;y=u+bevelS(.5)*sm((-.42-u)/.08)*f
   if iz==NV+NB:x,y,z=roofmap(u,-.5) if face=='S' else roofmap(.5,u)
   row.append(vertex((x,y,z)))
  grid.append(row)
 for iz in range(len(grid)-1):
  for iu in range(L-1):quad(grid[iz][iu],grid[iz][iu+1],grid[iz+1][iu+1],grid[iz+1][iu])
# Explicit whole-cell floor provides finite grounded support, connected at all four extreme corners.
floorids=[vertex((-.5,-.5,0)),vertex((.5,-.5,0)),vertex((.5,.5,0)),vertex((-.5,.5,0))];fs.append(tuple(reversed(floorids)))
me=bpy.data.meshes.new('rock-wall-corner__unified_worn_stone');me.from_pydata(vs,[],fs);me.update();body=bpy.data.objects.new(me.name,me);coll.objects.link(body);body.parent=root;me.materials.append(mat)
for f in me.polygons:f.use_smooth=True
# Offset the one connected surface in its native normal direction with one shared field.
basepoints=[v.co.copy() for v in me.vertices];basenorms=[v.normal.copy() for v in me.vertices];colors=[]
for i,(p,n) in enumerate(zip(basepoints,basenorms)):
 fade=sm((p.x+.5)/.20)*sm((.5-p.y)/.20);rel,cav,tone=field3(p);support=sm(p.z/.035)
 q=p+n*(rel*fade*support);q.z=max(0,q.z);me.vertices[i].co=q
 co=color(q.z,cav,tone);dw=p.x+.5;dn=.5-p.y;w=dn/(dw+dn) if dw+dn>1e-8 else .5
 cw,_=sample(p.y,p.z,'E');cn,_=sample(-p.x,p.z,'W');bc=tuple(mix(cn[k],cw[k],w) for k in range(4));colors.append(tuple(mix(bc[k],co[k],fade) for k in range(4)))
me.update();ca=me.color_attributes.new(name='stone_albedo',type='FLOAT_COLOR',domain='POINT')
for i,c in enumerate(colors):ca.data[i].color=c
norms=[v.normal.copy() for v in me.vertices]
# Actual native boundary albedo and port normals stay exact, independent of the new construction elsewhere.
for i,v in enumerate(me.vertices):
 p=v.co
 for port in ['W','N']:
  on=abs(p.x+.5)<1e-7 if port=='W' else abs(p.y-.5)<1e-7
  if not on:continue
  # NW floor is the hidden three-way floor point, not exposed stone profile shading.
  if p.z<1e-8 and abs(p.x+.5)<1e-7 and abs(p.y-.5)<1e-7:continue
  t=p.y if port=='W' else -p.x;c,n=sample(t,p.z,'E' if port=='W' else 'W')
  if port=='N':n=Vector((-n.y,n.x,n.z))
  norms[i]=n;ca.data[i].color=c;boundary.append({'port':port,'index':i,'profile':[t,p.z],'expectedColor':c,'expectedNormal':list(n)})
me.normals_split_custom_set_from_vertices(norms)
# The single conical NW crown apex has two correct native limiting normals across a real triangle edge.
apex=roofgrid[-1][0];westNeighbor=roofgrid[-2][0];loopNormals=[Vector(n.vector) for n in me.corner_normals]
for poly in me.polygons:
 if apex in poly.vertices and westNeighbor in poly.vertices:
  for li in poly.loop_indices:
   if me.loops[li].vertex_index==apex:loopNormals[li]=sample(.5,.67,'E')[1]
me.normals_split_custom_set(loopNormals)
# Geometry, vertex color and normals now cross the former crown/exterior boundary in one mesh.
# Retain canonical capture/light/shader without any per-view setting changes.
sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.fps=12;sc.frame_start=1;sc.frame_end=1;sc.frame_set(1);root.rotation_euler.z=0;bpy.context.view_layer.update()
def px(v):p=world_to_camera_view(sc,cam,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
def matrix(o):return [list(r) for r in o.matrix_world]
verts=[o.matrix_world@v.co for o in coll.objects if o.type=='MESH' for v in o.data.vertices]
recipe={'asset':'rock-wall-corner','round':4,'modeling':'Single welded worn-stone volume with curved descending outer shoulder, native rounded exterior junction and one continuous 3D carved stone field; analytic flat longitudinal tangent at both ports; exact canonical native connector caps/profile/albedo/normal and unchanged canonical shader/light/capture. No source part-count lock.','briefSHA256':hashlib.sha256((RES/'brief.json').read_bytes()).hexdigest(),'nativeContractSHA256':hashlib.sha256((RES/'inputs/root-native-contract.json').read_bytes()).hexdigest(),'capture':{'nativeCaptureScale':4,'nativeFrame':[768,1408],'publishedScale':2,'publishedFrame':[384,704],'publication':'whole-frame Pillow BOX 4x to 2x','fps':12,'frames':1,'loop':False,'directions':DIR},'canonicalSceneSHA256':hashlib.sha256((RES/'approved-middle/project.blend').read_bytes()).hexdigest(),'implementation':'round-04.py'}
(BASE/'source/round-04-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
# Standalone saved BEFORE any companion import. No later saving allowed in this script.
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'source/round-04.blend'),compress=True)
audit={'asset':'rock-wall-corner','scene':sc.name,'collection':coll.name,'root':root.name,'intrinsicRootMatrix':matrix(root),'bounds':{'min':[min(v[i] for v in verts) for i in range(3)],'max':[max(v[i] for v in verts) for i in range(3)]},'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'coordinateSHA256':hashlib.sha256(b''.join(struct.pack('fff',*v.co) for v in o.data.vertices)).hexdigest(),'modifiers':[m.type for m in o.modifiers]} for o in coll.objects if o.type=='MESH'],'nativeGeometry':True,'camera':{'worldMatrix':matrix(cam),'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'calibration':{'root':px((0,0,0)),'unitX':[px((1,0,0))[i]-px((0,0,0))[i] for i in range(2)],'unitDepth':[px((0,-1,0))[i]-px((0,0,0))[i] for i in range(2)],'unitHeight':[px((0,0,1))[i]-px((0,0,0))[i] for i in range(2)]}},'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'denoise':sc.cycles.use_denoising,'pixelFilter':sc.cycles.pixel_filter_type,'filterSize':sc.render.filter_size,'viewTransform':sc.view_settings.view_transform,'frame':[sc.render.resolution_x,sc.render.resolution_y],'fps':sc.render.fps,'transparent':sc.render.film_transparent},'actualLights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'shadow':o.data.use_shadow,'matrix':matrix(o)} for o in sc.objects if o.type=='LIGHT'],'actualMaterial':{'name':mat.name,'nodes':[n.type for n in mat.node_tree.nodes],'imageNodes':len([n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE'])},'resourceClosure':{'images':[{'name':i.name,'source':i.source,'path':i.filepath} for i in bpy.data.images if i.source!='VIEWER'],'libraries':[l.filepath for l in bpy.data.libraries]},'ports':{'W':{'axis':'X','plane':-.5,'transverse':'Y'},'N':{'axis':'Y','plane':.5,'transverse':'-X'},'profile':PROFILE,'noOverlap':True},'static':{'frames':1,'fps':12,'loop':False,'actions':len(bpy.data.actions),'armatures':len([o for o in sc.objects if o.type=='ARMATURE'])},'views':{}}
(OUT/'boundary-intent.json').write_text(json.dumps(boundary,indent=2)+'\n')
for d,deg in DIR.items():
 root.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();sc.render.filepath=str(OUT/f'native-static-{d}.png');bpy.ops.render.render(write_still=True)
 audit['views'][d]={'direction':d,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootRotationZ':root.rotation_euler.z,'actualRootMatrix':matrix(root),'rootPixel':px((0,0,0)),'path':f'native-static-{d}.png'}
(OUT/'native-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
# Exact independently assembled three native objects at W/N. Append only in memory, saved own source untouched.
root.rotation_euler.z=0
with bpy.data.libraries.load(str(RES/'approved-middle/project.blend'),link=False) as (available,wanted):wanted.collections=['rock-wall-middle__asset']
mid=wanted.collections[0];sc.collection.children.link(mid);mroot=next(o for o in mid.objects if o.type=='EMPTY');assembly=bpy.data.objects.new('independent-corner-middle-assembly',None);sc.collection.objects.link(assembly)
root.parent=assembly;mroot.parent=assembly;mroot.location=(-1,0,0);mroot.rotation_euler.z=0
r2=mroot.copy();mid.objects.link(r2);r2.name='independent-N-middle-root';r2.parent=assembly;r2.location=(0,1,0);r2.rotation_euler.z=math.pi/2
for ob in list(mid.objects):
 if ob.type=='MESH' and ob.parent==mroot:du=ob.copy();mid.objects.link(du);du.parent=r2
sc.render.resolution_x=1792;sc.render.resolution_y=2432;cam.data.ortho_scale=3.5;cam.data.shift_x=0
for _ in range(2):
 bpy.context.view_layer.update();b=px((0,0,0));prev=cam.data.shift_y;cam.data.shift_y=prev+1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-b[1];cam.data.shift_y=prev+(1536-b[1])/dy
joins={}
for d,deg in DIR.items():
 assembly.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();sc.render.filepath=str(OUT/f'native-joined-{d}.png');bpy.ops.render.render(write_still=True)
 joins[d]={'direction':d,'actualAssemblyMatrix':matrix(assembly),'cornerMatrix':matrix(root),'W-middleMatrix':matrix(mroot),'N-middleMatrix':matrix(r2),'rootPixel':px((0,0,0))}
(OUT/'native-joins.json').write_text(json.dumps({'construction':'Three distinct native objects, exact saved canonical middle with both caps retained. No welding, cap removal, overlap, per-view correction or resaving source.','frame':[1792,2432],'root':[896,1536],'views':joins},indent=2)+'\n')
print('CORNER_ROUND04_DONE')
