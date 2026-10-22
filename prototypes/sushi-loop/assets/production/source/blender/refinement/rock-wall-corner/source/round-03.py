import bpy, math, json, hashlib, random, struct
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parents[1]; RES=BASE/'source/resources';OUT=BASE/'candidates/round-03';OUT.mkdir(parents=True,exist_ok=True)
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
bpy.ops.wm.open_mainfile(filepath=str(RES/'approved-middle/project.blend'));sc=bpy.context.scene;sc.name='Rock wall corner native refinement round 03';cam=sc.camera
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
# Broad irregular stone fields use native geometric recesses, with no image texture/noise texture.
rng=random.Random(221022);sites=[]
for row in range(5):
 for col in range(3):sites.append(((col+.5+rng.uniform(-.20,.20))/3,(row+.5+rng.uniform(-.18,.18))/5*1.25,rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)))
roofsites=[]
for iy in range(3):
 for ix in range(3):roofsites.append((-.5+(ix+.5+rng.uniform(-.18,.18))/3,-.5+(iy+.5+rng.uniform(-.18,.18))/3,rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)))
def field(u,v,roof=False):
 near=[];ss=roofsites if roof else sites
 for i,(sx,sy,c,sl,st) in enumerate(ss):
  dx=u-sx;dy=v-sy;dx+=.017*math.sin(v*8.2+sx*4);dy+=.014*math.sin(u*9+sy*3);near.append((dx*dx+dy*dy*.87,i,dx,dy))
 near.sort();a,b=near[:2];site=ss[a[1]];gap=(b[0]-a[0])/(2*math.sqrt(max(b[0],1e-8)));worn=sm(gap/.045)
 carve=-.039*(1-worn);plane=.085*(site[3]*a[2]+site[4]*a[3]);rel=min(0,carve+plane*worn-.004)
 return rel,1-worn,site[2]
def mesh(name,vs,fs,cs,normals=None):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);coll.objects.link(ob);ob.parent=root;me.materials.append(mat);ca=me.color_attributes.new(name='stone_albedo',type='FLOAT_COLOR',domain='POINT')
 for i,c in enumerate(cs):ca.data[i].color=c
 for f in me.polygons:f.use_smooth=True
 if normals:
  nn=[v.normal.copy() for v in me.vertices]
  for i,n in normals.items():nn[i]=n
  me.normals_split_custom_set_from_vertices(nn)
 return ob
# Grid explicitly contains every canonical upper-profile y sample and exact profile corners.
coords=sorted(set(round(p['yz'][0],9) for p in rings['E'] if p['yz'][1]>=.6699999))
# Remove float duplicate near profile corners.
coords2=[]
for t in coords:
 if not coords2 or abs(t-coords2[-1])>1e-7:coords2.append(t)
coords=coords2;L=len(coords);vs=[];cs=[];fs=[];norms={};boundary=[]
for iy,y in enumerate(coords):
 for ix,x in enumerate(coords):
  radius=math.hypot(x+.5,.5-y); z=top(.5-radius) if radius<=1 else .67;fade=sm((x+.5)/.20)*sm((.5-y)/.20);rel,cav,tone=field(x,y,True)
  # Exterior crown edges remain shared with native face meshes; relief stays inside functional envelope.
  edge=sm((.5-x)/.08)*sm((y+.5)/.08);zz=z+rel*fade*edge
  cw,nw=sample(y,top(y),'E');cn,nn=sample(-x,top(x),'W');nn=Vector((-nn.y,nn.x,nn.z))
  dw=x+.5;dn=.5-y;w=dn/(dw+dn) if dw+dn>1e-8 else .5
  bc=tuple(mix(cn[k],cw[k],w) for k in range(4));co=color(zz,cav,tone);c=tuple(mix(bc[k],co[k],fade) for k in range(4));ind=len(vs);vs.append((x,y,zz));cs.append(c)
  if ix==0:norms[ind]=nw;boundary.append({'port':'W','index':ind,'profile':[y,top(y)],'expectedColor':cw,'expectedNormal':list(nw)})
  if iy==L-1:norms[ind]=nn;boundary.append({'port':'N','index':ind,'profile':[-x,top(x)],'expectedColor':cn,'expectedNormal':list(nn)})
for iy in range(L-1):
 for ix in range(L-1):
  a=iy*L+ix
  if ix==0 and iy==L-2:fs.extend([(a,a+1,a+L),(a+1,a+1+L,a+L)])
  else:fs.append((a,a+1,a+1+L,a+L))
roof=mesh('rock-wall-corner__broad_worn_crown',vs,fs,cs,norms)
# At the single conical NW apex, the two limiting port normals differ physically.
# Split actual face-corner normals across a real diagonal triangle edge; both real join limits match.
apex=(L-1)*L;westNeighbor=(L-2)*L;loopNormals=[Vector(n.vector) for n in roof.data.corner_normals]
for poly in roof.data.polygons:
 if apex in poly.vertices and westNeighbor in poly.vertices:
  for li in poly.loop_indices:
   if roof.data.loops[li].vertex_index==apex:loopNormals[li]=sample(.5,.67,'E')[1]
roof.data.normals_split_custom_set(loopNormals)
# Two exterior faces wrap through SE; their new stone courses are physically inset, rounded and full scale.
faces=[]
for face in ['S','E']:
 vs=[];cs=[];fs=[];norms={};VZ=128;NU=128
 for iz in range(VZ+1):
  t=iz/VZ
  for iu in range(NU+1):
   u=-.5+iu/NU;z=t*.67;along=u+.5 if face=='S' else .5-u
   fade=sm(along/.20)*math.sin(math.pi*t)**2;rel,cav,tone=field(along,z);rr=rel*fade
   if face=='S':v=(u,-.5-rr,z);bc,bn=sample(-.5,z,'E')
   else:v=(.5+rr,u,z);bc,bn=sample(-.5,z,'W');bn=Vector((-bn.y,bn.x,bn.z))
   co=color(z,cav,tone);c=tuple(mix(bc[k],co[k],sm(along/.20)) for k in range(4));idx=len(vs);vs.append(v);cs.append(c)
   if along<1e-8:norms[idx]=bn;boundary.append({'port':'W' if face=='S' else 'N','meshFace':face,'index':idx,'profile':[-.5,z],'expectedColor':bc,'expectedNormal':list(bn)})
 for iz in range(VZ):
  for iu in range(NU):a=iz*(NU+1)+iu;fs.append((a,a+1,a+1+NU+1,a+NU+1) if face=='S' else (a+NU+1,a+1+NU+1,a+1,a))
 ob=mesh('rock-wall-corner__'+face+'_carved_stone_courses',vs,fs,cs,norms);faces.append(ob)
# Bottom is finite closed support across exactly one complete cell, no overhang and no shadow receiver.
floor=mesh('rock-wall-corner__full_ground_support',[(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)],[(3,2,1,0)],[color(0,0,0)]*4)
# Retain canonical capture/light/shader without any per-view setting changes.
sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.fps=12;sc.frame_start=1;sc.frame_end=1;sc.frame_set(1);root.rotation_euler.z=0;bpy.context.view_layer.update()
def px(v):p=world_to_camera_view(sc,cam,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
def matrix(o):return [list(r) for r in o.matrix_world]
verts=[o.matrix_world@v.co for o in coll.objects if o.type=='MESH' for v in o.data.vertices]
recipe={'asset':'rock-wall-corner','round':3,'modeling':'New full grounded quarter-turn volume; radial worn stone crown with analytic flat longitudinal tangent at both real ports; shallow worn exterior courses; exact canonical native connector caps/profile/albedo/normal and unchanged canonical shader/light/capture. No source part-count lock.','briefSHA256':hashlib.sha256((RES/'brief.json').read_bytes()).hexdigest(),'nativeContractSHA256':hashlib.sha256((RES/'inputs/root-native-contract.json').read_bytes()).hexdigest(),'capture':{'nativeCaptureScale':4,'nativeFrame':[768,1408],'publishedScale':2,'publishedFrame':[384,704],'publication':'whole-frame Pillow BOX 4x to 2x','fps':12,'frames':1,'loop':False,'directions':DIR},'canonicalSceneSHA256':hashlib.sha256((RES/'approved-middle/project.blend').read_bytes()).hexdigest(),'implementation':'round-03.py'}
(BASE/'source/round-03-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
# Standalone saved BEFORE any companion import. No later saving allowed in this script.
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'source/round-03.blend'),compress=True)
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
print('CORNER_ROUND01_DONE')
