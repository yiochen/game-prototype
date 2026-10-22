"""Native kelp reconstruction, from the untouched library, before capture adaptation."""
import bpy, bmesh, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix
sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
RES = BASE / 'round-01-resources'
OUT = BASE / 'round-01.blend'
assert not OUT.exists(), 'Do not replace a saved candidate'
bpy.ops.wm.open_mainfile(filepath=str(RES/'original-library.blend'))
scene = bpy.data.scenes['S33 Native Asset Library Export']
bpy.context.window.scene = scene
col = bpy.data.collections['S33 production concept kelp-fan']
root = bpy.data.objects['S33 production concept kelp-fan root']
for ob in list(bpy.data.objects):
    if ob != root: bpy.data.objects.remove(ob, do_unlink=True)
for sc in list(bpy.data.scenes):
    if sc != scene: bpy.data.scenes.remove(sc)
for c in list(bpy.data.collections):
    if c != col: bpy.data.collections.remove(c)
root.animation_data_clear()
root.location=(0,0,0); root.rotation_euler=(0,0,0); root.scale=(1,1,1)
for key in list(root.keys()): del root[key]
root['production_id']='decor-kelp'
root['artStyle']='warm-soft-native-round-01'
root['animation_recipes']=json.dumps({'idle':{'frames':12,'fps':12,'loop':True}})
for lc in bpy.context.view_layer.layer_collection.children: lc.exclude=False;lc.hide_viewport=False
col.hide_viewport=False; col.hide_render=False
for dat in list(bpy.data.actions): bpy.data.actions.remove(dat)
for dat in list(bpy.data.materials): bpy.data.materials.remove(dat)

def linear(hexcolor):
    a=[int(hexcolor[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in a)+(1,)

def material(name,color,roughness=.47,emission=.16):
    m=bpy.data.materials.new(name); m.use_nodes=True
    m.diffuse_color=linear(color)
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=linear(color)
    bs.inputs['Roughness'].default_value=roughness
    bs.inputs['Specular IOR Level'].default_value=.22
    bs.inputs['Emission Color'].default_value=linear(color)
    bs.inputs['Emission Strength'].default_value=emission
    return m

leafmats=[material('Kelp satin leaf '+str(i),c) for i,c in enumerate(['66BA2D','72C535','5EB12D','7BC73A','60B432','6FC033','65B92E'])]
blue=material('Cobalt stone','2866B5',.60,.12)
blue2=material('Cobalt stone lighter','3377C4',.60,.12)
blue3=material('Cobalt pebble','397CC6',.58,.12)

def mesh_obj(name,verts,faces,mat,parent=root):
    me=bpy.data.meshes.new(name+' mesh');me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    ob=bpy.data.objects.new(name,me);col.objects.link(ob);ob.parent=parent;ob.data.materials.append(mat)
    for f in me.polygons:f.use_smooth=True
    return ob

def stone(name,center,size,mat,angle=0):
    outline=[(-.5,-.29),(-.30,-.5),(.28,-.5),(.5,-.29),(.5,.30),(.29,.5),(-.31,.5),(-.5,.28)]
    vs=[]
    for ring,(scale,z) in enumerate([(.96,0),(1,.28),(.83,1)]):
        for k,(x,y) in enumerate(outline):
            height=z*size[2]*(1-.11*math.sin(k*1.9+len(name))) if ring==2 else z*size[2]
            vs.append((x*size[0]*scale,y*size[1]*scale,height))
    vs.append((.025*size[0],-.015*size[1],size[2]*1.03))
    fs=[tuple(reversed(range(8)))]
    for j in range(2):
        for k in range(8):fs.append((j*8+k,j*8+(k+1)%8,(j+1)*8+(k+1)%8,(j+1)*8+k))
    for k in range(8):fs.append((16+k,16+(k+1)%8,24))
    ob=mesh_obj(name,vs,fs,mat);ob.location=(center[0],center[1],0)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    bevel=ob.modifiers.new('Soft irregular stone edges','BEVEL');bevel.width=.013;bevel.segments=2
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    normal=ob.modifiers.new('Broad stone normals','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=40
    bpy.ops.object.modifier_apply(modifier=normal.name)
    ob.rotation_euler.z=angle;ob['role']='grounded-cobalt'
    return ob

stones=[]
specs=[(-.235,-.275,.455,.405,.18,0),(.235,-.275,.445,.405,.17,0),(-.245,.235,.445,.475,.225,0),(.235,.235,.445,.475,.205,0),(0,-.005,.68,.62,.245,0)]
for i,(x,y,w,d,h,a) in enumerate(specs):stones.append(stone('Kelp cobalt foundation '+str(i),(x,y),(w,d,h),blue if i%2 else blue2,a))
for i,(x,y,w,d,h) in enumerate([(-.39,-.12,.115,.135,.10),(.39,.02,.12,.13,.105),(0,-.44,.13,.105,.09),(.08,.385,.14,.115,.085)]):
    stones.append(stone('Kelp cobalt small rubble '+str(i),(x,y),(w,d,h),blue3))

N=48; SIDES=16
specs=[(-.235,.225,1.78,12,.2),(.225,.225,1.99,65,1.6),(.25,-.035,1.60,110,2.9),(-.23,-.045,1.55,-33,4.1),(-.22,-.285,1.27,30,5.0),(.22,-.285,1.45,-48,2.0),(0,.01,1.80,88,3.2)]
construction=[];primaries=[];actions=[]

def center(t,h,a,p):
    U=Vector((math.cos(a),math.sin(a),0));V=Vector((-math.sin(a),math.cos(a),0))
    return U*(.115*math.sin(t*2.2*math.pi+p)*math.sin(t*math.pi*.86)**1.15)+V*(.037*math.sin(math.pi*t+p)*t)+Vector((0,0,h*t))

def frame(t,h,a,p):
    lo=max(0,t-.0001);hi=min(1,t+.0001)
    tangent=(center(hi,h,a,p)-center(lo,h,a,p)).normalized()
    angle=a+.34*math.sin(math.pi*t+p)+.22*t
    u=Vector((math.cos(angle),math.sin(angle),0));u=(u-tangent*u.dot(tangent)).normalized()
    return u,tangent.cross(u).normalized()

def tube(name,path,width,thick,orient,mat,parent):
    vs=[];fs=[]
    for j in range(N+1):
        t=j/N;c=path(t);u,v=orient(t);w=width(t);d=thick(t)
        for k in range(SIDES):
            q=2*math.pi*k/SIDES;co=math.cos(q);si=math.sin(q)
            # A rounded lens retains a broad ridge and soft returning edge.
            x=math.copysign(abs(co)**.77,co)*w
            y=math.copysign(abs(si)**1.20,si)*d
            vs.append(tuple(c+u*x+v*y))
    for j in range(N):
        for k in range(SIDES):
            a=j*SIDES+k;b=j*SIDES+(k+1)%SIDES
            fs.append((a,b,b+SIDES,a+SIDES))
    fs.append(tuple(reversed(range(SIDES))))
    fs.append(tuple(N*SIDES+k for k in range(SIDES)))
    ob=mesh_obj(name,vs,fs,mat,parent);return ob

def taper(t):return 1 if t<.73 else max(.007,((1-t)/.27)**.58)
for i,(x,y,h,deg,p) in enumerate(specs):
    a=math.radians(deg)
    ob=tube('Kelp flowing primary '+str(i),lambda t,h=h,a=a,p=p:center(t,h,a,p),lambda t:(.077+.042*math.sin(math.pi*t))*taper(t),lambda t:(.028+.007*math.sin(math.pi*t))*taper(t),lambda t,h=h,a=a,p=p:frame(t,h,a,p),leafmats[i],root)
    ob.location=(x,y,.075);ob['role']='primary-frond';ob['capRingIndices']=list(range(SIDES));primaries.append(ob)
    children=[]
    if i in [0,1,2,3,5]:
        at=.47 if i%2 else .53;c=center(at,h,a,p);u,v=frame(at,h,a,p);side=-1 if i%2 else 1
        def branch_path(t,c=c,u=u,v=v,h=h,side=side):
            return c+u*(side*.19*math.sin(t*math.pi*.52))+v*(.018*math.sin(t*math.pi))+Vector((0,0,h*.285*t))
        br=tube('Kelp attached fork '+str(i),branch_path,lambda t:(.029+.041*math.sin(math.pi*t))*max(.009,(1-t)**.45),lambda t:.018*max(.01,(1-t)**.4),lambda t,u=u,v=v:(u,v),leafmats[(i+1)%7],ob)
        br['role']='attached-fork';br['primary']=ob.name;br['capRingIndices']=list(range(SIDES));children.append(br.name)
    for f in range(1,14):
        phase=2*math.pi*(f-1)/12
        ob.rotation_euler=(.008*math.sin(phase+p),.014*math.sin(phase+p*.73),0)
        ob.keyframe_insert(data_path='rotation_euler',frame=f,group='Gentle rooted sway')
    action=ob.animation_data.action;action.name='KELP_WARM__idle__'+str(i)
    slot=ob.animation_data.action_slot
    for layer in action.layers:
        for strip in layer.strips:
            bag=strip.channelbag(slot)
            if bag:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
    actions.append({'target':ob.name,'action':action.name,'slot':slot.identifier})
    construction.append({'primary':ob.name,'anchor':[x,y,.075],'height':h,'angleDegrees':deg,'phase':p,'children':children})

root['native_action_record']=json.dumps({'source':'build-round-01.py','assetId':'decor-kelp','clips':{'idle':[a['action'] for a in actions]}})
camera=bpy.data.cameras.new('Kelp registered camera data');cam=bpy.data.objects.new('Kelp registered camera',camera);scene.collection.objects.link(cam);scene.camera=cam
meta=json.loads((RES/'source-camera.json').read_text());cam.matrix_world=Matrix(meta['camera']['worldMatrix']);camera.type='ORTHO';camera.sensor_fit='HORIZONTAL';camera.ortho_scale=1.5;camera.shift_x=0;camera.shift_y=.75
def area(name,loc,power,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.9))-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Kelp broad overhead',(0,0,5),85,4.5)
for i,(x,y) in enumerate([(3,0),(0,3),(-3,0),(0,-3)]):area('Kelp symmetric fill '+str(i),(x,y,2.6),30,4)
world=bpy.data.worlds.new('Kelp soft world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.70,.60,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.15;scene.world=world
scene.use_nodes=False
scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=48
scene.render.resolution_x=768;scene.render.resolution_y=1920;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=1;scene.render.pixel_aspect_y=1;scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.dither_intensity=0
scene.render.fps=12;scene.frame_start=1;scene.frame_end=12;scene.frame_set(1)
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
bpy.context.view_layer.update()
for datablocks in (bpy.data.meshes,bpy.data.materials,bpy.data.cameras,bpy.data.lights,bpy.data.worlds):
    for data in list(datablocks):
        if data.users==0:datablocks.remove(data)
rig={'asset':'decor-kelp','root':root.name,'clips':{'idle':{'frames':12,'fps':12,'loop':True,'closureFrame':13,'actions':actions}},'method':'Seven native object rotation action owners; five fork children inherit their primary motion. Root and all nine cobalt stones stationary. No modifiers/shape keys/texture animation.'}
(BASE/'round-01-rig.json').write_text(json.dumps(rig,indent=2)+'\n')
(BASE/'round-01-construction.json').write_text(json.dumps({'construction':construction,'crossSection':'closed rounded lens16 sides,48 axial segments','stones':[o.name for o in stones],'motionMethodCorrection':'The prebuild acknowledgment considered shape keys. Native object rotations were selected before construction to preserve the historical mesh-data adapter evaluation order without shape-key bypass.','nativeOriginalSHA256':hashlib.sha256((RES/'original-library.blend').read_bytes()).hexdigest()},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
print('KELP_BUILD_SAVED',str(OUT))
