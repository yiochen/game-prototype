import bpy, math, json, hashlib, random, sys
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parents[1]; OUT=BASE/'candidates/round-02'; OUT.mkdir(parents=True,exist_ok=True)
PROFILE=[(-.5,0),(.5,0),(.5,.67),(.45,1.04),(.31,1.15),(-.31,1.15),(-.45,1.04),(-.5,.67)]
DIR={'S':0,'E':90,'N':180,'W':-90}
# Fresh isolated native scene, retaining the read-only source through hashes.
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='Rock wall middle native refinement round 02'
coll=bpy.data.collections.new('rock-wall-middle__asset');sc.collection.children.link(coll)
root=bpy.data.objects.new('rock-wall-middle__root',None);coll.objects.link(root)
root['assetId']='rock-wall-middle';root['intrinsicRotationDegrees']=0;root['cellSize']=128

def clamp(x,a=0,b=1):return min(b,max(a,x))
def smooth(x): x=clamp(x);return x*x*(3-2*x)
def mix(a,b,t):return a*(1-t)+b*t

def srgb(v):return ((v+.055)/1.055)**2.4 if v>.04045 else v/12.92
rng=random.Random(10621)
lengths=[math.dist(PROFILE[i],PROFILE[(i+1)%8]) for i in range(8)]
PER=sum(lengths); starts=[0]
for v in lengths: starts.append(starts[-1]+v)
# Continuous X-periodic stone layout, all geometry relief vanishes with a flat tangent at exact cuts.
sites=[]
for row in range(9):
 for col in range(3):
  sites.append(((col+.5+.23*rng.uniform(-1,1))/3-.5,(row+.5+.20*rng.uniform(-1,1))/9*PER,rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)))
capSites=[]
for row in range(4):
 for col in range(3):capSites.append(((col+.5+.2*rng.uniform(-1,1))/3-.5,(row+.5+.2*rng.uniform(-1,1))/4*1.15,rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)))

def field(x,q,cap=False):
 ss=capSites if cap else sites
 near=[]
 for i,(sx,sy,c,sl,st) in enumerate(ss):
  dx=x-sx
  if not cap:dx=(dx+.5)%1-.5
  dy=q-sy
  if not cap:dy=(dy+PER/2)%PER-PER/2
  # Warped broad cell boundaries, with different transverse courses.
  dx+=.023*math.sin(q*9.2+sx*3);dy+=.020*math.sin(x*11+sy*2)
  d=dx*dx+dy*dy*.88;near.append((d,i,dx,dy))
 near.sort();a,b=near[:2];site=ss[a[1]]
 gap=(b[0]-a[0])/(2*math.sqrt(max(b[0],1e-8)))
 worn=smooth(gap/.036)
 carve=-.043*(1-worn)
 plane=.10*(site[3]*a[2]+site[4]*a[3])
 # Broad very shallow irregular turning planes; no noise texture or floating plates.
 rel=min(.005,carve+plane*worn-.006)
 return rel,1-worn,site[2],worn

def color(z,cavity,tone,normalz):
 # Colors declared in sRGB; shader uses scene-linear native vertex albedo.
 h=smooth(z/1.15)
 low=(.14,.34,.59);mid=(.12,.47,.74);top=(.24,.67,.87)
 base=[mix(low[i],mid[i],smooth(h/.72)) for i in range(3)]
 base=[mix(base[i],top[i],smooth((h-.60)/.40)*.65) for i in range(3)]
 f=(1-.34*cavity)*(1+.055*tone)
 return tuple(srgb(clamp(c*f)) for c in base)+(1,)

mat=bpy.data.materials.new('Rock family soft cobalt native');mat.use_nodes=True
nt=mat.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');p=nt.nodes.new('ShaderNodeBsdfPrincipled');att=nt.nodes.new('ShaderNodeVertexColor');att.layer_name='stone_albedo'
nt.links.new(att.outputs['Color'],p.inputs['Base Color']);nt.links.new(att.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=.38
p.inputs['Roughness'].default_value=.88;p.inputs['Specular IOR Level'].default_value=.12
nt.links.new(p.outputs['BSDF'],out.inputs['Surface'])


def mesh_obj(name,vs,fs,cs,parent=root):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
 ob=bpy.data.objects.new(name,me);coll.objects.link(ob);ob.parent=parent;me.materials.append(mat)
 ca=me.color_attributes.new(name='stone_albedo',type='FLOAT_COLOR',domain='POINT')
 for i,c in enumerate(cs):ca.data[i].color=c
 for f in me.polygons:f.use_smooth=True
 return ob

# Sample side profile edges; exact corners occur in every ring.
qs=[]
for e,n in enumerate([1,58,34,18,58,18,34,58]):
 for j in range(n):qs.append((e,j/n,starts[e]+lengths[e]*j/n))
NX=128;NQ=len(qs)
vs=[];cs=[];fs=[]
for ix in range(NX+1):
 x=-.5+ix/NX;fade=math.sin(math.pi*(x+.5))**2
 for e,t,q in qs:
  ay,az=PROFILE[e];by,bz=PROFILE[(e+1)%8];y=mix(ay,by,t);z=mix(az,bz,t)
  dy,dz=by-ay,bz-az;le=math.hypot(dy,dz);ny,nz=dz/le,-dy/le
  rel,cav,tone,worn=field(x,q)
  if e==0:rel=0;cav=0
  else:rel*=fade
  yy=y+ny*rel;zz=z+nz*rel
  vs.append((x,yy,max(0,zz)));cs.append(color(zz,cav*fade,tone,nz))
for ix in range(NX):
 for j in range(NQ):
  a=ix*NQ+j;b=ix*NQ+(j+1)%NQ;c=(ix+1)*NQ+(j+1)%NQ;d=(ix+1)*NQ+j
  fs.append((a,b,c,d))
side=mesh_obj('rock-wall-middle__continuous_carved_stone',vs,fs,cs)
# Explicit analytic zero-X tangent at both cut planes; adjacent periodic surfaces share this normal.
side.data.update()
norms=[v.normal.copy() for v in side.data.vertices]
for ix in [0,NX]:
 for j in range(NQ):
  n=norms[ix*NQ+j];n.x=0;n.normalize()
side.data.normals_split_custom_set_from_vertices(norms)

# Native connector cap relief remains entirely inside X planes. Outer boundary exactly locked.
def top_at(y):
 if abs(y)<=.31:return 1.15
 if abs(y)<=.45:return 1.15-(abs(y)-.31)/.14*.11
 return 1.04-(abs(y)-.45)/.05*.37
caps=[]
for sign in [-1,1]:
 cv=[];cc=[];cf=[];NY=100;NZ=110
 for iz in range(NZ+1):
  t=iz/NZ
  for iy in range(NY+1):
   y=-.5+iy/NY;z=t*top_at(y)
   rel,cav,tone,worn=field(y,z,True)
   fade=math.sin(math.pi*iy/NY)**2*math.sin(math.pi*t)**2
   x=sign*(.5+min(0,rel)*fade)
   cv.append((x,y,z));cc.append(color(z,cav*fade,tone,0))
 for iz in range(NZ):
  for iy in range(NY):
   a=iz*(NY+1)+iy;b=a+1;c=b+NY+1;d=a+NY+1
   cf.append((a,b,c,d) if sign>0 else (d,c,b,a))
 ob=mesh_obj('rock-wall-middle__W_connector_stone' if sign<0 else 'rock-wall-middle__E_connector_stone',cv,cf,cc);caps.append(ob)

# Symmetric translation-invariant illumination: no horizontal preferred direction and no cast shadow.
world=bpy.data.worlds.new('Rock family neutral world');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs['Strength'].default_value=0;sc.world=world
lights=[]
for name,loc,power,size in [('overhead',(0,0,6),1.35,1),('north',(0,3,2),.42,1),('east',(3,0,2),.42,1),('south',(0,-3,2),.42,1),('west',(-3,0,2),.42,1)]:
 ld=bpy.data.lights.new('rock-family-'+name,'SUN');ld.energy=power;ld.angle=math.radians(20);ld.use_shadow=False
 lo=bpy.data.objects.new(ld.name,ld);sc.collection.objects.link(lo);lo.location=loc;lo.rotation_euler=(-Vector(loc)).to_track_quat('-Z','Y').to_euler();lights.append(lo)
cam=bpy.data.objects.new('Registered square top-front camera',bpy.data.cameras.new('Registered square top-front camera'));sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_x=0;cam.data.shift_y=.458332
cam.matrix_world=Matrix(json.loads((BASE/'inputs/source-camera.json').read_text())['camera']['worldMatrix'])
sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.cycles.seed=0
sc.cycles.pixel_filter_type='BOX';sc.render.resolution_x=768;sc.render.resolution_y=1408;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=1.2206555604934692;sc.render.pixel_aspect_y=1;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.dither_intensity=0
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.render.fps=12
sc.use_nodes=False
# Set root registration from actual native projection, not an inferred silhouette.
bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
base=px((0,0,0));cam.data.shift_y+= (1024-base[1])/(sc.render.resolution_x*sc.render.pixel_aspect_x/sc.render.pixel_aspect_y)
bpy.context.view_layer.update()
# Calibration shift scale is determined through actual native projection.
for _ in range(2):
 base=px((0,0,0));prev=cam.data.shift_y;cam.data.shift_y=prev+1;bpy.context.view_layer.update();delta=px((0,0,0))[1]-base[1];cam.data.shift_y=prev+(1024-base[1])/delta;bpy.context.view_layer.update()
recipe={'asset':'rock-wall-middle','round':2,'geometry':'periodic broad irregular Voronoi stone cells physically carved into full volumetric crag; native connector cap relief inside cut planes','sourceIntegrity':{'project':'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend','sha256':'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'},'frozenCriteriaSHA256':'8d81c78a53863ebe0cb910124338354e218fbe25d6607175a573d20280635239','capture':{'logicalFrame':[192,352],'logicalRoot':[96,256],'nativeScale':4,'nativeFrame':[768,1408],'publishedScale':2,'publishedFrame':[384,704],'pixelAspect':[sc.render.pixel_aspect_x,1],'cameraElevation':55.00797980144134,'rotationsDegrees':DIR},'material':{'nativeAttribute':'stone_albedo','roughness':.88,'specularIORLevel':.12,'emissionStrength':.38,'paletteSRGB':{'low':[.14,.34,.59],'mid':[.12,.47,.74],'top':[.24,.67,.87]},'detail':'Native geometric recesses; no texture images, target card, paint, raster repair or per-view treatment'},'lighting':{'type':'translation-invariant SUN','overheadEnergy':1.35,'fourCardinalEnergyEach':.42,'horizontalSymmetry':4,'castShadow':False,'worldStrength':0},'render':{'engine':'CYCLES','samples':48,'denoising':False,'pixelFilter':'BOX','viewTransform':'Standard','seed':0},'ports':{'planes':[-.5,.5],'profileYThenZ':PROFILE,'repeatUnit':1,'intrinsicRootTransform':'identity'},'resources':[]}
(BASE/'source/round-02-recipe.json').write_text(json.dumps(recipe,indent=2))
# Save S intrinsic scene for portable exact render replay.
root.rotation_euler.z=0;bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'source/round-02.blend'),compress=True)
views={}
for direction,degrees in DIR.items():
 root.rotation_euler.z=math.radians(degrees);bpy.context.view_layer.update()
 sc.render.filepath=str(OUT/f'native-static-{direction}.png');bpy.ops.render.render(write_still=True)
 views[direction]={'actualRootMatrix':[list(v) for v in root.matrix_world],'rotationDegrees':degrees,'rootPixel':px((0,0,0))}
# Save connected native runs by duplicating the exact side surface and retaining only external caps.
root.rotation_euler.z=0;bpy.context.view_layer.update()
assembled=bpy.data.collections.new('Connected three-module native comparison');sc.collection.children.link(assembled)
aroot=bpy.data.objects.new('connected-run__root',None);assembled.objects.link(aroot)
for i in [-1,0,1]:
 ob=side.copy();ob.data=side.data.copy();assembled.objects.link(ob);ob.parent=aroot;ob.location.x=i
for cap,i in [(caps[0],-1),(caps[1],1)]:
 ob=cap.copy();ob.data=cap.data.copy();assembled.objects.link(ob);ob.parent=aroot;ob.location.x=i
coll.hide_render=True
# Run frames enlarge canvas only: cell scale, native projection and center root fixed.
sc.render.resolution_x=1792;sc.render.resolution_y=2432;cam.data.ortho_scale=3.5;cam.data.shift_x=0
for _ in range(2):
 base=px((0,0,0));prev=cam.data.shift_y;cam.data.shift_y=prev+1;bpy.context.view_layer.update();delta=px((0,0,0))[1]-base[1];cam.data.shift_y=prev+(1536-base[1])/delta;bpy.context.view_layer.update()
for direction,degrees in DIR.items():
 aroot.rotation_euler.z=math.radians(degrees);bpy.context.view_layer.update();sc.render.filepath=str(OUT/f'connected-native-{direction}.png');bpy.ops.render.render(write_still=True)
# Restore source capture and no comparison geometry in deliverable blend.
for ob in list(assembled.objects):bpy.data.objects.remove(ob,do_unlink=True)
bpy.data.collections.remove(assembled);coll.hide_render=False;sc.render.resolution_x=768;sc.render.resolution_y=1408;cam.data.ortho_scale=1.5
for _ in range(2):
 base=px((0,0,0));prev=cam.data.shift_y;cam.data.shift_y=prev+1;bpy.context.view_layer.update();delta=px((0,0,0))[1]-base[1];cam.data.shift_y=prev+(1024-base[1])/delta;bpy.context.view_layer.update()
root.rotation_euler.z=0;bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'source/round-02.blend'),compress=True)
# Compact actual audit and family recipe, without geometry dumps.
allvs=[o.matrix_world@v.co for o in coll.objects if o.type=='MESH' for v in o.data.vertices]
audit={'asset':'rock-wall-middle','scene':sc.name,'collection':coll.name,'root':root.name,'intrinsicRootMatrix':[list(v) for v in root.matrix_world],'bounds':{'min':[min(v[i] for v in allvs) for i in range(3)],'max':[max(v[i] for v in allvs) for i in range(3)]},'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'coordinateSHA256':hashlib.sha256(b''.join(__import__('struct').pack('fff',*v.co) for v in o.data.vertices)).hexdigest(),'modifiers':[m.type for m in o.modifiers]} for o in coll.objects if o.type=='MESH'],'camera':{'worldMatrix':[list(v) for v in cam.matrix_world],'projectionMatrix':[list(v) for v in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=768,y=1408,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,1],'calibration':{'root':px((0,0,0)),'unitX':[px((1,0,0))[i]-px((0,0,0))[i] for i in range(2)],'unitDepth':[px((0,-1,0))[i]-px((0,0,0))[i] for i in range(2)],'unitHeight':[px((0,0,1))[i]-px((0,0,0))[i] for i in range(2)]}},'views':views,'ports':recipe['ports'],'resourceClosure':{'images':[],'libraries':[],'externalFiles':[]},'nativeGeometry':True,'animations':[]}
(OUT/'native-audit.json').write_text(json.dumps(audit,indent=2));print('ROUND_DONE',str(OUT))
