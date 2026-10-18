"""Native static B Playful / C Chunky character study, issue 33.

Author through Blender MCP with create_study(runtime, output_dir=NEW_FOLDER).
Render the isolated editable project with Blender --background character-scale-study.blend
--python THIS_FILE -- --capture --manifest study.json. No production objects are edited.
All sizes are authored in world cells. Each scale is a true uniform root transform.
"""
import argparse
import contextlib
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import time
import uuid
import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

CELL = 128
SOURCE_SCALE = 4
FRAME = [192, 448]
ROOT = [96, 368]
ELEVATION = 35.
SCALES = [('100', 1.), ('125', 1.25), ('150', 1.5)]
DIRECTIONS = {'S': 0., 'E': math.pi/2, 'N': math.pi, 'W': -math.pi/2}
PALETTE = {'white':'FFF4DE','skin':'9C5736','hair':'4D2B24','navy':'253D65',
           'blue':'2473C7','red':'D94C42','shoe':'68462E','sole':'3D3029',
           'eye':'2B2023','blush':'D8776B'}


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.writing');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)


def mat_rows(m):
    return [[round(float(v),9) for v in row] for row in m]


def vec(v):
    return [round(float(x),9) for x in v]


@contextlib.contextmanager
def activate(scene):
    window=bpy.context.window
    previous=(window.scene,window.view_layer) if window else None
    try:
        if window:window.scene=scene;window.view_layer=scene.view_layers[0]
        with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0]):
            scene.view_layers[0].update();yield
    finally:
        if window and previous:window.scene,window.view_layer=previous


def production_snapshot(runtime):
    assets=getattr(runtime,'assets',{})
    records=[]
    for aid,asset in sorted(assets.items()):
        for o in sorted(asset['collection'].all_objects,key=lambda o:o.name):
            rec={'id':aid,'name':o.name,'matrix':mat_rows(o.matrix_basis),'parent':o.parent.name if o.parent else None,
                 'hidden':[bool(o.hide_render),bool(o.hide_viewport)],
                 'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None}
            if o.type=='MESH':
                rec['vertices']=[vec(v.co) for v in o.data.vertices]
                rec['faces']=[list(p.vertices) for p in o.data.polygons]
            elif o.type=='ARMATURE':rec['bones']={b.name:mat_rows(b.matrix_basis) for b in o.pose.bones}
            records.append(rec)
    return canonical_hash(records)


def _lin(v):
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4


class StaticCharacter:
    """Designed native parts in a relaxed one-frame pose; independent editable meshes."""
    def __init__(self, scene, prefix, design):
        self.id=design;self.prefix=prefix+'__'+design
        self.collection=bpy.data.collections.new(self.prefix)
        scene.collection.children.link(self.collection)
        self.root=bpy.data.objects.new(self.prefix+'__ground-root',None)
        self.collection.objects.link(self.root);self.root.empty_display_size=.15
        self.root['role']='Canonical foot-ground centre; static proportion study; uniform scale and facing control'
        self.parts=[];self.materials={}
        self.anatomy={}
    def material(self,color):
        if color in self.materials:return self.materials[color]
        h=PALETTE.get(color,color).lstrip('#');rgb=tuple(_lin(int(h[i:i+2],16)/255) for i in (0,2,4))
        m=bpy.data.materials.new(self.prefix+'__'+color);m.use_nodes=True;m.diffuse_color=(*rgb,1.)
        p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.88
        if 'Specular IOR Level' in p.inputs:p.inputs['Specular IOR Level'].default_value=.18
        self.materials[color]=m;return m
    def add(self,obj,name,color,role):
        obj.name=self.prefix+'__'+name
        for c in list(obj.users_collection):c.objects.unlink(obj)
        self.collection.objects.link(obj);obj.parent=self.root
        obj.data.materials.append(self.material(color))
        obj['studyDesign']=self.id;obj['anatomyRole']=role;self.parts.append(obj)
        return obj
    def mesh(self,name,vertices,faces,color,role):
        data=bpy.data.meshes.new(self.prefix+'__'+name);data.from_pydata(vertices,[],faces);data.update()
        obj=bpy.data.objects.new(self.prefix+'__'+name,data)
        self.collection.objects.link(obj)
        return self.add(obj,name,color,role)
    def box(self,name,loc,size,color,bevel=.015,rot=(0,0,0),role='detail',segments=2):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
        obj=bpy.context.object;obj.dimensions=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        obj.rotation_euler=rot
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        self.add(obj,name,color,role)
        if bevel:
            mod=obj.modifiers.new('Soft illustrated bevel','BEVEL');mod.width=bevel;mod.segments=segments
            mod.affect='EDGES'
        return obj
    def ico(self,name,loc,scale,color,role='detail',subdivisions=1):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions,radius=1,location=loc)
        obj=bpy.context.object;obj.scale=scale
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        return self.add(obj,name,color,role)
    def sleeve(self,name,start,end,r1,r2,color):
        a,b=Vector(start),Vector(end);axis=(b-a).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized()
        vertices=[]
        for centre,r in ((a,r1),(b,r2)):
            for i in range(8):
                ang=math.tau*i/8+math.pi/8
                vertices.append(tuple(centre+u*(math.cos(ang)*r)+v*(math.sin(ang)*r*.98)))
        faces=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
        return self.mesh(name,vertices,faces,color,'arm')
    def torso(self,rings):
        # Eight-sided shaped torso has a true belly/back, rather than a flat cutout.
        vertices=[]
        for z,width,front,back in rings:
            vertices += [(-width*.73,-front,z),(width*.73,-front,z),(width,-front*.60,z),(width,back*.62,z),
                         (width*.73,back,z),(-width*.73,back,z),(-width,back*.62,z),(-width,-front*.60,z)]
        faces=[tuple(reversed(range(8))),tuple(range((len(rings)-1)*8,len(rings)*8))]
        faces += [(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i) for j in range(len(rings)-1) for i in range(8)]
        self.mesh('shaped-coat',vertices,faces,'white','torso')
    def apron(self,zbottom,ztop,width,depth):
        # Solid wrap has visible side and back volume, avoiding a paper-thin front sheet.
        verts=[]
        for z,w,d in ((zbottom,width,depth),(ztop,width*.91,depth*.91)):
            verts += [(-w,-d,z),(w,-d,z),(w,d*.72,z),(-w,d*.72,z)]
        faces=[(0,3,2,1),(4,5,6,7)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
        self.mesh('wrap-apron-skirt',verts,faces,'blue','apron')
        self.box('apron-waist',(0,-depth*.035,ztop-.008),(width*1.84,depth*1.62,.035),'blue',.008,role='apron')
        self.box('apron-pocket',(0,-depth-.006,(zbottom+ztop)/2+.012),(.115,.016,.052),'blue',.008,role='apron')
        for sign in (-1,1):
            self.box('apron-back-tie-'+str(sign),(sign*.045,depth*.77,ztop-.015),(.10,.025,.025),'blue',.006,rot=(0,0,sign*.2),role='apron')
    def build(self):
        chunky=self.id=='C'
        if chunky:
            leg_top=.30;torso_top=.535;head_bottom=.58;head_height=.48;head_width=.56;head_depth=.48
            head_y=.005;hat_base=1.135;hair_top=1.115;arm_top=.502;elbow=.397;hand_z=.315
            waist=.355;apron_bottom=.232;apron_width=.205;apron_depth=.177
            torso_rings=[(.285,.172,.137,.122),(.355,.192,.163,.140),(.455,.212,.152,.143),(.535,.209,.117,.112)]
            boot_height=.139;trouser_width=.151;body_depth=.303
        else:
            leg_top=.385;torso_top=.675;head_bottom=.72;head_height=.43;head_width=.51;head_depth=.42
            head_y=.001;hat_base=1.225;hair_top=1.205;arm_top=.64;elbow=.517;hand_z=.405
            waist=.435;apron_bottom=.295;apron_width=.191;apron_depth=.155
            torso_rings=[(.375,.161,.121,.112),(.445,.177,.135,.125),(.585,.195,.130,.122),(.675,.203,.111,.102)]
            boot_height=.153;trouser_width=.145;body_depth=.26
        lower_body_drop=.15
        for sign in (-1,1):
            side='L' if sign<0 else 'R';x=sign*.115
            # Minimal matching-color toe ends, no boot shafts, cuffs or stacked soles.
            self.box('minimal-foot-'+side,(x,-.020,.0215),(.148,.170,.043),'navy',.012,role='shoe')
            leg_bottom=.025;actual_leg_top=leg_top-lower_body_drop
            self.box('short-trouser-'+side,(x,.005,(leg_bottom+actual_leg_top)/2),(trouser_width,.157,actual_leg_top-leg_bottom),'navy',.012,role='leg')
        self.box('hips',(0,.006,leg_top-.015),(.322,.248,.13),'navy',.027,role='pelvis')
        self.torso(torso_rings)
        self.apron(apron_bottom,waist,apron_width,apron_depth)
        self.box('neck',(0,.005,torso_top+.031),(.126,.130,.09),'skin',.027,role='neck')
        for sign in (-1,1):
            shoulder=(sign*.198,.004,arm_top);elbow_pos=(sign*.249,-.002,elbow)
            cuff=(sign*.267,-.023,hand_z+.046)
            self.sleeve('upper-sleeve-'+str(sign),shoulder,elbow_pos,.065,.057,'white')
            self.sleeve('fore-sleeve-'+str(sign),elbow_pos,cuff,.057,.048,'white')
            self.box('relaxed-palm-'+str(sign),(sign*.267,-.025,hand_z),(.09,.103,.104),'skin',.023,rot=(0,sign*-.10,0),role='hand')
            self.box('thumb-'+str(sign),(sign*.229,-.064,hand_z+.018),(.035,.046,.054),'skin',.013,role='hand')
        # Pointed white collars and a thick red tied kerchief hold Lena's identity.
        for sign in (-1,1):
            self.box('collar-'+str(sign),(sign*.054,-.123,torso_top-.010),(.09,.029,.073),'white',.010,rot=(0,sign*.18,0),role='costume')
        scarf_z=torso_top-.050
        self.box('kerchief-knot',(0,-.150,scarf_z),(.056,.055,.058),'red',.014,role='costume')
        for sign in (-1,1):
            self.box('kerchief-tail-'+str(sign),(sign*.035,-.157,scarf_z-.050),(.045,.028,.085),'red',.007,rot=(0,sign*.28,0),role='costume')
        for sign in (-1,1):
            self.ico('coat-button-'+str(sign),(sign*.072,-.148,waist+.055),(.009,.007,.009),'white',role='costume')
        # C has added physical occiput, cheek, temple and torso depth; camera is identical.
        head_mid=head_bottom+head_height/2
        self.box('head',(0,head_y,head_mid),(head_width,head_depth,head_height),'skin',.105,role='head',segments=6)
        front=head_y-head_depth/2
        ear_x=head_width/2+.013
        for sign in (-1,1):
            self.box('ear-'+str(sign),(sign*ear_x,.013,head_mid-.020),(.058,.104,.119),'skin',.024,role='head')
            eye_z=head_bottom+head_height*.54;eye_x=.103 if chunky else .095
            self.ico('eye-'+str(sign),(sign*eye_x,front-.008,eye_z),(.023,.012,.034),'eye',role='face',subdivisions=2)
            self.ico('eye-glint-'+str(sign),(sign*eye_x-.004,front-.019,eye_z+.009),(.006,.004,.009),'white',role='face',subdivisions=1)
            self.box('eyebrow-'+str(sign),(sign*(eye_x+.002),front-.006,eye_z+.073),(.067,.017,.017),'hair',.004,rot=(0,sign*.12,0),role='face',segments=1)
            self.ico('blush-'+str(sign),(sign*head_width*.325,front-.007,head_bottom+head_height*.335),(.037,.009,.020),'blush',role='face')
        nose_z=head_bottom+head_height*.40
        self.box('nose',(0,front-.020,nose_z),(.059,.047,.051),'skin',.018,role='face')
        mouth_z=head_bottom+head_height*.235
        self.mesh('smile',[(-.044,front-.014,mouth_z+.011),(0,front-.019,mouth_z-.007),(.044,front-.014,mouth_z+.011),(.036,front-.017,mouth_z-.009),(0,front-.022,mouth_z-.021),(-.036,front-.017,mouth_z-.009)],[(0,1,4,5),(1,2,3,4)],'eye','face')
        # Rounded scalp and occiput, with overlapping sculpted curl groups.
        # Real depth on all sides; no box cap or front-only hair strip.
        def curl(name, location, radius, shade='hair', phase=0.):
            obj=self.ico(name,location,radius,shade,role='hair',subdivisions=2)
            centre=Vector(location)
            for vertex in obj.data.vertices:
                q=vertex.co-centre
                # Small broad lobes avoid identical beads without noisy micro-detail.
                angle=math.atan2(q.y/max(radius[1],.001),q.x/max(radius[0],.001))
                wave=1.+.035*math.sin(3.*angle+phase)
                vertex.co=centre+q*wave
            for polygon in obj.data.polygons:polygon.use_smooth=True
            return obj
        hair_width=.292 if chunky else .272
        hair_depth=.255 if chunky else .232
        curl('rounded-crown',(0,.025,head_bottom+head_height*.89),
             (hair_width,hair_depth,.157),'hair')
        curl('rounded-occiput',(0,.160 if chunky else .138,head_bottom+head_height*.62),
             (.243 if chunky else .223,.155,.201),'hair')
        # Staggered back rows follow an oval skull; the lower row wraps the nape.
        for row,(fraction,spread,depth) in enumerate(((.52,.205,.250),(.75,.221,.241),(.94,.200,.219))):
            if not chunky:depth-=.020;spread-=.013
            for i,t in enumerate((-1.,-.50,0.,.50,1.)):
                x=t*spread
                y=depth-.068*abs(t)**1.7
                z=head_bottom+head_height*fraction+.016*math.cos(i*1.8+row)
                curl('back-curl-%s-%s'%(row,i),(x,y,z),(.078,.068,.075),
                     '563027' if (i+row)%3==0 else 'hair',i+row*.7)
        # Temple curls overlap the fringe and back instead of forming straight rails.
        for sign in (-1,1):
            for j,(y,fraction,radius) in enumerate(((-.086,.83,.059),(.023,.77,.062),(.115,.71,.061),(.178,.62,.057))):
                x=sign*(.265 if chunky else .246)
                curl('temple-curl-%s-%s'%(sign,j),(x,y,head_bottom+head_height*fraction),
                     (radius,.075,.083),'563027' if j==1 else 'hair',j*.9+sign)
            curl('side-crown-'+str(sign),(sign*(.246 if chunky else .228),.045,head_bottom+head_height*1.005),
                 (.072,.111,.078),'hair',sign)
        # Uneven overlapping fringe: larger central locks, shorter corner curls.
        for i,(x,fraction,rx,rz) in enumerate(((-.224,.93,.063,.065),(-.136,.90,.080,.077),(-.045,.94,.082,.070),(.049,.91,.084,.078),(.143,.94,.077,.070),(.225,.96,.059,.062))):
            if not chunky:x*=.93
            curl('fringe-curl-'+str(i),(x,front+.006,head_bottom+head_height*fraction),
                 (rx,.071,rz),'5A3329' if i in (1,4) else 'hair',i*.8)
        self.box('toque-band',(0,.009,hat_base),(.553 if chunky else .528,.458 if chunky else .413,.088),'white',.013,role='hat')
        for row,y in enumerate((-.096,.096)):
            for i,x in enumerate((-.166,0,.166)):
                h=(.218 if i!=1 else .257)+(row*.012)
                self.box('toque-puff-'+str(row)+'-'+str(i),(x,y,hat_base+.028+h/2),(.201,.218,h),'white',.032,rot=(0,(-.055 if i==0 else .055 if i==2 else 0),0),role='hat')
        # Shorten actual legs and lower the intact upper body by the removed boot height.
        # This changes native anatomy, never the finished sprite or art-camera projection.
        for part in self.parts:
            if part.get('anatomyRole') not in ('shoe','leg'):
                for vertex in part.data.vertices:vertex.co.z-=lower_body_drop
        self.anatomy={'hairRevision':'Rounded crown and occiput; staggered overlapping smooth curls, fuller temples and back; softened cheek corners.','selectedScale':'125','minimalFootHeight':.043,'lowerBodyDrop':lower_body_drop,'footwear':'Tiny navy toe ends; no boots, cuffs or stacked soles.',
                      'legTop':leg_top-lower_body_drop,'torsoTop':torso_top-lower_body_drop,'headBottom':head_bottom-lower_body_drop,'headWidth':head_width,'headDepth':head_depth,'headHeight':head_height,
                      'torsoDepth':body_depth,'hatBandHeight':hat_base-lower_body_drop,'pose':'relaxed arms, both soles planted, no held food',
                      'designNotes':'Deeper occiput, broader cheeks, rounder belly/back and shorter exposed legs.' if chunky else 'Playful enlarged head, moderate side depth and short but visible trousers.'}
        bpy.context.view_layer.update()
        return self


def geometry_receipt(collection):
    deps=bpy.context.evaluated_depsgraph_get();objects=[];points=[]
    for o in sorted(collection.all_objects,key=lambda o:o.name):
        if o.type!='MESH' or o.hide_render:continue
        e=o.evaluated_get(deps);me=e.to_mesh()
        try:
            local=[vec(v.co) for v in me.vertices]
            world=[vec(e.matrix_world@v.co) for v in me.vertices];points += world
            objects.append({'id':o.name,'role':o.get('anatomyRole'),'localVertices':local,'worldVertices':world,
                            'faces':[list(p.vertices) for p in me.polygons],'worldMatrix':mat_rows(e.matrix_world),
                            'nativeMeshHash':canonical_hash({'vertices':[vec(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons]})})
        finally:e.to_mesh_clear()
    mins=[min(p[i] for p in points) for i in range(3)];maxs=[max(p[i] for p in points) for i in range(3)]
    return {'objects':objects,'bounds':{'min':mins,'max':maxs,'dimensions':[maxs[i]-mins[i] for i in range(3)]},
            'geometryHash':canonical_hash([{'id':o['id'],'vertices':o['localVertices'],'faces':o['faces']} for o in objects]),
            'placementsHash':canonical_hash([{'id':o['id'],'worldMatrix':o['worldMatrix']} for o in objects])}


def materials_receipt(collection):
    mats={m.name:m for o in collection.all_objects if o.type=='MESH' for m in o.data.materials if m}
    return [{'name':name,'diffuseColor':vec(m.diffuse_color),'nodes':[{'type':n.type,'name':n.name,'values':{s.name:vec(s.default_value) if hasattr(s.default_value,'__len__') else round(float(s.default_value),9) for s in n.inputs if hasattr(s,'default_value') and isinstance(s.default_value,(float,int)) or hasattr(s,'default_value') and hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str)}} for n in m.node_tree.nodes]} for name,m in sorted(mats.items())]


def render_settings(scene,samples=48):
    scene.render.engine='BLENDER_EEVEE';scene.render.film_transparent=True
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=30
    scene.render.resolution_x=FRAME[0]*SOURCE_SCALE;scene.render.resolution_y=FRAME[1]*SOURCE_SCALE
    scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1.
    scene.render.use_file_extension=True;scene.render.use_persistent_data=True
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0.;scene.view_settings.gamma=1.
    eevee=getattr(scene,'eevee',None)
    for key in ('taa_render_samples','taa_samples'):
        if eevee and hasattr(eevee,key):setattr(eevee,key,samples);break


def lighting(scene,prefix):
    scene.world=bpy.data.worlds.new(prefix+'__World');scene.world.use_nodes=True
    bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.78,.84,1.,1.);bg.inputs['Strength'].default_value=.65
    for name,position,energy,size in [('Key',(-3,-4,7),450,5),('Fill',(4,-1,3),175,4),('Rim',(1,4,5),175,3)]:
        data=bpy.data.lights.new(prefix+'__'+name,'AREA');obj=bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj)
        data.energy=energy;data.shape='DISK';data.size=size;obj.location=position;obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()


def configure_camera(scene):
    c=scene.camera;angle=math.radians(ELEVATION)
    c.data.type='ORTHO';c.data.sensor_fit='HORIZONTAL';c.data.ortho_scale=FRAME[0]/CELL
    c.location=(0,-10*math.cos(angle),10*math.sin(angle));c.rotation_euler=(-c.location).to_track_quat('-Z','Y').to_euler();c.data.shift_x=c.data.shift_y=0.
    scene.view_layers[0].update()
    def px(point):
        v=world_to_camera_view(scene,c,Vector(point));return Vector((v.x*scene.render.resolution_x,(1-v.y)*scene.render.resolution_y))
    origin=px((0,0,0));c.data.shift_x=1.;scene.view_layers[0].update();dx=px((0,0,0)).x-origin.x;c.data.shift_x=(ROOT[0]*SOURCE_SCALE-origin.x)/dx
    c.data.shift_y=1.;scene.view_layers[0].update();dy=px((0,0,0)).y-origin.y;c.data.shift_y=(ROOT[1]*SOURCE_SCALE-origin.y)/dy;scene.view_layers[0].update()
    origin=px((0,0,0));vectors={key:vec(px(point)-origin) for key,point in [('unitX',(1,0,0)),('unitDepth',(0,-1,0)),('unitHeight',(0,0,1))]}
    if (origin-Vector((ROOT[0]*SOURCE_SCALE,ROOT[1]*SOURCE_SCALE))).length>.05:raise RuntimeError('Root camera shift failed')
    if abs(vectors['unitX'][0]-CELL*SOURCE_SCALE)>.05:raise RuntimeError('X camera calibration failed')
    if abs(vectors['unitDepth'][1]-CELL*SOURCE_SCALE*math.sin(angle))>.05:raise RuntimeError('Depth camera calibration failed')
    if abs(vectors['unitHeight'][1]+CELL*SOURCE_SCALE*math.cos(angle))>.05:raise RuntimeError('Height camera calibration failed')
    projection=c.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=scene.render.resolution_x,y=scene.render.resolution_y,scale_x=1.,scale_y=1.)
    return {'projection':'character-orthographic','cellSize':CELL,'sourceScale':SOURCE_SCALE,'frameSize':FRAME,'root':ROOT,'renderResolution':[scene.render.resolution_x,scene.render.resolution_y],
            'camera':{'type':'orthographic','elevationDegrees':ELEVATION,'worldMatrix':mat_rows(c.matrix_world),'projectionMatrix':mat_rows(projection),'pixelAspect':[1.,1.],'orthoScale':c.data.ortho_scale,'sensorFit':'HORIZONTAL','shift':[c.data.shift_x,c.data.shift_y]},
            'calibration':{'root':vec(origin),**vectors},'calibrationLogical':{'root':vec(origin/SOURCE_SCALE),**{k:[v/SOURCE_SCALE for v in values] for k,values in vectors.items()}}}


def projected_bounds(scene,geometry):
    values=[]
    for o in geometry['objects']:
        for p in o['worldVertices']:
            v=world_to_camera_view(scene,scene.camera,Vector(p));values.append([v.x*FRAME[0],(1-v.y)*FRAME[1]])
    minimum=[min(p[i] for p in values) for i in range(2)];maximum=[max(p[i] for p in values) for i in range(2)]
    return {'min':minimum,'max':maximum,'dimensions':[maximum[i]-minimum[i] for i in range(2)]}


def set_pose(scene,manifest,variant,factor=1.,direction='S'):
    for candidate in manifest['variants']:
        col=bpy.data.collections[candidate['source']['collection']];col.hide_render=candidate['id']!=variant['id'];col.hide_viewport=candidate['id']!=variant['id']
    root=bpy.data.objects[variant['source']['root']];root.location=(0,0,0);root.scale=(factor,)*3;root.rotation_euler=(0,0,DIRECTIONS[direction])
    scene.view_layers[0].update()
    return bpy.data.collections[variant['source']['collection']]


def create_study(runtime,output_dir='/private/tmp/sushi33-bc-study',keep_scene=False):
    output=Path(output_dir).resolve();output.mkdir(parents=True,exist_ok=True);project=output/'character-scale-study.blend'
    if project.exists():raise FileExistsError('Use a new output folder: '+str(project))
    before=production_snapshot(runtime);original_filepath=bpy.data.filepath
    original_scene=bpy.context.scene;original_frame=original_scene.frame_current
    original_selection=[o.name for o in bpy.context.selected_objects];original_active=bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None
    prefix='S33 B C Study '+uuid.uuid4().hex[:8];scene=bpy.data.scenes.new(prefix)
    scene['role']='Isolated new static B and C proportions; production remains unchanged'
    manifest={'schemaVersion':1,'title':'B Playful / C Chunky native proportion and scale comparison','status':'models-authored-capture-pending',
              'cellSize':CELL,'sourceScale':SOURCE_SCALE,'frameSize':FRAME,'root':ROOT,'projection':'character-orthographic',
              'camera':{'elevationDegrees':ELEVATION,'pixelAspect':[1,1],'projection':'character-orthographic'},
              'selectedScale':'125','revision':3,'scales':[{'id':i,'factor':v,'label':i+'%'} for i,v in SCALES],'directions':['S','E','N','W'],
              'scene':scene.name,'nativeProject':project.name,'createdAtUnix':time.time(),'sourceScriptSHA256':file_hash(__file__),
              'sourceConcept':'../../design/art-directions/character-proportions-v1.png',
              'productionPresentationHashBefore':before,'userLiveFileBefore':original_filepath,
              'notes':['New static editable native anatomy, not resized finished sprites or a whole-body squash.',
                       'Uniform world scaling 1.0 / 1.25 / 1.5 with common fixed frame, ground root, camera, lighting and material colors.',
                       'One tile means full horizontal silhouette width and physical XY extent; head and hat can rise above the tile.',
                       'Ordinary 35 degree character camera is retained. Ground tile guides on the review site use the square game layout.',
                       'Standing still comparison only; no animation was requested or captured.',
                       'Revision3: fuller rounded hair crown and occiput, staggered curls, softened cheek corners; user selected125percent. Revision2 removed bulky boots; tiny matching-color foot ends and shorter actual leg stubs. Intact upper body lowered by0.15cells; camera/proportions/scales unchanged.'],
              'variants':[]}
    try:
        with activate(scene):
            render_settings(scene);lighting(scene,prefix)
            c=bpy.data.objects.new(prefix+'__Camera',bpy.data.cameras.new(prefix+'__Camera'));scene.collection.objects.link(c);scene.camera=c
            configure_camera(scene)
            for ident in ('B','C'):
                model=StaticCharacter(scene,prefix,ident).build()
                variant={'id':ident,'name':ident+' · '+('Playful' if ident=='B' else 'Chunky'),
                         'description':model.anatomy['designNotes'],'frameSize':FRAME,'root':ROOT,'gridBounds':[-.5,-.5,1,1],
                         'source':{'collection':model.collection.name,'root':model.root.name,'editableStaticMesh':True,'pose':model.anatomy['pose']},
                         'anatomy':model.anatomy,'scales':{}}
                manifest['variants'].append(variant)
            for variant in manifest['variants']:
                base_collection=set_pose(scene,manifest,variant)
                base=geometry_receipt(base_collection);variant['source']['geometryHash']=base['geometryHash'];variant['baseBounds']=base['bounds']
                variant['source']['materialsHash']=canonical_hash(materials_receipt(base_collection))
                variant['source']['materials']=materials_receipt(base_collection)
                if max(base['bounds']['dimensions'][:2])>1/1.5:raise RuntimeError('Authored model exceeds one-cell maximum at 150%: '+variant['id'])
                for scale_id,factor in SCALES:
                    rec={'factor':factor,'images':{},'cameras':{},'geometry':{},'heightTiles':0.,'projectedWidthTiles':0.,'footprint':{'width':0.,'depth':0.},'fitsOneTile':True}
                    for direction in DIRECTIONS:
                        collection=set_pose(scene,manifest,variant,factor,direction)
                        geometry=geometry_receipt(collection);bounds=geometry['bounds'];pb=projected_bounds(scene,geometry)
                        width,depth=bounds['dimensions'][:2]
                        rec['footprint']['width']=max(rec['footprint']['width'],width);rec['footprint']['depth']=max(rec['footprint']['depth'],depth)
                        rec['heightTiles']=max(rec['heightTiles'],pb['dimensions'][1]/CELL);rec['projectedWidthTiles']=max(rec['projectedWidthTiles'],pb['dimensions'][0]/CELL)
                        fits=max(width,depth,pb['dimensions'][0]/CELL)<=1.+1e-6 and min(bounds['min'][:2])>=-.5-1e-6 and max(bounds['max'][:2])<=.5+1e-6
                        rec['fitsOneTile']=rec['fitsOneTile'] and fits
                        if not fits:raise RuntimeError('One-tile bound exceeded: '+variant['id']+'/'+scale_id+'/'+direction)
                        rec['images'][direction]='sprites/'+variant['id']+'/'+scale_id+'/'+direction+'.png'
                        rec['cameras'][direction]='cameras/'+variant['id']+'/'+scale_id+'/'+direction+'.json'
                        rec['geometry'][direction]='geometry/'+variant['id']+'/'+scale_id+'/'+direction+'.json'
                    variant['scales'][scale_id]=rec
                set_pose(scene,manifest,variant)
            set_pose(scene,manifest,manifest['variants'][0]);configure_camera(scene)
            after=production_snapshot(runtime);manifest['productionPresentationHashAfter']=after
            if before!=after:raise RuntimeError('Production source snapshot changed')
            if bpy.data.filepath!=original_filepath or original_scene.frame_current!=original_frame:raise RuntimeError('Live user project/frame changed')
            bpy.data.libraries.write(str(project),{scene},fake_user=True,compress=True)
            manifest['nativeProjectSHA256']=file_hash(project);write_json(output/'study.json',manifest)
    finally:
        with activate(original_scene):
            for o in bpy.context.selected_objects:o.select_set(False)
            for name in original_selection:
                o=bpy.data.objects.get(name)
                if o and o.name in bpy.context.view_layer.objects:o.select_set(True)
            if original_active and original_active in bpy.context.view_layer.objects:bpy.context.view_layer.objects.active=bpy.data.objects[original_active]
        if not keep_scene:
            objects=list(scene.objects);collections=[bpy.data.collections[v['source']['collection']] for v in manifest['variants']]
            bpy.data.scenes.remove(scene)
            for col in collections:bpy.data.collections.remove(col)
            for o in objects:
                if o.name in bpy.data.objects:bpy.data.objects.remove(o,do_unlink=True)
    return {'manifest':str(output/'study.json'),'project':str(project),'scene':scene.name if keep_scene else None,'variants':2,'captures':24,
            'productionUnchanged':before==manifest.get('productionPresentationHashAfter'),
            'measurements':{v['id']:{i:{k:r[k] for k in ('footprint','heightTiles','projectedWidthTiles','fitsOneTile')} for i,r in v['scales'].items()} for v in manifest['variants']}}


def png_size(path):
    data=Path(path).read_bytes()[:24]
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Not a PNG')
    return list(struct.unpack('>II',data[16:24]))


def capture_study(manifest_path,variants=None,scales=None,directions=None,limit=None):
    manifest_path=Path(manifest_path).resolve();output=manifest_path.parent;manifest=json.loads(manifest_path.read_text())
    expected=(output/manifest['nativeProject']).resolve()
    if Path(bpy.data.filepath).resolve()!=expected or file_hash(expected)!=manifest['nativeProjectSHA256']:raise RuntimeError('Load exact native study .blend first')
    scene=bpy.data.scenes[manifest['scene']];completed=0
    with activate(scene):
        render_settings(scene)
        for variant in manifest['variants']:
            if variants and variant['id'] not in variants:continue
            for scale_id,factor in SCALES:
                if scales and scale_id not in scales:continue
                rec=variant['scales'][scale_id]
                for direction in DIRECTIONS:
                    if directions and direction not in directions:continue
                    collection=set_pose(scene,manifest,variant,factor,direction);camera=configure_camera(scene)
                    geometry=geometry_receipt(collection)
                    if geometry['geometryHash']!=variant['source']['geometryHash']:raise RuntimeError('Authored geometry changed')
                    material_hash=canonical_hash(materials_receipt(collection))
                    if material_hash!=variant['source']['materialsHash']:raise RuntimeError('Material colors changed')
                    projected=projected_bounds(scene,geometry)
                    if projected['min'][0]<4 or projected['min'][1]<4 or projected['max'][0]>FRAME[0]-4 or projected['max'][1]>FRAME[1]-4:raise RuntimeError('Capture frame clips character')
                    geometry.update(variantId=variant['id'],scaleId=scale_id,factor=factor,direction=direction,rootWorldMatrix=mat_rows(bpy.data.objects[variant['source']['root']].matrix_world),projectedBoundsLogical=projected,materialsHash=material_hash)
                    geometry_path=output/rec['geometry'][direction];write_json(geometry_path,geometry)
                    image_path=output/rec['images'][direction];image_path.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(image_path)
                    bpy.ops.render.render(write_still=True,scene=scene.name)
                    dimensions=png_size(image_path)
                    if dimensions!=[n*SOURCE_SCALE for n in FRAME]:raise RuntimeError('Native PNG dimensions differ')
                    camera.update(variantId=variant['id'],scaleId=scale_id,factor=factor,direction=direction,geometryHash=geometry['geometryHash'],placementsHash=geometry['placementsHash'],materialsHash=material_hash,nativeProjectSHA256=manifest['nativeProjectSHA256'],
                                  geometry={'path':rec['geometry'][direction],'sha256':file_hash(geometry_path),'bounds':geometry['bounds'],'projectedBoundsLogical':projected},
                                  png={'path':rec['images'][direction],'dimensions':dimensions,'sha256':file_hash(image_path),'sourceScale':SOURCE_SCALE})
                    write_json(output/rec['cameras'][direction],camera)
                    completed+=1;print('S33_BC_CAPTURE '+variant['id']+'/'+scale_id+'/'+direction,flush=True)
                    if limit and completed>=limit:return {'captures':completed,'limited':True}
    manifest['status']='captured' if not variants and not scales and not directions else 'partial-capture-selection';manifest['capturedAtUnix']=time.time();write_json(manifest_path,manifest)
    return {'captures':completed,'manifest':str(manifest_path),'status':manifest['status']}


if __name__=='__main__' and '--capture' in sys.argv:
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture',action='store_true');parser.add_argument('--manifest',required=True)
    parser.add_argument('--variants',nargs='*');parser.add_argument('--scales',nargs='*');parser.add_argument('--directions',nargs='*');parser.add_argument('--limit',type=int)
    options=parser.parse_args(args);print(json.dumps(capture_study(options.manifest,options.variants,options.scales,options.directions,options.limit)))
