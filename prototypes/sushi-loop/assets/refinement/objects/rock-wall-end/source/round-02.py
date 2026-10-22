"""Editable native rock-wall-end. Canonical family source is read, never saved.
Reproduce: blender -b --python source/round-02.py
Saves standalone source before any in-memory pairing. No target pixels are used.
"""
import bpy,math,json,hashlib,random,struct,sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-02';OUT.mkdir(parents=True,exist_ok=True)
REF=BASE/'inputs/approved-middle/project.blend'
bpy.ops.wm.open_mainfile(filepath=str(REF));sc=bpy.context.scene;cam=sc.camera
canonicalRoot=bpy.data.objects['rock-wall-middle__root'];canonicalSide=bpy.data.objects['rock-wall-middle__continuous_carved_stone']
canonicalRoot.rotation_euler=(0,0,0);bpy.context.view_layer.update()
# Exact E cut of the approved source becomes the end W cut after translation.
me=canonicalSide.data;NQ=279;NX=128
ce=[v for v in me.vertices if abs(v.co.x-.5)<1e-7]
assert len(ce)==NQ
loops={}
for i,l in enumerate(me.loops):loops.setdefault(l.vertex_index,[]).append(i)
boundary=[]
for v in ce:
 ns=[me.corner_normals[i].vector for i in loops[v.index]];n=sum((Vector(n) for n in ns),Vector())/len(ns)
 boundary.append({'y':v.co.y,'z':v.co.z,'color':tuple(me.color_attributes['stone_albedo'].data[v.index].color),'normal':tuple(n.normalized())})
mat=canonicalSide.data.materials[0];mat.name='Rock family soft cobalt native — end'
for o in list(bpy.data.objects):
 if o.type not in ['CAMERA','LIGHT']:bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):
 if c.name!='Collection' and not len(c.objects):bpy.data.collections.remove(c)
coll=bpy.data.collections.new('rock-wall-end__asset');sc.collection.children.link(coll)
root=bpy.data.objects.new('rock-wall-end__root',None);coll.objects.link(root)
root['assetId']='rock-wall-end';root['intrinsicRotationDegrees']=0;root['cellSize']=128;root['port_W']='rock-wall-full-cell-v2';root['footprint']=[1,1]
PROFILE=[(-.5,0),(.5,0),(.5,.67),(.45,1.04),(.31,1.15),(-.31,1.15),(-.45,1.04),(-.5,.67)]
DIR={'S':0,'E':90,'N':180,'W':-90}
def clamp(x,a=0,b=1):return min(b,max(a,x))
def smooth(x):x=clamp(x);return x*x*(3-2*x)
def mix(a,b,t):return a*(1-t)+b*t
def srgb(v):return ((v+.055)/1.055)**2.4 if v>.04045 else v/12.92
lengths=[math.dist(PROFILE[i],PROFILE[(i+1)%8]) for i in range(8)];PER=sum(lengths);starts=[0]
for v in lengths:starts.append(starts[-1]+v)
rng=random.Random(3407);sites=[]
for row in range(9):
 for col in range(2):
  sites.append(((col+.5+.22*rng.uniform(-1,1))/2-.5,(row+.5+.22*rng.uniform(-1,1))/9*PER,rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)))
capSites=[]
for row in range(3):
 for col in range(2):capSites.append(((col+.5+.23*rng.uniform(-1,1))/2-.5,(row+.5+.22*rng.uniform(-1,1))/3*1.15,rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)))
def field(x,q,cap=False):
 ss=capSites if cap else sites;near=[]
 for i,(sx,sy,c,sl,st) in enumerate(ss):
  dx=x-sx;dy=q-sy
  if not cap:dy=(dy+PER/2)%PER-PER/2
  dx+=.022*math.sin(q*8.2+sx*3);dy+=.024*math.sin(2*math.pi*x+sy*2)
  d=dx*dx+dy*dy*.9;near.append((d,i,dx,dy))
 near.sort();a,b=near[:2];site=ss[a[1]]
 gap=(b[0]-a[0])/(2*math.sqrt(max(b[0],1e-8)))
 worn=smooth(gap/.045);cav=1-worn
 # Native concave joints surrounded by broad worn turning planes.
 carve=-.048*cav
 plane=.065*(site[3]*a[2]+site[4]*a[3])
 rel=min(.006,carve+plane*worn-.005)
 return rel,cav,site[2],worn

def color(z,cavity,tone,nz):
 h=smooth(z/1.15);low=(.15,.40,.67);mid=(.14,.49,.77);top=(.26,.68,.88)
 base=[mix(low[i],mid[i],smooth(h/.72)) for i in range(3)]
 base=[mix(base[i],top[i],smooth((h-.60)/.40)*.65) for i in range(3)]
 f=(1-.27*cavity)*(1+.045*tone)
 return tuple(srgb(clamp(c*f)) for c in base)+(1,)
def mesh_obj(name,vs,fs,cs):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);coll.objects.link(ob);ob.parent=root;me.materials.append(mat)
 ca=me.color_attributes.new(name='stone_albedo',type='FLOAT_COLOR',domain='POINT')
 for i,c in enumerate(cs):ca.data[i].color=c
 for f in me.polygons:f.use_smooth=True
 return ob
qs=[]
for e,n in enumerate([1,58,34,18,58,18,34,58]):
 for j in range(n):qs.append((e,j/n,starts[e]+lengths[e]*j/n))
assert len(qs)==NQ
# Soft end turn is carved inward; full Z0 ground footprint remains finite and broad.
def endturn(y,z):
 t=smooth(z/.13)
 return y*(1-.075*t),z-.027*smooth(z/.70)
# Blend displacement directions around upper profile corners to avoid offset-surface folds.
# The exact west ring and custom cut normals stay unchanged.
edgeNormals=[]
for k in range(8):
 ay,az=PROFILE[k];by,bz=PROFILE[(k+1)%8];le=math.hypot(by-ay,bz-az);edgeNormals.append(((bz-az)/le,-(by-ay)/le))
def offset_normal(e,q):
 for k in range(2,8):
  d=q-starts[k]
  if abs(d)<.08:
   a=edgeNormals[(k-1)%8];b=edgeNormals[k];t=smooth((d+.08)/.16)
   ny=mix(a[0],b[0],t);nz=mix(a[1],b[1],t);le=math.hypot(ny,nz);return ny/le,nz/le
 return edgeNormals[e]
vs=[];cs=[];fs=[]
for ix in range(NX+1):
 x=-.5+ix/NX;fade=smooth((x+.5)/.36);endT=clamp((x-.40)/.10)
 turn=1-math.sqrt(max(0,1-endT*endT));edgeFade=1-smooth((x-.39)/.11)
 for j,(e,t,q) in enumerate(qs):
  ay,az=PROFILE[e];by,bz=PROFILE[(e+1)%8];y=mix(ay,by,t);z=mix(az,bz,t)
  dy,dz=by-ay,bz-az;le=math.hypot(dy,dz);ny,nz=offset_normal(e,q)
  rel,cav,tone,worn=field(x,q)
  if e==0:rel=0;cav=0
  rel*=fade*edgeFade;yy=y+ny*rel;zz=max(0,z+nz*rel)
  ey,ez=endturn(yy,zz);yy=mix(yy,ey,turn);zz=mix(zz,ez,turn)
  vs.append((x,yy,zz));own=color(zz,cav*fade*edgeFade,tone,nz)
  bc=boundary[j]['color'];ct=smooth((x+.5)/.45)
  cs.append(tuple(mix(bc[k],own[k],ct) for k in range(4)))
  if ix==0:vs[-1]=(-.5,boundary[j]['y'],boundary[j]['z']);cs[-1]=boundary[j]['color']
for ix in range(NX):
 for j in range(NQ):
  a=ix*NQ+j;b=ix*NQ+(j+1)%NQ;c=(ix+1)*NQ+(j+1)%NQ;d=(ix+1)*NQ+j;fs.append((a,b,c,d))
side=mesh_obj('rock-wall-end__continuous_worn_cobalt',vs,fs,cs)
norms=[v.normal.copy() for v in side.data.vertices]
for j in range(NQ):norms[j]=Vector(boundary[j]['normal'])
side.data.normals_split_custom_set_from_vertices(norms)
# End faces are modeled stone, with a large irregular 2x3 rhythm and curved recesses.
def top_at(y):
 if abs(y)<=.31:return 1.15
 if abs(y)<=.45:return 1.15-(abs(y)-.31)/.14*.11
 return 1.04-(abs(y)-.45)/.05*.37
caps=[]
for sign in [-1,1]:
 cv=[];cc=[];cf=[];NY=112;NZ=128
 for iz in range(NZ+1):
  t=iz/NZ
  for iy in range(NY+1):
   y=-.5+iy/NY;z=t*top_at(y);rel,cav,tone,worn=field(y,z,True)
   fade=math.sin(math.pi*iy/NY)**2*math.sin(math.pi*t)**2
   x=sign*(.5+min(0,rel)*fade)
   if sign>0:y,z=endturn(y,z)
   cv.append((x,y,z));cc.append(color(z,cav*fade,tone,0))
 for iz in range(NZ):
  for iy in range(NY):
   a=iz*(NY+1)+iy;b=a+1;c=b+NY+1;d=a+NY+1;cf.append((a,b,c,d) if sign>0 else (d,c,b,a))
 ob=mesh_obj('rock-wall-end__W_connector_stone' if sign<0 else 'rock-wall-end__finished_E_stone',cv,cf,cc);caps.append(ob)
# Actual canonical scene camera/light/render are inherited unchanged from approved bytes.
sc.name='Rock wall end native refinement round02';sc.render.filepath='//render.png';sc.render.fps=12;sc.frame_set(1)
assert sc.render.engine=='CYCLES' and sc.cycles.samples==48 and abs(sc.cycles.filter_width-1.5)<1e-7
root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
def px(p):
 q=world_to_camera_view(sc,cam,Vector(p));return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
recipe={'asset':'rock-wall-end','round':2,'geometry':'Continuous native worn broad stone relief, exact approved-middle E cut copied to west boundary, one finished east termination; old plates and dark shoulder replaced','frozenBriefSHA256':'3eca876bf4744fd9b3be88afe15228bcab882e1a9599ade89c6bb297b4711a79','rootContractSHA256':'20e29b693453dd2df26ad35d0bcee4b20a40d4bd417f940b468d836b18647bc9','referenceSHA256':hashlib.sha256(REF.read_bytes()).hexdigest(),'capture':{'nativeCaptureScale':4,'nativeFrame':[768,1408],'publishedCaptureScale':2,'publishedFrame':[384,704],'logicalFrame':[192,352],'logicalRoot':[96,256],'cell':128,'publication':'whole native frame BOX to published2x'},'material':{'attribute':'stone_albedo','roughness':.88,'specular':.12,'emission':.38,'boundary':'exact approved-middle E linear point albedo and custom normal'},'assembly':'end.W to approved middle.E, roots1 apart, all4 same intrinsic facing; no overlap','resources':[]}
(BASE/'source/round-02-settings.json').write_text(json.dumps(recipe,indent=2)+'\n')
# Standalone saved BEFORE in-memory import of companion or assembly geometry.
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'source/round-02.blend'),compress=True)
audit={'asset':'rock-wall-end','project':'source/round-02.blend','sourceSHA256':hashlib.sha256((BASE/'source/round-02.blend').read_bytes()).hexdigest(),'standaloneSavedBeforeAssembly':True,'nativeFrame':[768,1408],'camera':{'worldMatrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'calibration':{'root':px((0,0,0)),'unitX':[px((1,0,0))[i]-px((0,0,0))[i] for i in [0,1]],'unitDepth':[px((0,-1,0))[i]-px((0,0,0))[i] for i in [0,1]],'unitHeight':[px((0,0,1))[i]-px((0,0,0))[i] for i in [0,1]]}},'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'denoising':sc.cycles.use_denoising,'filter':sc.cycles.pixel_filter_type,'filterWidth':sc.cycles.filter_width,'seed':sc.cycles.seed,'view':sc.view_settings.view_transform,'look':sc.view_settings.look,'dither':sc.render.dither_intensity,'transparent':sc.render.film_transparent,'compositor':sc.use_nodes},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'angle':o.data.angle,'shadow':o.data.use_shadow,'matrix':[list(r) for r in o.matrix_world]} for o in sc.objects if o.type=='LIGHT'],'worldStrength':next(n for n in sc.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value,'meshes':[],'views':{},'resources':{'images':[{'name':i.name,'source':i.source,'filepath':i.filepath} for i in bpy.data.images if i.type!='RENDER_RESULT'],'libraries':[l.filepath for l in bpy.data.libraries]},'actions':[a.name for a in bpy.data.actions],'armatures':[o.name for o in coll.objects if o.type=='ARMATURE']}
allv=[]
for ob in coll.objects:
 if ob.type!='MESH':continue
 me=ob.data;allv.extend([ob.matrix_world@v.co for v in me.vertices]);audit['meshes'].append({'name':ob.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'coordinateSHA256':hashlib.sha256(b''.join(struct.pack('fff',*v.co) for v in me.vertices)).hexdigest(),'customNormals':me.has_custom_normals,'smoothPolygons':sum(p.use_smooth for p in me.polygons),'colorAttributes':[{'name':a.name,'domain':a.domain,'dataType':a.data_type} for a in me.color_attributes],'uvLayers':[u.name for u in me.uv_layers],'materials':[m.name for m in me.materials],'modifiers':[m.type for m in ob.modifiers]})
audit['bounds']={'min':[min(v[i] for v in allv) for i in range(3)],'max':[max(v[i] for v in allv) for i in range(3)]}
# Port residuals against actual immutable source E boundary, including actual corner normals.
sm=side.data;sloops={}
for i,l in enumerate(sm.loops):sloops.setdefault(l.vertex_index,[]).append(i)
ps=[]
for j,b in enumerate(boundary):
 v=sm.vertices[j];ns=[sm.corner_normals[i].vector for i in sloops[j]];n=sum((Vector(n) for n in ns),Vector())/len(ns);co=sm.color_attributes['stone_albedo'].data[j].color
 ps.append({'y':v.co.y,'z':v.co.z,'profileDelta':math.hypot(v.co.y-b['y'],v.co.z-b['z']),'albedoDelta':max(abs(co[k]-b['color'][k]) for k in range(4)),'normalDelta':(n-Vector(b['normal'])).length})
audit['westPort']={'plane':-.5,'profileYThenZ':PROFILE,'sampleCount':len(ps),'maxProfileDelta':max(p['profileDelta'] for p in ps),'maxLinearAlbedoChannelDelta':max(p['albedoDelta'] for p in ps),'maxMeanCornerNormalDelta':max(p['normalDelta'] for p in ps),'samples':ps}
for direction,degrees in DIR.items():
 root.rotation_euler.z=math.radians(degrees);bpy.context.view_layer.update();path=OUT/f'native-static-{direction}.png';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 audit['views'][direction]={'direction':direction,'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world],'rootPixel':px((0,0,0)),'path':str(path.relative_to(BASE))}
# In-memory same-handed source assembly; no standalone source is re-saved.
root.rotation_euler.z=0
with bpy.data.libraries.load(str(REF),link=False) as(src,dst):dst.collections=['rock-wall-middle__asset']
mc=dst.collections[0];sc.collection.children.link(mc);mr=next(o for o in mc.objects if o.type=='EMPTY');mr.rotation_euler=(0,0,0)
assembly=bpy.data.objects.new('temporary-pair-root',None);sc.collection.objects.link(assembly);root.parent=assembly;mr.parent=assembly;root.location=(.5,0,0);mr.location=(-.5,0,0)
caps[0].hide_render=True
next(o for o in mc.objects if 'E_connector' in o.name).hide_render=True
sc.render.resolution_x=1280;sc.render.resolution_y=1920;cam.data.ortho_scale=2.5
for _ in range(2):
 base=px((0,0,0));old=cam.data.shift_y;cam.data.shift_y=old+1;bpy.context.view_layer.update();delta=px((0,0,0))[1]-base[1];cam.data.shift_y=old+(1280-base[1])/delta;bpy.context.view_layer.update()
audit['assembly']={'sameHanded':True,'relativeRoots':{'end':[.5,0,0],'middle':[-.5,0,0]},'pitchNative':1,'internalCapsHidden':True,'noAddedOverlap':True,'frame':[1280,1920],'cameraRoot':px((0,0,0)),'views':{}}
for direction,degrees in DIR.items():
 assembly.rotation_euler.z=math.radians(degrees);bpy.context.view_layer.update();path=OUT/f'joined-native-{direction}.png';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);audit['assembly']['views'][direction]={'direction':direction,'rootRotationZ':assembly.rotation_euler.z,'rootRotationDegrees':math.degrees(assembly.rotation_euler.z),'rootMatrix':[list(r) for r in assembly.matrix_world],'path':str(path.relative_to(BASE))}
(OUT/'native-audit.json').write_text(json.dumps(audit,indent=2)+'\n');print('END_ROUND02_DONE')
