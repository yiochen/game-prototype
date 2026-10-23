"""Portable native reconstruction and capture. Run with Blender --background --python this.py.
Optional COIN_RENDER=hero renders only S/005 for draft inspection. Otherwise renders all48.
"""
import bpy,math,json,hashlib,os,shutil
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
OBJ=Path(__file__).resolve().parent.parent
SRC=OBJ/'source'; OUT=OBJ/'candidates'/'round-01'; OUT.mkdir(parents=True,exist_ok=True)
ORIGINAL=SRC/'original-library.blend'
if not ORIGINAL.exists():
 ref=(OBJ/json.loads((OBJ/'brief.json').read_text())['source']['project']).resolve()
 shutil.copyfile(ref,ORIGINAL)
assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
bpy.ops.wm.open_mainfile(filepath=str(ORIGINAL))
scene=bpy.context.scene
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):bpy.data.collections.remove(c)
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
coll=bpy.data.collections.new('Coin Pop | Native Soft Gold');scene.collection.children.link(coll)
def obj(name,data=None,parent=None):
 o=bpy.data.objects.new(name,data);coll.objects.link(o);o.parent=parent;return o
root=obj('coin-pop__ground_root');root['asset_id']='coin-pop';root['footprint_cells']='[1,1]';root['ground_root']='[0,0,0]';root['facingPolicy']='camera-facing'
visual=obj('coin-pop__camera_facing_visual',parent=root)
f=visual.driver_add('rotation_euler',2);f.driver.expression='-host_z';v=f.driver.variables.new();v.name='host_z';v.type='SINGLE_PROP';v.targets[0].id=root;v.targets[0].data_path='rotation_euler[2]'
emitter=obj('coin-pop__semantic_coin_emitter',parent=visual)
emitter['meaning']='Locked principal coin pivot: loc(0,0,.66+.42t), Euler(pi/2,0,.7t), uniform max(.025,sin(pi*t)**.45)'
def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def mat(name,h,rough=.36,metal=.16):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)];b.inputs['Base Color'].default_value=(*map(linear,rgb),1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal;b.inputs['Specular IOR Level'].default_value=.28;b.inputs['Coat Weight'].default_value=.12;b.inputs['Coat Roughness'].default_value=.28;return m
mats=[mat('Warm orange gold | turned edge','EAA024',.4,.1),mat('Gold rounded rim','FFBF2F',.34,.18),mat('Pale edge reflection band','FFDA66',.32,.16),mat('Inset gold face','FFD25A',.4,.1),mat('Relief orange gold','EB9D19',.34,.1),mat('Glints warm cream gold','FFE47A',.33,.1)]
# Continuous radial profile, no intersecting rim torus. Adjacent rings share vertices.
profile=[(0,-.052,0),(.187,-.052,0),(.209,-.045,0),(.220,-.031,0),(.224,-.012,0),(.224,.017,0),(.216,.037,1),(.201,.052,1),(.179,.055,1),(.171,.052,2),(.166,.046,2),(.158,.042,3),(0,.042,3)]
verts=[];faces=[];mi=[];N=64
for r,z,_ in profile:
 for i in range(N):
  ang=2*math.pi*i/N;verts.append((r*math.cos(ang),r*math.sin(ang),z))
for j in range(len(profile)-1):
 for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i));mi.append(profile[j+1][2])
mesh=bpy.data.meshes.new('Continuous dimensional coin lathe');mesh.from_pydata(verts,[],faces);mesh.update();coin=obj('coin-pop__rounded_coin_rim_and_face',mesh,emitter)
for m in mats:mesh.materials.append(m)
for p,idx in zip(mesh.polygons,mi):p.material_index=idx;p.use_smooth=True
# Real beveled raised bar, local height follows coin face.
bpy.ops.mesh.primitive_cube_add(size=1)
bar=bpy.context.object;bar.name='coin-pop__raised_currency_bar';
for c in list(bar.users_collection):c.objects.unlink(bar)
coll.objects.link(bar);bar.parent=emitter;bar.location=(0,0,.060);bar.dimensions=(.047,.183,.036);bpy.context.view_layer.objects.active=bar;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bar.data.materials.append(mats[4]);bevel=bar.modifiers.new('Rounded crafted relief edges','BEVEL');bevel.width=.009;bevel.segments=5
bar.modifiers.new('Face weighted normals','WEIGHTED_NORMAL')
for p in bar.data.polygons:p.use_smooth=True
# Curved concave four-point sparkles. Thick profile, separate front/edge surfaces.
sparks=[]
for q,(x,z,r) in enumerate([(-.11,.86,.052),(.16,.96,.043),(.31,.70,.050)]):
 pivot=obj('coin-pop__spark_emitter_%d'%q,parent=visual);pivot.location=(x,-.02,z);sparks.append(pivot)
 # plane front XZ; native depth .012, with softly beveled cusps via cubic samples
 boundary=[]
 # Each quadrant has concave control approaching a tapered tip. Eight subdivisions per quarter.
 tips=[(r,0),(0,r*1.32),(-r,0),(0,-r*1.32)]
 for side in range(4):
  a=Vector(tips[side]);b=Vector(tips[(side+1)%4]);control=Vector((0,0))
  for j in range(10):
   t=j/10;p=(1-t)**2*a+2*(1-t)*t*control+t*t*b;boundary.append(p)
 n=len(boundary);sv=[]
 for y,s in [(.007,.90),(-.001,1.0),(-.009,.86)]:
  sv.extend([(p.x*s,y,p.y*s) for p in boundary])
 sv.extend([(0,.007,0),(0,-.011,0)])
 sf=[]
 for j in range(2):
  for k in range(n):sf.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
 for k in range(n):sf.append((3*n,k,(k+1)%n));sf.append((3*n+1,2*n+(k+1)%n,2*n+k))
 sm=bpy.data.meshes.new('Curved four-point glint solid %d'%q);sm.from_pydata(sv,[],sf);sm.materials.append(mats[5]);sm.update();so=obj('coin-pop__dimensional_glint_%d'%q,sm,pivot)
 for p in sm.polygons:p.use_smooth=True
for i in range(12):
 t=i/11;s=max(.025,max(0,math.sin(math.pi*t))**.45)
 emitter.location=(0,0,.66+.42*t);emitter.rotation_euler=(math.pi/2,0,.7*t);emitter.scale=(s,)*3
 for key in ['location','rotation_euler','scale']:emitter.keyframe_insert(data_path=key,frame=i+1,group='Frozen source pop phase')
 for q,p in enumerate(sparks):
  x,z,_=[(-.11,.86,.052),(.16,.96,.043),(.31,.70,.050)][q];p.location=(x,-.02,z+.42*t);p.scale=(s,)*3
  for key in ['location','scale']:p.keyframe_insert(data_path=key,frame=i+1,group='Frozen source sparkle rise and collapse')
# Linear interpolation of the exact integer samples.
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for f in bag.fcurves:
     for k in f.keyframe_points:k.interpolation='LINEAR'
# Actual recovered registered camera; one shared camera for all frames and facings.
cd=bpy.data.cameras.new('Registered coin-pop orthographic');cam=obj('Coin Pop Registered Camera',cd);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=1.5;cd.sensor_fit='HORIZONTAL';cd.shift_x=0;cd.shift_y=.34134501218795776
cam.matrix_world=Matrix([[1,0,0,0],[0,.8192317485809326,-.5734625458717346,-5.734623432159424],[0,.5734625458717346,.8192317485809326,8.1923189163208],[0,0,0,1]])
# Equal cardinal area lights + centered overhead: no preferred horizontal illumination.
def area(name,loc,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=obj(name,d);o.location=loc;o.rotation_euler=(Vector((0,0,.85))-o.location).to_track_quat('-Z','Y').to_euler()
area('Centered broad overhead',(0,0,4.5),180,3.5)
for i in range(8):
 a=2*math.pi*i/8;area('Equal radial softbox %d'%i,(3*math.cos(a),3*math.sin(a),2.2),65,4)
world=bpy.data.worlds.new('Symmetric soft neutral world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18;scene.world=world
scene.use_nodes=False;scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=384;scene.render.resolution_y=704;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=1.2206555604934692;scene.render.pixel_aspect_y=1
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True;scene.render.fps=12;scene.frame_start=1;scene.frame_end=12
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.render.image_settings.color_depth='8';scene.render.use_file_extension=True
scene.frame_set(6);root.rotation_euler[2]=0;bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'round-01.blend'))
def bounds():
 deps=bpy.context.evaluated_depsgraph_get();allv=[];objects=[]
 for o in coll.objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(deps);me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();allv+=vs
  objects.append({'name':o.name,'vertices':len(vs),'bounds':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]],'worldMatrix':[list(row) for row in o.matrix_world]})
 return [[min(v[i] for v in allv) for i in range(3)],[max(v[i] for v in allv) for i in range(3)]],objects
records=[]
for direction,yaw in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler[2]=yaw;bpy.context.view_layer.update()
 for i in range(12):
  if os.getenv('COIN_RENDER')=='hero' and (direction!='S' or i!=5):continue
  scene.frame_set(i+1);bpy.context.view_layer.update();b,parts=bounds();path=OUT/'raw'/('pop-'+direction)/('%03d.png'%i);path.parent.mkdir(parents=True,exist_ok=True)
  scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  records.append({'clip':'pop','direction':direction,'index':i,'nativeFrame':i+1,'phase':i/11,'path':str(path.relative_to(OBJ)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rootRotationZ':float(root.rotation_euler.z),'rootMatrix':[list(row) for row in root.matrix_world],'visualCounterrotationZ':float(visual.rotation_euler.z),'visualWorldMatrix':[list(row) for row in visual.matrix_world],'semanticEmitter':{'name':emitter.name,'location':list(emitter.location),'rotationEuler':list(emitter.rotation_euler),'scale':list(emitter.scale),'matrixWorld':[list(row) for row in emitter.matrix_world]},'bounds':b,'objects':parts})
(OUT/('draft-hero-ledger.json' if os.getenv('COIN_RENDER')=='hero' else 'candidate-phases.json')).write_text(json.dumps(records,indent=2))
# Measured camera record at current native capture; logical dimensions and source scale are explicit.
pts={}
for name,p in [('root',(0,0,0)),('unitX',(1,0,0)),('unitDepth',(0,-1,0)),('unitHeight',(0,0,1))]:
 v=world_to_camera_view(scene,cam,Vector(p));pts[name]=[v.x*384,(1-v.y)*704]
camera={'assetId':'coin-pop','frame':[192,352],'anchor':[96,256],'captureScale':2,'fps':12,'cellSize':128,'nativeFrame':[384,704],'camera':{'name':cam.name,'type':cd.type,'orthoScale':cd.ortho_scale,'sensorFit':cd.sensor_fit,'worldMatrix':[list(row) for row in cam.matrix_world],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'shift':[cd.shift_x,cd.shift_y]},'measuredProjectedCoordinatesNative':pts}
(OUT/'camera.json').write_text(json.dumps(camera,indent=2))
asset={'id':'coin-pop','frame':[192,352],'anchor':[96,256],'scale':2,'footprint':[1,1],'height':1.12,'facingPolicy':'camera-facing','sockets':{},'clips':{'pop':{'frames':12,'fps':12,'loop':False,'static':False}},'directions':['N','E','S','W']}
(OUT/'asset-record.json').write_text(json.dumps(asset,indent=2))
rig={'assetId':'coin-pop','fps':12,'groundRootObject':root.name,'visualCounterrotation':{'object':visual.name,'dataPath':'rotation_euler[2]','expression':'-host_z','target':root.name},'semanticEmitter':emitter.name,'clips':{'pop':{'frames':12,'fps':12,'loop':False,'firstFrame':1,'lastUniqueFrame':12,'closingKeyFrame':None,'actions':[a.name for a in bpy.data.actions]}}}
(OUT/'rig.json').write_text(json.dumps(rig,indent=2))
print('COIN_NATIVE_CAPTURE_COMPLETE',len(records))
