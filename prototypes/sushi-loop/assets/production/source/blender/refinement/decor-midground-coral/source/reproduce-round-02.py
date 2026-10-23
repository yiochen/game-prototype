"""Portable native coral build and exact registered capture. Run Blender -b --python THIS -- [--study]."""
import bpy, math, json, sys, hashlib
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
SRC=Path(__file__).resolve().parent
OBJ=SRC.parent
OUT=OBJ/'candidates/round-02'
STUDY='--study' in sys.argv
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='Refined Midground Coral'
col=bpy.data.collections.new('decor-midground-coral refined');sc.collection.children.link(col)
root=bpy.data.objects.new('decor-midground-coral root',None);col.objects.link(root);root['production_id']='decor-midground-coral'
root['semantics']='Fixed registered ground root, nonblocking layer2'

def lin(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

def rgb(h):return tuple(lin(int(h[i:i+2],16)/255) for i in (0,2,4))

def mat(name,hexcolor,rough=.63,variation=.0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb(hexcolor),1);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(*rgb(hexcolor),1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.23
 # A little colored self-fill keeps actual deep interiors readable without a black height ramp.
 bs.inputs['Emission Color'].default_value=(*rgb(hexcolor),1);bs.inputs['Emission Strength'].default_value=.035
 l.new(bs.outputs['BSDF'],out.inputs['Surface'])
 if variation:
  tex=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=5;noise.inputs['Detail'].default_value=1;noise.inputs['Roughness'].default_value=.5
  l.new(tex.outputs['Generated'],noise.inputs['Vector']);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.25;ramp.color_ramp.elements[1].position=.75
  ramp.color_ramp.elements[0].color=(*[v*(1-variation) for v in rgb(hexcolor)],1);ramp.color_ramp.elements[1].color=(*[v*(1+variation) for v in rgb(hexcolor)],1)
  l.new(noise.outputs['Fac'],ramp.inputs['Fac'])
  if name in ('Coral rose body','Violet body'):
   sep=n.new('ShaderNodeSeparateXYZ');l.new(tex.outputs['Generated'],sep.inputs['Vector'])
   grad=n.new('ShaderNodeMapRange');grad.inputs['From Min'].default_value=0;grad.inputs['From Max'].default_value=1;grad.inputs['To Min'].default_value=.73;grad.inputs['To Max'].default_value=1.04;l.new(sep.outputs['Z'],grad.inputs['Value'])
   multiply=n.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1;l.new(ramp.outputs['Color'],multiply.inputs[1]);l.new(grad.outputs['Result'],multiply.inputs[2])
   # Coarse sparse organic albedo spots, generated in the native tube coordinate system.
   stretch=n.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(2.7,2.7,5.7);l.new(tex.outputs['Generated'],stretch.inputs[0])
   vor=n.new('ShaderNodeTexVoronoi');vor.inputs['Scale'].default_value=1;l.new(stretch.outputs['Vector'],vor.inputs['Vector'])
   mask=n.new('ShaderNodeValToRGB');mask.color_ramp.elements[0].position=.18;mask.color_ramp.elements[0].color=(.84,.84,.84,1);mask.color_ramp.elements[1].position=.24;mask.color_ramp.elements[1].color=(1,1,1,1);l.new(vor.outputs['Distance'],mask.inputs['Fac'])
   patches=n.new('ShaderNodeMixRGB');patches.blend_type='MULTIPLY';patches.inputs[0].default_value=1;l.new(multiply.outputs['Color'],patches.inputs[1]);l.new(mask.outputs['Color'],patches.inputs[2]);l.new(patches.outputs['Color'],bs.inputs['Base Color'])
  else:l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
 return m
pink=mat('Coral rose body','CB3B6C',.59,.08)
pinkLip=mat('Coral warm peach lip','E8798E',.63,.025)
pinkIn=mat('Coral colored inner wall','A42659',.77,.035)
violet=mat('Violet body','744CD3',.67,.08)
violetLip=mat('Violet softened lilac lip','AA7DED',.59,.025)
violetIn=mat('Violet inner wall','4B2A92',.78,.025)
blue=mat('Cobalt reef','12517C',.75,.07)
blueTop=mat('Cobalt upper shoulder','19698E',.72,.05)
green=mat('Small seaweed jade','448F39',.76,.05)


def meshobj(name,verts,faces,mats,inds=None,smooth=True,role='reef'):
 me=bpy.data.meshes.new(name+' native mesh');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=root
 for m in mats:me.materials.append(m)
 for i,p in enumerate(me.polygons):p.use_smooth=smooth;p.material_index=inds[i] if inds else 0
 o['role']=role
 return o

# Compact finite irregular support. Ground remains Z0; high surface supports the tube roots.
outline=[(-.49,-.29),(-.45,-.44),(-.22,-.49),(.17,-.49),(.43,-.43),(.49,-.24),(.48,.20),(.38,.41),(.14,.49),(-.20,.48),(-.43,.34),(-.49,.07)]
verts=[]
for scale,z in [(.92,0),(1,.028),(1,.076),(.94,.115)]:
 for x,y in outline:verts.append((x*scale,y*scale,z))
N=len(outline);faces=[];inds=[]
faces.append(tuple(reversed(range(N))));inds.append(0)
for j in range(3):
 for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i));inds.append(0 if j<2 else 1)
faces.append(tuple(range(3*N,4*N)));inds.append(1)
reef=meshobj('Finite reef foundation',verts,faces,[blue,blueTop],inds,False)
be=reef.modifiers.new('Soft reef shoulders','BEVEL');be.width=.012;be.segments=3
be.affect='EDGES'
wn=reef.modifiers.new('Reef face normals','WEIGHTED_NORMAL');wn.keep_sharp=True

# Seven clear tubes with surface curvature and thick continuous rounded lips.
# z profile travels upward outside, across the lip, down the cavity and closes its rounded floor.
tubes=[]
specs=[
 ('Tall pink crown',(.015,.19),1.27,.143,(.006,.014),False,.4),
 ('Pink left fan',(-.282,.09),1.075,.139,(-.022,.018),False,1.6),
 ('Pink right fan',(.285,.075),1.015,.137,(.022,.006),False,2.7),
 ('Pink front left',(-.268,-.271),.735,.128,(-.011,-.018),False,4.2),
 ('Pink front right',(.274,-.267),.805,.127,(.014,-.012),False,5.2),
 ('Violet front',(.005,-.319),.565,.102,(.002,-.010),True,3.3),
 ('Violet rear',(-.205,.352),.765,.075,(-.005,.003),True,5.7),
 ('Violet small left',(-.425,-.355),.185,.043,(-.003,0),True,2.1),
 ('Violet small right',(.408,-.382),.215,.043,(.003,-.001),True,4.8),
]
for idx,(name,xy,H,R,lean,isV,phase) in enumerate(specs):
 # variable lip height is coherent across rings and does not alter actual base support
 profile=[(.00,.76),(.035,.84),(.14,.87),(.40,.98),(.68,1.02),(.88,1.025),(.955,1.035),(.980,1.02),(.997,.966),(1.002,.895),(.995,.81),(.979,.755),(.950,.735),(.88,.72),(.84,.70),(.80,.65),(.775,.51),(.77,.24)]
 seg=32;verts=[];faces=[];inds=[]
 for j,(t,r) in enumerate(profile):
  cx=lean[0]*(t*t);cy=lean[1]*(t*t)
  for i in range(seg):
   a=2*math.pi*i/seg
   wobble=1+.026*math.sin(3*a+phase)+.012*math.sin(5*a-phase)
   zz=H*t + (H*.006*math.sin(3*a+phase)*max(0,(t-.80)/.20))
   verts.append((cx+R*r*wobble*math.cos(a),cy+R*r*wobble*math.sin(a),zz))
 faces.append(tuple(reversed(range(seg))));inds.append(0)
 for j in range(len(profile)-1):
  for i in range(seg):faces.append((j*seg+i,j*seg+(i+1)%seg,(j+1)*seg+(i+1)%seg,(j+1)*seg+i));inds.append(0 if j<6 else 1 if j<12 else 2)
 # actual cavity floor, no external caps or painted mouth
 faces.append(tuple(range((len(profile)-1)*seg,len(profile)*seg)));inds.append(2)
 o=meshobj(name,verts,faces,[violet,violetLip,violetIn] if isV else [pink,pinkLip,pinkIn],inds,True,'coral')
 o.location=(*xy,.084);o['baseRingIndices']=list(range(seg));o['cavityInnerStart']=12*seg;o['cavityFloorStart']=(len(profile)-1)*seg;o['swayPhase']=phase
 # Small root-centered object rotation. Actual base plane remains embedded in finite reef.
 for f in range(1,14):
  t=(f-1)/12
  if f==13:t=0
  o.rotation_euler=(.0045*math.sin(2*math.pi*t+phase+.8),.009*math.sin(2*math.pi*t+phase),0)
  o.keyframe_insert('rotation_euler',frame=f)
 for layer in o.animation_data.action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 o.animation_data.action.name='idle · '+name
 tubes.append(o)

# Rock shoulders frame the colony rather than producing a slab stack.
def stone(name,x,y,rx,ry,zheight,phase):
 n=8;vv=[]
 for s,z in [(.80,0),(1,.035),(1,zheight*.63),(.66,zheight)]:
  for i in range(n):
   a=math.tau*i/n;w=1+.07*math.sin(i*2.3+phase);vv.append((x+math.cos(a)*rx*s*w,y+math.sin(a)*ry*s*w,z))
 ff=[tuple(reversed(range(n)))];ii=[0]
 for k in range(3):
  for i in range(n):ff.append((k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i));ii.append(0 if k<2 else 1)
 ff.append(tuple(range(3*n,4*n)));ii.append(1)
 o=meshobj(name,vv,ff,[blue,blueTop],ii,False)
 bevel=o.modifiers.new('Small stone edge softness','BEVEL');bevel.width=.009;bevel.segments=3
 norm=o.modifiers.new('Broad rock plane normals','WEIGHTED_NORMAL');norm.keep_sharp=True
 return o
stone('Front left cobalt shoulder',-.29,-.385,.173,.095,.20,.2)
stone('Front right cobalt shoulder',.278,-.391,.177,.091,.225,1.4)
stone('Left cobalt shoulder',-.397,.008,.08,.245,.169,2.0)
stone('Right cobalt shoulder',.403,.045,.074,.231,.181,3.1)
stone('Rear cobalt shoulder',.07,.387,.294,.084,.17,1.1)

# Restrained organic accents in gaps, all rooted in the same finite support.
def leaf(name,xy,H,dx,dy):
 vv=[];nn=12
 for t,w in [(0,.025),(.18,.037),(.50,.043),(.80,.030),(.97,.010)]:
  for i in range(nn):
   a=math.tau*i/nn
   vv.append((xy[0]+dx*t*t+w*math.cos(a),xy[1]+dy*t*t+w*.42*math.sin(a),.085+H*t))
 ff=[tuple(reversed(range(nn)))]
 for j in range(4):
  for i in range(nn):ff.append((j*nn+i,j*nn+(i+1)%nn,(j+1)*nn+(i+1)%nn,(j+1)*nn+i))
 vv.append((xy[0]+dx,xy[1]+dy,.085+H));tip=len(vv)-1
 for i in range(nn):ff.append((4*nn+i,4*nn+(i+1)%nn,tip))
 return meshobj(name,vv,ff,[green],smooth=True,role='accent')
leaf('Jade shoot left',(-.397,-.10),.25,-.025,.018)
leaf('Jade shoot middle',(.102,-.123),.22,.025,.010)
leaf('Jade shoot rear',(.358,.281),.24,.012,.022)

# Use the exact recorded world matrix, projection and registration. No per-view fit.
recorded=json.loads((SRC/'resources/source-camera.json').read_text())
cam=bpy.data.objects.new('Registered 55.00798 capture',bpy.data.cameras.new('Registered orthographic camera'));sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.clip_start=.1;cam.data.clip_end=1000
elev=math.radians(55.00797980144134)
cam.location=(0,-10*math.cos(elev),10*math.sin(elev));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.resolution_x=768;sc.render.resolution_y=1536;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=recorded['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1
sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.cycles.seed=17;sc.cycles.use_animated_seed=False
sc.cycles.max_bounces=5;sc.cycles.diffuse_bounces=3;sc.cycles.glossy_bounces=2;sc.cycles.transparent_max_bounces=4
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=60
sc.render.fps=12;sc.frame_start=1;sc.frame_end=12
sc.render.dither_intensity=0;sc.render.filter_size=1.2;sc.cycles.pixel_filter_type='BLACKMAN_HARRIS';sc.cycles.filter_width=1.2
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.use_nodes=False
sc.world=bpy.data.worlds.new('Symmetric soft ambient');sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.77,.83,1,1);bg.inputs['Strength'].default_value=.28

def light(name,pos,energy,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color
 o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.55))-o.location).to_track_quat('-Z','Y').to_euler();return o
light('Broad warm overhead',(0,0,4.5),155,4.0,(1,.89,.80))
for i in range(4):
 a=math.pi*i/2;light('Symmetric fill '+str(i),(3*math.cos(a),3*math.sin(a),2.2),76,4,(1,.96,.91))
bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*768,(1-p.y)*1536))
base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(1152-base.y)/dy;bpy.context.view_layer.update()
assert abs(px((0,0,0)).y-1152)<.02

def matrix(m):return [list(r) for r in m]
def camera_record(scale):
 p0=px((0,0,0));units=[px((1,0,0))-p0,px((0,-1,0))-p0,px((0,0,1))-p0]
 return {'projection':'top-down-oblique-square-grid','frame':[192,384],'anchor':[96,288],'cellSize':128,'captureScale':scale,'fps':12,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':matrix(cam.matrix_world),'projectionMatrix':matrix(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=768,y=1536,scale_x=sc.render.pixel_aspect_x,scale_y=1)),'pixelAspect':[sc.render.pixel_aspect_x,1],'worldUnitsPerCell':1,'elevationDegrees':55.00797980144134,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]},'calibration':{'root':[v*scale/4 for v in p0],'unitX':[v*scale/4 for v in units[0]],'unitDepth':[v*scale/4 for v in units[1]],'unitHeight':[v*scale/4 for v in units[2]]}}

def evaluated(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();pp=[root.matrix_world.inverted()@e.matrix_world@v.co for v in m.vertices];ff=[list(p.vertices) for p in m.polygons];e.to_mesh_clear();return pp,ff

def bounds(pp):return [[min(p[i] for p in pp),max(p[i] for p in pp)]for i in range(3)]

if STUDY:
 root.rotation_euler.z=0;sc.frame_set(4);bpy.context.view_layer.update();p=SRC/'study-02-S.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);print('STUDY_RENDER',p,flush=True)
else:
 OUT.mkdir(parents=True,exist_ok=True)
 # Save actual model/actions/materials/lighting and registered scene at representative S/frame4.
 root.rotation_euler.z=0;sc.frame_set(4);bpy.context.view_layer.update()
 project=SRC/'round-02.blend';bpy.ops.wm.save_as_mainfile(filepath=str(project),compress=True)
 source_sha=hashlib.sha256(project.read_bytes()).hexdigest()
 (OUT/'native-camera.json').write_text(json.dumps(camera_record(4),indent=2)+'\n')
 pub=camera_record(2);pub['publication']={'nativeFrame':[768,1536],'nativeCaptureScale':4,'publishedFrame':[384,768],'method':'uniform whole-frame LANCZOS resize','nativeCameraRecord':'native-camera.json'};(OUT/'published-camera.json').write_text(json.dumps(pub,indent=2)+'\n')
 records=[];posehashes={};contacts=[]
 for direction,ang in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
  for frame in range(1,14):
   root.rotation_euler.z=ang;sc.frame_set(frame);bpy.context.view_layer.update();pp=[];meshes={};rv=[];rf=[]
   for o in col.all_objects:
    if o.type!='MESH':continue
    pts,faces=evaluated(o);pp+=pts;meshes[o.name]={'boundsRoot':bounds(pts),'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale)}
    if o.get('role')=='reef':
     offset=len(rv);rv+=pts;rf += [[i+offset for i in f]for f in faces]
   tree=BVHTree.FromPolygons(rv,rf,all_triangles=False);tests=[]
   for o in tubes:
    pts,_=evaluated(o);ring=pts[:32];points=[]
    for p in ring:
     hit,normal,index,distance=tree.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)),3)
     points.append({'point':list(p),'surfaceZ':hit.z if hit else None,'penetration':hit.z-p.z if hit else None})
    tests.append({'name':o.name,'supported':sum(p['penetration'] is not None and p['penetration']>=-1e-5 for p in points),'total':len(points),'points':points})
   contacts.append({'direction':direction,'frame':frame,'tubeContacts':tests})
   projected=[world_to_camera_view(sc,cam,root.matrix_world@p)for p in pp]
   pose=hashlib.sha256(json.dumps([[round(v,7)for v in p]for p in pp]).encode()).hexdigest();posehashes[f'{direction}-{frame}']=pose
   p=OUT/('closure' if frame==13 else 'native')/direction/(f'{frame-1:03}.png');p.parent.mkdir(parents=True,exist_ok=True)
   records.append({'direction':direction,'clip':'idle','frame':frame,'index':frame-1,'rootRotationZ':root.rotation_euler.z,'rootMatrix':matrix(root.matrix_world),'rootLocation':list(root.location),'rootScale':list(root.scale),'cameraWorldMatrix':matrix(cam.matrix_world),'cameraProjectionMatrix':camera_record(4)['camera']['projectionMatrix'],'boundsRoot':bounds(pp),'projectedBoundsPixels':[min(p.x for p in projected)*768,min((1-p.y)for p in projected)*1536,max(p.x for p in projected)*768,max((1-p.y)for p in projected)*1536],'poseHashRounded1e7':pose,'objects':meshes,'sourceSHA256':source_sha,'path':str(p.relative_to(OBJ))})
   sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);print('CAPTURED',direction,frame,flush=True)
 # All active actual temporal channels.
 ownership=[]
 for o in col.all_objects:
  if not o.animation_data:continue
  action=o.animation_data.action;curves=[]
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for curve in bag.fcurves:curves.append({'path':curve.data_path,'index':curve.array_index,'keys':[[float(k.co.x),float(k.co.y),k.interpolation]for k in curve.keyframe_points]})
  ownership.append({'ownerName':o.name,'action':action.name,'slot':o.animation_data.action_slot.identifier,'channels':curves})
 topology=[]
 import bmesh
 for o in col.all_objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);topology.append({'name':o.name,'vertices':len(bm.verts),'polygons':len(bm.faces),'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges),'modifiers':[{'name':m.name,'type':m.type}for m in o.modifiers],'role':o.get('role')});bm.free()
 cm=camera_record(4)
 data={'asset':'decor-midground-coral','project':'source/round-02.blend','projectSHA256':source_sha,'blenderVersion':bpy.app.version_string,'camera':cm,'cameraMatrixMaxDifference':max(abs(cm['camera']['worldMatrix'][i][j]-recorded['camera']['worldMatrix'][i][j])for i in range(4)for j in range(4)),'projectionMatrixMaxDifference':max(abs(cm['camera']['projectionMatrix'][i][j]-recorded['camera']['projectionMatrix'][i][j])for i in range(4)for j in range(4)),'captureRecords':records,'finiteSupport':contacts,'temporalOwnership':ownership,'closureEvaluatedPose':{d:posehashes[f'{d}-1']==posehashes[f'{d}-13']for d in 'NESW'},'nativeSettings':{'engine':sc.render.engine,'samples':sc.cycles.samples,'denoising':sc.cycles.use_denoising,'seed':sc.cycles.seed,'animatedSeed':sc.cycles.use_animated_seed,'pixelFilter':sc.cycles.pixel_filter_type,'filterWidth':sc.cycles.filter_width,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':0,'gamma':1,'compositor':False,'frame':[768,1536],'pixelAspect':[sc.render.pixel_aspect_x,1]},'topology':topology,'lighting':{'world':{'color':list(bg.inputs['Color'].default_value),'strength':bg.inputs['Strength'].default_value},'lamps':[{'name':o.name,'position':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)}for o in sc.objects if o.type=='LIGHT'],'horizontalSymmetry':4,'groundPlane':False},'otherTemporalChannels':{'root':False,'reef':False,'materials':False,'shader':False,'visibility':False,'drivers':False,'shapeKeys':False,'constraints':False,'armatures':False},'ownedTextures':[],'limitations':['Native model/style is submitted for independent judge review; no editor aesthetic approval.']}
 (OUT/'native-validation.json').write_text(json.dumps(data,indent=2)+'\n')
 print('NATIVE_CAPTURE_COMPLETE',flush=True)
