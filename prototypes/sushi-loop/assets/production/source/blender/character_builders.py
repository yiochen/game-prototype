"""Issue 33 approved chibi character models, native armatures and weighted motion.
Load in Blender MCP; call create_character(id). No scene deletion or rendering.
Canonical front -Y, root ground-centred, scale one world unit per logical cell.
Art camera: ordinary orthographic, 35 degree elevation, no vertical stretch.
"""
import bpy
import math
import json
from mathutils import Vector, Matrix

COLORS={
 'white':'FFF4DE','skin_lena':'9C5736','skin_omar':'C8844F','skin_ama':'8F4D2C','skin_mateo':'DE9760','skin_noor':'D49360','skin_dalia':'A45D3A','skin_ellis':'F2BC87','skin_rowan':'E9AB74',
 'skin_rosa':'E8AA78','skin_samir':'CB8653','skin_june':'F4C08C','hair_brown':'4D2B24','hair_black':'252C38','hair_ginger':'A95327','hair_pink':'E64D9C',
 'navy':'253D65','blue':'2473C7','teal':'149C9D','green':'2D8D57','purple':'78465F','orange':'EF8E36','red':'D94C42','yellow':'F6C33D','yellow_light':'FFE579','coral':'EB685C',
 'shoe':'68462E','sole':'3D3029','eye':'2B2023','blush':'D8776B','plate':'F0EEE1','metal':'9AB0B8','rice':'FFF5D9','salmon':'F37E52','seaweed':'293B38',
}

def _lin(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

def material(name):
    key='S33_CHAR_'+name;m=bpy.data.materials.get(key)
    if m:return m
    h=COLORS.get(name,name).lstrip('#');rgb=tuple(_lin(int(h[i:i+2],16)/255) for i in (0,2,4))
    m=bpy.data.materials.new(key);m.use_nodes=True;m.diffuse_color=(*rgb,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.84
    if 'Specular IOR Level' in p.inputs:p.inputs['Specular IOR Level'].default_value=.22
    return m

ROSTER={
 'chef_lena':dict(name='Lena Brooks',skin='skin_lena',hair='hair_brown',style='curls',hat='chef',accent='red',apron='blue',top='white',kind='chef'),
 'chef_omar':dict(name='Omar Haddad',skin='skin_omar',hair='hair_black',style='short',hat='chef',accent='teal',apron='teal',top='white',kind='chef',mustache=True),
 'chef_ama':dict(name='Ama Mensah',skin='skin_ama',hair='hair_brown',style='short',hat='turban',accent='green',apron='green',top='white',kind='chef'),
 'chef_mateo':dict(name='Mateo Rivera',skin='skin_mateo',hair='hair_brown',style='quiff',hat='headband',accent='red',apron='blue',top='white',kind='chef'),
 'chef_noor':dict(name='Noor Haddad',skin='skin_noor',hair='hair_black',style='bob',hat='beret',accent='purple',apron='purple',top='white',kind='chef'),
 'chef_dalia':dict(name='Dalia Farouk',skin='skin_dalia',hair='hair_brown',style='curls',hat='cream_cap',accent='red',apron='teal',top='white',kind='chef'),
 'chef_ellis':dict(name='Ellis Morgan',skin='skin_ellis',hair='hair_ginger',style='curls',hat='flat_cap',accent='orange',apron='orange',top='white',kind='chef',glasses=True),
 'chef_rowan':dict(name='Rowan McLeod',skin='skin_rowan',hair='hair_ginger',style='waves',hat='teal_cap',accent='teal',apron='green',top='white',kind='chef',mustache=True),
 'customer_rosa':dict(name='Rosa',skin='skin_rosa',hair='hair_brown',style='bob',hat=None,accent='coral',apron=None,top='coral',kind='customer'),
 'customer_ellis':dict(name='Ellis',skin='skin_ellis',hair='hair_black',style='square',hat=None,accent='blue',apron=None,top='blue',kind='customer',glasses=True),
 'customer_samir':dict(name='Samir',skin='skin_samir',hair='hair_black',style='short',hat='orange_cap',accent='green',apron=None,top='green',kind='customer',mustache=True),
 'customer_june':dict(name='June',skin='skin_june',hair='hair_pink',style='bob',hat=None,accent='yellow',apron=None,top='yellow',kind='customer'),
}
CHARACTER_IDS=list(ROSTER)
# C / Chunky revision 3: actual native anatomy from the approved 125% study.
# Coordinates below are unscaled C anatomy; the ground root applies uniform 1.25.
CHARACTER_SCALE = 1.25
ENVIRONMENT_FRONT_SCALE = .70
WALK_STRIDE_CELLS = .18 * CHARACTER_SCALE
REST={
 'pelvis':((0,0,.15),(0,0,.205)),
 'spine':((0,0,.205),(0,0,.385)),
 'neck':((0,.005,.385),(0,.005,.43)),
 'head':((0,.005,.43),(0,.005,.91)),
}
for side,sign in [('L',-1),('R',1)]:
    REST['upper_arm_'+side]=((sign*.198,.004,.352),(sign*.249,-.002,.247))
    REST['forearm_'+side]=((sign*.249,-.002,.247),(sign*.267,-.023,.211))
    REST['hand_'+side]=((sign*.267,-.023,.211),(sign*.267,-.025,.125))
    REST['thigh_'+side]=((sign*.115,.005,.15),(sign*.115,-.013,.085))
    REST['shin_'+side]=((sign*.115,-.013,.085),(sign*.115,0,.035))
    REST['foot_'+side]=((sign*.115,0,.035),(sign*.115,-.12,.035))


def frame(head,tail):
    h=Vector(head);y=(Vector(tail)-h).normalized()
    ref=Vector((1,0,0))
    if abs(y.dot(ref))>.96:ref=Vector((0,0,1))
    x=(ref-y*y.dot(ref)).normalized();z=x.cross(y).normalized()
    m=Matrix(((x.x,y.x,z.x,0),(x.y,y.y,z.y,0),(x.z,y.z,z.z,0),(0,0,0,1)))
    m.translation=h
    return m

class CharacterBuilder:
    def __init__(self,ident):
        self.id=ident;self.cfg=ROSTER[ident];self.parts={};self.sockets={};self.weight_stats={};self.layer_tags={}
        self.collection=bpy.data.collections.new('S33_CHARACTER_'+ident);bpy.context.scene.collection.children.link(self.collection)
        self.root=bpy.data.objects.new(ident+'__ground_root',None);self.collection.objects.link(self.root);self.root.empty_display_size=.15
        self.armature=None
    def add(self,o,name,color,bone='spine',weights=None,layer='body'):
        o.name=self.id+'__'+name
        for c in list(o.users_collection):c.objects.unlink(o)
        self.collection.objects.link(o);o.parent=self.root
        if color:o.data.materials.append(material(color))
        self.parts[name]=o;self.layer_tags[name]=layer
        if bone or weights:
            if weights:
                names=set(n for pervert in weights for n in pervert)
                groups={n:o.vertex_groups.new(name=n) for n in names}
                for i,pervert in enumerate(weights):
                    for n,w in pervert.items():
                        if w>0:groups[n].add([i],w,'REPLACE')
            else:
                vg=o.vertex_groups.new(name=bone);vg.add(list(range(len(o.data.vertices))),1.,'REPLACE')
            o['weighted_character_geometry']=True
        return o
    def mesh(self,name,verts,faces,color,bone='spine',weights=None,layer='body'):
        me=bpy.data.meshes.new(self.id+'__'+name);me.from_pydata(verts,[],faces);me.update()
        o=bpy.data.objects.new(name,me);self.collection.objects.link(o)
        return self.add(o,name,color,bone,weights,layer)
    def box(self,name,loc,size,color,bone='spine',bevel=.02,rot=(0,0,0),layer='body'):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
        o=bpy.context.object;o.dimensions=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        o.rotation_euler=rot
        # Apply object transform into mesh before weighting so armature math uses common coordinates.
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        self.add(o,name,color,bone,layer=layer)
        if bevel:
            mod=o.modifiers.new('Soft faceted edges','BEVEL');mod.width=bevel;mod.segments=2
        return o
    def ico(self,name,loc,scale,color,bone='head',subdiv=1):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv,radius=1,location=loc)
        o=bpy.context.object;o.scale=scale
        bpy.ops.object.transform_apply(location=True,rotation=False,scale=True)
        return self.add(o,name,color,bone)
    def cyl(self,name,loc,radius,depth,color,bone='head',vertices=12,rot=(0,0,0),layer='body'):
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
        o=bpy.context.object;o.rotation_euler=rot
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        return self.add(o,name,color,bone,layer=layer)
    def ring(self,name,loc,radius,tube,color,bone='head'):
        bpy.ops.mesh.primitive_torus_add(major_segments=12,minor_segments=4,major_radius=radius,minor_radius=tube,location=loc,rotation=(math.pi/2,0,0))
        o=bpy.context.object;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        return self.add(o,name,color,bone)
    def garment(self):
        c=self.cfg
        # Broad eight-sided belly/back follows the selected C study, lowered .15.
        rings=[(.135,.172,.137,.122),(.205,.192,.163,.140),(.305,.212,.152,.143),(.385,.209,.117,.112)]
        vertices=[];weights=[]
        for z,w,front,back in rings:
            vertices += [(-w*.73,-front,z),(w*.73,-front,z),(w,-front*.60,z),(w,back*.62,z),
                         (w*.73,back,z),(-w*.73,back,z),(-w,back*.62,z),(-w,-front*.60,z)]
            t=max(0,min(1,(z-.16)/.18));weights += [{'pelvis':1-t,'spine':t}]*8
        faces=[tuple(reversed(range(8))),tuple(range(24,32))]+[(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i) for j in range(3) for i in range(8)]
        self.mesh('tailored_tunic',vertices,faces,c['top'],weights=weights,bone=None)
        self.box('pelvis',(0,.006,.135),(.322,.248,.13),'navy','pelvis',.027)
        self.box('neck',(0,.005,.416),(.126,.130,.09),c['skin'],'neck',.027)
        for sign in (-1,1):
            self.box('collar_'+str(sign),(sign*.054,-.123,.375),(.09,.029,.073),'white' if c['kind']=='chef' else c['top'],'spine',.010,rot=(0,sign*.18,0))
        if c['kind']=='chef':
            self.box('kerchief_knot',(0,-.150,.335),(.056,.055,.058),c['accent'],'spine',.014)
            for sign in (-1,1):self.box('kerchief_tail_'+str(sign),(sign*.035,-.157,.285),(.045,.028,.085),c['accent'],'spine',.007,rot=(0,sign*.28,0))
            # Solid wrap skirt and thick bib carry readable volume from the side.
            verts=[]
            for z,w,d in ((.082,.205,.177),(.205,.205*.91,.177*.91)):
                verts += [(-w,-d,z),(w,-d,z),(w,d*.72,z),(-w,d*.72,z)]
            faces=[(0,3,2,1),(4,5,6,7)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
            self.mesh('apron_skirt',verts,faces,c['apron'],bone='pelvis')
            self.box('apron_bib',(0,-.155,.277),(.26,.023,.145),c['apron'],'spine',.006)
            self.box('apron_waist',(0,-.006,.197),(.377,.287,.035),c['apron'],'pelvis',.008)
            self.box('apron_pocket',(0,-.183,.155),(.115,.016,.052),c['apron'],'pelvis',.008)
            for sign in (-1,1):
                self.box('apron_back_tie_'+str(sign),(sign*.045,.136,.190),(.10,.025,.025),c['apron'],'pelvis',.006,rot=(0,0,sign*.2))
                self.ico('coat_button_'+str(sign),(sign*.072,-.150,.260),(.009,.007,.009),'white','spine')
        elif self.id=='customer_samir':
            self.box('shirt_insert',(0,-.157,.270),(.15,.018,.19),'teal','spine',.005)
            for sign in (-1,1):self.box('jacket_lapel_'+str(sign),(sign*.095,-.174,.300),(.05,.025,.15),'green','spine',.008,rot=(0,sign*.08,0))
        else:self.box('shirt_hem',(0,-.143,.160),(.34,.025,.035),c['top'],'pelvis',.004)
    def limb(self,side,kind):
        c=self.cfg;sgn=-1 if side=='L' else 1
        if kind=='arm':
            names=['upper_arm_'+side,'forearm_'+side,'hand_'+side]
            a=Vector(REST[names[0]][0]);j=Vector(REST[names[0]][1]);end=Vector(REST[names[1]][1])
            ring_data=[(a,.065,{names[0]:.85,'spine':.15}),((a+j)*.5,.061,{names[0]:1}), (j,.057,{names[0]:.50,names[1]:.50}),((j+end)*.5,.052,{names[1]:1}),(end,.048,{names[1]:.35,names[2]:.65})]
        else:
            names=['thigh_'+side,'shin_'+side,'foot_'+side]
            a=Vector(REST[names[0]][0]);j=Vector(REST[names[0]][1]);end=Vector(REST[names[1]][1])
            ring_data=[(a,.069,{names[0]:.85,'pelvis':.15}),((a+j)*.5,.067,{names[0]:1}),(j,.063,{names[0]:.5,names[1]:.5}),((j+end)*.5,.060,{names[1]:1}),(end,.058,{names[1]:1})]
        verts=[];weights=[]
        for i,(p,r,w) in enumerate(ring_data):
            d=(ring_data[min(i+1,4)][0]-ring_data[max(0,i-1)][0]).normalized();ref=Vector((0,1,0));u=d.cross(ref).normalized();v=d.cross(u).normalized()
            for k in range(8):
                angle=math.tau*k/8;verts.append(tuple(p+u*math.cos(angle)*r+v*math.sin(angle)*r*.88));weights.append(w)
        faces=[tuple(reversed(range(8))),tuple(range(32,40))]+[(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i) for j in range(4) for i in range(8)]
        o=self.mesh(kind+'_'+side,verts,faces,c['top'] if kind=='arm' else 'navy',bone=None,weights=weights)
        if kind=='arm':
            o.data.materials.append(material(c['skin']))
            for poly in o.data.polygons:
                if poly.index==1 or poly.index>=2+2*8:poly.material_index=1
            hand=Vector(REST[names[2]][0])+Vector((0,-.002,-.046))
            self.box('palm_'+side,hand,(.09,.103,.104),c['skin'],names[2],.023)
            self.box('thumb_'+side,hand+Vector((-sgn*.038,-.033,.018)),(.035,.046,.054),c['skin'],names[2],.016)
        else:
            # Minimal navy toe ends: no boot shaft, cuff or separate sole.
            self.box('minimal_foot_'+side,(sgn*.115,-.020,.0215),(.148,.170,.043),'navy',names[2],.012)
    def face_and_hair(self):
        c=self.cfg;bottom=.43;height=.48;front=-.235
        head=self.box('head',(0,.005,.67),(.56,.48,.48),c['skin'],'head',.125)
        bevel=head.modifiers.get('Soft faceted edges');bevel.segments=8
        for polygon in head.data.polygons:polygon.use_smooth=True
        normal=head.modifiers.new('Weighted rounded face normals','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=50
        for sign in (-1,1):
            self.box('ear_'+str(sign),(sign*.293,.013,.65),(.058,.104,.119),c['skin'],'head',.024)
            self.ico('eye_'+str(sign),(sign*.103,front-.008,.6892),(.023,.012,.034),'eye',subdiv=2)
            self.ico('eye_glint_'+str(sign),(sign*.103-.004,front-.019,.6982),(.006,.004,.009),'white')
            self.box('brow_'+str(sign),(sign*.105,front-.006,.7622),(.067,.017,.017),c['hair'],'head',.004,rot=(0,sign*.12,0))
            self.ico('cheek_'+str(sign),(sign*.182,front-.007,.5908),(.037,.009,.020),'blush')
        self.box('nose',(0,front-.020,.622),(.059,.047,.051),c['skin'],'head',.018)
        z=.5428
        self.mesh('smile',[(-.044,front-.014,z+.011),(0,front-.019,z-.007),(.044,front-.014,z+.011),(.036,front-.017,z-.009),(0,front-.022,z-.021),(-.036,front-.017,z-.009)],[(0,1,4,5),(1,2,3,4)],'eye',bone='head')
        if c.get('mustache'):
            for sign in (-1,1):self.ico('mustache_'+str(sign),(sign*.039,-.273,.574),(.053,.021,.022),c['hair'],subdiv=2)
        if c.get('glasses'):
            for sign in (-1,1):self.ring('glasses_'+str(sign),(sign*.113,-.267,.694),.070,.011,'eye')
            self.box('glasses_bridge',(0,-.269,.694),(.080,.018,.012),'eye','head',.003)
            for sign in (-1,1):self.box('glasses_arm_'+str(sign),(sign*.208,-.090,.694),(.014,.30,.014),'eye','head',.003)
        # Every identity gets a rounded crown and actual occiput. Hair silhouette
        # remains specific to curls / cropped / bob / quiff / waves, never a box cap.
        def lock(name,loc,radius,phase=0.,shade=None):
            obj=self.ico(name,loc,radius,shade or c['hair'],subdiv=2);centre=Vector(loc)
            for v in obj.data.vertices:
                q=v.co-centre;angle=math.atan2(q.y/max(radius[1],.001),q.x/max(radius[0],.001))
                v.co=centre+q*(1.+.035*math.sin(3.*angle+phase))
            for polygon in obj.data.polygons:polygon.use_smooth=True
            return obj
        style=c['style'];bob=style=='bob';curly=style=='curls'
        lock('rounded_crown',(0,.025,.8572),(.292,.255,.157))
        lock('rounded_occiput',(0,.123,.7132),(.270,.190,.255 if curly or bob else .207))
        # Slight material differences preserve large readable locks after grading.
        h=COLORS[c['hair']];channels=[int(h[i:i+2],16) for i in (0,2,4)]
        shade=''.join('%02X'%min(255,round(x*1.13+3)) for x in channels)
        if curly:
            for row,(fraction,spread,depth) in enumerate(((.25,.185,.235),(.46,.221,.262),(.69,.232,.258),(.91,.203,.230))):
                for i,t in enumerate((-1.,-.5,0.,.5,1.)):
                    lock('back_curl_%s_%s'%(row,i),(t*spread,depth-.035*abs(t)**1.7,bottom+height*fraction+.016*math.cos(i*1.8+row)),(.083,.060,.082),i+row*.7,shade if (i+row)%3==0 else None)
            for sign in (-1,1):
                for j,(y,fraction,radius) in enumerate(((-.086,.83,.059),(.023,.77,.062),(.115,.71,.061),(.178,.57,.057),(.180,.36,.054))):
                    lock('temple_curl_%s_%s'%(sign,j),(sign*.265,y,bottom+height*fraction),(radius,.075,.083),j*.9+sign,shade if j==1 else None)
                lock('side_crown_'+str(sign),(sign*.246,.045,.9124),(.072,.111,.078),sign)
            for i,(x,fraction,rx,rz) in enumerate(((-.224,.93,.063,.065),(-.136,.90,.080,.077),(-.045,.94,.082,.070),(.049,.91,.084,.078),(.143,.94,.077,.070),(.225,.96,.059,.062))):
                lock('fringe_curl_'+str(i),(x,front+.006,bottom+height*fraction),(rx,.071,rz),i*.8,shade if i in (1,4) else None)
        elif bob:
            for sign in (-1,1):
                for i,y in enumerate((-.06,.07,.19)):
                    lock('bob_side_%s_%s'%(sign,i),(sign*(.255-.012*i),y,.663+i*.022),(.078,.098,.203),i+sign,shade if i==1 else None)
            for i,x in enumerate((-.213,-.108,0,.108,.213)):
                lock('bob_fringe_'+str(i),(x,front+.006,.857-(.020 if i%2 else 0)),(.084,.069,.086),i*.7,shade if i in (1,4) else None)
            for i,x in enumerate((-.18,0,.18)):lock('bob_nape_'+str(i),(x,.230,.552),(.107,.078,.094),i)
        elif style=='quiff':
            for i,x in enumerate((-.18,-.06,.06,.18)):
                lock('swept_quiff_'+str(i),(x,-.135,.928+(.025 if i==1 else 0)),(.100,.155,.113),i*.7,shade if i==1 else None)
            for sign in (-1,1):lock('quiff_temple_'+str(sign),(sign*.265,.025,.788),(.058,.14,.10),sign)
            for i,x in enumerate((-.18,0,.18)):lock('quiff_back_'+str(i),(x,.24,.775),(.098,.075,.117),i)
        elif style=='waves':
            for i,x in enumerate((-.205,-.09,.04,.17)):
                lock('wave_'+str(i),(x,-.16,.877+.013*math.sin(i)),(.102,.106,.112),i*.9,shade if i==1 else None)
            for sign in (-1,1):lock('wave_temple_'+str(sign),(sign*.260,.06,.765),(.063,.150,.13),sign)
            for i,x in enumerate((-.18,0,.18)):lock('wave_back_'+str(i),(x,.24,.73),(.103,.068,.142),i)
        else:
            for i,x in enumerate((-.20,-.10,0,.10,.20)):
                lock('cropped_fringe_'+str(i),(x,-.20,.873-(.012 if i%2 else 0)),(.078,.069,.067),i*.8,shade if i in (1,4) else None)
            for sign in (-1,1):lock('cropped_temple_'+str(sign),(sign*.264,.04,.775),(.052,.137,.098),sign)
            for i,x in enumerate((-.18,0,.18)):lock('cropped_back_'+str(i),(x,.24,.742),(.092,.060,.118),i)
        self.hat(c.get('hat'))
    def hat(self,style):
        if not style:return
        previous=set(self.parts)
        if style=='chef':
            self.box('hat_band',(0,.01,1.425),(.46,.38,.10),'white','head',.015)
            for i,(x,y,h) in enumerate([(-.13,-.03,.20),(0,-.03,.25),(.13,-.03,.20),(-.11,.10,.21),(.10,.10,.23)]):
                self.box('toque_fold_'+str(i),(x,y,1.47+h/2),(.19,.21,h),'white','head',.026,rot=(0,(-.09 if i==0 else .06 if i==2 else 0),0))
        elif style=='turban':
            self.ico('turban',(0,.01,1.44),(.29,.24,.22),'yellow',subdiv=1)
            for i in range(3):self.box('turban_fold_'+str(i),(0,-.195,1.37+i*.065),(.48,.045,.075),'yellow_light' if i%2 else 'yellow','head',.015,rot=(0,-.12+i*.03,0))
            self.ico('turban_knot',(.20,-.10,1.54),(.10,.09,.12),'yellow_light')
        elif style=='headband':
            self.box('headband',(0,-.182,1.335),(.46,.055,.085),'red','head',.008)
            self.box('headband_back',(0,.205,1.335),(.44,.045,.08),'red','head',.008)
            self.mesh('headband_tails',[(.19,.19,1.35),(.29,.26,1.24),(.20,.24,1.22),(.17,.19,1.34),(.24,.23,1.16),(.15,.24,1.21)],[(0,1,2),(3,4,5)],'red','head')
        elif style=='beret':
            self.cyl('beret_band',(0,.01,1.40),.24,.075,'green','head',8)
            self.ico('beret_crown',(-.055,.025,1.49),(.30,.25,.14),'green')
            self.box('beret_tip',(-.055,.025,1.62),(.05,.045,.06),'green','head',.008)
        elif style=='cream_cap':
            self.box('cap',(0,.01,1.44),(.47,.39,.20),'white','head',.04)
            self.box('cap_front',(0,-.205,1.41),(.49,.10,.08),'white','head',.012)
        else:
            color={'flat_cap':'navy','teal_cap':'teal','orange_cap':'orange'}[style]
            self.box('cap_crown',(0,.025,1.43),(.46,.39,.19),color,'head',.035)
            self.box('cap_brim',(0,-.165,1.365),(.44,.15,.055),color,'head',.015)
            self.box('cap_button',(0,.025,1.54),(.045,.045,.035),color,'head',.009)
        # Match approved C hat placement without changing its recognizable style.
        for name in set(self.parts)-previous:
            obj=self.parts[name]
            for vertex in obj.data.vertices:
                vertex.co.x*=1.20;vertex.co.y*=1.20;vertex.co.z=.985+(vertex.co.z-1.425)
            bevel=obj.modifiers.get('Soft faceted edges')
            if bevel:bevel.width*=1.10
    def build_rig(self):
        data=bpy.data.armatures.new(self.id+'__skeleton');arm=bpy.data.objects.new(self.id+'__armature',data)
        self.collection.objects.link(arm);arm.parent=self.root;self.armature=arm
        for o in bpy.context.selected_objects:o.select_set(False)
        arm.select_set(True);bpy.context.view_layer.objects.active=arm
        bpy.ops.object.mode_set(mode='EDIT')
        parents={'pelvis':'ground','spine':'pelvis','neck':'spine','head':'neck'}
        for s in ('L','R'):
            parents.update({'upper_arm_'+s:'spine','forearm_'+s:'upper_arm_'+s,'hand_'+s:'forearm_'+s,'thigh_'+s:'pelvis','shin_'+s:'thigh_'+s,'foot_'+s:'shin_'+s})
        specs={'ground':((0,0,0),(0,0,.10)),**REST}
        for side,sign in [('L',-1),('R',1)]:
            specs['foot_goal_'+side]=((sign*.115,0,.035),(sign*.115,0,.11))
            specs['knee_pole_'+side]=((sign*.115,-.20,.085),(sign*.115,-.20,.16))
            specs['hand_goal_'+side]=(REST['hand_'+side][0],tuple(Vector(REST['hand_'+side][0])+Vector((0,0,.1))))
            specs['elbow_pole_'+side]=((sign*.48,-.06,.27),(sign*.48,-.06,.35))
            for n in ('foot_goal_','knee_pole_','hand_goal_','elbow_pole_'):parents[n+side]='ground'
        for name,(a,c) in specs.items():
            bone=data.edit_bones.new(name);bone.head=a;bone.tail=c;bone.matrix=frame(a,c);bone.length=(Vector(c)-Vector(a)).length
            if name=='ground' or any(name.startswith(x) for x in ('foot_goal','knee_pole','hand_goal','elbow_pole')):bone.use_deform=False
        for name,parent in parents.items():data.edit_bones[name].parent=data.edit_bones[parent]
        bpy.ops.object.mode_set(mode='OBJECT');arm.show_in_front=True
        for pb in arm.pose.bones:pb.rotation_mode='QUATERNION'
        for o in self.parts.values():
            if o.type=='MESH' and o.vertex_groups:
                mod=o.modifiers.new('Weighted character deformation','ARMATURE');mod.object=arm;mod.use_vertex_groups=True
                weighted=sum(1 for v in o.data.vertices if v.groups)
                self.weight_stats[o.name]={'vertices':len(o.data.vertices),'weighted':weighted,'unweighted':len(o.data.vertices)-weighted}
        # Goal and pole bones are explicit world-space controls. The authoring pose
        # solver evaluates their targets into the native deform chain each frame.
        arm['rig_solver']='analytic two-bone limbs, stable outward poles; native editable transform keys'
        arm['control_space']='ground-root-local world coordinates, independent of pelvis and head'
        arm['deformation']='continuous 8-sided limb rings; blended shoulder/elbow/knee and wrist weights'
        return arm
    def finish(self):
        self.garment()
        for side in ('L','R'):
            self.limb(side,'arm');self.limb(side,'leg')
        self.face_and_hair();arm=self.build_rig()
        clips=(
          {'idle':dict(frames=24,fps=12,loop=True),'work':dict(frames=24,fps=12,loop=True),'hold':dict(frames=24,fps=12,loop=True),'load':dict(frames=18,fps=12,loop=False)}
          if self.cfg['kind']=='chef' else
          {'stand':dict(frames=24,fps=12,loop=True),'walk':dict(frames=24,fps=12,loop=True),'seated_wait':dict(frames=24,fps=12,loop=True),'eat':dict(frames=24,fps=12,loop=True),
           'sit_down':dict(frames=18,fps=12,loop=False),'stand_up':dict(frames=18,fps=12,loop=False),'happy':dict(frames=18,fps=12,loop=False),'restless':dict(frames=24,fps=12,loop=True),
           'puzzled':dict(frames=24,fps=12,loop=True),'panic':dict(frames=24,fps=12,loop=True)})
        rest_mats={n:bone.matrix_local.copy() for n,bone in arm.data.bones.items()}
        baseline={n:o.hide_render for n,o in self.parts.items()}
        seat_plane=.655*ENVIRONMENT_FRONT_SCALE/(CHARACTER_SCALE*math.cos(math.radians(35)))
        self.sockets={'ground':[0,0,0],'seat_contact':[0,0,seat_plane],'hand_left':list(REST['hand_L'][0]),'hand_right':list(REST['hand_R'][0]),'mouth':[0,-.255,.543]}
        def pose(clip='idle',t=0):
            if clip=='idle' and clip not in clips:clip='stand'
            if clip not in clips:raise KeyError('Unknown clip %s for %s'%(clip,self.id))
            t=float(t)%1 if clips[clip]['loop'] else max(0.,min(1.,float(t)))
            _pose_character(arm,clip,t,rest_mats,self)
        def reset():
            for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
            for n,o in self.parts.items():o.hide_render=baseline[n]
            bpy.context.view_layer.update()
        self.root['asset_id']=self.id;self.root['display_name']=self.cfg['name'];self.root['kind']=self.cfg['kind'];self.root['projection']='character-orthographic'
        self.root['footprint_cells']=json.dumps([1,1]);self.root['ground_root']=json.dumps([0,0,0]);self.root['anatomy_height']=max(v.co.z for o in self.parts.values() if o.type=='MESH' for v in o.data.vertices)*CHARACTER_SCALE
        self.root.scale=(CHARACTER_SCALE,)*3
        self.root['anatomy_revision']='C-chunky-r3-125';self.root['uniform_native_scale']=CHARACTER_SCALE
        self.root['character_design']='Short native legs, minimal navy toe ends, rounded .56x.48 head and full identity-specific crown/occiput/fringe.'
        self.root['walk_stride_cells']=WALK_STRIDE_CELLS;self.root['walk_cycles_per_second']=1
        self.root['panic_cycles_per_second']=2
        self.root['sockets']=json.dumps(self.sockets);self.root['animation_recipes']=json.dumps(clips);self.root['identity_design']=json.dumps(self.cfg)
        self.root['source']='character_builders.py';self.root['weight_validation']=json.dumps(self.weight_stats)
        self.root['seat_environment_z']=.655
        self.root['seat_character_plane']=seat_plane
        self.root['seat_pelvis_offset']=.080
        self.root['seat_attachment']='seat contact at environmentZ*0.70/(1.25*cos35); local pelvis control0.080 above contact; scaled ordinary35 character and 70% environment share projected ground root'
        pose('idle' if self.cfg['kind']=='chef' else 'stand',0)
        return {'root':self.root,'collection':self.collection,'armature':arm,'parts':self.parts,'clips':clips,'pose':pose,'reset':reset,'sockets':self.sockets,'height':self.root['anatomy_height'],'footprint':[1,1],'directions':['N','E','S','W'],'weight_validation':self.weight_stats,'identity':self.cfg,'layer_tags':self.layer_tags,'rest_matrices':rest_mats,'sockets_current':lambda world=False:evaluated_sockets({'armature':arm,'root':self.root},world),'frameSize':[192,320],'frameRoot':[96,248],'walk_stride_cells':WALK_STRIDE_CELLS}


def _two_bone(a,c,l1,l2,pole):
    a,c=Vector(a),Vector(c);delta=c-a
    distance=max(.001,min(delta.length,l1+l2-.0001));axis=delta.normalized() if delta.length else Vector((0,0,-1))
    target=a+axis*distance
    along=(l1*l1-l2*l2+distance*distance)/(2*distance)
    height=math.sqrt(max(0,l1*l1-along*along))
    p=Vector(pole)-a;out=p-axis*p.dot(axis)
    if out.length<.00001:out=Vector((0,-1,0))
    joint=a+axis*along+out.normalized()*height
    return joint,target


def _lerp(a,b,t):return Vector(a).lerp(Vector(b),t)

def _smooth(t):return t*t*(3-2*t)


def _pose_character(arm,clip,t,rest_mats,builder):
    """C anatomy retargeting, solved from actual short limbs at every sample.

    Ground stance still travels rearward relative to canonical front (-Y).
    The shorter native stride is .18 cells/cycle before uniform 125% scaling;
    the matching world travel is .225 cells/cycle, never the legacy .56 stride.
    """
    phase=math.tau*t;sin=math.sin;cos=math.cos
    seated=1. if clip in ('seated_wait','eat') else _smooth(t) if clip=='sit_down' else 1-_smooth(t) if clip=='stand_up' else 0.
    seat_plane=float(builder.root.get('seat_character_plane',.655*ENVIRONMENT_FRONT_SCALE/(CHARACTER_SCALE*math.cos(math.radians(35)))))
    pelvis_offset=float(builder.root.get('seat_pelvis_offset',.080));seat_hip=seat_plane+pelvis_offset
    hip=Vector((0,0,.15+(seat_hip-.15)*seated));lean=.015*sin(phase);head_yaw=.025*sin(phase*.5);head_tilt=0.
    arm_targets={side:Vector(REST['hand_'+side][0]) for side in ('L','R')}
    hand_dirs={side:Vector((0,-.002,-.086)) for side in ('L','R')}
    feet={side:Vector(REST['foot_'+side][0]) for side in ('L','R')};foot_tilt={'L':0.,'R':0.}
    if clip in ('idle','stand'):
        hip.z+=.001*sin(phase);lean=.009*sin(phase)
        for side in ('L','R'):arm_targets[side].y-=.006*sin(phase+(0 if side=='L' else .5))
    elif clip=='work':
        lean=.08+.022*sin(phase*2)
        arm_targets['L']=Vector((-.115,-.156,.312+.012*sin(phase)))
        arm_targets['R']=Vector((.107,-.164,.318+.026*sin(phase*2)))
        hand_dirs={side:Vector((0,-.065,-.015)) for side in ('L','R')};head_yaw=.03*sin(phase)
    elif clip=='hold':
        lean=.014*sin(phase)
        arm_targets['R']=Vector((.131,-.180,.312+.004*sin(phase)))
        arm_targets['L']=Vector((-.205,-.049,.227+.004*sin(phase+.3)))
        hand_dirs['R']=Vector((0,-.07,0));head_yaw=.04*sin(phase)
    elif clip=='load':
        u=sin(math.pi*t);lean=.10*u
        arm_targets['R']=_lerp((.131,-.180,.312),(.131,-.238,.331),u)
        arm_targets['L']=_lerp((-.205,-.049,.227),(-.123,-.148,.305),u*.7)
        hand_dirs['R']=Vector((0,-.07,-.005));head_yaw=-.025*u
    if seated:
        for side,sign in [('L',-1),('R',1)]:
            feet[side]=_lerp(feet[side],(sign*.115,-.060,seat_plane+.006),seated)
            arm_targets[side]=_lerp(arm_targets[side],(sign*.148,-.139,.299),seated)
            hand_dirs[side]=_lerp(hand_dirs[side],(0,-.065,-.018),seated)
        lean=.014*sin(phase)
        if clip=='seated_wait':
            head_yaw=.055*sin(phase);head_tilt=.025*sin(phase);arm_targets['R'].z+=.008*sin(phase)
        elif clip=='eat':
            lift=(sin(phase)+1)*.5
            arm_targets['R']=_lerp((.115,-.180,.305),(.066,-.164,.474),lift)
            arm_targets['L']=Vector((-.123,-.189,.305))
            hand_dirs['R']=Vector((0,-.065,.005));head_tilt=.025*sin(phase)
    if clip in ('walk','panic'):
        quick=2 if clip=='panic' else 1
        for side,off in [('L',0),('R',.5)]:
            g=(t*quick+off)%1
            # Stance sole moves backward (+Y), recovery moves forward (-Y).
            # A matching root translation -.225*t cells cancels stance velocity.
            if g<.5:y=-.045+.18*g;z=.035
            else:
                u=(g-.5)*2;y=.045-.09*u;z=.035+.026*sin(math.pi*u)
            feet[side].y=y;feet[side].z=z
            arm_targets[side].y+=(-.055 if side=='L' else .055)*sin(phase*quick)
            arm_targets[side].z+=.012*cos(phase*quick)
        hip.z=.141+.001*cos(phase*quick*2);lean=.07 if clip=='panic' else .025
        if clip=='panic':head_yaw=.18*sin(phase);arm_targets['L'].z+=.06;arm_targets['R'].z+=.06
    elif clip=='happy':
        hop=sin(math.pi*t)**2;hip.z+=.05*hop
        for side,sign in [('L',-1),('R',1)]:
            feet[side].z+=.05*hop;arm_targets[side]=_lerp(arm_targets[side],(sign*.30,-.025,.41),hop)
        head_tilt=-.07*hop
    elif clip=='restless':
        hip.x=.012*sin(phase);hip.z=.148+.002*cos(phase*2);head_yaw=.13*sin(phase)
        feet['R'].z+=.018*max(0,sin(phase));foot_tilt['R']=.08*max(0,sin(phase))
        arm_targets['R']=Vector((.205,-.066,.266+.018*sin(phase)))
    elif clip=='puzzled':
        head_tilt=.14*sin(phase);head_yaw=.09*sin(phase+.4)
        arm_targets['R']=Vector((.197,-.074,.435+.015*sin(phase)))
        hand_dirs['R']=Vector((-.035,-.015,.06));arm_targets['L']=Vector((-.180,-.066,.247))
    rot=Matrix.Rotation(lean,3,'X');rest_hip=Vector((0,0,.15))
    def upper(point):return hip+rot@(Vector(point)-rest_hip)
    desired={'ground':rest_mats['ground'].copy()}
    for name in ('pelvis','spine','neck','head'):
        a,c=REST[name]
        if name=='pelvis' and seated:
            offset=hip-rest_hip;desired[name]=frame(Vector(a)+offset,Vector(c)+offset)
        else:desired[name]=frame(upper(a),upper(c))
    desired['head']=desired['head']@Matrix.Rotation(head_yaw,4,'Y')@Matrix.Rotation(head_tilt,4,'Z')
    actual_hands={}
    for side,sign in [('L',-1),('R',1)]:
        wrist=arm_targets[side]+Vector((hip.x,0,hip.z-.15))
        shoulder=upper(REST['upper_arm_'+side][0]);elbow_pole=Vector((sign*.48,-.02,.27))+Vector((hip.x,0,hip.z-.15))
        l1=(Vector(REST['upper_arm_'+side][1])-Vector(REST['upper_arm_'+side][0])).length
        l2=(Vector(REST['forearm_'+side][1])-Vector(REST['forearm_'+side][0])).length
        elbow,wrist=_two_bone(shoulder,wrist,l1,l2,elbow_pole)
        desired['upper_arm_'+side]=frame(shoulder,elbow);desired['forearm_'+side]=frame(elbow,wrist);desired['hand_'+side]=frame(wrist,wrist+hand_dirs[side])
        hip_joint=hip+Vector((sign*.115,.005,0));ankle=feet[side];pole=Vector((sign*.115,-.20,.085))
        l1=(Vector(REST['thigh_'+side][1])-Vector(REST['thigh_'+side][0])).length
        l2=(Vector(REST['shin_'+side][1])-Vector(REST['shin_'+side][0])).length
        knee,ankle=_two_bone(hip_joint,ankle,l1,l2,pole)
        desired['thigh_'+side]=frame(hip_joint,knee);desired['shin_'+side]=frame(knee,ankle)
        desired['foot_'+side]=frame(ankle,ankle+Vector((0,-.12,.12*foot_tilt[side])))
        desired['foot_goal_'+side]=frame(feet[side],feet[side]+Vector((0,0,.075)))
        desired['knee_pole_'+side]=frame(pole,pole+Vector((0,0,.075)))
        desired['hand_goal_'+side]=frame(wrist,wrist+Vector((0,0,.075)))
        desired['elbow_pole_'+side]=frame(elbow_pole,elbow_pole+Vector((0,0,.075)))
        actual_hands[side]=list(wrist+hand_dirs[side]*.6)
    for name,pb in arm.pose.bones.items():
        target=desired.get(name,rest_mats[name])
        if pb.parent:
            parent=pb.parent.name
            basis=(desired.get(parent,rest_mats[parent])@rest_mats[parent].inverted()@rest_mats[name]).inverted()@target
        else:basis=rest_mats[name].inverted()@target
        pb.matrix_basis=basis
    arm['current_clip']=clip;arm['current_phase']=t;arm['hand_sockets_current']=json.dumps(actual_hands)
    arm['seat_contact_current']=json.dumps([hip.x,0,hip.z-pelvis_offset]);arm['hip_control_current']=json.dumps(list(hip));arm['feet_current']=json.dumps({side:list(feet[side]) for side in feet})
    bpy.context.view_layer.update();sockets=evaluated_sockets({'armature':arm,'root':builder.root})
    arm['hand_sockets_current']=json.dumps({'L':sockets['hand_left'],'R':sockets['hand_right']})


def create_character(ident):
    if ident not in ROSTER:raise ValueError('Unknown character %s. Choices %s'%(ident,', '.join(CHARACTER_IDS)))
    return CharacterBuilder(ident).finish()


def bake_actions(character,start_frame=1):
    """Bake each clip into separate native Blender actions on this armature.
    World-root object is never keyed. All bones, including explicit controls,
    retain native editable channels. Closing loop keys are omitted from sprites.
    """
    arm=character['armature'];bpy.context.scene.render.fps=12;actions={}
    for clip,recipe in character['clips'].items():
        if arm.animation_data:arm.animation_data.action=None
        count=recipe['frames'];loop=recipe['loop']
        for f in range(count+(1 if loop else 0)):
            bpy.context.scene.frame_set(start_frame+f)
            character['pose'](clip,(f%count)/count if loop else f/max(1,count-1))
            for pb in arm.pose.bones:
                for path in ('location','rotation_quaternion','scale'):
                    if path=='rotation_quaternion':pb.rotation_mode='QUATERNION'
                    pb.keyframe_insert(data_path=path,frame=start_frame+f,group=pb.name)
        action=arm.animation_data.action;action.name=character['root'].name+'__'+clip+'__12fps';action.use_fake_user=True;actions[clip]=action
    arm.animation_data.action=None;character['reset']()
    return actions


def validate_character(character,samples=12):
    """Structural diagnostics only. Natural anatomy still needs angle/pose review.
    Checks weight coverage, finite evaluated matrices and standing contact goals.
    Does not render, save files, grade art or claim perceptual acceptance.
    """
    arm=character['armature'];bone_names=set(arm.data.bones.keys());issues=[];total=0
    for o in character['parts'].values():
        if o.type!='MESH':continue
        names={g.index:g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            total+=1
            weights=[g.weight for g in v.groups if names.get(g.group) in bone_names]
            if not weights or abs(sum(weights)-1)>1e-5:issues.append({'part':o.name,'vertex':v.index,'weight_sum':sum(weights)})
    max_contact_error=0.;max_matrix_nonfinite=0;root_matrix=character['root'].matrix_world.copy()
    for clip,recipe in character['clips'].items():
        for i in range(samples):
            t=i/samples if recipe['loop'] else i/max(1,samples-1)
            character['pose'](clip,t)
            for pb in arm.pose.bones:
                if any(not math.isfinite(x) for row in pb.matrix for x in row):max_matrix_nonfinite+=1
            if clip in ('idle','stand','work','hold','load'):
                goals=json.loads(arm['feet_current'])
                for s in ('L','R'):max_contact_error=max(max_contact_error,(arm.pose.bones['foot_'+s].head-Vector(goals[s])).length)
    unchanged=max(abs(a-b) for row_a,row_b in zip(root_matrix,character['root'].matrix_world) for a,b in zip(row_a,row_b))<1e-8
    character['pose']('idle' if character['identity']['kind']=='chef' else 'stand',0)
    return {'diagnostic_only':True,'weighted_vertices':total,'weight_issues':issues,'nonfinite_pose_matrices':max_matrix_nonfinite,'maximum_planted_ankle_goal_error':max_contact_error,'ground_root_unchanged':unchanged,'needs_visual_review':['front side three-quarter after posing','elbow wrist and shoulder deformation','knees and sole contact','complete temporal loop','seat and hand attachment composition']}


def evaluated_sockets(character,world=False):
    """Actual evaluated mesh attachment positions in armature or world space.
    Hands use the palm's modeled center transformed by its deform bone, rather
    than an estimated wrist goal. Plates can stay horizontal over these points;
    utensils can use socket_matrix() for the full hand orientation.
    """
    arm=character['armature'];root=character['root'];result={'ground':[0.,0.,0.]}
    points={
        'hand_left':('hand_L',Vector(REST['hand_L'][0])+Vector((0,-.002,-.046))),
        'hand_right':('hand_R',Vector(REST['hand_R'][0])+Vector((0,-.002,-.046))),
        'mouth':('head',Vector((0,-.255,.543))),
    }
    for name,(bone,point) in points.items():
        p=arm.pose.bones[bone].matrix@arm.data.bones[bone].matrix_local.inverted()@point
        if world:p=arm.matrix_world@p
        result[name]=list(p)
    contact=Vector(json.loads(arm.get('seat_contact_current','[0,0,0]')))
    if world:contact=arm.matrix_world@contact;result['ground']=list(root.matrix_world.translation)
    result['seat_contact']=list(contact)
    return result


def socket_matrix(character,socket,world=False):
    """Evaluated native attachment transform; caller owns any mesh-axis offset."""
    arm=character['armature'];lookup={'hand_left':'hand_L','hand_right':'hand_R','mouth':'head'}
    bone=lookup[socket];m=arm.pose.bones[bone].matrix.copy()
    m.translation=Vector(evaluated_sockets(character,False)[socket])
    return arm.matrix_world@m if world else m


def set_seat_environment_z(character,height=.655,elevation_degrees=35):
    """Select a complete support variant without scaling or moving sprite roots.
    Wood stool=.655; blue cushion=.685. Re-pose after changing this setting.
    """
    root=character['root'];root['seat_environment_z']=float(height)
    root['seat_character_plane']=float(height)*ENVIRONMENT_FRONT_SCALE/(CHARACTER_SCALE*math.cos(math.radians(elevation_degrees)))
    character['sockets']['seat_contact']=[0,0,root['seat_character_plane']]
    root['sockets']=json.dumps(character['sockets'])
