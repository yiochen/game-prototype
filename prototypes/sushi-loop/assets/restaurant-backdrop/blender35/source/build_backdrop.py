"""Editable native wall study: four-unit gate, two-unit aperture, ordinary35 camera.
Run through Blender MCP. This creates one isolated scene and never saves over
or changes any pre-existing scene, production library or active .blend file.
"""
from pathlib import Path
import bpy, math, json, importlib.util, hashlib
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT.parents[1] / 'production/source/blender'
SCENE_NAME = 'Sushi Loop Backdrop35 Study'
PITCH = 128
SCALE = 3
ELEVATION = math.radians(35)
BASELINE_Y = -.5
_original_scene = bpy.context.window.scene
_original_scene_name = _original_scene.get("previous_scene", _original_scene.name)

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

P = module('backdrop35_props', PRODUCTION / 'prop_builders.py')
STYLE = module('backdrop35_style', PRODUCTION / 'catalog_style.py')
FACETED = module('backdrop35_faceted', PRODUCTION / 'catalog_faceted.py')

# Rebuild only this study's own scene when iterating; other scenes are untouched.
old = bpy.data.scenes.get(SCENE_NAME)
if old:
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.scenes.remove(old)
for collection in list(bpy.data.collections):
    if (collection.name.startswith('S33_PROP_backdrop35-') or collection.name.startswith('Backdrop35 Assembled Seven Tiles')) and not collection.objects:
        bpy.data.collections.remove(collection)
scene = bpy.data.scenes.new(SCENE_NAME)
bpy.context.window.scene = scene
scene['source'] = str(Path(__file__).resolve())
scene['user_request'] = 'Blender gate and walls using the same 35 degree orthographic camera as characters'
scene['scope'] = 'Wireframe comparison only; production game unchanged'
assets = {}

# Unique material keys prevent changes to the live file's existing materials.
P.PALETTE.update({
 'b35_wood':'B77B3C', 'b35_wood_light':'D99F55', 'b35_wood_dark':'704727',
 'b35_goldwood':'C38B47', 'b35_plaster':'C6A267', 'b35_sill':'847569',
 'b35_blue':'2567C1', 'b35_blue_light':'3B8BDF', 'b35_blue_dark':'153B78',
 'b35_red':'DC4A42', 'b35_red_light':'EE584A', 'b35_red_dark':'B8312C',
 'b35_chalk':'FFF1D0', 'b35_door':'1E2738', 'b35_lattice':'57351F',
 'b35_lantern':'FFE388', 'b35_brass':'8F6023', 'b35_metal':'39332D',
})

def roof(b, width):
    # Shared native Y/Z profile. Modules end on identical X rings, with four
    # ceramic barrel tiles per unit in the gate and both wall variants.
    section = [(-.70,2.65),(-.70,2.77),(0,3.14),(.70,2.77),(.70,2.65),(0,3.00)]
    n = len(section)
    verts = [(x,y,z) for x in (-width/2,width/2) for y,z in section]
    faces = [tuple(reversed(range(n))),tuple(range(n,n*2))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    b.mesh('roof_structure',verts,faces,'b35_blue_dark')
    for index in range(round(width*4)):
        x = -width/2 + .125 + index*.25
        for side in (-1,1):
            # Cross-section has five deliberately flat facets.
            rows = [(0,3.15),(side*.34,2.97),(side*.70,2.78)]
            verts=[]
            for y,z in rows:
                for j in range(7):
                    angle = math.pi*j/6
                    verts.append((x-.112*math.cos(angle),y,z+.07*math.sin(angle)))
            faces=[(r*7+j,r*7+j+1,(r+1)*7+j+1,(r+1)*7+j) for r in range(2) for j in range(6)]
            b.mesh('roof_tile_%02d_%s'%(index,side),verts,faces,'b35_blue_light' if index%4==1 else 'b35_blue')
    # Front fascia and honeywood lintel remain continuous across joins.
    b.box('blue_fascia',(0,-.705,2.66),(width,.12,.19),'b35_blue_dark',.008)
    b.box('fascia_highlight',(0,-.772,2.74),(width,.025,.035),'b35_blue',.002)
    b.box('full_lintel',(0,-.08,2.47),(width,.64,.23),'b35_wood',.012)
    b.box('lintel_face',(0,-.415,2.45),(width,.07,.12),'b35_goldwood',.005)
    # One ridge cap per tile, no end overhang beyond the declared width.
    for i in range(round(width*4)):
        b.cyl('ridge_cap_%02d'%i,(-width/2+.125+i*.25,0,3.145),.105,.25,'b35_blue_dark',8,(0,math.pi/2,0))


def wall_structure(b, width=1):
    b.box('plaster_field',(0,0,1.30),(width,.50,2.54),'b35_plaster',0)
    b.box('lower_plinth',(0,-.01,.19),(width,.62,.38),'b35_wood_dark',.012)
    b.box('base_face',(0,-.335,.18),(width,.04,.25),'b35_wood',.005)
    b.box('bottom_sill',(0,-.05,.055),(width,.90,.11),'b35_wood_dark',.01)
    b.box('left_post',(-width/2+.065,-.29,1.32),(.13,.18,2.64),'b35_wood',.012)
    b.box('post_foot',(-width/2+.085,-.31,.18),(.17,.25,.36),'b35_goldwood',.014)
    b.box('top_joinery',(-width/2+.085,-.34,2.41),(.17,.24,.27),'b35_wood_light',.014)


def lattice_window(b):
    b.box('window_recess',(0,-.265,1.37),(.68,.035,1.17),'b35_door',.008)
    for x in (-.36,.36):
        b.box('window_jamb_'+str(x),(x,-.31,1.37),(.07,.13,1.30),'b35_wood_dark',.01)
    for z in (.72,2.02):
        b.box('window_sill_'+str(z),(0,-.31,z),(.79,.16,.075),'b35_goldwood',.008)
    for index,x in enumerate((-.25,-.083,.083,.25)):
        b.box('window_slat_'+str(index),(x,-.345,1.37),(.045,.07,1.22),'b35_lattice',.006)
    b.box('window_crossbar',(0,-.39,1.31),(.71,.045,.06),'b35_wood',.004)


def lantern(b, x):
    tag = 'left' if x < 0 else 'right'
    b.box(tag+'_hanger',(x,-.36,2.24),(.085,.18,.43),'b35_wood_dark',.008)
    b.box(tag+'_bracket',(x,-.49,2.40),(.18,.48,.09),'b35_wood',.012)
    # Native faceted glass/paper body, with narrow structural bands.
    profile = [(1.19,.11),(1.25,.19),(1.35,.22),(1.82,.22),(1.94,.17),(1.99,.11)]
    verts=[]
    for z,radius in profile:
        for i in range(12):
            a=math.tau*i/12
            verts.append((x+radius*math.cos(a),-.59+radius*math.sin(a),z))
    faces=[]
    for row in range(len(profile)-1):
        for i in range(12):faces.append((row*12+i,row*12+(i+1)%12,(row+1)*12+(i+1)%12,(row+1)*12+i))
    o=b.mesh(tag+'_paper_lantern',verts,faces,'b35_lantern')
    # Mild native emission preserves yellow readability without an added glow image.
    mat=o.data.materials[0].copy();mat.name=tag+'_backdrop35_paper';o.data.materials[0]=mat
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['Emission Color'].default_value=(1,.52,.10,1)
    shader.inputs['Emission Strength'].default_value=.5
    for z in (1.32,1.54,1.78):
        b.cyl(tag+'_band_'+str(z),(x,-.59,z),.223,.027,'b35_brass',12)
    for z in (1.21,1.98):b.cyl(tag+'_cap_'+str(z),(x,-.59,z),.15,.085,'b35_metal',10)
    b.cyl(tag+'_foot',(x,-.59,1.12),.08,.10,'b35_metal',8)


def line(b, name, points, radius=.016):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=1
    spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
    for point,co in zip(spline.points,points):point.co=(*co,1)
    curve.bevel_depth=radius;curve.bevel_resolution=0;curve.resolution_u=1
    obj=bpy.data.objects.new(name,curve);b.collection.objects.link(obj);obj.parent=b.root
    obj.data.materials.append(P.mat('b35_chalk'));b.parts[name]=obj


def curtains(b):
    for panel,cx in enumerate((-.66,0,.66)):
        verts=[]
        for row,z in enumerate((2.30,1.90,1.32)):
            for col,dx in enumerate((-.31,-.15,.15,.31)):
                bulge=.025 if col in (1,2) else 0
                bottom=.035 if row==2 and col in (0,3) else 0
                verts.append((cx+dx,-.47-bulge,z+bottom))
        faces=[(r*4+c,r*4+c+1,(r+1)*4+c+1,(r+1)*4+c) for r in range(2) for c in range(3)]
        obj=b.mesh('noren_panel_'+str(panel),verts,faces,'b35_red')
        obj.data.materials.append(P.mat('b35_red_dark'));obj.data.materials.append(P.mat('b35_red_light'))
        for polygon in obj.data.polygons:polygon.material_index=[1,0,2,0,0,1][polygon.index]
        mod=obj.modifiers.new('Cloth thickness','SOLIDIFY');mod.thickness=.015
        for x in (cx-.22,cx+.22):b.box('cloth_loop_'+str(panel)+'_'+str(x),(x,-.44,2.36),(.06,.065,.20),'b35_red_dark',.006)
    b.cyl('noren_rod',(0,-.40,2.38),.042,2.14,'b35_wood_dark',8,(0,math.pi/2,0))
    # Fish is actual white curve geometry on the central fabric, no bitmap decal.
    body=[(-.25,-.525,1.85),(-.15,-.525,1.98),(0,-.525,2.01),(.20,-.525,1.85),(0,-.525,1.69),(-.15,-.525,1.72),(-.25,-.525,1.85)]
    line(b,'fish_body',body,.018)
    line(b,'fish_tail',[(.15,-.528,1.85),(.30,-.528,1.99),(.30,-.528,1.71),(.15,-.528,1.85)],.018)
    b.cyl('fish_eye',(-.12,-.535,1.87),.025,.012,'b35_chalk',10,(math.pi/2,0,0))


def build_gate():
    b=P.Builder('backdrop35-gate');b.footprint=(4,1);b.height=3.25
    # Clear aperture x=-1..1 is structural, independent of sprite alpha.
    for sign in (-1,1):
        x=sign*1.50
        b.box('side_wall_'+str(sign),(x,0,1.30),(1,.50,2.6),'b35_plaster',0)
        b.box('side_plinth_'+str(sign),(x,-.01,.19),(1,.62,.38),'b35_wood_dark',.012)
        b.box('side_bottom_'+str(sign),(x,-.05,.055),(1,.90,.11),'b35_wood_dark',.01)
        b.box('inner_pillar_'+str(sign),(sign*1.125,-.24,1.32),(.25,.52,2.64),'b35_wood',.024)
        b.box('outer_pillar_'+str(sign),(sign*1.925,-.20,1.32),(.15,.48,2.64),'b35_wood',.012)
        b.box('inner_pillar_foot_'+str(sign),(sign*1.14,-.25,.19),(.28,.50,.38),'b35_goldwood',.018)
        b.box('pillar_joinery_'+str(sign),(sign*1.13,-.29,2.42),(.30,.60,.31),'b35_wood_light',.02)
        lantern(b,sign*1.56)
    b.box('deep_doorway',(0,.21,1.23),(2,.035,2.46),'b35_door',0)
    b.box('threshold',(0,-.17,.055),(2,.66,.11),'b35_sill',.01)
    b.box('threshold_center_joint',(0,-.4985,.055),(.014,.003,.11),'b35_wood_dark',0)
    curtains(b);roof(b,4)
    b.socket('threshold',(0,BASELINE_Y,0))
    b.notes.extend(['Outer width exactly 4; jamb inner faces x=-1 and +1 give aperture 2.','35 degree ordinary orthographic; physical height calibrated to complete 3-tile projected silhouette.'])
    return b.finish({'static':{'frames':1,'fps':12,'loop':False,'static':True}})

assets['gate']=build_gate()
for name in ('wall-plain','wall-window'):
    b=P.Builder('backdrop35-'+name);b.footprint=(1,1);b.height=3.25
    wall_structure(b)
    if name=='wall-window':lattice_window(b)
    roof(b,1);b.socket('baseline',(0,BASELINE_Y,0))
    assets[name]=b.finish({'static':{'frames':1,'fps':12,'loop':False,'static':True}})

# Internal half-width module finishes the seven-column assembly at the gate.
b=P.Builder('backdrop35-wall-half');b.footprint=(.5,1);b.height=3.25
wall_structure(b,.5);roof(b,.5)
assets['wall-half']=b.finish({'static':{'frames':1,'fps':12,'loop':False,'static':True}})

# Native construction calibration. Altering mesh Z is an editable geometry
# decision; it is not a pixel stretch, projection multiplier or camera distortion.
def top_min(asset, zscale):
    values=[]
    for obj in asset['collection'].all_objects:
        if obj.type!='MESH':continue
        for vertex in obj.data.vertices:
            p=obj.matrix_world@vertex.co
            values.append(-math.sin(ELEVATION)*p.y-math.cos(ELEVATION)*p.z*zscale)
    return min(values)

bpy.context.view_layer.update()
baseline=-math.sin(ELEVATION)*BASELINE_Y
low,high=.7,1.4
for _ in range(48):
    mid=(low+high)/2
    if baseline-top_min(assets['gate'],mid)>3:high=mid
    else:low=mid
zscale=(low+high)/2
for asset in assets.values():
    for obj in asset['collection'].all_objects:
        if obj==asset['root']:continue
        obj.matrix_world=Matrix.Diagonal((1,1,zscale,1)) @ obj.matrix_world
    asset['height']=3.25*zscale
    STYLE.apply(asset,asset['root'].name)
    asset['root']['nativeZScaleForProjectedHeight']=zscale
    asset['root']['cameraElevation']=35
    asset['root']['projectedHeightTiles']=3
scene['nativeZScale']=zscale

# 35 degrees, exactly the same square-pixel orthographic convention as the cast.
scene.render.engine='BLENDER_EEVEE'
scene.eevee.taa_render_samples=256
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=50
scene.render.film_transparent=True;scene.render.pixel_aspect_x=1;scene.render.pixel_aspect_y=1
scene.render.resolution_percentage=100
scene.render.fps=12;scene.render.dither_intensity=0
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.view_settings.exposure=0;scene.view_settings.gamma=1
FACETED.ensure_lights(scene);STYLE.ensure_compositor(scene)
cam=bpy.data.objects.new('Backdrop35 Camera',bpy.data.cameras.new('Backdrop35 Camera'))
scene.collection.objects.link(cam);scene.camera=cam
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL'
cam.location=(0,-10*math.cos(ELEVATION),10*math.sin(ELEVATION))
cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()

# All assets retain complete padded frames. Runtime uses the authored content
# viewport, not alpha fitting, with a shared 128 px pitch and 3x capture scale.
records={}
def configure(width):
    frame=(int(width*128+64),448);anchor=(frame[0]/2,416)
    scene.render.resolution_x=frame[0]*SCALE;scene.render.resolution_y=frame[1]*SCALE
    cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=0;cam.data.shift_y=0
    bpy.context.view_layer.update()
    def px(point):
        v=world_to_camera_view(scene,cam,Vector(point))
        return Vector((v.x*scene.render.resolution_x,(1-v.y)*scene.render.resolution_y))
    point=(0,BASELINE_Y,0);before=px(point)
    cam.data.shift_y=1;bpy.context.view_layer.update();dy=px(point).y-before.y
    cam.data.shift_y=(anchor[1]*SCALE-before.y)/dy
    bpy.context.view_layer.update()
    base=px(point);dx=px((1,BASELINE_Y,0))-base;dz=px((0,BASELINE_Y,1))-base
    assert abs(dx.x-128*SCALE)<.02 and abs(dz.y+128*SCALE*math.cos(ELEVATION))<.02
    return {'frame':list(frame),'anchor':list(anchor),'cellSize':128,'captureScale':SCALE,'contentRect':[32*SCALE,32*SCALE,int(width*128*SCALE),384*SCALE],
      'camera':{'type':'orthographic','elevationDegrees':35,'pixelAspect':[1,1],'worldMatrix':[list(row) for row in cam.matrix_world]},
      'calibration':{'baseline':list(base),'unitX':list(dx),'unitHeight':list(dz)},'nativeZScale':zscale}

for name,asset in assets.items():
    if name=='wall-half':continue
    records[name]={'widthTiles':4 if name=='gate' else 1,'heightTiles':3,'openingWidthTiles':2 if name=='gate' else None,'collection':asset['collection'].name}
    records[name].update(configure(records[name]['widthTiles']))
    records[name]['image']='renders/'+name+'.png'

# An assembled native model proves shared profiles independently of browser
# compositing. Linked-data mesh copies preserve the editable source modules.
assembly=bpy.data.collections.new('Backdrop35 Assembled Seven Tiles');scene.collection.children.link(assembly)
def instance(name,asset,location):
    for original in asset['collection'].all_objects:
        if original.type not in {'MESH','CURVE'}:continue
        obj=original.copy();obj.name=name+' '+original.name
        transform=original.matrix_world.copy();obj.parent=None
        transform.translation+=Vector(location);obj.matrix_world=transform
        assembly.objects.link(obj)
instance('Native facade gate',assets['gate'],(0,0,0))
for x in (-3,3):instance('Native facade window',assets['wall-window'],(x,0,0))
for x in (-2.25,2.25):instance('Native facade half panel',assets['wall-half'],(x,0,0))
assembly.hide_render=True;assembly.hide_viewport=True
for asset in assets.values():asset['collection'].hide_render=True;asset['collection'].hide_viewport=True
assets['gate']['collection'].hide_render=False;assets['gate']['collection'].hide_viewport=False
configure(4)
ROOT.mkdir(parents=True,exist_ok=True)
(ROOT/'camera.json').write_text(json.dumps({'schemaVersion':1,'projection':'ordinary35-character-camera','physicalCell':1,'renderPitch':128,'projectedHeightTiles':3,'sourceZCalibration':zscale,'assets':records},indent=2)+'\n')
scene['previous_scene']=_original_scene_name
scene['build_recipe_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
bpy.data.libraries.write(str(ROOT/'source/restaurant-backdrop-35.blend'),{scene},fake_user=True,compress=True)
print(json.dumps({'scene':scene.name,'objects':len(scene.objects),'collections':{name:value['collection'].name for name,value in assets.items()},'zScale':zscale,'source':str(ROOT/'source/restaurant-backdrop-35.blend')}))
# Keep the isolated study visible for inspection; the caller restores the prior
# scene after camera/multiple-angle checks. The .blend filepath is never changed.
scene['previous_scene']=_original_scene_name
