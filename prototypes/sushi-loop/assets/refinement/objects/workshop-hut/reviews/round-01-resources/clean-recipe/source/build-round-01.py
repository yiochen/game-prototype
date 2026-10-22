"""Workshop hut warm-soft native reconstruction. Background Blender 5.2.2.
No paired geometry imported while writing the immutable standalone project.
Reproduce: blender -b -t 6 --python source/build-round-01.py
"""
import bpy,math,json,hashlib,shutil
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent;B=HERE.parent;OUT=B/'candidates/round-01';RES=HERE/'resources'
for p in [OUT,RES,OUT/'native-records',OUT/'frames',OUT/'atlases']:p.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for n in ['source-camera.json','source-assetRecord.json','source-rig.json']:
 if not (RES/n).exists():shutil.copyfile(B/'inputs'/n,RES/n)
if not (RES/'frozen-brief.json').exists():shutil.copyfile(B/'brief.json',RES/'frozen-brief.json')
if not (RES/'paired-floor-round-04.blend').exists():shutil.copyfile(B/'inputs/paired-native/dock-floor-round-04.blend',RES/'paired-floor-round-04.blend')
assert sha(RES/'paired-floor-round-04.blend')=='94b509984dc442547602f32feada987c5119e3b9031eb1bd65a6a07769880418'
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.name='WorkshopHut_Standalone_WarmSoft'
col=bpy.data.collections.new('WarmSoft_workshop-hut');sc.collection.children.link(col)
root=bpy.data.objects.new('workshop-hut__root',None);col.objects.link(root);root['asset']='workshop-hut';root['footprint']=[1,1];root['height']=1.81
socket=bpy.data.objects.new('workshop-hut__door_socket',None);col.objects.link(socket);socket.parent=root;socket.location=(-.12,-.56,0);socket['semanticRole']='closed exterior interaction marker'
def mat(name,color,rough=.55,metal=0,grain=False,emission=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Specular IOR Level'].default_value=.32
 if grain:
  coord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(12,12,1.2);l.new(coord.outputs['Generated'],mapping.inputs[0]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=4;noise.inputs['Detail'].default_value=2;noise.inputs['Roughness'].default_value=.6;l.new(mapping.outputs[0],noise.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.22;r.color_ramp.elements[0].color=(*[v*.80 for v in color],1);r.color_ramp.elements[1].position=.78;r.color_ramp.elements[1].color=(*[min(v*1.10,1) for v in color],1);l.new(noise.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color'])
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 return m
wood=mat('Warm amber timber',(.62,.255,.058),.62,grain=True)
wood2=mat('Honey alternate timber',(.72,.325,.078),.61,grain=True)
wood3=mat('Golden panel timber',(.66,.283,.064),.61,grain=True)
trim=mat('Rounded walnut framing',(.32,.105,.025),.54,grain=True)
trimLight=mat('Amber trim edge',(.43,.16,.039),.55,grain=True)
doorMat=mat('Honey gold door boards',(.82,.43,.11),.53,grain=True)
blue=mat('Soft cornflower roof',(.045,.34,.72),.36)
aqua=mat('Soft turquoise roof',(.025,.59,.67),.38)
under=mat('Turquoise roof understructure',(.025,.33,.41),.55)
navy=mat('Deep blue roof framing',(.032,.105,.31),.39)
chimney=mat('Blue charcoal chimney',(.065,.12,.22),.46)
gold=mat('Warm brass hardware',(.63,.34,.075),.32,.65)
iron=mat('Forged hinge iron',(.16,.13,.10),.44,.5)
glass=mat('Warm golden window glass',(.98,.66,.15),.34,emission=.14)

def adopt(o,name,material):
 o.name='workshop-hut__'+name
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=root
 if material:o.data.materials.append(material)
 return o

def finish(o,bev=.015):
 if bev:
  b=o.modifiers.new('Broad rounded crafted edges','BEVEL');b.width=bev;b.segments=5;b.affect='EDGES';b.profile=.5
  bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
 for p in o.data.polygons:p.use_smooth=True
 n=o.modifiers.new('Weighted broad face normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=50
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=n.name)
 return o

def cube(name,loc,dims,material,bev=.015,rot=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if rot:o.rotation_euler=rot
 adopt(o,name,material);finish(o,bev);return o

def sphere(name,loc,scale,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=loc);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);adopt(o,name,material)
 for p in o.data.polygons:p.use_smooth=True
 return o

def beam(name,a,b,width,depth,material,bev=.01):
 a,b=Vector(a),Vector(b);o=cube(name,(a+b)/2,(width,depth,(b-a).length),material,bev);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

# Connected low body/sill. Flat broad support face is local -.01 at root .23.
base=cube('connected_foundation_sill',(0,0,.025),(.87,.90,.07),trim,.006)
base['supportContact']='Broad flat native underside localZ=-.01, finite areas on actual floor plateaux; bevel edges intentionally lifted.'
body=cube('solid_timber_body',(0,0,.665),(.79,.82,1.21),wood,.018)
# Native wall boards. Coherent all sides; front's closed openings sit over continuous body.
for side in [-1,1]:
 for i in range(5):
  y=-.32+i*.16
  cube(f'side_{side}_vertical_board_{i}',(side*.408,y,.665),(.035,.154,1.18),[wood,wood2,wood3,wood,wood2][i],.009)
for end in [-1,1]:
 for i in range(5):
  x=-.312+i*.156
  cube(f'end_{end}_vertical_board_{i}',(x,end*.421,.665),(.150,.030,1.18),[wood2,wood,wood3,wood2,wood][i],.008)
# Four real corner posts and foot capitals stay inside low repair box.
for x in [-.389,.389]:
 for y in [-.394,.394]:
  cube('corner_post',(x,y,.66),(.090,.105,1.24),trim,.018)
  cube('corner_foot',(x,y,.051),(.097,.112,.092),trimLight,.012)
  cube('corner_collar',(x,y,1.205),(.105,.117,.09),trimLight,.015)
# Side/rear sill bands make construction read intentionally from every facing.
for x in [-.410,.410]:cube('side_sill',(x,0,.104),(.048,.81,.072),trimLight,.010)
cube('rear_sill',(0,.427,.104),(.78,.047,.072),trimLight,.010)
# Door grows in useful proportion, retains fixed marker and closed exterior role.
# All hardware stops in front of or at localY=-.56, leaving outside corridor clear.
for x in [-.315,.075]:cube('door_frame_upright',(x,-.482,.564),(.070,.105,1.048),trim,.014)
cube('door_lintel',(-.12,-.490,1.099),(.470,.117,.110),trimLight,.018)
for x in [-.213,-.027]:cube('door_leaf_board',(x,-.500,.542),(.181,.060,1.012),doorMat,.012)
# Threshold top is exactly semantic world marker level; front edge at -.56.
threshold=cube('low_connected_threshold',(-.12,-.500,-.005),(.370,.120,.010),trimLight,.002)
threshold['role']='Low native threshold bottom local-.01/top0; fixed semantic marker local0.'
# Brass lintel pegs, iron hinge plates and softly rounded ring handle.
for x in [-.295,.055]:sphere('lintel_brass_peg',(x,-.551,1.101),(.020,.006,.020),gold)
for z in [.255,.825]:
 cube('door_hinge_strap',(-.246,-.536,z),(.110,.016,.042),iron,.008)
 cube('door_hinge_barrel',(-.292,-.543,z),(.022,.026,.075),iron,.009)
 sphere('hinge_pin',(-.230,-.547,z),(.009,.004,.009),gold)
sphere('handle_backplate',(.006,-.535,.514),(.032,.007,.042),gold)
sphere('handle_knob',(.006,-.548,.541),(.024,.010,.024),gold)
bpy.ops.mesh.primitive_torus_add(major_segments=28,minor_segments=10,location=(.006,-.546,.493),major_radius=.033,minor_radius=.007,rotation=(math.pi/2,0,0));adopt(bpy.context.object,'brass_ring_handle',gold)
for p in bpy.context.object.data.polygons:p.use_smooth=True
# Layered front window fits beside widened door. Four warm glass panes stay distinct.
cube('front_window_recess',(.259,-.453,.815),(.230,.066,.350),trim,.019)
for x in [.215,.303]:
 for z in [.749,.881]:cube('front_window_pane',(x,-.494,z),(.077,.018,.116),glass,.006)
for x in [.160,.358]:cube('front_window_side_frame',(x,-.498,.815),(.035,.063,.348),trimLight,.010)
for z in [.641,.989]:cube('front_window_header_sill',(.259,-.502,z),(.251,.075,.048),trimLight,.013)
cube('front_window_mullion',(.259,-.510,.815),(.020,.022,.286),trim,.004)
cube('front_window_crossbar',(.259,-.511,.815),(.179,.022,.025),trim,.004)
# A small side window and a rear framed repair hatch create coherent unseen views.
for side in [-1,1]:
 x=side*.437
 cube('side_window_recess',(x,.08,.827),(.036,.292,.315),trim,.015)
 for y in [.018,.142]:
  for z in [.766,.888]:cube('side_window_pane',(x+side*.021,y,z),(.016,.110,.110),glass,.006)
 cube('side_window_mullion',(x+side*.033,.08,.827),(.020,.021,.255),trim,.004)
 cube('side_window_crossbar',(x+side*.034,.08,.827),(.020,.255,.022),trim,.004)
 for z in [.670,.984]:cube('side_window_trim',(x+side*.015,.08,z),(.061,.320,.045),trimLight,.010)
# Back is articulated timber: framed inset hatch and cross bracing, distinct from entry facade.
cube('rear_workshop_hatch',(0,.448,.64),(.43,.04,.54),trimLight,.014)
for i in range(3):cube('rear_hatch_board',(-.131+i*.131,.473,.64),(.124,.020,.46),wood3,.007)
for z in [.389,.891]:cube('rear_hatch_rail',(0,.493,z),(.455,.035,.052),trim,.010)
beam('rear_hatch_diagonal',(-.17,.498,.425),(.17,.498,.855),.044,.033,trim,.007)
# Solid pitched roof understructure. Broad continuous volume under separate softened roof boards.
verts=[(-.54,-.57,1.255),(.54,-.57,1.255),(-.54,.57,1.255),(.54,.57,1.255),(-.54,0,1.586),(.54,0,1.586)]
faces=[(0,1,5,4),(4,5,3,2),(0,2,3,1),(0,4,2),(1,3,5)]
me=bpy.data.meshes.new('Pitched continuous roof');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Roof',me);col.objects.link(o);o.parent=root;o.name='workshop-hut__continuous_pitched_roof';o.data.materials.append(under);finish(o,.018)
# Five substantial slats per slope; slight longitudinal convex form, no per-view changes.
# Shape bottom/top via loft so rounded edges belong to the mesh.
for side in [-1,1]:
 for i,x in enumerate([-.424,-.212,0,.212,.424]):
  w=.201;ys=[0,.13,.30,.47,.588];zs=[1.615,1.558,1.463,1.365,1.305];v=[]
  for y,z in zip(ys,zs):
   v += [(x-w/2,side*y,z-.062),(x+w/2,side*y,z-.062),(x-w/2,side*y,z),(x+w/2,side*y,z)]
  f=[(0,2,3,1)]
  for j in range(len(ys)-1):
   a=j*4;b=(j+1)*4
   f.extend([(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)])
  a=(len(ys)-1)*4;f.append((a,a+1,a+3,a+2))
  me=bpy.data.meshes.new('Soft thick shaped roof board');me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new('board',me);col.objects.link(ob);ob.parent=root;ob.name=f'workshop-hut__roof_board_{side}_{i}';ob.data.materials.append(blue if i%2==0 else aqua)
  # Normals are made consistent before bevel.
  bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');ob.select_set(False);finish(ob,.023)
# Deep blue ridge and end caps, with brass fasteners, comfortably within frozen envelope.
cube('rounded_ridge',(0,0,1.638),(1.140,.165,.143),navy,.027)
for x in [-.548,.548]:
 cube('ridge_end_cap',(x,0,1.638),(.055,.185,.165),navy,.020)
 # Fasteners point to each slope and stay well inside roof envelope.
 for side in [-1,1]:sphere('ridge_brass_fastener',(x,side*.084,1.666),(.020,.007,.020),gold)
# Chimney rises through rear roof, with connected boot and cap. No smoke alpha/card.
cube('chimney_boot',(.25,.190,1.526),(.235,.236,.125),navy,.020)
cube('chimney_shaft',(.25,.190,1.644),(.145,.146,.260),chimney,.016)
cube('chimney_cap',(.25,.190,1.765),(.215,.214,.080),navy,.020)
# Exact calibrated camera is measured from projection; source unrelated active camera never used.
cd=bpy.data.cameras.new('Registered_camera');cam=bpy.data.objects.new('Registered_camera',cd);sc.collection.objects.link(cam);sc.camera=cam
metadata=json.load(open(RES/'source-camera.json'));cam.matrix_world=Matrix(metadata['camera']['worldMatrix']);cd.type='ORTHO';cd.sensor_fit='HORIZONTAL';cd.ortho_scale=1.5
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=384;sc.render.resolution_y=896;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1;sc.render.filter_size=.5;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.fps=12;sc.render.threads_mode='FIXED';sc.render.threads=6;sc.frame_start=1;sc.frame_end=1
sc.world=bpy.data.worlds.new('Neutral soft fill');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.83,.87,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.45
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=-1.8;sc.view_settings.gamma=1
# Same invariant fourfold soft rig for every facing, no directional ground shadow catcher.
def light(name,loc,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.5))-o.location).to_track_quat('-Z','Y').to_euler()
light('Soft centered overhead',(0,0,4.5),360,4)
for loc in [(3,0,2.5),(-3,0,2.5),(0,3,2.5),(0,-3,2.5)]:light('Equal cardinal broad fill',loc,180,4)
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*384,(1-p.y)*896))
cd.shift_x=0;cd.shift_y=0;bpy.context.view_layer.update();base=px((0,0,0));cd.shift_y=1;bpy.context.view_layer.update();delta=px((0,0,0)).y-base.y;cd.shift_y=(704-base.y)/delta;bpy.context.view_layer.update()
root.rotation_euler=(0,0,0);root.location=(0,0,0);root.scale=(1,1,1);sc.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'round-01.blend'),compress=True)
print('IMMUTABLE_STANDALONE_READY',str(HERE/'round-01.blend'),sha(HERE/'round-01.blend'),flush=True)
(OUT/'source-ready.json').write_text(json.dumps({'asset':'workshop-hut','project':'source/round-01.blend','sha256':sha(HERE/'round-01.blend'),'recipe':'source/build-round-01.py','standaloneSavedBeforePairing':True,'pairedFloorSHA256':sha(RES/'paired-floor-round-04.blend'),'frozenBriefSHA256':sha(B/'brief.json'),'approval':'pending independent review'},indent=2))
