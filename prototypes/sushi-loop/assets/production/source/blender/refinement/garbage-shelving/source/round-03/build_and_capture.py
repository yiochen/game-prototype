"""Portable native recipe. Blender 5.2.2 --background --python this.py -- [--full|--build-only|--reproduce].
Only immutable source-native actions are evaluated; no regenerated pose routine.
"""
import sys
sys.dont_write_bytecode=True
import bpy,bmesh,math,json,hashlib,shutil,os
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent; OBJ=HERE.parents[1]; OUT=OBJ/'candidates/round-03'; OUT.mkdir(parents=True,exist_ok=True)
RES=HERE/'resources'; RIG=json.loads((RES/'original-rig.json').read_text()); CAM=json.loads((RES/'original-camera.json').read_text()); CATALOG=json.loads((RES/'original-catalog.json').read_text())
FLAGS=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
REPRO='--reproduce' in FLAGS
if REPRO:OUT=OBJ/'candidates/round-03/reproduction';OUT.mkdir(parents=True,exist_ok=True)
def plain(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
 try:return [plain(v) for v in x]
 except:return str(x)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def fcurves(a):
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for c in bag.fcurves:yield c
def action_record(a):return {'name':a.name,'slots':[s.identifier for s in a.slots],'curves':[{'path':c.data_path,'index':c.array_index,'keys':[[k.co.x,k.co.y,k.interpolation] for k in c.keyframe_points]} for c in fcurves(a)]}
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name='garbage-shelving warm native round03'
with bpy.data.libraries.load(str(RES/'original-library.blend'),link=False) as (src,dst):
 dst.collections=['S33_PROP_garbage-shelving'];dst.actions=[a for a in src.actions if 'garbage-shelving__' in a]
col=bpy.data.collections['S33_PROP_garbage-shelving'];scene.collection.children.link(col)
col.hide_render=False;col.hide_viewport=False
for ob in col.all_objects:ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
for lc in scene.view_layers[0].layer_collection.children:lc.exclude=False;lc.hide_viewport=False
bpy.context.view_layer.update()
root=bpy.data.objects['garbage-shelving__root'];carriers=[o for o in col.objects if o.type=='MESH']
for a in bpy.data.actions:a.use_fake_user=True
ACTIONS_SOURCE=[action_record(a) for a in bpy.data.actions]
BASE={o.name:{'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrix':o.matrix_world.copy()} for o in carriers}
def apply(clip,frame,direction):
 for o in carriers:
  o.animation_data_create();o.animation_data.action=None
 for r in RIG['clips'][clip]['actions']:
  o=bpy.data.objects[r['ownerName']];a=bpy.data.actions[r['action']];o.animation_data.action=a;o.animation_data.action_slot=next(s for s in a.slots if s.identifier==r['slotIdentifier'])
 root.rotation_euler=(0,0,{'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[direction]);scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
def srgb(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def color(h):return tuple(srgb(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)
def mat(name,h,rough=.55,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=color(h);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color(h);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Specular IOR Level'].default_value=.22
 return m
def wood(name,cols,orient='X'):
 m=mat(name,cols[1],.5);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');sc=n.new('ShaderNodeVectorMath');sc.operation='MULTIPLY';sc.inputs[1].default_value=(.75,3.5,2) if orient=='X' else (3.5,3.5,.7);l.new(tc.outputs['Generated'],sc.inputs[0]);no=n.new('ShaderNodeTexNoise');no.inputs['Scale'].default_value=1.9;no.inputs['Detail'].default_value=1.4;no.inputs['Roughness'].default_value=.6;l.new(sc.outputs['Vector'],no.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements.remove(r.color_ramp.elements[1]);r.color_ramp.elements[0].position=.23;r.color_ramp.elements[0].color=color(cols[0]);r.color_ramp.elements.new(.52).color=color(cols[1]);r.color_ramp.elements.new(.78).color=color(cols[2]);l.new(no.outputs['Fac'],r.inputs['Fac']);l.new(r.outputs['Color'],p.inputs['Base Color']);return m
woodmain=wood('Honey oak broad flowing grain',['AE6626','CC8734','DA9B45'])
woodalt=wood('Honey oak neighboring plank',['AF6727','D18C39','E0A34E'])
woodpost=wood('Honey oak upright long grain',['9F5924','BD7630','D59644'],'Z')
edge=mat('Warm worn wood turning edges','D99A4B',.44);edgeDark=mat('Warm edge end grain','C3853D',.6)
grainless=mat('Dark warm scored wood','925323',.7)
boxTan=mat('Parchment brown cardboard','AE8D5D',.78);boxCream=mat('Worn tan cardboard','C4A97C',.8);boxOlive=mat('Muted olive storage carton','777B48',.8);boxEdge=mat('Cardboard rounded folds','B59D72',.82);tape=mat('Wide faded linen packing tape','D3BB8C',.85);tapeOlive=mat('Olive box fold line','929161',.82)
metal=mat('Graphite iron fittings','454B4D',.38,.65);metalEdge=mat('Iron rivet rounded heads','7C8584',.27,.7)
parts={o.name:[] for o in carriers}
def mesh_obj(name,vs,fs,mats):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.clear()
 for m in mats:me.materials.append(m)
 me.update();o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);return o
def finish(o,bevel=.015,segments=3,edgeMat=None):
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 if edgeMat:
  o.data.materials.append(edgeMat)
 if bevel:
  mo=o.modifiers.new('Native rounded worn edges','BEVEL');mo.width=bevel;mo.segments=segments;mo.affect='EDGES';mo.limit_method='ANGLE';mo.angle_limit=.45;mo.harden_normals=True
  if edgeMat:mo.material=len(o.data.materials)-1
  bpy.ops.object.modifier_apply(modifier=mo.name)
 for p in o.data.polygons:p.use_smooth=True
 mo=o.modifiers.new('Stable broad face normals','WEIGHTED_NORMAL');mo.keep_sharp=True;mo.weight=50;bpy.ops.object.modifier_apply(modifier=mo.name)
 o.select_set(False);return o
def cube(name,loc,dims,ma,bevel=.015,edgeMa=None):
 x,y,z=[d/2 for d in dims];vs=[(a*x+loc[0],b*y+loc[1],c*z+loc[2]) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]];fs=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)];return finish(mesh_obj(name,vs,fs,[ma]),bevel,3,edgeMa)
def carrierpart(o,part,local=True):
 if local:part.matrix_world=o.matrix_world.copy()
 parts[o.name].append(part)
 return part
def polyplank(name,yc,width,length,t,sag,chip,ma):
 # Separate closed top and bottom strips. Unequal edge samples create deliberate breakouts.
 xs=[-length/2,-length/2+.10,-.64,-.38,-.1,.20,.49,length/2-.1,length/2]
 vs=[]
 for side in [-1,1]:
  for i,x in enumerate(xs):
   yy=yc+side*width/2
   if side==-1:
    yy+= (.018 if i in (1,6) else 0)
    if chip and i==6:yy+=.062
   else:yy-=.013 if i in (2,7) else 0
   zz=-sag*(1-(x/(length/2))**2)+.004*math.sin(x*4+yc*8)
   vs.extend([(x,yy,zz-t/2),(x,yy,zz+t/2)])
 fs=[];N=len(xs)
 for i in range(N-1):
  a=2*i;b=2*(i+1);c=2*(N+i);d=2*(N+i+1)
  fs.extend([(a,c,d,b),(a+1,b+1,d+1,c+1),(a,b,b+1,a+1),(c+1,d+1,d,c)])
 fs.extend([(0,1,2*N+1,2*N),(2*(N-1),2*(2*N-1),2*(2*N-1)+1,2*(N-1)+1)])
 return finish(mesh_obj(name,vs,fs,[ma]),.016,3,edge)
def curve(name,coords,rad,ma):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=2;c.bevel_depth=rad;c.bevel_resolution=2;s=c.splines.new('POLY');s.points.add(len(coords)-1)
 for p,v in zip(s.points,coords):p.co=(*v,1)
 o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);o.data.materials.append(ma);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return o
def sphere(name,loc,radius,ma,scale=(1,1,1)):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=radius,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma)
 for p in o.data.polygons:p.use_smooth=True
 o.select_set(False);return o
apply('idle',1,'S')
# Chunky uprights: tilted original centerline; horizontal native contact faces at actual ground0.
for o in carriers:
 if 'old_upright' not in o.name:continue
 x,y,z=o.location
 zlevels=[0,.12,.66,1.20,1.60];vs=[]
 for zi in zlevels:
  cx=x+.03846*(zi-.8);w=.088 if zi<.2 else .084
  vs.extend([(cx+dx*w,y+dy*.087,zi) for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]])
 fs=[(3,2,1,0)]
 for k in range(4):
  for j in range(4):fs.append((4*k+j,4*k+(j+1)%4,4*(k+1)+(j+1)%4,4*(k+1)+j))
 fs.append((16,17,18,19));part=finish(mesh_obj('crafted leaning post',vs,fs,[woodpost]),.018,3,edgeDark);carrierpart(o,part,False)
 # Fasteners on front and rear, seated into wood.
 for sign in (-1,1):
  for zz in (.58,1.12):
   xx=x+.03846*(zz-.8)
   p=sphere('rounded iron peg',(xx,y+sign*.087,zz),.032,metalEdge,(1,.38,1));carrierpart(o,p,False)
for k in range(4):
 o=bpy.data.objects[f'garbage-shelving__warped_shelf_{k}']
 for j in range(3):
  yc=(j-1)*.268
  p=polyplank(f'tier{k} crafted board{j}',yc,.259,1.964,.115 if k==3 else .102,.018 if k in(1,2) else .008,(k+j)%3==0,woodmain if j!=1 else woodalt);carrierpart(o,p)
  # Sparse irregular broad dark grain tracks, embedded in the top face, never external auras.
  for lane in range(2):
   pts=[]
   for i in range(27):
    x=-.83+i*1.66/26;y=yc+(lane-.5)*.083+.012*math.sin(x*5+j*1.8+k)+.005*math.sin(x*11+lane)
    z=(.115 if k==3 else .102)/2-(.018 if k in(1,2) else .008)*(1-(x/.982)**2)+.004*math.sin(x*4+yc*8)+.0005
    pts.append((x,y,z))
   p=curve(f'tier{k} grain{j}-{lane}',pts,.0018,grainless);carrierpart(o,p)
 # Endward shallow saw crack on visible front edge, native dark groove.
 pts=[(.54,-.382,.056),(.57,-.353,.055),(.59,-.330,.051)]
 carrierpart(o,curve('weathered split',pts,.0035,grainless))
# Rear diagonal bracing remains its own original semantic trajectory.
o=bpy.data.objects['garbage-shelving__back_brace'];carrierpart(o,cube('substantial diagonal rear brace',(0,0,0),(.095,.075,2.23),woodpost,.012,edgeDark))
for z in(-.94,.94):carrierpart(o,sphere('rear brace inset peg',(0,-.045,z),.027,metalEdge,(1,.4,1)))
# Six stored cartons have fully native rounded volumes and wrapping bands on all useful sides.
for i in range(6):
 o=bpy.data.objects[f'garbage-shelving__stored_box_{i}'];ma=[boxCream,boxOlive,boxTan,boxOlive,boxCream,boxTan][i]
 carrierpart(o,cube('rounded storage carton',(0,0,0),(.39,.475,.31),ma,.019,boxEdge if i%3!=1 else tapeOlive))
 # Wrap through x narrow and around y/z with clean softened corners, avoids penetrating body.
 carrierpart(o,cube('broad top packing band',(.015,0,.155),(.082,.454,.007),tape,.003))
 carrierpart(o,cube('front packing band',(.015,-.238,0),(.082,.007,.294),tape,.003))
 carrierpart(o,cube('back packing band',(.015,.238,0),(.082,.007,.294),tape,.003))
 carrierpart(o,cube('bottom packing band',(.015,0,-.155),(.082,.454,.006),tape,.002))
 # A dark folded lid seam is embedded into the top surface; broad short tape is easy to read.
 carrierpart(o,cube('folded carton lid seam',(-.095,0,.155),(.003,.425,.0015),boxEdge if i%3!=1 else tapeOlive,.0005))
# Fallen wood: two slightly parted native slats create a split, source origin and keys untouched.
o=bpy.data.objects['garbage-shelving__fallen_board']
for j in range(2):
 p=polyplank('detached broken shelf slat',(-.074 if j==0 else .074),.142,1.76,.085,.002,j==0,woodalt);carrierpart(o,p)
# Ground loose metal with unchanged original origins: elongated fitting bottoms meet floor.
for i in range(2):
 o=bpy.data.objects[f'garbage-shelving__loose_debris_{i}'];carrierpart(o,cube('discarded square bracket',(0,0,-.005),(.16,.105,.07),metal,.009,metalEdge));carrierpart(o,sphere('bracket stud',(0,-.012,.032),.028,metalEdge,(1,1,.42)))
# Bake piece geometry and normals into each unchanged semantic owner, in original local coordinates.
for o in carriers:
 verts=[];faces=[];mats=[];pindices=[]
 for part in parts[o.name]:
  bpy.context.view_layer.update();transform=o.matrix_world.inverted()@part.matrix_world
  offset=len(verts);verts.extend([transform@v.co for v in part.data.vertices]);mi=[]
  for m in part.data.materials:
   if m not in mats:mats.append(m)
   mi.append(mats.index(m))
  faces.extend([tuple(offset+i for i in p.vertices) for p in part.data.polygons]);pindices.extend([mi[p.material_index] for p in part.data.polygons])
  bpy.data.objects.remove(part,do_unlink=True)
 for mo in list(o.modifiers):o.modifiers.remove(mo)
 me=bpy.data.meshes.new(o.name+'__native_crafted_mesh');me.from_pydata(verts,[],faces);me.update()
 for m in mats:me.materials.append(m)
 for p,idx in zip(me.polygons,pindices):p.material_index=idx;p.use_smooth=True
 o.data=me
 # Native horizontal cut/extension repairs idle contact. This adjusts vertices, never root or keys.
 if 'old_upright' in o.name or 'fallen_board' in o.name or 'loose_debris' in o.name:
  bpy.context.view_layer.update();world=[o.matrix_world@v.co for v in me.vertices];minimum=min(v.z for v in world)
  # Lower tiny gaps by extending low vertices, not translating the carrier or its unchanged trajectory.
  # Board contact uses its naturally lower right end; a buried same-material foot wedge reaches exactly floor.
  if abs(minimum)>.00001:
   cut=minimum+.021 if 'old_upright' in o.name else minimum+.004
   for v,w in zip(me.vertices,world):
    if w.z<=cut:w.z-=minimum;v.co=o.matrix_world.inverted()@w
 # Parcel body and its native wrapping move together toward the accessible shelf edge.
 if 'stored_box_' in o.name:
  for v in me.vertices:v.co.y-=.175
 # Final static normals: native mesh remains editable and can be rebuilt by recipe.
 mo=o.modifiers.new('Crafted surface weighted normals','WEIGHTED_NORMAL');mo.keep_sharp=True;mo.weight=50
 o['refinementSemanticSource']=o.name;o['motionSource']='exact source native actions, original owner and slot';o['constructionPieces']=len(parts[o.name])
# Remove unreferenced imported material/data resources; untouched library stays external exact backup.
for mesh in list(bpy.data.meshes):
 if mesh.users==0:bpy.data.meshes.remove(mesh)
for ma in list(bpy.data.materials):
 if ma.users==0:bpy.data.materials.remove(ma)
# Fixed camera direct-native scale2; matrix and shift are the asset's own declared values.
cam=bpy.data.objects.new('garbage-shelving registered asset camera',bpy.data.cameras.new('garbage-shelving fixed orthographic'));scene.collection.objects.link(cam);cam.matrix_world=Matrix(CAM['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.ortho_scale=3.5;cam.data.shift_x=0;cam.data.shift_y=.20480744540691376;cam.data.sensor_fit='HORIZONTAL';cam.data.clip_start=.1;cam.data.clip_end=1000;scene.camera=cam
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=896;scene.render.resolution_y=1344;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=CAM['camera']['pixelAspect'][0];scene.render.pixel_aspect_y=1;scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=15;scene.render.fps=12;scene.render.dither_intensity=0
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.world=bpy.data.worlds.new('Neutral transparent studio world');scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.12
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.8,.8,.8,1)
# No floor receiver, no directional light bias. Equal cardinal areas and centered overhead.
for j,(pos,energy,size) in enumerate([((0,0,4.5),140,4.0)]+[((3*math.cos(a),3*math.sin(a),2.3),55,4.0) for a in (0,math.pi/2,math.pi,3*math.pi/2)]):
 d=bpy.data.lights.new('Balanced broad area '+str(j),'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=(1,1,1);ob=bpy.data.objects.new(d.name,d);scene.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(-Vector(pos)+Vector((0,0,.7))).to_track_quat('-Z','Y').to_euler()
if hasattr(scene,'eevee'):
 scene.eevee.taa_render_samples=48
apply('idle',1,'S')
# Current records are actual measurement, historical sourceScale4 is retained only as provenance.
def camera_record():
 dg=bpy.context.evaluated_depsgraph_get()
 def px(v):p=world_to_camera_view(scene,cam,Vector(v));return Vector((p.x*896,(1-p.y)*1344))
 base=px((0,0,0));return {'projection':'top-down-oblique-square-grid','frame':[448,672],'anchor':[224,448],'cellSize':128,'captureScale':2,'fps':12,'nativeFrame':[896,1344],'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':plain(cam.matrix_world),'projectionMatrix':plain(cam.calc_matrix_camera(dg,x=896,y=1344,scale_x=scene.render.pixel_aspect_x,scale_y=1)),'pixelAspect':[scene.render.pixel_aspect_x,1.0],'worldUnitsPerCell':1,'elevationDegrees':55.00797980144134},'calibration':{'root':list(base),'unitX':list(px((1,0,0))-base),'unitDepth':list(px((0,-1,0))-base),'unitHeight':list(px((0,0,1))-base)}}
dump(OUT/'camera.json',camera_record());assetRecord={k:CATALOG[k] for k in('id','footprint','height','projection')};assetRecord.update(frame=[448,672],anchor=[224,448],scale=2,directions=['N','E','S','W'],clips={k:{q:v[q] for q in ('frames','fps','loop','static') if q in v} for k,v in RIG['clips'].items()},sockets={},refinement='warm-soft native round03');dump(OUT/'asset-record.json',assetRecord);dump(OUT/'rig.json',RIG)
if not REPRO:bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'round-03.blend'),compress=True)
if '--build-only' in FLAGS:sys.exit(0)
# Exhaustive native key and quarter-frame geometry/trajectory ledger.
def measure(clip,frame,direction):
 apply(clip,frame,direction);dg=bpy.context.evaluated_depsgraph_get();allverts=[];rl=[];info=[]
 for o in carriers:
  eo=o.evaluated_get(dg);me=eo.to_mesh();vs=[eo.matrix_world@v.co for v in me.vertices];rv=[root.matrix_world.inverted()@v for v in vs];allverts+=vs;rl+=rv
  info.append({'name':o.name,'location':plain(o.location),'rotationEuler':plain(o.rotation_euler),'scale':plain(o.scale),'matrixWorld':plain(o.matrix_world),'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'vertexCount':len(vs),'boundsMin':[min(v[i] for v in vs) for i in range(3)],'boundsMax':[max(v[i] for v in vs) for i in range(3)],'rootLocalMin':[min(v[i] for v in rv) for i in range(3)],'rootLocalMax':[max(v[i] for v in rv) for i in range(3)]});eo.to_mesh_clear()
 ps=[world_to_camera_view(scene,cam,v) for v in allverts]
 return {'direction':direction,'clip':clip,'frame1':frame,'frame0':frame-1,'rootRotationZ':root.rotation_euler.z,'rootMatrix':plain(root.matrix_world),'rootLocation':plain(root.location),'rootScale':plain(root.scale),'boundsMin':[min(v[i] for v in allverts) for i in range(3)],'boundsMax':[max(v[i] for v in allverts) for i in range(3)],'rootLocalMin':[min(v[i] for v in rl) for i in range(3)],'rootLocalMax':[max(v[i] for v in rl) for i in range(3)],'projectedNativeBounds':[min(p.x*896 for p in ps),min((1-p.y)*1344 for p in ps),max(p.x*896 for p in ps),max((1-p.y)*1344 for p in ps)],'objects':info}
phases=[]
full='--full' in FLAGS
for direction in ['S','E','N','W']:
 for clip,v in RIG['clips'].items():
  frames=range(1,v['frames']+1) if full else [1]
  for frame in frames:
   p=measure(clip,frame,direction);phases.append(p)
   folder=OUT/'frames'/f'{clip}-{direction}';folder.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(folder/f'{frame-1:03d}.png');bpy.ops.render.render(write_still=True);print('GS_NATIVE_RENDER',direction,clip,frame,flush=True)
  if clip=='highlighted' and full:
   p=measure(clip,13,direction);phases.append(p);folder=OUT/'closure';folder.mkdir(exist_ok=True);scene.render.filepath=str(folder/f'highlighted-{direction}-013.png');bpy.ops.render.render(write_still=True)
 dump(OUT/'candidate-phases.json',phases)
if full:
 inbetweens=[]
 for direction in ['S','E','N','W']:
  for clip in ['highlighted','clearance']:
   for i in range(1,13 if clip=='highlighted' else 12):
    for f in (.25,.5,.75):inbetweens.append(measure(clip,i+f,direction))
 dump(OUT/'candidate-inbetweens.json',inbetweens)
# Structural raw native audit and resource closure. No unreported material action or invisible projection card.
def minfo(m):
 return {'name':m.name,'diffuseColor':plain(m.diffuse_color),'surfaceRenderMethod':getattr(m,'surface_render_method',None),'animation':m.node_tree.animation_data is not None,'nodes':[{'name':n.name,'type':n.type,'image':n.image.filepath if hasattr(n,'image') and n.image else None,'inputs':{s.name:plain(s.default_value) for s in n.inputs if hasattr(s,'default_value') and not s.is_linked}} for n in m.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links]}
report={'asset':'garbage-shelving','blenderVersion':bpy.app.version_string,'sourceBlendSHA256':sha(RES/'original-library.blend'),'camera':camera_record(),'rootObject':root.name,'objects':[{'name':o.name,'parent':o.parent.name if o.parent else None,'type':o.type,'meshVertices':len(o.data.vertices),'meshFaces':len(o.data.polygons),'materials':[m.name for m in o.data.materials],'modifiers':[{'type':m.type,'name':m.name} for m in o.modifiers],'constraints':[c.type for c in o.constraints],'shapeKeys':bool(o.data.shape_keys),'properties':plain(dict(o.items()))} for o in carriers],'materials':[minfo(m) for m in bpy.data.materials if m.users],'actions':ACTIONS_SOURCE,'actionsAfter': [action_record(a) for a in bpy.data.actions],'externalImages':[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if im.source=='FILE'],'libraries':[l.filepath for l in bpy.data.libraries],'lights':[{'name':o.name,'position':plain(o.location),'rotation':plain(o.rotation_euler),'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'color':plain(o.data.color)} for o in scene.objects if o.type=='LIGHT'],'sceneMeshOwners':[o.name for o in scene.objects if o.type=='MESH'],'render':{'engine':scene.render.engine,'frame':[896,1344],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'filmTransparent':scene.render.film_transparent,'fps':12,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma},'rootCarrierMapping':'source/frozen-contract-acknowledgment.json','nativeCaptures':phases,'allSourceActionsCopiedWithoutRegeneration':True,'roleSpecificOpaqueMeshRebuild':True,'noGroundReceiver':True,'recipeSourcePath':str(Path(__file__).resolve())}
dump(OUT/'native-audit.json',report)
print('GS_NATIVE_DONE',OUT,flush=True)
