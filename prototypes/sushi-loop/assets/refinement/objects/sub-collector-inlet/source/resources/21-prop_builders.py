"""Issue 33 approved low-poly world props. Authoring source, not a render proxy.
Canonical coordinates X=right, -Y=depth toward viewer, Z=up; one unit per tile.
Call create_asset(id), then result['pose'](clip, normalized_time) for capture.
All geometry is native and all animation can be baked to editable object actions.
No scene deletion, camera changes, render operations or external I/O are performed.
"""
import bpy
import math
import json
import random
from mathutils import Vector

PALETTE = {
 'wood':'B77B3C','wood_light':'D99F55','wood_dark':'704727','wood_end':'E7B36B',
 'blue':'2567C1','blue_light':'3B8BDF','blue_dark':'153B78','navy':'253B62',
 'cream':'F7DFA6','sand':'D8B477','chalk':'FFF1D0','board':'253C48',
 'green':'26864B','leaf':'42B54E','leaf_light':'78D34D','teal':'239D91',
 'yellow':'FFC638','yellow_light':'FFE577','gold':'D99819','red':'DC4A42',
 'rock':'315B8D','rock_light':'5483B2','rock_dark':'224165','metal':'6B8491',
 'metal_light':'A3B7BF','metal_dark':'3D5265','coral':'F26484','purple':'885DB4',
 'cyan':'56DDF0','aqua':'26B4D2','orange':'F38C3F','white':'F6F3DF',
}

def _linear(v):
    return v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4

def mat(name, color=None, emission=0.0):
    """Shared matte materials with correct sRGB-to-linear conversion."""
    key='S33_'+name
    m=bpy.data.materials.get(key)
    if m: return m
    h=(color or PALETTE.get(name,name)).lstrip('#')
    rgb=tuple(_linear(int(h[i:i+2],16)/255) for i in (0,2,4))
    m=bpy.data.materials.new(key); m.diffuse_color=(*rgb,1)
    m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*rgb,1)
    p.inputs['Roughness'].default_value=.82
    p.inputs['Metallic'].default_value=.0
    if 'Specular IOR Level' in p.inputs: p.inputs['Specular IOR Level'].default_value=.24
    if emission:
        if 'Emission Color' in p.inputs: p.inputs['Emission Color'].default_value=(*rgb,1)
        elif 'Emission' in p.inputs: p.inputs['Emission'].default_value=(*rgb,1)
        if 'Emission Strength' in p.inputs: p.inputs['Emission Strength'].default_value=emission
    return m

class Builder:
    def __init__(self, asset_id):
        self.id=asset_id; self.parts={}; self.sockets={}; self.motion={}
        self.collection=bpy.data.collections.new('S33_PROP_'+asset_id)
        bpy.context.scene.collection.children.link(self.collection)
        self.root=bpy.data.objects.new(asset_id+'__root',None)
        self.collection.objects.link(self.root)
        self.root.empty_display_type='PLAIN_AXES'; self.root.empty_display_size=.22
        self.footprint=(1,1); self.height=1.; self.layers=['world']; self.notes=[]
    def add(self,obj,name,color):
        obj.name=self.id+'__'+name
        for c in list(obj.users_collection): c.objects.unlink(obj)
        self.collection.objects.link(obj); obj.parent=self.root
        if color: obj.data.materials.append(mat(color))
        self.parts[name]=obj
        return obj
    def box(self,name,loc,size,color='wood',bevel=.025,rot=(0,0,0)):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
        o=self.add(bpy.context.object,name,color);o.dimensions=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        o.rotation_euler=rot
        if bevel:
            mod=o.modifiers.new('Hand-cut bevel','BEVEL');mod.width=bevel;mod.segments=1
            mod.affect='EDGES'
        return o
    def cyl(self,name,loc,radius,depth,color='wood',vertices=8,rot=(0,0,0),r2=None):
        if r2 is None:
            bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
        else:
            bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=radius,radius2=r2,depth=depth,location=loc)
        o=self.add(bpy.context.object,name,color);o.rotation_euler=rot
        return o
    def ico(self,name,loc,scale,color='rock',subdiv=1):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv,radius=1,location=loc)
        o=self.add(bpy.context.object,name,color);o.scale=scale;return o
    def mesh(self,name,verts,faces,color):
        me=bpy.data.meshes.new(self.id+'__'+name);me.from_pydata(verts,[],faces);me.update()
        o=bpy.data.objects.new(name,me); self.collection.objects.link(o);o.parent=self.root
        o.name=self.id+'__'+name; o.data.materials.append(mat(color));self.parts[name]=o;return o
    def beam(self,name,a,b,width,color='wood',depth=None):
        a,b=Vector(a),Vector(b);d=b-a
        o=self.box(name,(a+b)/2,(width,depth or width,d.length),color,.012)
        o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
    def socket(self,name,loc):
        self.sockets[name]=list(loc)
    def finish(self,clips=None):
        clips=clips or {'idle':{'frames':12,'fps':12,'loop':True,'static':True}}
        baseline={n:(o.location.copy(),o.rotation_euler.copy(),o.scale.copy(),o.hide_render) for n,o in self.parts.items()}
        def reset():
            for n,o in self.parts.items():
                l,r,s,h=baseline[n];o.location=l;o.rotation_euler=r;o.scale=s;o.hide_render=h
        def pose(clip='idle',t=0.0):
            reset()
            fn=self.motion.get(clip) or self.motion.get('idle')
            if fn:
                loop=clips.get(clip,{}).get('loop',False)
                fn(float(t)%1.0 if loop else max(0.0,min(1.0,float(t))))
        self.root['asset_id']=self.id;self.root['family']='issue-33-world-props'
        self.root['footprint_cells']=json.dumps(self.footprint)
        self.root['ground_root']=json.dumps([0,0,0]);self.root['visual_height']=self.height
        self.root['sockets']=json.dumps(self.sockets);self.root['directions']=json.dumps(['N','E','S','W'])
        self.root['animation_recipes']=json.dumps(clips);self.root['axis_convention']='X=x; depth=-Y; height=Z'
        self.root['source']='prop_builders.py';self.root['notes']=json.dumps(self.notes)
        return {'root':self.root,'collection':self.collection,'parts':self.parts,'footprint':list(self.footprint),'height':self.height,'directions':['N','E','S','W'],'sockets':self.sockets,'clips':clips,'pose':pose,'reset':reset,'notes':self.notes}


def build_stool(b,blue=False):
    b.height=.64
    for x in (-.22,.22):
        for y in (-.22,.22):
            b.beam('leg_%s_%s'%(x,y),(x*1.13,y*1.13,.035),(x,y,.53),.095,'wood_dark')
    b.beam('rung_front',(-.23,-.23,.25),(.23,-.23,.25),.055,'wood')
    b.beam('rung_back',(-.23,.23,.25),(.23,.23,.25),.055,'wood')
    b.beam('rung_left',(-.23,-.23,.28),(-.23,.23,.28),.055,'wood')
    b.beam('rung_right',(.23,-.23,.28),(.23,.23,.28),.055,'wood')
    b.box('seat',(0,0,.58),(.66,.66,.14),'blue' if blue else 'wood_light',.035)
    if blue:b.box('cushion_top',(0,0,.66),(.62,.62,.05),'blue_light',.03)
    else:
        for y in (-.105,.105):b.box('seat_seam_'+str(y),(0,y,.652),(.59,.012,.004),'wood',0)
    b.socket('seat',(0,0,.685 if blue else .655));b.socket('occupant_ground',(0,0,0))
    b.notes.append('Backless stool. Seat socket separate from ground root; no baked occupant.')
    return b.finish()


def build_blackboard(b):
    b.height=1.02
    for x in (-.29,.29):
        b.beam('front_leg_'+str(x),(x,-.27,.025),(x,.07,.98),.075,'wood')
        b.beam('back_leg_'+str(x),(x,.29,.025),(x,.08,.95),.065,'wood_dark')
    b.box('blackboard',(0,-.055,.59),(.55,.08,.62),'board',.008)
    for x in (-.31,.31):b.box('frame_side_'+str(x),(x,-.09,.59),(.075,.09,.74),'wood_light',.014)
    for z in (.24,.94):b.box('frame_end_'+str(z),(0,-.09,z),(.68,.09,.075),'wood_light',.014)
    b.box('chalk_ledge',(0,-.18,.24),(.65,.17,.07),'wood',.015)
    # Three modeled recipe tokens sit on the actual board plane, never a fixed photograph.
    for i,(x,c) in enumerate([(-.17,'orange'),(0,'green'),(.17,'wood_dark')]):
        b.cyl('token_plate_'+str(i),(x,-.113,.62),.078,.013,'white',12,(math.pi/2,0,0))
        b.box('token_recipe_'+str(i),(x,-.129,.625),(.095,.025,.07),c,.01)
    for i,w in enumerate([.29,.37,.21]):b.box('chalk_dash_'+str(i),(-.04,-.103,.45-i*.06),(w,.008,.012),'chalk',.002)
    def shake(t):
        a=.035*math.sin(t*math.tau)*math.sin(t*math.pi)
        for o in b.parts.values():o.rotation_euler.z+=a
    def selected(t):
        for i in range(3):
            b.parts['token_plate_'+str(i)].scale*=1+.04*math.sin(t*math.tau+i*.3)
    b.motion.update(recipe_change=shake,selected=selected)
    b.socket('recipe_face',(0,-.14,.62))
    return b.finish({'idle':{'frames':1,'fps':12,'loop':False,'static':True},'selected':{'frames':12,'fps':12,'loop':True},'recipe_change':{'frames':12,'fps':12,'loop':False}})


def _plant(b,offset=(0,0,0),scale=1.,prefix='plant'):
    ox,oy,oz=offset
    def p(v):return(ox+v[0]*scale,oy+v[1]*scale,oz+v[2]*scale)
    b.cyl(prefix+'_pot',p((0,0,.19)),.27*scale,.35*scale,'wood',4,r2=.33*scale,rot=(0,0,math.pi/4))
    b.cyl(prefix+'_rim',p((0,0,.37)),.345*scale,.07*scale,'wood_light',4,rot=(0,0,math.pi/4))
    b.box(prefix+'_soil',p((0,0,.408)),(.44*scale,.44*scale,.03*scale),'wood_dark',.01)
    leaves=[]
    branches=[(-.16,.05,.86,-.25,.05,1.15),(.15,.03,.78,.28,.06,1.02),(0,0,.94,.0,.0,1.38),(-.08,-.1,.73,-.2,-.17,.95),(.07,-.1,.62,.18,-.14,.86)]
    for i,(x,y,z,tx,ty,tz) in enumerate(branches):
        b.beam(prefix+'_stem_'+str(i),p((0,0,.40)),p((x,y,z)),.045*scale,'green')
        o=b.ico(prefix+'_leaf_'+str(i),p(((x+tx)/2,(y+ty)/2,(z+tz)/2)),(.12*scale,.095*scale,.25*scale),'leaf_light' if i%2 else 'leaf')
        o.rotation_euler=(0,(tx-x)*1.5,(ty-y));leaves.append(o)
    return leaves

def build_plant(b):
    leaves=_plant(b);b.height=1.45
    def sway(t):
        for i,o in enumerate(leaves):o.rotation_euler.y+=.035*math.sin(t*math.tau+i*.7)
    b.motion['idle']=sway
    return b.finish({'idle':{'frames':24,'fps':12,'loop':True}})


def build_barrel(b):
    b.height=.84
    for i in range(12):
        a=i*math.tau/12
        # Individual coopered planks retain alternating matte faces and readable seams.
        coords=[]
        for z,r in ((.035,.25),(.16,.30),(.66,.30),(.8,.25)):
            coords.extend([(r*math.cos(a-.245),r*math.sin(a-.245),z),(r*math.cos(a+.245),r*math.sin(a+.245),z)])
        faces=[(0,1,3,2),(2,3,5,4),(4,5,7,6)]
        b.mesh('stave_'+str(i),coords,faces,'wood_light' if i%3==0 else 'wood')
    for z in (.16,.66):b.cyl('iron_band_'+str(z),(0,0,z),.313,.065,'blue_dark',12)
    b.cyl('lid',(0,0,.805),.255,.035,'wood_end',12)
    for x in (-.12,.04,.16):b.box('lid_seam_'+str(x),(x,0,.826),(.009,.43,.006),'wood',0)
    return b.finish()


def _crate(b,loc=(0,0,0),size=.7,prefix='crate'):
    x,y,z=loc
    b.box(prefix+'_body',(x,y,z+size/2),(size,size,size),'wood',.02)
    for side in (-1,1):
        for k in (-.35,.35):
            b.box(prefix+'_rail_x'+str(side)+str(k),(x,y+side*(size/2+.012),z+size*(.5+k)),(size,.055,size*.1),'wood_light',.008)
            b.box(prefix+'_rail_y'+str(side)+str(k),(x+side*(size/2+.012),y,z+size*(.5+k)),(.055,size,size*.1),'wood_light',.008)
        b.beam(prefix+'_diagonal_'+str(side),(x-size*.36,y+side*(size/2+.045),z+size*.14),(x+size*.36,y+side*(size/2+.045),z+size*.86),size*.105,'wood_light',.045)
    for i in (-.23,0,.23):b.box(prefix+'_top_slats'+str(i),(x+i*size,y,z+size+.006),(size*.2,size,.018),'wood_end',.006)

def build_crate(b):
    _crate(b);b.height=.73;return b.finish()


def build_lantern(b):
    b.height=1.34
    b.box('plinth',(0,0,.055),(.36,.36,.11),'wood_dark',.02)
    b.box('post',(0,.07,.63),(.1,.1,1.15),'wood',.015)
    b.box('overhang',(0,-.075,1.21),(.12,.41,.1),'wood',.015)
    b.cyl('hanging_hook',(0,-.20,1.13),.025,.13,'metal_dark',8)
    b.cyl('glow_body',(0,-.20,.88),.16,.37,'yellow_light',8)
    for z in (.68,.76,.88,1.,1.07):b.cyl('rib_'+str(z),(0,-.20,z),.176,.025,'gold',8)
    for z in (.66,1.09):b.cyl('cap_'+str(z),(0,-.20,z),.12,.04,'wood_dark',8)
    b.parts['glow_body'].data.materials.clear();b.parts['glow_body'].data.materials.append(mat('lantern_glow','FFD85C',.3))
    def ambient(t):
        # Modeled lantern cage sways together around the hanging point, not the pole.
        phase=.022*math.sin(math.tau*t)
        for n,o in b.parts.items():
            if n.startswith(('glow','rib','cap')):o.location.x+=phase*(1.15-o.location.z)
    b.motion['idle']=ambient
    return b.finish({'idle':{'frames':24,'fps':12,'loop':True}})


def build_sign(b):
    b.height=1.12
    for x in (-.23,.23):b.box('post_'+str(x),(x,.06,.53),(.095,.095,1.06),'wood_dark',.012)
    for i in range(3):b.box('blank_plank_'+str(i),(0,0,.64+i*.13),(.83,.1,.125),'wood_light' if i%2 else 'wood',.012)
    for x in (-.28,.28):
        for z in (.66,.9):b.cyl('nail_'+str(x)+str(z),(x,-.058,z),.014,.012,'metal_dark',6,(math.pi/2,0,0))
    b.notes.append('Blank native wood face, suitable for later game branding without baked title.')
    return b.finish()


def _roof(b,cx,cy,z,width,depth,prefix='roof',color='blue'):
    # Actual ridge/pitch mesh; individual ceramic bars make the silhouette legible.
    verts=[(cx-width/2,cy-depth/2,z),(cx+width/2,cy-depth/2,z),(cx-width/2,cy,z+.35),(cx+width/2,cy,z+.35),(cx-width/2,cy+depth/2,z),(cx+width/2,cy+depth/2,z)]
    b.mesh(prefix+'_structure',verts,[(0,1,3,2),(2,3,5,4)],color)
    for i in range(max(4,int(width/.19))):
        x=cx-width/2+(i+.5)*width/max(4,int(width/.19))
        for side in (-1,1):
            b.beam(prefix+'_tile_'+str(i)+str(side),(x,cy,z+.37),(x,cy+side*depth*.53,z-.015),.15,color if i%2 else 'blue_light',.065)
    b.beam(prefix+'_ridge',(cx-width*.55,cy,z+.40),(cx+width*.55,cy,z+.40),.16,'blue_dark')



def _rubbish(b,extent=(1,1),count=10,seed=4):
    rng=random.Random(seed);pieces=[]
    for i in range(count):
        a=rng.uniform(0,math.tau);r=rng.uniform(.6,1.0)
        loc=(math.cos(a)*extent[0]*r,math.sin(a)*extent[1]*r,.1)
        if i%3==0:o=b.box('rubbish_'+str(i),loc,(.20,.16,.18),'wood_light',.015,rot=(0,0,a))
        elif i%3==1:o=b.ico('rubbish_'+str(i),loc,(.18,.15,.15),'rock_dark')
        else:o=b.cyl('rubbish_'+str(i),loc,.10,.13,'metal_dark',8,rot=(.3,.4,a))
        pieces.append(o)
    return pieces


def _clearance_motion(b,pieces):
    def clear(t):
        for i,o in enumerate(pieces):
            radial=Vector((o.location.x,o.location.y,0));radial.normalize()
            o.location+=radial*(t*.7);o.location.z+=math.sin(t*math.pi)*(.2+.04*i)
            o.rotation_euler.z+=t*(i%3-1)*1.7;o.scale*=max(.005,1-t*.9)
    def highlighted(t):
        for o in pieces:o.scale*=1+.008*math.sin(t*math.tau)
    b.motion.update(clearance=clear,highlighted=highlighted)
    return {'idle':{'frames':1,'fps':12,'loop':False,'static':True},'highlighted':{'frames':12,'fps':12,'loop':True},'clearance':{'frames':18,'fps':12,'loop':False}}


def build_sofa(b):
    b.footprint=(2,2);b.height=1.08
    b.box('base',(0,0,.27),(1.64,.95,.25),'wood_dark',.04)
    for x in (-.63,.63):
        for y in (-.33,.33):b.box('foot_'+str(x)+str(y),(x,y,.10),(.15,.16,.20),'wood',.015)
    b.box('back',(0,.38,.72),(1.74,.26,.73),'red',.065,rot=(.08,0,.025))
    for x in (-.75,.75):b.box('arm_'+str(x),(x,-.02,.59),(.24,1.05,.52),'red',.045)
    for i,x in enumerate((-.43,0,.43)):
        b.box('seat_cushion_'+str(i),(x,-.14,.48),(.42,.74,.22),'coral' if i==1 else 'red',.05,rot=(0,.025*i,.03*(i-1)))
        b.box('back_cushion_'+str(i),(x,.20,.82),(.43,.24,.45),'red',.05,rot=(.08,0,.035*(i-1)))
    b.box('torn_patch',(-.43,-.24,.60),(.14,.13,.015),'wood_end',.005,rot=(0,0,-.2))
    b.beam('exposed_spring',(.27,-.32,.60),(.4,-.2,.68),.025,'metal_dark')
    pieces=_rubbish(b,(.85,.75),9,3)
    b.notes.append('One whole sofa, not a per-cell stamp; 2x2 integer support footprint.')
    return b.finish(_clearance_motion(b,list(b.parts.values())))


def build_car(b):
    b.footprint=(3,2);b.height=1.3
    b.box('chassis',(0,0,.29),(2.37,1.28,.25),'metal_dark',.06)
    b.box('body',(0,0,.52),(2.45,1.30,.45),'blue',.08)
    # Faceted five-window cabin with actual roof and distinct pillars.
    verts=[(-.65,-.63,.68),(.78,-.63,.68),(-.42,-.50,1.17),(.48,-.50,1.17),(-.65,.63,.68),(.78,.63,.68),(-.42,.50,1.17),(.48,.50,1.17)]
    b.mesh('cabin',verts,[(0,1,3,2),(4,6,7,5),(0,2,6,4),(1,5,7,3),(2,3,7,6)],'blue_dark')
    for y in (-.641,.641):
        for i,(a,c) in enumerate([(-.49,-.05),(.05,.59)]):
            b.mesh('side_window_'+str(y)+str(i),[(a,y,.76),(c,y,.76),(c*.76,y*.83,1.09),(a*.76,y*.83,1.09)],[(0,1,2,3)],'aqua')
        b.beam('side_center_pillar_'+str(y),(.0,y,.72),(0,y*.83,1.15),.07,'blue')
        b.box('door_handle_'+str(y),(.26,y,.64),(.19,.025,.04),'metal_light',.01)
    b.box('roof',(0.02,0,1.18),(1.04,1.08,.1),'blue_light',.025,rot=(0,.025,0))
    for x in (-.79,.79):
        for y in (-.68,.68):
            b.cyl('tire_'+str(x)+str(y),(x,y,.30),.30,.19,'metal_dark',12,(math.pi/2,0,0))
            b.cyl('hub_'+str(x)+str(y),(x,y+math.copysign(.103,y),.30),.135,.02,'metal',8,(math.pi/2,0,0))
    for y in (-.40,.40):b.box('headlamp_'+str(y),(-1.235,y,.58),(.025,.24,.15),'cream',.015)
    b.box('front_bumper',(-1.25,0,.32),(.13,1.25,.11),'metal',.018,rot=(0,.05,-.035))
    b.box('broken_hood',(-.96,0,.79),(.55,1.19,.08),'blue_light',.025,rot=(0,-.09,.04))
    b.box('loose_plate',(1.13,-.38,.18),(.46,.4,.05),'metal_light',.01,rot=(0,.3,.2))
    _rubbish(b,(1.25,.78),11,9)
    b.notes.append('Whole wrecked compact car with modeled cabin, windows, wheels, broken hood and supporting rubble. 3x2 support mask.')
    return b.finish(_clearance_motion(b,list(b.parts.values())))


def build_shelf(b):
    b.footprint=(2,2);b.height=1.68
    for x in (-.72,.72):
        for y in (-.30,.30):b.beam('upright_'+str(x)+str(y),(x,y,.02),(x+.08,y,1.58),.10,'wood_dark')
    for j,z in enumerate((.18,.69,1.20,1.57)):
        b.box('shelf_'+str(j),(.04,0,z),(1.64,.79,.095),'wood',.025,rot=(0,.025*(-1 if j%2 else 1),0))
    b.beam('back_brace',(-.69,.34,.13),(.83,.34,1.54),.065,'wood_light')
    rng=random.Random(22)
    for i in range(7):
        x=-.52+(i%3)*.47;z=.38+(i//3)*.51
        o=b.box('stored_box_'+str(i),(x,-.02,z),(.30,.44,.31),'wood_light' if i%2 else 'wood_end',.015,rot=(0,.04*(i%2),rng.uniform(-.12,.12)))
    b.box('fallen_board',(0,-.72,.12),(1.28,.3,.075),'wood_light',.012,rot=(0,.08,.3))
    _rubbish(b,(.82,.8),8,7)
    return b.finish(_clearance_motion(b,list(b.parts.values())))


def _submarine(b,offset=(0,0,0),scale=1.,prefix='sub',equipment=False):
    ox,oy,oz=offset
    def p(v):return(ox+v[0]*scale,oy+v[1]*scale,oz+v[2]*scale)
    b.ico(prefix+'_hull',p((0,0,.40)),(.36*scale,.50*scale,.33*scale),'yellow',2)
    b.ico(prefix+'_belly',p((0,-.03,.27)),(.33*scale,.45*scale,.18*scale),'gold',1)
    # Upper-front canopy normal(0,-.6,.8): visible in both dock and65deg
    # overhead art cameras, rather than reading as a front-facing icon.
    canopy_angle=math.atan2(.6,.8)
    b.cyl(prefix+'_port_rim',p((0,-.25,.66)),.218*scale,.075*scale,'yellow_light',12,(canopy_angle,0,0))
    b.cyl(prefix+'_port_glass',p((0,-.280,.700)),.171*scale,.035*scale,'blue_light',12,(canopy_angle,0,0))
    glint=b.ico(prefix+'_glass_glint',p((-.047,-.303,.735)),(.047*scale,.057*scale,.012*scale),'cyan')
    glint.rotation_euler.x=canopy_angle
    b.cyl(prefix+'_nose_headlight_rim',p((0,-.481,.38)),.080*scale,.048*scale,'gold',8,(math.pi/2,0,0))
    b.cyl(prefix+'_nose_headlight_lens',p((0,-.510,.38)),.057*scale,.020*scale,'yellow_light',8,(math.pi/2,0,0))
    for s in (-1,1):
        b.cyl(prefix+'_side_thruster_'+str(s),p((s*.39,.04,.37)),.14*scale,.40*scale,'red',8,(math.pi/2,0,0))
        b.cyl(prefix+'_thruster_lip_'+str(s),p((s*.39,-.17,.37)),.15*scale,.05*scale,'gold',8,(math.pi/2,0,0))
        b.box(prefix+'_fin_'+str(s),p((s*.37,.30,.39)),(.24*scale,.24*scale,.065*scale),'yellow',.015*scale,rot=(0,0,s*.2))
        b.beam(prefix+'_skid_'+str(s),p((s*.23,-.30,.08)),p((s*.23,.32,.08)),.07*scale,'gold')
        b.beam(prefix+'_strut_'+str(s),p((s*.23,-.10,.08)),p((s*.22,-.08,.24)),.05*scale,'yellow')
    b.cyl(prefix+'_periscope_stem',p((0,.10,.80)),.065*scale,.28*scale,'gold',8)
    b.cyl(prefix+'_periscope_cap',p((0,.10,.95)),.13*scale,.075*scale,'yellow_light',8)
    b.cyl(prefix+'_tail_shaft',p((0,.53,.36)),.045*scale,.18*scale,'metal_dark',8,(math.pi/2,0,0))
    prop=b.box(prefix+'_propeller',p((0,.64,.36)),(.38*scale,.045*scale,.065*scale),'gold',.01*scale)
    for x in (-.16,.16):b.cyl(prefix+'_bolt_'+str(x),p((x,-.502,.33)),.026*scale,.02*scale,'gold',8,(math.pi/2,0,0))
    b.socket(prefix+'_harpoon',p((.24,-.40,.37)));b.socket(prefix+'_collector',p((0,-.53,.21)))
    if equipment:
        b.box(prefix+'_armor_left',p((-.21,-.02,.67)),(.18*scale,.47*scale,.075*scale),'yellow_light',.02*scale)
        b.box(prefix+'_armor_right',p((.21,-.02,.67)),(.18*scale,.47*scale,.075*scale),'yellow_light',.02*scale)
        b.cyl(prefix+'_harpoon_barrel',p((.29,-.25,.66)),.055*scale,.40*scale,'metal_dark',8,(math.pi/2,0,0))
        b.box(prefix+'_harpoon_rail',p((.29,-.08,.67)),(.14*scale,.28*scale,.10*scale),'red',.01*scale)
        b.box(prefix+'_collector_intake',p((0,-.49,.21)),(.28*scale,.19*scale,.14*scale),'metal_dark',.02*scale)
        b.box(prefix+'_collector_lip',p((0,-.59,.21)),(.32*scale,.045*scale,.18*scale),'metal_light',.01*scale)
    return prop


def build_submarine(b,upgraded=False):
    prop=_submarine(b,equipment=upgraded);b.height=1.02
    def idle(t):
        for n,o in b.parts.items():o.location.z+=.018*math.sin(math.tau*t)
        prop.rotation_euler.y+=math.tau*t
    def travel(t):
        for n,o in b.parts.items():
            o.location.z+=.01*math.sin(math.tau*t*2)
            o.location.x+=.012*math.sin(math.tau*t+.37)
        prop.rotation_euler.y+=math.tau*t*2
    def impact(t):
        for o in b.parts.values():o.location.x+=.045*math.sin(t*math.tau*3)*(1-t)
    b.motion.update(idle=idle,travel=travel,impact=impact,protected=idle)
    b.notes.append('Same recognizable yellow ship as the dock. Front toward -Y; rotated N for upward overhead travel. Equipment stays inside 1x1 footprint, separate attachment sockets.')
    return b.finish({k:{'frames':24 if k in ('idle','travel','protected') else 12,'fps':12,'loop':k!='impact'} for k in ('idle','travel','impact','protected')})


def build_equipment(b,kind):
    b.height=.55
    if kind=='hull_panel':
        b.box('plate',(0,0,.18),(.58,.73,.30),'yellow',.07)
        b.box('ridge',(0,0,.35),(.17,.59,.06),'yellow_light',.02)
        for x in (-.22,.22):
            for y in (-.26,.26):b.cyl('rivet_'+str(x)+str(y),(x,y,.34),.025,.025,'gold',8)
    elif kind=='harpoon_mount':
        b.box('base',(0,.1,.10),(.50,.56,.20),'red',.04)
        b.box('rail',(0,0,.26),(.24,.68,.14),'metal',.02)
        b.cyl('barrel',(0,-.18,.34),.08,.65,'metal_dark',8,(math.pi/2,0,0))
        b.cyl('muzzle',(0,-.51,.34),.10,.08,'metal_light',8,(math.pi/2,0,0))
    else:
        b.box('inlet_frame',(0,0,.22),(.62,.50,.43),'metal_light',.04)
        b.box('dark_mouth',(0,-.26,.24),(.43,.025,.27),'metal_dark',.015)
        for x in (-.14,0,.14):b.box('guard_'+str(x),(x,-.28,.24),(.024,.025,.29),'metal',.004)
        b.box('lower_lip',(0,-.34,.075),(.65,.20,.10),'yellow',.025)
    return b.finish()


def build_dock(b,covered=False):
    b.footprint=(3,3);b.height=2.26
    for i in range(12):
        b.box('plank_'+str(i),(-1.375+i*.25,0,.13),(.238,3.,.18),'wood_light' if i%3==0 else 'wood',.012)
    for x in (-1.40,1.40):
        for y in (-1.40,1.40):
            b.cyl('post_'+str(x)+str(y),(x,y,.28),.115,.56,'wood_end',8)
            b.cyl('post_band_'+str(x)+str(y),(x,y,.40),.12,.035,'wood_dark',8)
    b.beam('left_rope',(-1.40,-1.40,.40),(-1.40,1.40,.40),.045,'cream')
    # Workshop is explicitly to the RIGHT of the submarine.
    hx,hy=.67,.37
    b.box('hut',(hx,hy,.86),(1.15,1.35,1.35),'wood',.035)
    for x in (hx-.56,hx+.56):b.box('hut_corner_'+str(x),(x,hy,.88),(.10,1.39,1.43),'wood_dark',.012)
    for j in range(6):b.box('front_plank_'+str(j),(hx-.46+j*.185,hy-.69,.88),(.17,.04,1.29),'wood_light' if j%3==0 else 'wood',.006)
    b.box('door_frame',(hx-.12,hy-.73,.67),(.55,.12,1.12),'wood_dark',.02)
    b.box('door',(hx-.12,hy-.80,.65),(.41,.04,.99),'wood_light',.015)
    b.cyl('door_knob',(hx+.02,hy-.835,.63),.037,.045,'gold',8,(math.pi/2,0,0))
    b.box('window_frame',(hx+.37,hy-.74,1.07),(.25,.08,.34),'wood_dark',.01)
    b.box('window_glow',(hx+.37,hy-.79,1.07),(.19,.02,.26),'yellow_light',.005)
    for x in (hx+.37,):b.box('window_bar',(x,hy-.81,1.07),(.025,.02,.28),'wood',.002)
    b.box('window_cross',(hx+.37,hy-.81,1.07),(.21,.02,.025),'wood',.002)
    _roof(b,hx,hy,1.61,1.55,1.73,'hut_roof','aqua')
    _crate(b,(-.95,.78,.23),.38,'dock_crate')
    prop=_submarine(b,(-.67,-.45,.22),.90,'dock_sub',False)
    # Ring and cleats remain separate readable geometry.
    b.cyl('life_ring',(.99,-.57,.55),.23,.085,'white',12,(math.pi/2,0,0))
    b.cyl('life_ring_hole',(.99,-.62,.55),.125,.03,'wood',12,(math.pi/2,0,0))
    for z in (.34,.76):b.box('life_ring_red_'+str(z),(.99,-.63,z),(.15,.035,.09),'red',.01)
    for x in (-1.1,.1):b.box('cleat_'+str(x),(x,-1.24,.26),(.24,.08,.065),'metal_dark',.012)
    if covered:
        # Pitched, contiguous patchwork tarp. Open front peek holes reveal ship identity.
        verts=[(-1.40,-1.12,1.18),(-.03,-1.12,1.18),(-1.40,.02,1.48),(-.03,.02,1.48),(-1.40,.85,1.04),(-.03,.85,1.04)]
        b.mesh('cover_sheet',verts,[(0,1,3,2),(2,3,5,4)],'sand')
        for i,(x,y,c) in enumerate([(-1.08,-.71,'teal'),(-.56,-.72,'sand'),(-1.04,-.15,'sand'),(-.52,-.16,'blue_dark')]):
            b.box('cover_patch_'+str(i),(x,y,1.30+(y+.71)*.263),(.45,.50,.018),c,.004,rot=(.257,0,0))
        for x in (-1.4,-.03):b.beam('cover_pole_'+str(x),(x,-1.11,.22),(x,-1.11,1.20),.04,'wood_dark')
        b.notes.append('Partial patchwork cover and open front allow identity peek; cover is geometry, no bitmap overlay.')
    def charging(t):
        prop.rotation_euler.y+=math.tau*t
        for n,o in b.parts.items():
            if n.startswith('dock_sub'):o.location.z+=.008*math.sin(t*math.tau)
    def ready(t):
        charging(t)
        b.parts['dock_sub_glass_glint'].scale*=1+.12*math.sin(math.tau*t)
    b.motion.update(charging=charging,ready=ready,idle=charging)
    b.socket('entry',(0,-1.5,.23));b.socket('ship_ground',(-.67,-.45,.22))
    return b.finish({k:{'frames':24,'fps':12,'loop':True} for k in ('charging','ready')})


def _rock_column(b,name,xy,width,depth,z,height,color='rock',seed=0):
    rng=random.Random(seed)
    x,y=xy
    # Eight-sided clipped block. Exact aligned outer extents retain modular pitch.
    clip=min(width,depth)*.17
    ring=[(-width/2+clip,-depth/2),(width/2-clip,-depth/2),(width/2,-depth/2+clip),(width/2,depth/2-clip),(width/2-clip,depth/2),(-width/2+clip,depth/2),(-width/2,depth/2-clip),(-width/2,-depth/2+clip)]
    verts=[(x+vx,y+vy,z) for vx,vy in ring]+[(x+vx,y+vy,z+height+rng.uniform(-.025,.025)) for vx,vy in ring]
    faces=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    o=b.mesh(name,verts,faces,color)
    o.data.materials.append(mat('rock_light'));o.data.materials.append(mat('rock_dark'))
    for poly in o.data.polygons:
        if poly.index==1:poly.material_index=1
        elif poly.index%4==0:poly.material_index=2
    return o


def _kelp(b,loc=(0,0,0),scale=1,prefix='kelp',branches=4):
    x,y,z=loc;leaves=[]
    for i in range(branches):
        phase=i*1.9
        base=(x+math.cos(phase)*.08*scale,y+math.sin(phase)*.08*scale,z)
        ht=(.64+.16*(i%3))*scale
        dx=math.sin(phase)*.16*scale;dy=math.cos(phase)*.06*scale
        points=[base,(base[0]+dx*.7,base[1]+dy,z+ht*.35),(base[0]-dx*.4,base[1]+dy*.7,z+ht*.7),(base[0]+dx*.6,base[1]+dy,z+ht)]
        for j in range(3):
            a,c=Vector(points[j]),Vector(points[j+1]);d=c-a
            o=b.ico(prefix+'_'+str(i)+'_'+str(j),(a+c)/2,(.07*scale,.045*scale,d.length*.67),'leaf' if i%2 else 'green')
            o.rotation_euler=d.to_track_quat('Z','Y').to_euler();leaves.append((o,i,j))
    return leaves


def _kelp_sway(leaves,t,amount=.06):
    for o,i,j in leaves:
        o.rotation_euler.y+=amount*(j+1)/3*math.sin(math.tau*t+i*.7)
        o.location.x+=amount*.16*(j+1)*math.sin(math.tau*t+i*.7)


def build_rock(b,kind):
    b.height=1.18
    if kind in ('rock_wall_middle','rock_wall_end','rock_wall_corner','rock_wall_half'):
        width=1. if kind!='rock_wall_half' else .5
        b.box('seam_core',(0,0,.35),(width,.61,.70),'rock_dark',0)
        cols=[(-width*.33,0,.32,.65,.93),(0,.02,width*.34,.68,1.19),(width*.33,-.02,width*.34,.62,.99)]
        if kind=='rock_wall_end':cols=[(-.28,0,.44,.63,1.12),(.14,.03,.48,.64,.91)]
        for i,(x,y,w,d,h) in enumerate(cols):_rock_column(b,'wall_column_'+str(i),(x,y),w,d,.03,h,'rock' if i%2 else 'blue_dark',9+i)
        if kind=='rock_wall_corner':
            b.box('corner_join',(0,.30,.35),(.61,.4,.70),'rock_dark',0)
            _rock_column(b,'corner_column',(0,.34),.60,.32,.02,1.04,'rock',42)
        if kind=='rock_wall_half':b.notes.append('Half-width barrier inside a 1x1 logical cell; narrow support mask is intentional.')
        b.notes.append('Middle/end/corner seam core is grid-aligned. Connecting edge is a module port, visual height is independent.')
        b.socket('port_left',(-.5,0,0))
        if kind=='rock_wall_corner':b.socket('port_back',(0,.5,0))
        elif kind!='rock_wall_end':b.socket('port_right',(.5,0,0))
    elif kind=='rock_shelf':
        b.footprint=(2,1);b.height=.72
        for i in range(4):_rock_column(b,'shelf_support_'+str(i),(-.75+i*.50,.08),.50,.62,0,.43+.07*(i%2),'rock_dark',i)
        b.box('shelf_cap',(0,0,.56),(2.,.93,.18),'rock',.025)
        for i in range(4):b.box('shelf_crack_'+str(i),(-.76+i*.5,-.04,.656),(.012,.65,.004),'rock_dark',0,rot=(0,0,.08*(-1 if i%2 else 1)))
        b.socket('port_left',(-1,0,0));b.socket('port_right',(1,0,0))
    elif kind=='boulder':
        b.footprint=(2,2);b.height=1.28
        for i,(x,y,z,s) in enumerate([(-.43,.28,.48,.69),(.40,.26,.60,.66),(-.1,-.40,.38,.66),(.42,-.35,.22,.43)]):
            o=b.ico('boulder_mass_'+str(i),(x,y,z),(s,s*.85,s),'rock' if i%2 else 'rock_dark');o.rotation_euler.z=i*.6
    elif kind=='rubble':
        b.height=.53
        for i,(x,y,s) in enumerate([(-.22,-.2,.24),(.24,-.1,.22),(.08,.23,.31),(-.27,.22,.21)]):
            b.ico('rubble_'+str(i),(x,y,s*.53),(s,s*.8,s*.65),'rock' if i%2 else 'rock_dark')
    elif kind=='reef_rock':
        b.height=.82
        for i,(x,y,s) in enumerate([(-.18,-.06,.35),(.23,.13,.30),(-.20,.28,.23)]):b.ico('reef_stone_'+str(i),(x,y,s*.64),(s,s*.85,s*.9),'rock' if i%2 else 'rock_dark')
        leaves=_kelp(b,(.28,-.23,.02),.65,'reef_kelp',3)
        b.motion['idle']=lambda t:_kelp_sway(leaves,t,.04)
        return b.finish({'idle':{'frames':24,'fps':12,'loop':True}})
    elif kind=='ruin_column':
        b.height=1.41
        b.box('base',(0,0,.10),(.65,.65,.20),'metal_light',.035)
        b.box('base_top',(0,0,.23),(.49,.49,.10),'metal',.018)
        _rock_column(b,'broken_shaft',(0,0),.38,.38,.27,1.02,'metal_light',27)
        b.box('fallen_cap',(.26,-.26,.16),(.34,.31,.26),'metal',.025,rot=(0,.2,.3))
        b.box('shaft_fissure',(0,-.198,.79),(.019,.01,.48),'metal_dark',0,rot=(0,0,.08))
        leaves=_kelp(b,(-.28,.21,.02),.42,'column_kelp',2)
        b.motion['idle']=lambda t:_kelp_sway(leaves,t,.04)
        return b.finish({'idle':{'frames':24,'fps':12,'loop':True}})
    else:raise ValueError(kind)
    return b.finish()


def build_wreck_beam(b,kind='wreck_beam'):
    b.footprint=(2,1);b.height=.72
    b.box('long_beam',(0,.09,.24),(2.,.25,.42),'blue_dark',.018)
    for x in (-.73,0,.73):
        b.box('upright_'+str(x),(x,.07,.43),(.13,.39,.75),'rock_dark',.015,rot=(0,.1 if x<0 else -.08,0))
        b.box('riveted_plate_'+str(x),(x,-.133,.41),(.28,.035,.28),'metal_dark',.008)
        for z in (.33,.49):b.cyl('rivet_'+str(x)+str(z),(x,-.157,z),.022,.025,'metal',6,(math.pi/2,0,0))
    if kind=='wreck_corner':
        b.footprint=(2,2)
        b.box('return_beam',(.73,.51,.24),(.25,.98,.42),'blue_dark',.018)
        b.box('return_post',(.73,.90,.43),(.30,.13,.75),'rock_dark',.015)
    b.notes.append('Old wreck structure; no gate, mine, spike or interaction implied.')
    return b.finish()


def build_kelp(b,group=False):
    leaves=_kelp(b,scale=.95 if not group else .8,branches=4)
    if group:
        leaves+=_kelp(b,(-.27,.19,0),.65,'kelp_b',3)
        leaves+=_kelp(b,(.23,.15,0),.73,'kelp_c',3)
    b.height=1.10
    for i,(x,y) in enumerate([(-.15,.04),(.12,.04)]):b.ico('anchor_rock_'+str(i),(x,y,.045),(.15,.12,.07),'rock_dark')
    b.motion['idle']=lambda t:_kelp_sway(leaves,t,.10)
    return b.finish({'idle':{'frames':24,'fps':12,'loop':True}})


def build_coral(b,kind='coral'): 
    b.height=.84
    if kind=='coral_branch':
        for i,(x,y,h) in enumerate([(-.20,0,.57),(0,.03,.80),(.21,.06,.65)]):
            b.cyl('stalk_'+str(i),(x,y,h/2),.075,h,'coral',8)
            b.ico('tip_'+str(i),(x,y,h),(.075,.075,.075),'coral',1)
            if i!=1:
                b.beam('branch_'+str(i),(x,y,h*.50),(x+(-.15 if i==0 else .15),y,h*.75),.11,'coral')
        b.ico('coral_base',(0,0,.07),(.32,.20,.09),'purple')
    else:
        for i,(x,y,h) in enumerate([(-.22,0,.45),(0,.04,.69),(.23,.06,.40),(0,-.2,.32)]):
            b.cyl('tube_'+str(i),(x,y,h/2),.115,h,'purple' if i%2 else 'coral',8)
            b.cyl('tube_mouth_'+str(i),(x,y,h+.004),.077,.012,'blue_dark',8)
            b.cyl('tube_lip_'+str(i),(x,y,h-.035),.127,.07,'purple' if i%2 else 'coral',8)
    def sway(t):
        for i,(n,o) in enumerate(b.parts.items()):o.rotation_euler.y+=.018*math.sin(t*math.tau+i*.3)
    b.motion['idle']=sway
    return b.finish({'idle':{'frames':24,'fps':12,'loop':True}})


def build_starfish(b):
    b.height=.20
    pts=[]
    for i in range(10):
        a=-math.pi/2+i*math.pi/5;r=.38 if i%2==0 else .16
        pts.append((math.cos(a)*r,math.sin(a)*r,.07))
    verts=pts+[(0,0,.17)]
    b.mesh('starfish',verts,[(i,(i+1)%10,10) for i in range(10)],'orange')
    for i in range(5):
        a=-math.pi/2+i*math.tau/5
        for j in (1,2):b.ico('spot_'+str(i)+str(j),(math.cos(a)*j*.105,math.sin(a)*j*.105,.16-j*.025),(.025,.025,.012),'yellow_light')
    return b.finish()


def build_salvage(b,variant='a'):
    b.height=.62
    if variant=='a':
        b.box('fragment',(0,0,.25),(.59,.49,.47),'metal',.018,rot=(.10,.13,.08))
        b.box('top_plate',(0,0,.50),(.68,.55,.055),'metal_light',.012,rot=(.12,.13,.08))
        for x in (-.20,.20):b.cyl('rivet_'+str(x),(x,-.26,.25),.034,.03,'metal_dark',8,(math.pi/2,0,0))
    elif variant=='b':
        verts=[(-.22,-.22,0),(.25,-.22,0),(.25,.22,0),(-.22,.22,0),(-.16,-.18,.61),(.19,-.18,.42),(.20,.17,.43),(-.13,.17,.64)]
        b.mesh('shard',verts,[(0,1,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0),(4,7,6,5)],'metal_dark')
        for z in (.16,.32):b.cyl('bolt_'+str(z),(.025,-.234,z),.03,.02,'metal',6,(math.pi/2,0,0))
    else:
        b.box('block',(-.13,0,.17),(.37,.43,.34),'wood',.022)
        b.box('angled_scrap',(.16,.03,.34),(.27,.40,.63),'metal',.018,rot=(0,-.25,0))
        b.box('brace',(0,-.235,.23),(.54,.035,.07),'metal_dark',.008,rot=(0,0,.12))
    def shimmer(t):
        for i,o in enumerate(b.parts.values()):o.rotation_euler.z+=.015*math.sin(t*math.tau+i)
    def collect(t):
        for o in b.parts.values():o.location.z+=t*.75;o.scale*=max(.025,1-t*.93)
    b.motion.update(idle=shimmer,attraction=shimmer,collection=collect)
    return b.finish({'idle':{'frames':24,'fps':12,'loop':True},'attraction':{'frames':12,'fps':12,'loop':True},'collection':{'frames':12,'fps':12,'loop':False}})


def build_portal(b):
    b.height=1.48
    # Vertical open ring; world and ground-root remain independent of visible center.
    bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=6,location=(0,0,.74),major_radius=.54,minor_radius=.075,rotation=(math.pi/2,0,0))
    ring=b.add(bpy.context.object,'portal_ring','cyan')
    bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=4,location=(0,.01,.74),major_radius=.66,minor_radius=.026,rotation=(math.pi/2,0,0))
    outer=b.add(bpy.context.object,'outer_ring','aqua')
    for i in range(8):
        a=math.tau*i/8
        o=b.box('rune_'+str(i),(math.cos(a)*.67,-.015,.74+math.sin(a)*.67),(.085,.045,.15),'blue_light',.012,rot=(0,-a,0))
    for x in (-.40,.40):b.ico('base_rock_'+str(x),(x,.03,.16),(.29,.25,.22),'rock_dark')
    def idle(t):
        ring.scale*=1+.025*math.sin(t*math.tau);outer.scale*=1-.018*math.sin(t*math.tau)
        for i in range(8):
            a=math.tau*(i/8+t/8)
            o=b.parts['rune_'+str(i)];o.location.x=math.cos(a)*.67;o.location.z=.74+math.sin(a)*.67;o.rotation_euler.y=-a
    def entry(t):
        idle(t)
        ring.scale*=1+.18*math.sin(t*math.pi)
        for i in range(8):b.parts['rune_'+str(i)].scale*=1+.4*math.sin(t*math.pi)
    b.motion.update(idle=idle,entry=entry)
    b.socket('entry',(0,0,.74))
    b.notes.append('Open geometry ring, no opaque disk. Layer as separate rim/decor, no access mechanic.')
    return b.finish({'idle':{'frames':24,'fps':12,'loop':True},'entry':{'frames':18,'fps':12,'loop':False}})


ASSET_IDS=[
 'stool_wood','stool_blue','chef_blackboard','potted_plant','barrel','crate','lantern','blank_sign',
 'garbage_sofa','garbage_car','garbage_shelf','dock_uncovered','dock_covered','submarine_base','submarine_upgraded',
 'hull_panel','harpoon_mount','collector_inlet','rock_wall_end','rock_wall_middle','rock_wall_corner','rock_wall_half',
 'rock_shelf','reef_rock','ruin_column','rubble','boulder','wreck_beam','wreck_corner','kelp_single','kelp_group',
 'coral_tubes','coral_branch','starfish','salvage_a','salvage_b','salvage_c','portal_rim'
]


def create_asset(asset_id):
    """Build one independent editable object collection. Existing scene is preserved.
    Returns root, parts, footprint, height, directions, sockets, clips, pose and reset.
    Clip time is normalized [0,1); frames are f/frame_count, duplicate end excluded.
    """
    if asset_id not in ASSET_IDS:raise ValueError('Unknown prop %r. Choices: %s'%(asset_id,', '.join(ASSET_IDS)))
    b=Builder(asset_id)
    if asset_id in ('stool_wood','stool_blue'):return build_stool(b,asset_id=='stool_blue')
    if asset_id=='chef_blackboard':return build_blackboard(b)
    if asset_id=='potted_plant':return build_plant(b)
    if asset_id=='barrel':return build_barrel(b)
    if asset_id=='crate':return build_crate(b)
    if asset_id=='lantern':return build_lantern(b)
    if asset_id=='blank_sign':return build_sign(b)
    if asset_id=='garbage_sofa':return build_sofa(b)
    if asset_id=='garbage_car':return build_car(b)
    if asset_id=='garbage_shelf':return build_shelf(b)
    if asset_id in ('dock_uncovered','dock_covered'):return build_dock(b,asset_id=='dock_covered')
    if asset_id in ('submarine_base','submarine_upgraded'):return build_submarine(b,asset_id=='submarine_upgraded')
    if asset_id in ('hull_panel','harpoon_mount','collector_inlet'):return build_equipment(b,asset_id)
    if asset_id.startswith('rock_') or asset_id in ('reef_rock','ruin_column','rubble','boulder'):return build_rock(b,asset_id)
    if asset_id.startswith('wreck_'):return build_wreck_beam(b,asset_id)
    if asset_id.startswith('kelp_'):return build_kelp(b,asset_id=='kelp_group')
    if asset_id.startswith('coral_'):return build_coral(b,asset_id)
    if asset_id=='starfish':return build_starfish(b)
    if asset_id.startswith('salvage_'):return build_salvage(b,asset_id[-1])
    if asset_id=='portal_rim':return build_portal(b)
    raise ValueError(asset_id)


def bake_animation(asset,clip,start_frame=1):
    """Bake native editable transforms at exactly 12 fps; original capture uses pose.
    Returns last unique frame. Holds the duplicate endpoint key only in Blender's
    action for interpolation closure; sprites must omit that final duplicate key.
    """
    recipe=asset['clips'][clip];count=recipe['frames'];loop=recipe.get('loop',False)
    bpy.context.scene.render.fps=12
    for f in range(count+(1 if loop else 0)):
        bpy.context.scene.frame_set(start_frame+f)
        asset['pose'](clip,(f%count)/count if loop else f/max(1,count-1))
        for part in asset['parts'].values():
            for path in ('location','rotation_euler','scale'):part.keyframe_insert(data_path=path,frame=start_frame+f,group=clip)
    for part in asset['parts'].values():
        action=part.animation_data.action if part.animation_data else None
        if action:action.name=asset['root'].name+'__'+clip+'__12fps'
    asset['reset']()
    return start_frame+count-1


def metadata(asset):
    """Serializable capture contract. Live bpy objects/callables stay separate."""
    return {k:asset[k] for k in ('footprint','height','directions','sockets','clips','notes')}
