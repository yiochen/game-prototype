"""Portal-rim round01. Native geometry, materials, lights and object actions.
Run Blender --background round-01-resources/native/original.blend --python this.
No external images, mesh cards, image compositor or raster repair.
"""
import bpy, bmesh, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'candidates'/'round-01-development-final-budget'
OUT.mkdir(parents=True,exist_ok=True)
original=HERE/'round-01-resources/native/original.blend'
assert hashlib.sha256(original.read_bytes()).hexdigest()=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
rawprops={k:bpy.data.objects['portal_rim__root.002'][k] for k in bpy.data.objects['portal_rim__root.002'].keys()}
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='S33 Native Asset Library Export'
col=bpy.data.collections.new('S33_PROP_portal_rim.002');sc.collection.children.link(col)
root=bpy.data.objects.new('portal_rim__root.002',None);col.objects.link(root)
for k,v in rawprops.items():root[k]=v
for k in ['native_action_record','artStyle']:del root[k]
root['artStyle']='warm-soft-native-round-01'
root['refinementNotes']='Continuous cyan annular volume, warm rail, double-sided inset housings and stable faceted navy saddle supports. Open center, no access mechanic.'

def rgba(hexcolor):
    rgb=[int(hexcolor[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb)+(1,)

def material(name,color,rough=.5,metal=0,emission=0):
    m=bpy.data.materials.new('portal-rim '+name);m.diffuse_color=rgba(color);m.use_nodes=True
    n=m.node_tree.nodes;n.clear();o=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value=rgba(color);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    p.inputs['Specular IOR Level'].default_value=.28
    p.inputs['Emission Color'].default_value=rgba(color);p.inputs['Emission Strength'].default_value=emission
    m.node_tree.links.new(p.outputs['BSDF'],o.inputs['Surface'])
    m['nativeRole']=name
    return m
cyan=material('cyan core','11CDE7',.34,0,.11)
aqua=material('aqua turning plane','12A9CB',.44,0,.04)
lightcyan=material('cyan soft bevel','56E8F0',.36,0,.08)
gold=material('warm brass construction','B17B35',.50,.12)
goldlight=material('warm brass bevel','D2A354',.48,.12)
blue=material('blue inset','137BD7',.30,.04,.05)
bluelight=material('blue inset bevel','28B7F0',.32,.04,.06)
navy=material('navy stone','30486D',.72)
navy2=material('navy stone plane','3E587C',.7)
navy3=material('navy stone dark plane','283B5B',.72)
teal=material('deep aqua saddle','147C96',.56)

def move_own(o,name,parent=root):
    o.name='portal_rim__'+name
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o);o.parent=parent
    return o

def profile_ring(name,profile,mats,indices,major=96,smooth=True):
    vertices=[];faces=[];count=len(profile)
    for i in range(major):
        a=2*math.pi*i/major
        for r,y in profile:vertices.append((r*math.cos(a),y,.74+r*math.sin(a)))
    for i in range(major):
        for j in range(count):faces.append((i*count+j,((i+1)%major)*count+j,((i+1)%major)*count+(j+1)%count,i*count+(j+1)%count))
    mesh=bpy.data.meshes.new('portal-rim '+name);mesh.from_pydata(vertices,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    o=bpy.data.objects.new('portal_rim__'+name,mesh);col.objects.link(o);o.parent=root
    for m in mats:mesh.materials.append(m)
    for i,p in enumerate(mesh.polygons):p.material_index=indices[i%count];p.use_smooth=smooth
    # Vertices are authored around entry center; move local origin there for pulse.
    for v in mesh.vertices:v.co.z-=.74
    o.location.z=.74
    return o

# Elliptical cross-section with readable front/back bands and rounded inner edge.
profile=[]
for j in range(20):
    a=2*math.pi*j/20
    profile.append((.542+.075*math.cos(a),.086*math.sin(a)))
core=profile_ring('cyan_continuous_band',profile,[cyan,aqua,lightcyan],[1 if j in (0,1,9,10,11,19) else 2 if j in (3,4,5,14,15,16) else 0 for j in range(20)])
# The outer frame has real profile depth, front/back brass bevels and a muted side.
railprofile=[(.625,-.066),(.626,-.082),(.637,-.095),(.671,-.095),(.685,-.081),(.690,-.058),(.690,.058),(.685,.081),(.671,.095),(.637,.095),(.626,.082),(.625,.066)]
rail=profile_ring('outer_structural_rail',railprofile,[gold,goldlight,teal],[0,1,1,1,0,2,0,1,1,1,0,2])
# Narrow aqua channel joins the energy core and outer rail without coplanar surfaces.
channel=profile_ring('aqua_channel',[(.607,-.057),(.612,-.073),(.629,-.073),(.635,-.057),(.635,.057),(.629,.073),(.612,.073),(.607,.057)],[aqua,lightcyan],[0,1,1,0,0,1,1,0])

def box(name,location,size,mat,bevel=.018,segments=3,parent=root):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    o=move_own(bpy.context.object,name,parent);o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if bevel:
        m=o.modifiers.new('native softened corner','BEVEL');m.width=bevel;m.segments=segments
        m.affect='EDGES'
        n=o.modifiers.new('stable broad face normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=40
    return o

# Eight identical assemblies orbit slowly on a continuous structural rail.
# At the discrete closing slot, ownership permutes over visually identical slots.
ornaments=[]
for i in range(8):
    pivot=bpy.data.objects.new('portal_rim__orbit_housing_'+str(i),None);col.objects.link(pivot);pivot.parent=root
    housing=box('warm_housing_'+str(i),(0,0,0),(.102,.225,.152),goldlight,.021,3,pivot)
    for side in [-1,1]:
        inset=box('blue_inset_'+str(i)+'_'+str(side),(0,side*.119,0),(.070,.035,.110),blue,.013,1,pivot)
        # A native wide center plane, with beveled gem edges supplied by geometry.
        inset.data.materials.append(bluelight)
        bevel=inset.modifiers.get('native softened corner');bevel.material=1
    crown=box('blue_crown_'+str(i),(.050,0,0),(.026,.155,.105),blue,.010,1,pivot)
    crown.data.materials.append(bluelight);crown.modifiers.get('native softened corner').material=1
    ornaments.append(pivot)

def rock(name,x):
    verts=[];faces=[];rings=[(-.045,.215,.162),(.105,.257,.205),(.278,.204,.168),(.351,.125,.112)]
    for ri,(z,rx,ry) in enumerate(rings):
        for i in range(8):
            a=2*math.pi*i/8+math.pi/8
            verts.append((x+rx*math.cos(a),.025+ry*math.sin(a),z+(0.009*math.cos(a*3) if ri==2 else 0)))
    faces.append(tuple(range(7,-1,-1)))
    for r in range(3):
        for i in range(8):
            a=r*8+i;b=r*8+(i+1)%8;c=(r+1)*8+(i+1)%8;d=(r+1)*8+i
            if r==1 and i%2==0:faces.extend([(a,b,d),(b,c,d)])
            else:faces.append((a,b,c,d))
    faces.append(tuple(range(24,32)))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new('portal_rim__'+name,mesh);col.objects.link(o);o.parent=root
    for m in [navy,navy2,navy3]:mesh.materials.append(m)
    for i,p in enumerate(mesh.polygons):p.material_index=[0,0,1,0,2,0,1,0][i%8]
    m=o.modifiers.new('soft stone edge','BEVEL');m.width=.010;m.segments=2
    n=o.modifiers.new('broad stone normals','WEIGHTED_NORMAL');n.keep_sharp=True
    o['supportGroup']=name
    return o
supports=[]
for side in [-1,1]:
    name='support_left' if side<0 else 'support_right';stone=rock(name,side*.412);supports.append(stone)
    saddle=box('saddle_'+str(side),(side*.435,0,.289),(.192,.235,.166),teal,.025,3)
    saddle['supportGroup']=name
    # Native broad warm collar across the stone shoulder; ring intersects this saddle.
    collar=box('shoulder_collar_'+str(side),(side*.435,0,.320),(.207,.249,.058),gold,.014,3)
    collar['supportGroup']=name

# Bake the one required idle into actual Blender object actions, frame13=frame1.
for frame in range(1,14):
    t=(frame-1)/12 if frame<13 else 0
    pulse=1+.012*math.sin(2*math.pi*t)
    core.scale=(pulse,1,pulse);core.keyframe_insert('scale',frame=frame,group='soft annular pulse')
    for i,pivot in enumerate(ornaments):
        a=i*math.pi/4+(math.pi/4*t)
        pivot.location=(.660*math.cos(a),0,.74+.660*math.sin(a));pivot.rotation_euler=(0,-a,0)
        pivot.keyframe_insert('location',frame=frame,group='circulation');pivot.keyframe_insert('rotation_euler',frame=frame,group='circulation')
for o in [core,*ornaments]:
    a=o.animation_data.action;a.name='PORTAL_WARM_NATIVE__idle__'+o.name
    for layer in a.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for f in bag.fcurves:
                    for k in f.keyframe_points:k.interpolation='LINEAR'
sc.frame_start=1;sc.frame_end=12;sc.render.fps=12;sc.frame_set(1)

# Fixed registered capture camera. A single configuration is used for all facings.
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=768;sc.render.resolution_y=1536;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1
cam=bpy.data.objects.new('Portal registered capture camera',bpy.data.cameras.new('Portal registered capture camera'));sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
elev=math.atan(1/.7);cam.location=(0,-10*math.cos(elev),10*math.sin(elev));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.shift_x=0;cam.data.shift_y=.4096146523952484;cam.data.clip_start=.1;cam.data.clip_end=1000
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=15
sc.render.dither_intensity=0;sc.render.filter_size=1.5;sc.render.use_persistent_data=True;sc.render.threads_mode='FIXED';sc.render.threads=4
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.world=bpy.data.worlds.new('Portal broad ambient');sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.62,.72,.88,1);bg.inputs['Strength'].default_value=.12
def area(name,loc,power,size,color):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.65))-o.location).to_track_quat('-Z','Y').to_euler()
    return o
area('Broad centered overhead',(0,0,4.5),160,4,(1,.95,.88))
for i in range(4):
    a=i*math.pi/2;area('Equal cardinal soft fill '+str(i),(3*math.cos(a),3*math.sin(a),2.1),55,4,(.82,.92,1))

bpy.context.view_layer.update()
actions=[]
for o in [core,*ornaments]:
    a=o.animation_data.action
    count=sum(len(f.keyframe_points) for l in a.layers for s in l.strips for b in s.channelbags for f in b.fcurves)
    actions.append({'ownerType':'Object','ownerName':o.name,'action':a.name,'slotIdentifier':o.animation_data.action_slot.identifier,'keyframeCount':count})
rig={'assetId':'portal-rim','fps':12,'source':'build-round-01.py','static':False,'clips':{'idle':{'frames':12,'fps':12,'loop':True,'static':False,'firstFrame':1,'lastUniqueFrame':12,'closingKeyFrame':13,'actions':actions,'controlsByFrame':[{} for i in range(12)],'geometryOwners':[],'shaderChannels':[],'shaderLoopClosure':{}}},'armatures':[],'footprint':[1,1],'projection':'square-top-front-oblique','groundRootObject':root.name,'sockets':{'entry':[0,0,.74]},'actionCount':len(actions),'status':'native-baked-awaiting-independent-review','notes':['12-frame published discrete circulation over eight identical assemblies; frame13 resets each owner to frame1 with setwise slot invariance and actual closure evidence.','Static stones, saddles, structural rail, root and entry reference.','Full native4x canvas uniformly reduced to published2x; no fitted camera.']}
(HERE/'round-01-rig.json').write_text(json.dumps(rig,indent=2)+'\n')
root['native_action_record']=json.dumps({'source':'build-round-01.py','assetId':'portal-rim','clips':{'idle':[a['action'] for a in actions]}})
settings={'asset':'portal-rim','nativeConstruction':'continuous96x20 elliptical annular core; continuous12-profile brass rail; native aqua channel; eight double-sided beveled inset assemblies; faceted finite support stones and saddle collars','materials':{m.name:{'base':list(m.diffuse_color),'nodes':[(n.bl_idname,n.name) for n in m.node_tree.nodes]} for m in [cyan,aqua,lightcyan,gold,goldlight,blue,bluelight,navy,navy2,navy3,teal]},'lighting':{'horizontalSymmetry':4,'overhead':{'energy':160,'z':4.5,'size':4,'color':[1,.95,.88]},'equalCardinalFills':{'count':4,'energy':55,'radius':3,'z':2.1,'size':4,'color':[.82,.92,1]},'worldStrength':.12,'floor':False,'directionalGroundShadow':False},'render':{'engine':sc.render.engine,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'filterSize':sc.render.filter_size,'dither':sc.render.dither_intensity},'motion':rig['notes']}
(HERE/'round-01-settings.json').write_text(json.dumps(settings,indent=2)+'\n')
path=HERE/'round-01.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
for facing,angle in [('S',0),('E',90),('N',180),('W',-90)]:
    root.rotation_euler.z=math.radians(angle);sc.frame_set(1);bpy.context.view_layer.update();sc.render.filepath=str(OUT/(facing+'-000.png'));bpy.ops.render.render(write_still=True)
print('PORTAL_BUILD_COMPLETE',str(path),flush=True)
