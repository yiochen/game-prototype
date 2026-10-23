"""Rebuild safe-passage native forms from its authorized raw root; private outputs only."""
import sys
sys.dont_write_bytecode = True
import bpy, bmesh, math, json, hashlib, shutil
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
RAW = BASE / 'reviews/preparation-v1/resources/original-library.blend'
EXPECTED = 'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
assert hashlib.sha256(RAW.read_bytes()).hexdigest() == EXPECTED
assert (HERE/'construction-acknowledgment-v1.json').is_file()
OUT = HERE/'working-v2.blend'
assert not OUT.exists()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f: json.dump(value, f, indent=2); f.write('\n')

bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(RAW), link=False) as (available, chosen):
    chosen.collections = ['S33_PROP_safe-passage.001']
sc = bpy.context.scene
sc.name = 'safe-passage warm-soft round-01'
col = chosen.collections[0]
sc.collection.children.link(col)
col.hide_viewport = col.hide_render = False
root = next(o for o in col.objects if o.name.startswith('safe-passage__root'))
original_props = {k:root[k] for k in root.keys()}
for o in list(col.objects):
    if o != root: bpy.data.objects.remove(o, do_unlink=True)
for data in list(bpy.data.meshes):
    if data.users == 0: bpy.data.meshes.remove(data)
for data in list(bpy.data.materials):
    if data.users == 0: bpy.data.materials.remove(data)
root.name = 'safe-passage__root'
root.location = (0,0,0); root.rotation_euler = (0,0,0); root.scale=(1,1,1)
root['artStyle'] = 'safe-passage-warm-soft-round-01'
root['animation_recipes'] = json.dumps({'ambient':{'frames':12,'fps':12,'loop':True}})

def rgba(h):
    values=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values)+(1,)

def material(name, low, high=None, zmax=.5, rough=.46, spec=.32, coat=.1):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nt=m.node_tree;nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial');p=nt.nodes.new('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value=rgba(low)
    p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=spec
    p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.34
    nt.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    if high:
        geo=nt.nodes.new('ShaderNodeNewGeometry');xyz=nt.nodes.new('ShaderNodeSeparateXYZ')
        ramp=nt.nodes.new('ShaderNodeValToRGB');rng=nt.nodes.new('ShaderNodeMapRange')
        rng.inputs['From Min'].default_value=-.03;rng.inputs['From Max'].default_value=zmax
        ramp.color_ramp.elements[0].color=rgba(low);ramp.color_ramp.elements[1].color=rgba(high)
        ramp.color_ramp.interpolation='EASE'
        nt.links.new(geo.outputs['Position'],xyz.inputs['Vector']);nt.links.new(xyz.outputs['Z'],rng.inputs['Value'])
        nt.links.new(rng.outputs['Result'],ramp.inputs['Fac']);nt.links.new(ramp.outputs['Color'],p.inputs['Base Color'])
    m.diffuse_color=rgba(high or low)
    return m

blue=material('Mineral blue · broad height color', '155CBB','51BCEE',.34,.48,.32,.10)
smallblue=material('Mineral blue · small stone', '1856AD','42A7DD',.23,.50,.30,.08)
green=material('Leaf green · thick living volume','146E32','9EDB23',.51,.47,.28,.07)
green2=material('Leaf green · young crown','238237','BBE747',.51,.48,.28,.07)
cyan=material('Lane guide · turquoise body','087C9E','29D8E4',.03,.33,.38,.15)
cyanface=material('Lane guide · inset cyan face','28BDD2',None,.03,.40,.32,.10)

def own(o,name,role,mat):
    for c in list(o.users_collection): c.objects.unlink(o)
    col.objects.link(o);o.name='safe-passage__'+name;o.parent=root
    o['role']=role;o.data.materials.append(mat)
    o.hide_viewport=o.hide_render=False;o.hide_set(False)
    return o

def bevel(o,width,segments=3):
    mod=o.modifiers.new('Native softened mineral edges','BEVEL');mod.width=width;mod.segments=segments
    mod.affect='EDGES';mod.harden_normals=True
    normal=o.modifiers.new('Broad plane normals','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=50

stones=[]
for name,loc,scale,rot,mat,w in [
    ('main_blue_stone',(-.305,.140,.137),(.166,.218,.182),(.04,-.09,.12),blue,.014),
    ('small_blue_stone',(-.190,-.230,.073),(.133,.127,.106),(.10,.06,-.14),smallblue,.010)]:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=loc)
    o=own(bpy.context.object,name,'stable_stone',mat)
    # Bake the crafted unequal scale/rotation into real mesh vertices, then round edges in native units.
    from mathutils import Euler, Matrix
    transform=Euler(rot).to_matrix() @ Matrix.Diagonal(scale)
    for v in o.data.vertices: v.co=transform @ v.co
    # Preserve finite original support embedding while remaining inside the frozen budget.
    minz=min(v.co.z+o.location.z for v in o.data.vertices)
    target=-.047 if name=='main_blue_stone' else -.029
    o.location.z += target-minz
    bevel(o,w);stones.append(o)

leaves=[]
def leaf(name,base,length,width,lean,angle,phase,index,mat):
    verts=[(0,0,0)];rings=[];sides=10;steps=10
    for j in range(1,steps):
        t=j/steps;profile=math.sin(math.pi*t)**.85
        row=[]
        for k in range(sides):
            a=2*math.pi*k/sides
            row.append(len(verts))
            verts.append((width*profile*math.cos(a),lean*t*t + width*.27*profile*math.sin(a),length*t))
        rings.append(row)
    tip=len(verts);verts.append((0,lean,length));faces=[]
    for k in range(sides):faces.append((0,rings[0][(k+1)%sides],rings[0][k]))
    for a,b in zip(rings,rings[1:]):
        for k in range(sides):faces.append((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]))
    for k in range(sides):faces.append((rings[-1][k],rings[-1][(k+1)%sides],tip))
    me=bpy.data.meshes.new(name+' closed fleshy mesh');me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=root;o.location=base;o.rotation_euler=(0,0,angle)
    o.name='safe-passage__'+name;o['role']='attached_foliage';o['attachmentStone']=stones[index].name
    o['attachmentPivot']=list(base);o['leafClosedThickness']=width*.54;o.data.materials.append(mat)
    for p in me.polygons:p.use_smooth=True
    sub=o.modifiers.new('Soft fleshy leaf curvature','SUBSURF');sub.subdivision_type='CATMULL_CLARK';sub.levels=1;sub.render_levels=1
    amp=.035 if index==0 else .045
    for frame in range(1,14):
        theta=0 if frame==13 else 2*math.pi*(frame-1)/12
        o.rotation_euler=(amp*math.sin(theta+phase),amp*.7*math.cos(theta+phase),angle)
        o.keyframe_insert(data_path='rotation_euler',frame=frame,group='Rooted ambient sway')
    o.animation_data.action.name='safe-passage__ambient__'+name
    # Default BEZIER keys are sampled at the exact required phase slots; no duplicated published last frame.
    leaves.append(o);return o

# One coherent crown rooted inside the main stone; radial leaves remain deliberate in every facing.
base=(-.305,.145,.278)
leaf('crown_center',base,.226,.041,.010,.2,.2,0,green2)
for i,(length,width,lean) in enumerate([(.185,.043,.100),(.175,.046,.105),(.203,.043,.075),(.165,.043,.108),(.183,.044,.095),(.175,.042,.100)]):
    leaf('crown_leaf_'+str(i),base,length,width,lean,i*math.tau/6+.16,i*.67,0,green if i%2 else green2)
smallbase=(-.190,-.230,.158)
for i in range(3):
    leaf('small_growth_'+str(i),smallbase,.115+(i==1)*.025,.029,.061,i*math.tau/3+.5,i*.8+.3,1,green)

marks=[]
for i,y in enumerate([-.31,-.02,.27]):
    for part,z,scale,mat,w in [('body',.015,(.126,.046,.018),cyan,.007),('inset',.024,(.101,.027,.004),cyanface,.002)]:
        bpy.ops.mesh.primitive_cube_add(size=1,location=(.266,y,z))
        o=own(bpy.context.object,'lane_guide_'+str(i)+'_'+part,'stable_lane_guide',mat)
        for v in o.data.vertices:v.co=Vector((v.co.x*scale[0],v.co.y*scale[1],v.co.z*scale[2]))
        bevel(o,w,3);marks.append(o)

root['native_action_record']=json.dumps({'source':'build-round-01-v2.py','assetId':'safe-passage','clips':{'ambient':[o.animation_data.action.name for o in leaves]}})
root['sourceRawSHA256']=EXPECTED
root['designBudgetCanonicalS']=json.dumps({'X':[-.5,.5],'Y':[-.5,.5],'Z':[-.05,.53]})

# Exact original registered projection; no per-view fitting or adjustments.
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=768;sc.render.resolution_y=1408;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1
cam=bpy.data.objects.new('safe-passage registered capture camera',bpy.data.cameras.new('Registered camera'));sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
def px(v):
    p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update();p0=px((0,0,0))
cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-p0.y
cam.data.shift_y=(992-p0.y)/dy;cam.data.shift_x=0;bpy.context.view_layer.update()
assert (px((0,0,0))-Vector((384,992))).length<.001
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=35
sc.render.fps=12;sc.frame_start=1;sc.frame_end=12
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.render.dither_intensity=0
sc.world=bpy.data.worlds.new('Symmetric soft cool fill');sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.68,.78,1,1);bg.inputs['Strength'].default_value=.10
def area(name,location,energy,size,color):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=color
    o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=location;o.rotation_euler=(Vector((0,0,.17))-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Warm broad overhead',(0,0,4),150,4.5,(1,.96,.87))
for i in range(4):
    a=i*math.pi/2;area('Equal cardinal fill '+str(i),(2.5*math.cos(a),2.5*math.sin(a),2.0),45,4,(.83,.93,1))
sc.render.threads_mode='FIXED';sc.render.threads=4
sc.frame_set(1);bpy.context.view_layer.update()
sc['sourceRawSHA256']=EXPECTED;sc['recipe']='build-round-01-v2.py'
write(HERE/'original-root-metadata-v2.json',original_props)
write(HERE/'working-v2-build-record.json',{'rawSHA256':EXPECTED,'root':root.name,'collection':col.name,'scene':sc.name,'objects':len(col.all_objects),'leaves':len(leaves),'stones':len(stones),'guideBodies':3,'guideInsets':3,'cameraShift':[cam.data.shift_x,cam.data.shift_y],'nativeFrame':[768,1408],'frame13IsClosingNotPublished':True,'methods':'closed native leaf meshes with Catmull-Clark1; unequal ico mineral meshes with real bevel3/weighted normals; shallow beveled cyan marks; coherent native height colors, one symmetric lighting recipe'})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
print('BUILD_COMPLETE '+str(OUT),flush=True)
