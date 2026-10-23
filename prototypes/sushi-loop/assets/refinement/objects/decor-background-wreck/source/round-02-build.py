"""Rebuild the inspected distant wreck as editable, static native timber forms.
Run: blender --background --factory-startup --python round-02-build.py
Only Python standard library plus bundled bpy/bmesh/mathutils are used.
"""
import bpy, bmesh, math, json, hashlib, sys
from pathlib import Path
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

P=Path(__file__).resolve().parent
B=P.parent
O=B/'candidates/round-02'
R=P/'round-02-resources/native'
record=json.loads((R/'registered-camera.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene
c=bpy.data.collections.new('S33_PROP_decor-background-wreck.001');s.collection.children.link(c)
root=bpy.data.objects.new('decor-background-wreck__root.001',None);c.objects.link(root)
root['role']='quiet standalone nonblocking distant blue wreck; registration root only'
root['source_native_sha256']='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'

def linear(x):return x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4
def material(name,hexcolor):
    rgb=[linear(int(hexcolor[i:i+2],16)/255) for i in (0,2,4)]
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*rgb,1)
    n.inputs['Roughness'].default_value=.64;n.inputs['Specular IOR Level'].default_value=.2
    return m
blue=material('Quiet blue timber','3D7189')
blue_low=material('Lower worn blue timber','37667F')
blue_top=material('Upper faded blue timber','487F94')
blue_cabin=material('Cabin blue timber','40748A')
rope=material('Muted aged rope','7B8069')
cut=material('Muted exposed timber','778177')
blue_mid=material('Dark weathered blue timber','3C687F')
blue_faded=material('Faded weathered blue timber','4C7B8D')
inner=material('Recessed blue structural timber','355B6C')

def own(o,name,mat):
    o.name='decor-background-wreck__'+name
    for oc in list(o.users_collection):oc.objects.unlink(o)
    c.objects.link(o);o.parent=root
    o.data.materials.append(mat)
    return o

def finish(o,bevel=.009):
    if bevel:
        m=o.modifiers.new('Rounded worn timber edges','BEVEL');m.width=bevel;m.segments=3;m.affect='EDGES'
        m.harden_normals=True
    for p in o.data.polygons:p.use_smooth=True
    m=o.modifiers.new('Broad crafted face normals','WEIGHTED_NORMAL');m.keep_sharp=True;m.weight=40
    return o

def prism(name,poly,depth,mat,bevel=.009):
    n=len(poly);verts=[(x,y,z) for y in [-depth/2,depth/2] for x,z in poly]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
    for i in range(n):j=(i+1)%n;faces.append((i,j,n+j,n+i))
    mesh=bpy.data.meshes.new(name+' editable mesh');mesh.from_pydata(verts,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
    o=bpy.data.objects.new(name,mesh);c.objects.link(o);o.parent=root;o.data.materials.append(mat)
    o.name='decor-background-wreck__'+name
    return finish(o,bevel)

# Staggered timber courses surround a recessed structural core. Native broken
# boundaries and broad muted end-wear interrupt the formerly continuous panels.
prism('hull_inner_structure',[(-.43,.09),(.42,.09),(.455,.300),(-.45,.300)],.132,inner,.010)
prism('lower_keel_course',[(-.421,.075),(.400,.080),(.450,.157),(-.453,.159),(-.445,.115)],.146,blue_low,.012)
prism('middle_port_stub',[(-.463,.153),(-.286,.157),(-.302,.186),(-.273,.201),(-.290,.226),(-.461,.245),(-.478,.216)],.176,blue_mid,.007)
prism('middle_main_plank',[(-.219,.157),(.451,.156),(.477,.242),(.120,.247),(-.207,.234),(-.189,.207),(-.230,.193)],.178,blue,.009)
prism('upper_port_plank',[(-.477,.236),(-.329,.244),(-.347,.270),(-.316,.292),(-.337,.328),(-.476,.343),(-.490,.306)],.190,blue_faded,.009)
prism('upper_main_plank',[(-.253,.241),(.216,.240),(.225,.327),(.060,.335),(-.218,.324),(-.244,.296),(-.220,.280)],.188,blue_top,.009)
prism('upper_bow_plank',[(.224,.241),(.477,.240),(.490,.315),(.451,.343),(.232,.335)],.186,blue_faded,.010)
# Small coarse exposed splinter sections occupy the actual worn breaks. Their
# low-saturation gray wood is deliberately subordinate to the broad blue timber.
prism('middle_broken_timber',[(-.231,.164),(-.175,.163),(-.192,.187),(-.222,.193)],.168,cut,.004)
prism('upper_broken_timber',[(-.321,.242),(-.259,.245),(-.245,.270),(-.286,.279)],.181,cut,.004)

# Mast and crossbar have actual rounded timber cross-sections rather than strips.
def log(name,start,end,radius,mat):
    a,b=Vector(start),Vector(end);axis=(b-a).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized()
    verts=[]
    for center,r in [(a,radius*1.05),(b,radius*.90)]:
        for i in range(10):verts.append(tuple(center+r*(u*math.cos(i*math.tau/10)+v*math.sin(i*math.tau/10))))
    faces=[tuple(range(9,-1,-1)),tuple(range(10,20))]+[(i,(i+1)%10,(i+1)%10+10,i+10) for i in range(10)]
    mesh=bpy.data.meshes.new(name+' editable mesh');mesh.from_pydata(verts,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
    o=bpy.data.objects.new('decor-background-wreck__'+name,mesh);c.objects.link(o);o.parent=root;o.data.materials.append(mat)
    return finish(o,.0035)
log('mast',(-.045,0,.310),(-.086,0,.737),.029,blue)
log('crossbar',(-.310,0,.640),(.185,0,.619),.025,blue_top)

# Cabin is a small weathered timber crate: an internal block supports three
# uneven vertical staves and two lengthwise cap boards with chipped end profiles.
prism('cabin_inner',[(.112,.327),(.309,.327),(.309,.448),(.112,.448)],.122,blue_mid,.006)
prism('cabin_stave_left',[(.102,.327),(.167,.332),(.164,.458),(.107,.464)],.144,blue_faded,.006)
prism('cabin_stave_center',[(.170,.331),(.237,.329),(.236,.451),(.178,.460)],.147,blue_cabin,.006)
prism('cabin_stave_right',[(.240,.328),(.317,.329),(.311,.454),(.248,.458)],.142,blue_mid,.006)

def roofboard(name,poly,ymin,ymax,mat):
    o=prism(name,poly,ymax-ymin,mat,.006)
    for v in o.data.vertices:v.co.y+=(ymin+ymax)/2
    return o
roofboard('cabin_front_cap_board',[(.091,.451),(.314,.452),(.332,.468),(.299,.477),(.105,.482)],-.087,-.002,blue_faded)
roofboard('cabin_rear_cap_board',[(.097,.453),(.328,.451),(.329,.477),(.235,.481),(.219,.470),(.180,.484),(.096,.479)],.002,.087,blue_top)
roofboard('cabin_worn_cap_tip',[(.300,.452),(.330,.453),(.331,.466),(.313,.469)],-.084,-.006,cut)

# Coarse muted rope grouping at the real intersection; no floating decorations.
for i,z in enumerate([.603,.650]):
    x=-.045+(-.041)*((z-.310)/.427)
    bpy.ops.mesh.primitive_torus_add(major_radius=.032,minor_radius=.008,major_segments=24,minor_segments=8,location=(x,0,z))
    o=own(bpy.context.object,'rope_wrap_'+str(i),rope)
    o.rotation_euler.y=math.atan2(-.041,.427)
    for p in o.data.polygons:p.use_smooth=True

# Worn end grain is a small integrated native piece at the shorter crossbar tip.
log('crossbar_end_grain',(.179,0,.6193),(.187,0,.619),.0216,cut)

# A fixed horizontally symmetric broad soft light recipe, no ground plane.
world=bpy.data.worlds.new('Quiet neutral ambient');s.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.7,.75,.8,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
def light(name,loc,energy,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);s.collection.objects.link(o);o.location=loc
    o.rotation_euler=(Vector((0,0,.3))-o.location).to_track_quat('-Z','Y').to_euler()
light('Broad overhead',(0,0,4),160,4)
for i,(x,y) in enumerate([(3,0),(0,3),(-3,0),(0,-3)]):light('Symmetric broad fill '+str(i),(x,y,2),65,4)

data=bpy.data.cameras.new('Registered own orthographic camera');cam=bpy.data.objects.new('Registered own orthographic camera',data);s.collection.objects.link(cam);s.camera=cam
cam.matrix_world=Matrix(record['camera']['worldMatrix']);data.type='ORTHO';data.sensor_fit='HORIZONTAL';data.ortho_scale=1.5;data.clip_start=.1;data.clip_end=1000
s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True;s.cycles.seed=17
s.render.resolution_x=768;s.render.resolution_y=1408;s.render.resolution_percentage=100
s.render.pixel_aspect_x=record['camera']['pixelAspect'][0];s.render.pixel_aspect_y=1
s.render.fps=12;s.render.fps_base=1;s.render.film_transparent=True
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='8';s.render.dither_intensity=0
s.render.filter_size=1.5
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
s.frame_start=1;s.frame_end=1;s.frame_set(1)
def px(pt):
    v=world_to_camera_view(s,cam,Vector(pt));return [v.x*768,(1-v.y)*1408]
bpy.context.view_layer.update();base=px((0,0,0));data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-base[1];data.shift_y=(992-base[1])/dy
bpy.context.view_layer.update()
root.rotation_euler=(0,0,0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'round-02.blend'))
recipe={'asset':'decor-background-wreck','round':'round-02','blenderVersion':bpy.app.version_string,'buildScriptSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'originalNativeSHA256':root['source_native_sha256'],'modeling':'Native editable rebuilt staggered broken blue timber courses over a recessed structural core, rounded mast/crossbar, uneven stave cabin and chipped two-board cap with restrained muted end wear; two rope wraps. No image textures or geometry cards.','render':{'engine':s.render.engine,'samples':48,'denoising':True,'seed':17,'pixelFilter':'Cycles Blackman-Harris','filterWidth':s.render.filter_size,'colorManagement':'Standard/None/exposure0/gamma1/dither0/RGBA8','lighting':'one broad overhead + four identical broad horizontal fills plus neutral constant ambient; no ground plane'},'registeredCameraInputSHA256':hashlib.sha256((R/'registered-camera.json').read_bytes()).hexdigest(),'rootPixels':px((0,0,0)),'captureScript':'source/round-02-capture.py','sourceProject':'source/round-02.blend','resources':'Native geometry/materials/light/world fully stored in blend; no image or external linked dependencies; only standard Blender/Python modules.'}
(P/'round-02-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
print('BUILD COMPLETE',len(c.all_objects),px((0,0,0)))
