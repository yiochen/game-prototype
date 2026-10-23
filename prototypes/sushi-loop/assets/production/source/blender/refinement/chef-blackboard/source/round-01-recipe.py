"""Rebuild editable chef-blackboard from untouched native collection/actions.
Build: blender -b --python source/round-01-recipe.py
Capture: blender -b source/round-01.blend --python source/capture-round-01.py
"""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector, Matrix
P=Path(__file__).resolve().parent;O=P.parent
SOURCE=P/'original-library.blend'
EXPECTED='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.name='Chef Blackboard Native Round01'
with bpy.data.libraries.load(str(SOURCE),link=False) as (a,b):
 b.collections=['S33_PROP_chef-blackboard']
 b.actions=[n for n in a.actions if n.startswith('S33_NATIVE__chef-blackboard__')]
c=b.collections[0];s.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
for x in c.all_objects:x.hide_render=False;x.hide_viewport=False;x.hide_set(False)
root=bpy.data.objects['chef-blackboard__root'];root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1)
rig=json.loads((P/'resources/original-rig.json').read_text());camera_ref=json.loads((P/'resources/registered-camera.json').read_text())
(P/'resources').mkdir(exist_ok=True)
for name,data in [('original-rig.json',rig),('registered-camera.json',camera_ref)]:
 (P/'resources'/name).write_text(json.dumps(data,indent=2)+'\n')

def mat(name,lo,hi,grain_axis='H',rough=.42,metal=0):
 m=bpy.data.materials.new('CB01_'+name);m.use_nodes=True
 n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
 out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs['BSDF'],out.inputs['Surface'])
 bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 bs.inputs['Specular IOR Level'].default_value=.24 if not metal else .38
 bs.inputs['Coat Weight'].default_value=.08 if name!='slate' else .0;bs.inputs['Coat Roughness'].default_value=.4
 tc=n.new('ShaderNodeTexCoord');mp=n.new('ShaderNodeVectorMath');mp.operation='MULTIPLY'
 mp.inputs[1].default_value={'H':(.55,2,4),'V':(4,2,.55),'S':(8,8,8)}[grain_axis]
 l.new(tc.outputs['Generated'],mp.inputs[0]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.5;noise.inputs['Detail'].default_value=2;noise.inputs['Roughness'].default_value=.55;l.new(mp.outputs[0],noise.inputs['Vector'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[0].color=(*lo,1);ramp.color_ramp.elements[1].position=.85;ramp.color_ramp.elements[1].color=(*hi,1);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
 m.diffuse_color=(*[(a+b)/2 for a,b in zip(lo,hi)],1)
 return m
woodH=mat('honey_longgrain',(.45,.18,.025),(.60,.275,.050))
woodV=mat('honey_uprightgrain',(.45,.18,.025),(.60,.275,.050),'V')
woodD=mat('warm_endgrain',(.25,.080,.015),(.36,.14,.030),'V',.5)
slate=mat('slate',(.012,.034,.050),(.016,.042,.060),'S',.86)
brass=mat('brass_pegs',(.58,.33,.070),(.78,.52,.15),'S',.31,.50)

def replace_box(obj,dims,bevel,material,offset=(0,0,0)):
 # Build mesh in the original animated owner's local coordinates.
 v=[(x*dims[0]/2+offset[0],y*dims[1]/2+offset[1],z*dims[2]/2+offset[2]) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
 f=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
 me=bpy.data.meshes.new(obj.name+'_rounded');me.from_pydata(v,[],f);me.materials.append(material);me.update();obj.data=me
 for mod in list(obj.modifiers):obj.modifiers.remove(mod)
 for q in me.polygons:q.use_smooth=True
 b=obj.modifiers.new('Soft carved edge radii','BEVEL');b.width=bevel;b.segments=5;b.affect='EDGES';b.harden_normals=True
 wn=obj.modifiers.new('Stable flat centers','WEIGHTED_NORMAL');wn.keep_sharp=True;wn.weight=50
 obj['refinement_modeling']='Native rebuilt rounded wood/slate box; original action owner and origin retained'
 return obj
for o in list(c.objects):
 if o.type!='MESH':continue
 n=o.name
 if '__front_post_' in n:replace_box(o,(.085,.11,.98),.021,woodV)
 elif '__short_foot_' in n:replace_box(o,(.13,.21,.07),.019,woodD)
 elif '__blank_dynamic_face' in n:replace_box(o,(.62,.055,.57),.015,slate)
 elif '__frame_side_' in n:
  sign=-1 if o.location.x<0 else 1
  replace_box(o,(.085,.105,.67),.020,woodV,(sign*.0025,0,0))
 elif '__frame_end_' in n:replace_box(o,(.80,.125,.088),.022,woodH,(0,-.015,0))
 elif '__chalk_ledge' in n:replace_box(o,(.75,.065,.036),.013,woodH,(0,-.0175,.004))

def box_child(name,parent,loc,dims,bevel,material):
 me=bpy.data.meshes.new(name);o=bpy.data.objects.new(name,me);c.objects.link(o);o.parent=parent;o.location=Vector(loc)-parent.location
 return replace_box(o,dims,bevel,material)
for sign in [-1,1]:
 post=bpy.data.objects[f'chef-blackboard__front_post_{sign*.33}']
 box_child('CB01_rounded_cap_'+str(sign),post,(sign*.33,-.355,.938),(.108,.112,.104),.025,woodV)
for z in [.275,.945]:
 rail=bpy.data.objects['chef-blackboard__frame_end_'+str(z)]
 for x in [-.342,.342]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=(0,0,0));o=bpy.context.object;o.name=f'CB01_brass_join_{x}_{z}'
  for co in list(o.users_collection):co.objects.unlink(o)
  c.objects.link(o);o.parent=rail;o.location=Vector((x,-.490,z))-rail.location;o.scale=(.019,.008,.019);o.data.materials.append(brass)
  for f in o.data.polygons:f.use_smooth=True
  o['purpose']='Wood joint peg, outside the blank writing panel'
# Actual native attachment transforms at the unchanged local recipe/display point.
for label in ['recipe_face','display_face']:
 o=bpy.data.objects.new('CB01_socket_'+label,None);c.objects.link(o);o.parent=root;o.location=(0,-.434,.61);o.empty_display_type='ARROWS';o.empty_display_size=.025;o['functional_attachment']=label
root['refinement_round']='chef-blackboard-round01';root['blank_face_clearance']='Actual front plane y=-.4275, socket y=-.434, outward clearance .0065; no baked display content'
# Registered camera matrix is restored directly from asset metadata.
cam=bpy.data.objects.new('Registered S Camera',bpy.data.cameras.new('Registered S Camera'));s.collection.objects.link(cam);s.camera=cam
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_x=0;cam.data.shift_y=.20454464852809906
cam.data.clip_start=.1;cam.data.clip_end=1000;cam.matrix_world=Matrix(camera_ref['camera']['worldMatrix'])
s.render.engine='CYCLES';s.cycles.samples=40;s.cycles.use_denoising=True;s.cycles.seed=17
s.render.resolution_x=768;s.render.resolution_y=1408;s.render.resolution_percentage=100
s.render.pixel_aspect_x=camera_ref['camera']['pixelAspect'][0];s.render.pixel_aspect_y=1
# Derive lens shift from the fixed projection matrix, never silhouette bounds.
cam.data.shift_y=0;bpy.context.view_layer.update()
def projection():return cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)
baseline=projection()[1][3];cam.data.shift_y=1;bpy.context.view_layer.update();slope=projection()[1][3]-baseline
cam.data.shift_y=(camera_ref['camera']['projectionMatrix'][1][3]-baseline)/slope;bpy.context.view_layer.update()
assert max(abs(projection()[i][j]-camera_ref['camera']['projectionMatrix'][i][j]) for i in range(4) for j in range(4))<1e-6
s.render.fps=12;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='8';s.render.image_settings.compression=50;s.render.dither_intensity=0
s.render.threads_mode='FIXED';s.render.threads=6
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
s.use_nodes=False
world=bpy.data.worlds.new('Neutral soft surrounding light');s.world=world;world.use_nodes=True
world.node_tree.nodes.get('Background').inputs['Color'].default_value=(1,1,1,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.24

def area(name,loc,power,size):
 o=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));s.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.shape='DISK';o.data.size=size
area('Soft centered overhead',(0,0,4),100,4)
for i,(x,y) in enumerate([(3,0),(-3,0),(0,3),(0,-3)]):area('Equal cardinal fill '+str(i),(x,y,2.8),70,4)
# Only original native actions are used for the animated ten original owners.
for a in rig['clips']['idle']['actions']:
 o=bpy.data.objects[a['ownerName']];act=bpy.data.actions[a['action']];o.animation_data_create();o.animation_data.action=act;o.animation_data.action_slot=next(q for q in act.slots if q.identifier==a['slotIdentifier'])
for a in bpy.data.actions:a.use_fake_user=True
s.frame_set(1);bpy.context.view_layer.update()
# Snapshot original action curves for byte-independent comparison in validation.
def curves(action):
 for la in action.layers:
  for st in la.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:yield fc
acts={a.name:[{'path':f.data_path,'index':f.array_index,'keys':[[float(x.co.x),float(x.co.y),x.interpolation] for x in f.keyframe_points]} for f in curves(a)] for a in bpy.data.actions}
(P/'resources/original-actions.json').write_text(json.dumps(acts,separators=(',',':')))
for t in list(bpy.data.texts):bpy.data.texts.remove(t)
for name in ['round-01-recipe.py','capture-round-01.py']:
 if (P/name).exists():bpy.data.texts.new(name).write((P/name).read_text())
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'round-01.blend'),compress=True)
recipe={'asset':'chef-blackboard','round':1,'sourceSHA256':EXPECTED,'project':'source/round-01.blend','buildScript':'source/round-01-recipe.py','captureScript':'source/capture-round-01.py','modeling':['Rebuilt original owner meshes with broad multi-segment edge radii and stable normals','Rounded cap blocks and four native brass join pegs, parented to original animated structural owners','Restrained procedural local-space longitudinal grain; quiet unmarked blue slate'],'locked':{'root':[0,0,0],'footprint':[1,1],'height':1.0,'bandY':[-.5,-.27],'socket':[0,-.434,.61],'blankFaceFrontY':-.4275,'blankFaceDimensions':[.62,.57],'originalActionCount':30},'render':{'engine':'CYCLES','samples':40,'seed':17,'denoise':True,'frame':[768,1408],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'viewTransform':'Standard','lighting':'Centered overhead plus four identical cardinal area lights; neutral world .24; no ground plane'},'replay':'Open closed round-01.blend and run capture-round-01.py. Capture script uses bound resources only; no rebuild or source library is required.'}
(P/'round-01-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
print('BUILT',P/'round-01.blend')
