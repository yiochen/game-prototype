"""Eel BODY round 01 native build. Run only against the hash-bound raw library."""
import sys
sys.dont_write_bytecode = True
import bpy, bmesh, math, json, hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

P = Path(__file__).resolve().parent
E = P.parent
RAW = E.parents[2] / 'production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'
RAW_SHA = 'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
assert hashlib.sha256(RAW.read_bytes()).hexdigest() == RAW_SHA
assert Path(bpy.data.filepath) == RAW
assert (P/'construction-acknowledgment.json').is_file()
root = bpy.data.objects['creature-eel__ground_root.003']
arm = bpy.data.objects['creature-eel__armature.003']
col = bpy.data.collections['S33_CFX_creature-eel.003']
action_record = json.loads(root['native_action_record'])
own_actions = [bpy.data.actions[n] for names in action_record['clips'].values() for n in names]
for a in own_actions:
    a.use_fake_user = True
for bone in arm.pose.bones:
    bone.rotation_mode = 'XYZ'
    bone.rotation_euler = (0, 0, 0)
arm.animation_data_clear()
for o in list(col.all_objects):
    if o.type == 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)

scene = bpy.data.scenes.new('Eel BODY round 01')
bpy.context.window.scene = scene
scene.collection.children.link(col)
col.hide_render = col.hide_viewport = False
for o in col.all_objects:
    o.hide_render = o.hide_viewport = False
    o.hide_set(False)

def linear(hexcolor):
    a=[int(hexcolor[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)+(1,)

def material(name, color, rough=.34, emission=.12, coat=.12):
    m=bpy.data.materials.new('Eel01 '+name);m.diffuse_color=linear(color);m.use_nodes=True
    n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value=linear(color)
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Specular IOR Level'].default_value=.32
    bs.inputs['Coat Weight'].default_value=coat
    bs.inputs['Coat Roughness'].default_value=.24
    bs.inputs['Emission Color'].default_value=linear(color)
    bs.inputs['Emission Strength'].default_value=emission
    m.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    return m,bs

blue,bs=material('rounded cyan blue skin','079FE8',.34,.16,.12)
n=blue.node_tree.nodes;l=blue.node_tree.links
geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');ramp=n.new('ShaderNodeValToRGB')
l.new(geo.outputs['Normal'],sep.inputs[0]);l.new(sep.outputs['Z'],ramp.inputs[0])
ramp.color_ramp.elements[0].position=0.0;ramp.color_ramp.elements[0].color=linear('037ABF')
ramp.color_ramp.elements[1].position=.95;ramp.color_ramp.elements[1].color=linear('10A8EC')
l.new(ramp.outputs['Color'],bs.inputs['Base Color']);l.new(ramp.outputs['Color'],bs.inputs['Emission Color'])
yellow,_=material('warm rounded yellow fins','FFD12D',.32,.14,.15)
white,_=material('eye ivory','FFF9E9',.22,.18,.12)
navy,_=material('deep navy eyes and mouth','052A4E',.26,.18,.12)
glint,_=material('eye glints','FFFFFF',.18,.45,.1)

def weights(o, head=False):
    groups=[o.vertex_groups.new(name='spine_'+str(i)) for i in range(7)]
    for v in o.data.vertices:
        if head:
            groups[0].add([v.index],1,'REPLACE');continue
        t=max(0,min(6,(.52-v.co.y)/(.21714285714285714)))
        i=int(t);j=min(6,i+1);f=t-i
        groups[i].add([v.index],1-f,'REPLACE')
        if j!=i and f>0:groups[j].add([v.index],f,'REPLACE')
    o.parent=arm
    mod=o.modifiers.new('Coherent native spine','ARMATURE');mod.object=arm

def mesh(name, vs, fs, mat, head=False):
    me=bpy.data.meshes.new('Eel01 '+name+' mesh');me.from_pydata(vs,[],fs);me.materials.append(mat);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new('creature-eel__'+name+'.003',me);col.objects.link(o)
    for p in me.polygons:p.use_smooth=True
    weights(o,head)
    return o

profile=[(-1.02,.022,.025),(-.9,.042,.039),(-.70,.07,.061),(-.45,.103,.088),(-.2,.14,.118),(.05,.177,.148),(.25,.211,.174),(.39,.228,.181),(.48,.214,.163),(.56,.176,.127),(.62,.113,.074),(.655,.025,.024)]
def radii(y):
    for i in range(len(profile)-1):
        p,q=profile[i],profile[i+1]
        if p[0]<=y<=q[0]:
            t=(y-p[0])/(q[0]-p[0]);out=[]
            for c in (1,2):
                m0=(q[c]-profile[max(0,i-1)][c])/(q[0]-profile[max(0,i-1)][0])
                m1=(profile[min(len(profile)-1,i+2)][c]-p[c])/(profile[min(len(profile)-1,i+2)][0]-p[0])
                h=q[0]-p[0]
                v=(2*t**3-3*t*t+1)*p[c]+(t**3-2*t*t+t)*h*m0+(-2*t**3+3*t*t)*q[c]+(t**3-t*t)*h*m1
                out.append(max(min(p[c],q[c]),min(max(p[c],q[c]),v)))
            return out
    return list(profile[0 if y<profile[0][0] else -1][1:])

vs=[];fs=[];rings=81;sides=48
for i in range(rings):
    y=-1.02+1.675*i/(rings-1);rx,rz=radii(y)
    for j in range(sides):
        th=2*math.pi*j/sides;x=rx*math.cos(th);z=.44+rz*math.sin(th)
        # Small continuous skin volumes seat the eyes without separate glued collars.
        if math.sin(th)>0:
            z+=.018*math.exp(-((y-.43)/.11)**2)*sum(math.exp(-((x-s*.145)/.065)**2) for s in [-1,1])*math.sin(th)**2
        vs.append((x,y,z))
for i in range(rings-1):
    for j in range(sides):
        a=i*sides+j;b=i*sides+(j+1)%sides
        fs.append((a,a+sides,b+sides,b))
fs.append(tuple(reversed(range(sides))))
fs.append(tuple((rings-1)*sides+j for j in range(sides)))
body=mesh('continuous_body',vs,fs,blue)

# Solid rounded dorsal ribbon: lower half penetrates the skin, upper edge remains continuous.
vs=[];fs=[];nr=65;ns=12
for i in range(nr):
    t=i/(nr-1);y=-1.005+1.49*t;_,rz=radii(y)
    taper=max(.12,math.sin(math.pi*t)**.35)
    width=.024*taper;height=(.063+.025*(1-t))*taper
    base=.44+rz-.019
    for j in range(ns):
        th=2*math.pi*j/ns
        vs.append((width*math.cos(th),y,base+height*(.45+.55*math.sin(th))))
for i in range(nr-1):
    for j in range(ns):
        a=i*ns+j;b=i*ns+(j+1)%ns;fs.append((a,a+ns,b+ns,b))
fs.extend([tuple(reversed(range(ns))),tuple((nr-1)*ns+j for j in range(ns))])
mesh('continuous_dorsal_fin',vs,fs,yellow)

def leaf(name, path, width, thickness, mat):
    vs=[];fs=[];nr=25;ns=16
    for i in range(nr):
        t=i/(nr-1);c=Vector(path(t));lo=Vector(path(max(0,t-.001)));hi=Vector(path(min(1,t+.001)))
        tangent=(hi-lo).normalized();across=Vector((-tangent.y,tangent.x,0)).normalized()
        w=width*(.035+math.sin(math.pi*t)**.72)
        h=thickness*(.12+math.sin(math.pi*t)**.7)
        for j in range(ns):
            th=j*2*math.pi/ns;v=c+across*w*math.cos(th)+Vector((0,0,h*math.sin(th)))
            vs.append(tuple(v))
    for i in range(nr-1):
        for j in range(ns):
            a=i*ns+j;b=i*ns+(j+1)%ns;fs.append((a,a+ns,b+ns,b))
    fs.extend([tuple(reversed(range(ns))),tuple((nr-1)*ns+j for j in range(ns))])
    return mesh(name,vs,fs,mat)

leaf('tail_fin',lambda t:(.012+.15*t*t,-.97-.30*t,.446+.046*math.sin(t*math.pi*.75)),.073,.021,yellow)
for s in [-1,1]:
    leaf('side_fin_'+str(s),lambda t,s=s:(s*(.15+.205*t),.12-.12*t+.035*math.sin(math.pi*t),.43-.012*t+.025*math.sin(math.pi*t)),.071,.018,yellow)

def ellipsoid(name, loc, scale, mat, head=True):
    vs=[];fs=[];nu=40;nv=24
    for i in range(nv+1):
        th=math.pi*(.001+.998*i/nv)
        for j in range(nu):
            ph=j*2*math.pi/nu
            vs.append((loc[0]+scale[0]*math.sin(th)*math.cos(ph),loc[1]+scale[1]*math.sin(th)*math.sin(ph),loc[2]+scale[2]*math.cos(th)))
    for i in range(nv):
        for j in range(nu):
            a=i*nu+j;b=i*nu+(j+1)%nu;fs.append((a,b,b+nu,a+nu))
    fs.extend([tuple(reversed(range(nu))),tuple(nv*nu+j for j in range(nu))])
    return mesh(name,vs,fs,mat,head)

for s in [-1,1]:
    ellipsoid('eye_white_'+str(s),(s*.149,.49,.596),(.074,.065,.073),white)
    ellipsoid('eye_pupil_'+str(s),(s*.149,.531,.622),(.043,.035,.045),navy)
    ellipsoid('eye_glint_'+str(s),(s*.149-.011,.556,.646),(.011,.008,.012),glint)

# A native curved solid smile follows the rounded muzzle rather than a straight bar.
vs=[];fs=[];nr=33;ns=12
for i in range(nr):
    t=-1+2*i/(nr-1);x=.067*t;y=.648-.042*t*t;z=.417+.023*t*t
    r=.010*(.40+.60*math.sin(math.pi*(t+1)/2)**.3)
    for j in range(ns):
        a=j*2*math.pi/ns;vs.append((x,y+r*math.cos(a),z+r*math.sin(a)))
for i in range(nr-1):
    for j in range(ns):
        a=i*ns+j;b=i*ns+(j+1)%ns;fs.append((a,b,b+ns,a+ns))
fs.extend([tuple(reversed(range(ns))),tuple((nr-1)*ns+j for j in range(ns))])
mesh('mouth',vs,fs,navy,True)

# Camera and illumination are one fixed reproducible recipe for every pose/facing.
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1792;scene.render.resolution_y=2048;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
scene.render.fps=12;scene.frame_start=1;scene.frame_end=12
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=70
scene.render.dither_intensity=0;scene.render.filter_size=1.5
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.world=bpy.data.worlds.new('Eel01 neutral world');scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.75,.8,1,1);bg.inputs['Strength'].default_value=.18
cam=bpy.data.objects.new('Eel01 registered 35 degree camera',bpy.data.cameras.new('Eel01 registered camera'))
scene.collection.objects.link(cam);scene.camera=cam
cam.location=(0,-10*math.cos(math.radians(35)),10*math.sin(math.radians(35)))
cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=3.5;cam.data.shift_x=0;cam.data.shift_y=.21428516507148743
def light(name,loc,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
    o.rotation_euler=(-o.location+Vector((0,0,.4))).to_track_quat('-Z','Y').to_euler()
light('Eel01 broad overhead',(0,0,4.5),160,4.0,(1,.95,.86))
for i,(x,y) in enumerate([(3,0),(0,3),(-3,0),(0,-3)]):
    light('Eel01 symmetric fill '+str(i),(x,y,1.5),65,4.0,(.88,.95,1))
light('Eel01 underside lift',(0,0,-3),20,4.0,(.8,.9,1))

# A small portable .blend closure: source actor, native actions, camera and lights only.
for old in list(bpy.data.scenes):
    if old!=scene:bpy.data.scenes.remove(old)
for o in list(bpy.data.objects):
    if o.name not in scene.objects:bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):
    if c!=col and c.users==0:bpy.data.collections.remove(c)
for a in list(bpy.data.actions):
    if a not in own_actions:bpy.data.actions.remove(a)
for _ in range(3):
    bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
root['refinement_round']=1
root['refinement_recipe']='build-round-01.py'
root.rotation_euler=(0,0,0)
arm.animation_data_create();arm.animation_data.action=own_actions[0];arm.animation_data.action_slot=own_actions[0].slots[0]
scene.frame_set(1);bpy.context.view_layer.update()
dest=P/'round-01.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)
recipe={'asset':'creature-eel','round':1,'sourceSHA256':RAW_SHA,'scriptSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'projectSHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,
        'rigRepair':'All7 native pose bones now XYZ to match retained original11 Euler-keyed actions. No action key values, timing or IDs changed.',
        'geometry':'Continuous81x48 elliptical tapered rounded body with integrated eye-seat skin bumps; solid65x12 dorsal ribbon; curved solid tail/side leaves; round eye parts and native curved smile. Source7bone weights retained in semantic order with smooth adjacent weighting.',
        'light':'Centered160W4m disk overhead and4equal65W4m disks at cardinal radius3/z1.5; centered20W underside lift; world strength.18. No floor or cast-shadow plane.',
        'materials':'Native Principled blueNormalZ color progression, warmyellow/ivory/navy. Broad roughness.22-.34, modest coat and emissionfill. No textures or external images.',
        'camera':{'elevation':35,'type':'ORTHO','orthoScale':3.5,'sensorFit':'HORIZONTAL','shift':[0,.21428516507148743],'nativeFrame':[1792,2048],'pixelAspect':[1,1]},
        'publication':'Uniform wholecanvas LANCZOS to896x1024; unchanged logical448x512/root224352 and6x2atlas.'}
(P/'round-01-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
assert hashlib.sha256(RAW.read_bytes()).hexdigest()==RAW_SHA
print('SAVED',dest,recipe['projectSHA256'],flush=True)
