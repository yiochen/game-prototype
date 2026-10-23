"""Portal-entry round-01 native build. Run against the authorized RAW .blend.
No runtime/application helper is imported; all geometry and native actions are here.
"""
import bpy, math, json, hashlib, sys
from pathlib import Path
from mathutils import Matrix, Vector
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
OBJ=HERE.parent
RAW=OBJ.parents[2]/'production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'
EXPECTED='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
assert hashlib.sha256(RAW.read_bytes()).hexdigest()==EXPECTED
assert Path(bpy.data.filepath).resolve()==RAW.resolve()
assert (HERE/'construction-acknowledgment-v1.json').exists()
OUT=HERE/'round-01.blend'
assert not OUT.exists()
sc=bpy.data.scenes['S33 Native Asset Library Export']
bpy.context.window.scene=sc
root=bpy.data.objects['portal_rim__root.003']
col=bpy.data.collections['S33_PROP_portal_rim.003']
# An isolated editable asset source: preserve the real owner/root, remove unrelated assets.
for s in list(bpy.data.scenes):
    if s!=sc:bpy.data.scenes.remove(s)
for o in list(bpy.data.objects):
    if o!=root:bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):
    if c!=col:bpy.data.collections.remove(c)
if col.name not in sc.collection.children:sc.collection.children.link(col)
col.hide_render=False;col.hide_viewport=False
root.hide_render=False;root.hide_viewport=False;root.hide_set(False)
root.animation_data_clear();root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1)
root['artStyle']='warm-soft-native-portal-entry-round-01'
root['ground_root']='[0,0,0]';root['sockets']='{"entry":[0,0,0.74]}'
root['visual_height']=1.48
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
for me in list(bpy.data.meshes):
    if me.users==0:bpy.data.meshes.remove(me)

def lin(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def material(name,rgb,rough=.4,metal=0,coat=.12,emission=.06):
    m=bpy.data.materials.new(name);m.use_nodes=True
    m.diffuse_color=(*[lin(c) for c in rgb],1)
    nt=m.node_tree;nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial');p=nt.nodes.new('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value=m.diffuse_color
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    p.inputs['Specular IOR Level'].default_value=.3;p.inputs['Coat Weight'].default_value=coat
    p.inputs['Coat Roughness'].default_value=.3
    p.inputs['Emission Color'].default_value=m.diffuse_color;p.inputs['Emission Strength'].default_value=emission
    nt.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    return m
cyan=material('Portal | soft cyan enamel',(.17,.80,.86),.37,0,.18,.055)
aqua=material('Portal | turning aqua',(.10,.65,.75),.4,0,.12,.06)
navy=material('Portal | navy blue stone',(.14,.29,.46),.57,0,.02,.16)
navylight=material('Portal | cut blue stone',(.18,.35,.52),.54,0,.02,.14)
gold=material('Portal | warm brass fittings',(.88,.62,.25),.35,.3,.18,.055)
blue=material('Portal | cobalt inset',(.08,.41,.76),.28,.06,.24,.08)
gem=material('Portal | cyan gem face',(.22,.82,.89),.27,.02,.22,.07)

def mesh_obj(name,verts,faces,mats,parent=root,smooth=False):
    me=bpy.data.meshes.new(name+' mesh');me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);col.objects.link(ob);ob.parent=parent
    for m in mats:me.materials.append(m)
    for p in me.polygons:p.use_smooth=smooth
    return ob
def weighted(ob):
    m=ob.modifiers.new('Weighted face normals','WEIGHTED_NORMAL');m.keep_sharp=True;m.weight=50
def bevel(ob,width,segments=3):
    m=ob.modifiers.new('Soft physical edge bevel','BEVEL');m.width=width;m.segments=segments
    m.limit_method='ANGLE';m.angle_limit=.35
    return m
def box(name,loc,dims,mat,bev=.01,parent=root):
    x,y,z=[v*.5 for v in dims]
    vs=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]
    fs=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    o=mesh_obj(name,vs,fs,[mat],parent)
    o.location=loc
    if bev:bevel(o,bev,3);weighted(o)
    return o
def rim(name,radius,radial,depth,mats,start=0,end=2*math.pi,segments=96,parent=root):
    # A continuous open annulus with a rounded-square physical cross section.
    profile=[]
    for j in range(20):
        a=2*math.pi*j/20
        profile.append((radial*math.copysign(abs(math.cos(a))**.62,math.cos(a)),depth*math.copysign(abs(math.sin(a))**.62,math.sin(a))))
    closed=abs(end-start-2*math.pi)<1e-5;n=segments if closed else segments+1
    vs=[];fs=[]
    for i in range(n):
        a=start+(end-start)*i/segments
        for dr,y in profile:vs.append(((radius+dr)*math.cos(a),y,(radius+dr)*math.sin(a)))
    for i in range(segments):
        ni=(i+1)%n
        for j in range(20):fs.append((i*20+j,i*20+(j+1)%20,ni*20+(j+1)%20,ni*20+j))
    if not closed:
        fs.extend([tuple(reversed(range(20))),tuple((n-1)*20+j for j in range(20))])
    ob=mesh_obj(name,vs,fs,mats,parent,True);ob.location=(0,0,.74)
    if len(mats)>1:
        for p in ob.data.polygons:
            j=p.index%20
            # Inner turning strip is subtly deeper aqua, shared on both sides.
            p.material_index=1 if 7<=j<=12 else 0
    return ob

rimob=rim('portal_entry | continuous cyan rim',.585,.104,.099,[cyan,aqua])
rimob['native_role']='continuous genuinely open structural rim'
# A narrow aqua inset follows the inner turning edge; geometry remains an open annulus.
inner=rim('portal_entry | inner enamel reveal',.489,.009,.101,[aqua])

support_names=[]
for side in (-1,1):
    cx=side*.435
    # Octagonal stone with deliberate shoulders and broad retained planar facets.
    levels=[(-.045,.178,.166),(.006,.244,.218),(.235,.232,.219),(.345,.166,.168)]
    vs=[]
    for z,rx,ry in levels:
        for k in range(8):
            a=2*math.pi*(k+.5)/8;vs.append((cx+rx*math.cos(a),ry*math.sin(a),z))
    fs=[tuple(reversed(range(8)))]
    for lev in range(len(levels)-1):
        for k in range(8):fs.append((lev*8+k,lev*8+(k+1)%8,(lev+1)*8+(k+1)%8,(lev+1)*8+k))
    fs.append(tuple(24+k for k in range(8)))
    stone=mesh_obj(f'portal_entry | fixed navy support {side:+d}',vs,fs,[navy,navylight])
    for p in stone.data.polygons:
        if p.index==len(fs)-1 or (p.index>8 and p.index%4==0):p.material_index=1
    bevel(stone,.018,3);weighted(stone);stone['native_role']='fixed finite support crossing Z0'
    support_names.append(stone.name)
    # Rim seats are short fitted annular bands around the ring inserted into each stone.
    mid=math.radians(-48 if side==1 else 228)
    seat=rim(f'portal_entry | fitted brass seat {side:+d}',.585,.116,.111,[gold],mid-math.radians(7),mid+math.radians(7),12)
    seat['native_role']='fixed structural rim to stone fitting'
    for front in (-1,1):
        frame=box(f'portal_entry | foot jewel frame {side:+d} {front:+d}',(cx,front*.204,.158),(.108,.023,.13),gold,.012)
        frame.rotation_euler.y=math.pi/4
        jewel=box(f'portal_entry | foot cyan inset {side:+d} {front:+d}',(cx,front*.218,.158),(.065,.019,.085),gem,.01)
        jewel.rotation_euler.y=math.pi/4

motor=bpy.data.objects.new('portal_entry | native activation orbit',None);col.objects.link(motor);motor.parent=root;motor.location=(0,0,.74)
motor['native_role']='native transform animation owner for physically mounted orbiting panels'
for k in range(6):
    a=2*math.pi*k/6+math.radians(15)
    for front in (-1,1):
        # A tangible blue inset with small brass edge surround on both physical sides.
        loc=(.585*math.cos(a),front*.114,.585*math.sin(a))
        frame=box(f'portal_entry | orbit brass frame {k:02d} {front:+d}',loc,(.104,.034,.172),gold,.014,motor)
        frame.rotation_euler.y=-a
        loc2=(loc[0],front*.137,loc[2])
        inset=box(f'portal_entry | orbit cobalt face {k:02d} {front:+d}',loc2,(.073,.032,.132),blue,.015,motor)
        inset.rotation_euler.y=-a

animated=[rimob,inner,motor]
for i in range(12):
    t=i/11;ease=(1-math.cos(math.pi*t))/2;pulse=math.sin(math.pi*t)**2
    for ob in (rimob,inner):
        ob.scale=(1+.018*pulse,1+.018*pulse,1+.018*pulse);ob.keyframe_insert('scale',frame=i+1,group='Soft native activation pulse')
    motor.rotation_euler.y=-math.radians(30)*ease
    motor.keyframe_insert('rotation_euler',frame=i+1,group='Ordered native orbit')
for ob in animated:
    act=ob.animation_data.action;act.name='PORTAL_ENTRY_ROUND01_ENTER__'+ob.name;act.use_fake_user=True
    act['clip']='enter';act['frames']=12;act['fps']=12;act['loop']=False
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for k in curve.keyframe_points:k.interpolation='LINEAR'
root['native_action_record']=json.dumps({'source':'build-round-01.py','assetId':'portal-entry','clips':{'enter':[o.animation_data.action.name for o in animated]}})
root['animation_recipes']='{"enter":{"frames":12,"fps":12,"loop":false,"terminal":"hold frame 11"}}'

# Exact frozen portal capture. No view-dependent fit, material, light or camera changes.
cam_input=json.loads((HERE/'round-01-inputs/native-camera.json').read_text())
camdata=bpy.data.cameras.new('Portal entry registered camera');cam=bpy.data.objects.new('Portal entry registered camera',camdata);sc.collection.objects.link(cam)
cam.matrix_world=Matrix(cam_input['camera']['worldMatrix']);camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL';camdata.ortho_scale=1.5
camdata.shift_x=0;camdata.shift_y=.4096146523952484;camdata.clip_start=.01;camdata.clip_end=100
sc.camera=cam
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=768;sc.render.resolution_y=1536;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=1.2206555604934692;sc.render.pixel_aspect_y=1
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=15
sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.dither_intensity=0
sc.render.use_compositing=False;sc.render.use_sequencer=False
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
world=bpy.data.worlds.new('Portal warm soft symmetric environment');world.use_nodes=True;sc.world=world
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.8,.84,.9,1);bg.inputs['Strength'].default_value=.12
def light(name,location,energy,size,color,target=(0,0,.65)):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=color
    ob=bpy.data.objects.new(name,data);sc.collection.objects.link(ob);ob.location=location
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    ob['native_role']='horizontally symmetric soft light';return ob
light('Portal centered warm overhead',(0,0,4.5),235,4.0,(1,.93,.83))
for i in range(4):
    a=i*math.pi/2;light(f'Portal symmetric broad fill {i}',(3*math.cos(a),3*math.sin(a),1.3),100,4.0,(.88,.95,1))
sc.frame_start=1;sc.frame_end=12;sc.render.fps=12
sc.frame_set(1);root.rotation_euler=(0,0,0)
def enable(l):
    l.exclude=False;l.hide_viewport=False
    for c in l.children:enable(c)
enable(sc.view_layers[0].layer_collection)
for ob in col.all_objects:ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
sc.view_layers[0].update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
settings={'asset':'portal-entry','round':'round-01','project':'source/round-01.blend','recipe':'source/build-round-01.py','nativeSourceSHA256':EXPECTED,'constructionAcknowledgment':'source/construction-acknowledgment-v1.json','designMethods':'Continuous rounded-square-profile native annulus, fixed beveled blue octagonal supports, small fitted brass seats and inset ornaments, front/back orbiting native panel pieces.','animation':{'clip':'enter','nativeFrames':[1,12],'publishedPhases':12,'fps':12,'loop':False,'terminal':'hold','pulseAmplitude':.018,'orbitDegrees':30,'easing':'sampled cosine ease/orbit and sine-squared pulse; linear interpolation between all 12 authored native keys','owners':[o.name for o in animated]},'supports':support_names,'entrySocket':[0,0,.74],'nativeCapture':{'frame':[768,1536],'scale':4,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'publishedBy':'exact whole-canvas LANCZOS to384x768; no content changes'},'colorManagement':{'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':0,'gamma':1,'compositing':False},'horizontalLightSymmetry':4,'groundShadowCaster':False,'modelingApproval':None}
(HERE/'round-01-recipe.json').write_text(json.dumps(settings,indent=2)+'\n')
assert hashlib.sha256(RAW.read_bytes()).hexdigest()==EXPECTED
print('PORTAL_BUILD_SAVED',OUT,hashlib.sha256(OUT.read_bytes()).hexdigest(),flush=True)
