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
REST={
 'pelvis':((0,0,.65),(0,0,.77)),
 'spine':((0,0,.72),(0,0,.94)),
 'neck':((0,0,.93),(0,0,1.015)),
 'head':((0,0,1.015),(0,0,1.34)),
}
for side,sign in [('L',-1),('R',1)]:
    REST['upper_arm_'+side]=((sign*.225,0,.91),(sign*.305,-.005,.765))
    REST['forearm_'+side]=((sign*.305,-.005,.765),(sign*.325,-.03,.635))
    REST['hand_'+side]=((sign*.325,-.03,.635),(sign*.325,-.04,.565))
    REST['thigh_'+side]=((sign*.12,0,.65),(sign*.12,-.026,.38))
    REST['shin_'+side]=((sign*.12,-.026,.38),(sign*.12,0,.11))
    REST['foot_'+side]=((sign*.12,0,.11),(sign*.12,-.16,.11))


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
            mod=o.modifiers.new('Soft faceted edges','BEVEL');mod.width=bevel;mod.segments=1
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
        # Torso is a shaped continuous tunic; not a primitive cube held by a parent.
        verts=[];rings=[(.655,.175,.135),(.73,.19,.145),(.88,.205,.145),(.94,.23,.13)]
        weights=[]
        for z,w,d in rings:
            for x,y in [(-w,-d),(w,-d),(w,d),(-w,d)]:
                verts.append((x,y,z));s=max(0,min(1,(z-.69)/.18));weights.append({'pelvis':1-s,'spine':s})
        faces=[(0,3,2,1),(12,13,14,15)]+[(j*4+i,j*4+(i+1)%4,(j+1)*4+(i+1)%4,(j+1)*4+i) for j in range(3) for i in range(4)]
        self.mesh('tailored_tunic',verts,faces,c['top'],weights=weights,bone=None)
        self.box('pelvis',(0,0,.645),(.32,.255,.20),'navy','pelvis',.025)
        self.cyl('neck',(0,0,.98),.082,.11,c['skin'],'neck',8)
        # Collar pieces surround the neck and lie naturally on the garment.
        for x in (-.075,.075):self.box('collar_'+str(x),(x,-.125,.93),(.105,.035,.075),'white' if c['kind']=='chef' else c['top'],'spine',.012,rot=(0,x*1.8,0))
        if c['kind']=='chef':
            self.box('kerchief_knot',(0,-.17,.895),(.064,.05,.065),c['accent'],'spine',.015)
            self.mesh('kerchief_tails',[(-.025,-.18,.89),(-.08,-.18,.80),(0,-.18,.82),(.025,-.18,.89),(.07,-.18,.81),(0,-.18,.82)],[(0,1,2),(3,4,5)],c['accent'])
            self.mesh('apron_bib',[(-.125,-.153,.88),(.125,-.153,.88),(.15,-.159,.68),(-.15,-.159,.68)],[(0,1,2,3)],c['apron'])
            self.mesh('apron_skirt',[(-.17,-.158,.70),(.17,-.158,.70),(.19,-.17,.485),(-.19,-.17,.485)],[(0,1,2,3)],c['apron'],bone='pelvis')
            self.box('apron_waist',(0,-.157,.70),(.35,.025,.044),c['apron'],'pelvis',.004)
            self.box('apron_pocket',(0,-.176,.63),(.115,.018,.065),c['apron'],'pelvis',.004)
            for x in (-.105,.105):
                for z in (.79,.84):self.ico('coat_button_'+str(x)+str(z),(x,-.154,z),(.014,.008,.014),'navy','spine')
        elif self.id=='customer_samir':
            self.box('shirt_insert',(0,-.156,.80),(.18,.018,.23),'teal','spine',.005)
            for x in (-.115,.115):self.box('jacket_lapel_'+str(x),(x,-.174,.84),(.055,.025,.19),'green','spine',.008,rot=(0,x*.7,0))
        else:self.box('shirt_hem',(0,-.143,.675),(.34,.025,.035),c['top'],'pelvis',.004)
    def limb(self,side,kind):
        c=self.cfg;sgn=-1 if side=='L' else 1
        if kind=='arm':
            names=['upper_arm_'+side,'forearm_'+side,'hand_'+side]
            a=Vector(REST[names[0]][0]);j=Vector(REST[names[0]][1]);end=Vector(REST[names[1]][1])
            ring_data=[(a,.083,{names[0]:.85,'spine':.15}),((a+j)*.5,.078,{names[0]:1}), (j,.071,{names[0]:.50,names[1]:.50}),((j+end)*.5,.063,{names[1]:1}),(end,.061,{names[1]:.35,names[2]:.65})]
        else:
            names=['thigh_'+side,'shin_'+side,'foot_'+side]
            a=Vector(REST[names[0]][0]);j=Vector(REST[names[0]][1]);end=Vector(REST[names[1]][1])
            ring_data=[(a,.096,{names[0]:.85,'pelvis':.15}),((a+j)*.5,.090,{names[0]:1}),(j,.081,{names[0]:.5,names[1]:.5}),((j+end)*.5,.073,{names[1]:1}),(end,.068,{names[1]:1})]
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
            hand=Vector(REST[names[2]][0])+Vector((0,-.007,-.04))
            self.box('palm_'+side,hand,(.105,.105,.125),c['skin'],names[2],.024)
            self.box('thumb_'+side,hand+Vector((-sgn*.05,-.022,.007)),(.048,.065,.065),c['skin'],names[2],.016)
        else:
            self.box('boot_'+side,(sgn*.12,-.052,.092),(.18,.27,.18),'shoe',names[2],.025)
            self.box('sole_'+side,(sgn*.12,-.059,.022),(.187,.283,.044),'sole',names[2],.014)
            self.box('boot_cuff_'+side,(sgn*.12,.0,.175),(.16,.17,.06),'shoe',names[1],.013)
    def face_and_hair(self):
        c=self.cfg
        self.box('head',(0,-.005,1.17),(.45,.38,.40),c['skin'],'head',.055)
        for s in (-1,1):
            self.box('ear_'+str(s),(s*.234,-.015,1.15),(.075,.10,.12),c['skin'],'head',.025)
            self.ico('eye_'+str(s),(s*.092,-.201,1.175),(.025,.012,.039),'eye')
            self.ico('eye_glint_'+str(s),(s*.089,-.213,1.186),(.007,.004,.011),'white')
            self.box('brow_'+str(s),(s*.094,-.202,1.237),(.061,.018,.018),c['hair'],'head',.005,rot=(0,s*.12,0))
            self.ico('cheek_'+str(s),(s*.145,-.200,1.102),(.038,.009,.021),'blush')
        self.box('nose',(0,-.214,1.127),(.057,.045,.056),c['skin'],'head',.014)
        # Three-sided smile notch gives an expressive face without texture images.
        self.mesh('smile',[(-.050,-.213,1.083),(0,-.220,1.065),(.050,-.213,1.083),(.040,-.216,1.061),(0,-.222,1.048),(-.040,-.216,1.061)],[(0,1,4,5),(1,2,3,4)],'eye',bone='head')
        if c.get('mustache'):
            for s in (-1,1):self.box('mustache_'+str(s),(s*.036,-.233,1.091),(.088,.026,.035),c['hair'],'head',.01,rot=(0,s*.12,0))
        if c.get('glasses'):
            for s in (-1,1):self.ring('glasses_'+str(s),(s*.103,-.227,1.18),.067,.011,'eye')
            self.box('glasses_bridge',(0,-.229,1.18),(.075,.02,.012),'eye','head',.003)
            for s in (-1,1):self.box('glasses_arm_'+str(s),(s*.185,-.09,1.18),(.014,.26,.014),'eye','head',.003)
        self.box('hair_cap',(0,.022,1.35),(.46,.39,.15),c['hair'],'head',.035)
        style=c['style']
        if style in ('bob','square'):
            self.box('hair_back',(0,.162,1.195),(.47,.13,.36),c['hair'],'head',.025)
            for s in (-1,1):self.box('hair_side_'+str(s),(s*.205,.025,1.20),(.10,.32,.32 if style=='bob' else .21),c['hair'],'head',.022)
            for i,x in enumerate((-.16,-.055,.055,.16)):
                self.box('fringe_'+str(i),(x,-.177,1.315),(.11,.10,.16 if i%2==0 else .12),c['hair'],'head',.018,rot=(0,(-.07+i*.04),0))
        elif style=='curls':
            for i,(x,y,z) in enumerate([(-.21,.07,1.30),(.21,.07,1.30),(-.22,.10,1.15),(.22,.10,1.15),(-.15,.19,1.23),(.03,.20,1.23),(.17,.19,1.23),(-.17,-.12,1.36),(-.05,-.14,1.37),(.08,-.13,1.37),(.19,-.10,1.35)]):
                self.ico('curl_'+str(i),(x,y,z),(.088,.084,.085),c['hair'])
        elif style=='quiff':
            for i,x in enumerate((-.17,-.055,.06,.17)):
                self.box('quiff_'+str(i),(x,-.11,1.40+(.035 if i==1 else 0)),(.14,.27,.16),c['hair'],'head',.022,rot=(.12,-.08,0))
        elif style=='waves':
            for i,x in enumerate((-.17,-.05,.08,.19)):
                self.ico('wave_'+str(i),(x,-.12,1.34),(.087,.09,.10),c['hair'])
        else:
            for i,x in enumerate((-.15,-.05,.05,.15)):self.box('short_fringe_'+str(i),(x,-.17,1.33),(.105,.08,.10),c['hair'],'head',.015)
        self.hat(c.get('hat'))
    def hat(self,style):
        if not style:return
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
            self.box('cap_brim',(0,-.24,1.365),(.44,.23,.055),color,'head',.015)
            self.box('cap_button',(0,.025,1.54),(.045,.045,.035),color,'head',.009)
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
            specs['foot_goal_'+side]=((sign*.12,0,.11),(sign*.12,0,.23))
            specs['knee_pole_'+side]=((sign*.12,-.55,.4),(sign*.12,-.55,.50))
            specs['hand_goal_'+side]=(REST['hand_'+side][0],tuple(Vector(REST['hand_'+side][0])+Vector((0,0,.1))))
            specs['elbow_pole_'+side]=((sign*.60,-.08,.75),(sign*.60,-.08,.85))
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
        seat_plane=.655/math.cos(math.radians(35))
        self.sockets={'ground':[0,0,0],'seat_contact':[0,0,seat_plane],'hand_left':list(REST['hand_L'][0]),'hand_right':list(REST['hand_R'][0]),'mouth':[0,-.22,1.08]}
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
        self.root['footprint_cells']=json.dumps([1,1]);self.root['ground_root']=json.dumps([0,0,0]);self.root['anatomy_height']=1.72 if self.cfg.get('hat')=='chef' else 1.65 if self.cfg.get('hat') else 1.47
        self.root['sockets']=json.dumps(self.sockets);self.root['animation_recipes']=json.dumps(clips);self.root['identity_design']=json.dumps(self.cfg)
        self.root['source']='character_builders.py';self.root['weight_validation']=json.dumps(self.weight_stats)
        self.root['seat_environment_z']=.655
        self.root['seat_character_plane']=seat_plane
        self.root['seat_pelvis_offset']=.105
        self.root['seat_attachment']='seat contact at environment0.655/cos35; pelvis control0.105 above contact surface; common projected world ground root, do not apply stool height twice'
        pose('idle' if self.cfg['kind']=='chef' else 'stand',0)
        return {'root':self.root,'collection':self.collection,'armature':arm,'parts':self.parts,'clips':clips,'pose':pose,'reset':reset,'sockets':self.sockets,'height':self.root['anatomy_height'],'footprint':[1,1],'directions':['N','E','S','W'],'weight_validation':self.weight_stats,'identity':self.cfg,'layer_tags':self.layer_tags,'rest_matrices':rest_mats,'sockets_current':lambda world=False:evaluated_sockets({'armature':arm,'root':self.root},world)}


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
    phase=math.tau*t;sin=math.sin;cos=math.cos
    seated=1. if clip in ('seated_wait','eat') else _smooth(t) if clip=='sit_down' else 1-_smooth(t) if clip=='stand_up' else 0.
    seat_plane=float(builder.root.get('seat_character_plane',.655/math.cos(math.radians(35))))
    seat_hip=seat_plane+float(builder.root.get('seat_pelvis_offset',.105))
    hip=Vector((0,0,.65+(seat_hip-.65)*seated));lean=.025*sin(phase);head_yaw=.025*sin(phase*.5);head_tilt=0.
    arm_targets={s:Vector(REST['hand_'+s][0]) for s in ('L','R')}
    hand_dirs={s:Vector((0,-.01,-.07)) for s in ('L','R')}
    feet={s:Vector(REST['foot_'+s][0]) for s in ('L','R')}
    foot_tilt={'L':0.,'R':0.}
    if clip in ('idle','stand'):
        hip.z+=.0018*sin(phase);lean=.012*sin(phase)
        for s in ('L','R'):arm_targets[s].y-=.008*sin(phase+(0 if s=='L' else .5))
    elif clip=='work':
        lean=.09+.025*sin(phase*2)
        arm_targets['L']=Vector((-.14,-.19,.79+.018*sin(phase)))
        arm_targets['R']=Vector((.13,-.20,.80+.045*sin(phase*2)))
        hand_dirs={s:Vector((0,-.065,-.015)) for s in ('L','R')};head_yaw=.03*sin(phase)
    elif clip=='hold':
        lean=.018*sin(phase)
        arm_targets['R']=Vector((.16,-.22,.79+.006*sin(phase)))
        arm_targets['L']=Vector((-.25,-.06,.66+.006*sin(phase+.3)))
        hand_dirs['R']=Vector((0,-.07,0));head_yaw=.04*sin(phase)
    elif clip=='load':
        u=sin(math.pi*t);lean=.14*u
        arm_targets['R']=_lerp((.16,-.22,.79),(.16,-.29,.82),u)
        arm_targets['L']=_lerp((-.25,-.06,.66),(-.15,-.18,.78),u*.7)
        hand_dirs['R']=Vector((0,-.07,-.005));head_yaw=-.025*u
    if seated:
        for s,sign in [('L',-1),('R',1)]:
            feet[s]=_lerp(feet[s],(sign*.13,-.27,seat_plane-.17),seated)
            arm_targets[s]=_lerp(arm_targets[s],(sign*.18,-.17,.77),seated)
            hand_dirs[s]=_lerp(hand_dirs[s],(0,-.065,-.018),seated)
        lean=.018*sin(phase)
        if clip=='seated_wait':
            head_yaw=.055*sin(phase);head_tilt=.025*sin(phase)
            arm_targets['R'].z+=.012*sin(phase)
        elif clip=='eat':
            lift=(sin(phase)+1)*.5
            arm_targets['R']=_lerp((.14,-.22,.78),(.08,-.20,1.04),lift)
            arm_targets['L']=Vector((-.15,-.23,.78))
            hand_dirs['R']=Vector((0,-.065,.005));head_tilt=.025*sin(phase)
    if clip in ('walk','panic'):
        quick=2 if clip=='panic' else 1
        for s,off in [('L',0),('R',.5)]:
            g=(t*quick+off)%1
            # Canonical front is -Y. During stance the grounded sole travels
            # rearward relative to the body; forward root motion cancels it.
            if g<.5:y=-.14+.56*g;z=.11
            else:
                u=(g-.5)*2;y=.14-.28*u;z=.11+.085*sin(math.pi*u)
            feet[s].y=y;feet[s].z=z
            arm_targets[s].y+=(-.085 if s=='L' else .085)*sin(phase*quick)
            arm_targets[s].z+=.025*cos(phase*quick)
        hip.z=.625+.006*cos(phase*quick*2);lean=.08 if clip=='panic' else .025
        if clip=='panic':head_yaw=.18*sin(phase);arm_targets['L'].z+=.10;arm_targets['R'].z+=.10
    elif clip=='happy':
        hop=sin(math.pi*t)**2;hip.z+=.10*hop
        for s,sign in [('L',-1),('R',1)]:
            feet[s].z+=.10*hop;arm_targets[s]=_lerp(arm_targets[s],(sign*.37,-.03,.98),hop)
        head_tilt=-.07*hop
    elif clip=='restless':
        hip.x=.025*sin(phase);hip.z=.643+.004*cos(phase*2);head_yaw=.13*sin(phase)
        feet['R'].z+=.035*max(0,sin(phase));foot_tilt['R']=.08*max(0,sin(phase))
        arm_targets['R']=Vector((.25,-.08,.72+.03*sin(phase)))
    elif clip=='puzzled':
        head_tilt=.14*sin(phase);head_yaw=.09*sin(phase+.4)
        arm_targets['R']=Vector((.24,-.09,.98+.025*sin(phase)))
        hand_dirs['R']=Vector((-.035,-.015,.06))
        arm_targets['L']=Vector((-.22,-.08,.69))
    # Upper-body transform deliberately bends around the pelvis. Ground controls
    # stay fixed for planted clips, independent of breathing/cooking motion.
    rot=Matrix.Rotation(lean,3,'X')
    rest_hip=Vector((0,0,.65))
    def upper(p):return hip+rot@(Vector(p)-rest_hip)
    desired={'ground':rest_mats['ground'].copy()}
    for name in ('pelvis','spine','neck','head'):
        a,c=REST[name]
        if name=='pelvis' and seated:
            offset=hip-rest_hip
            desired[name]=frame(Vector(a)+offset,Vector(c)+offset)
        else:desired[name]=frame(upper(a),upper(c))
    desired['head']=desired['head']@Matrix.Rotation(head_yaw,4,'Y')@Matrix.Rotation(head_tilt,4,'Z')
    actual_hands={}
    for s,sign in [('L',-1),('R',1)]:
        # The small hip offset is inherited by hands as well as shoulder sockets.
        wrist=arm_targets[s]+Vector((hip.x,0,hip.z-.65))
        shoulder=upper(REST['upper_arm_'+s][0]);elbow_pole=Vector((sign*.64,-.02,.77))+Vector((hip.x,0,hip.z-.65))
        l1=(Vector(REST['upper_arm_'+s][1])-Vector(REST['upper_arm_'+s][0])).length
        l2=(Vector(REST['forearm_'+s][1])-Vector(REST['forearm_'+s][0])).length
        elbow,wrist=_two_bone(shoulder,wrist,l1,l2,elbow_pole)
        desired['upper_arm_'+s]=frame(shoulder,elbow);desired['forearm_'+s]=frame(elbow,wrist);desired['hand_'+s]=frame(wrist,wrist+hand_dirs[s])
        hip_joint=hip+Vector((sign*.12,0,0));ankle=feet[s];pole=Vector((sign*.12,-.65,.42))
        l1=(Vector(REST['thigh_'+s][1])-Vector(REST['thigh_'+s][0])).length
        l2=(Vector(REST['shin_'+s][1])-Vector(REST['shin_'+s][0])).length
        knee,ankle=_two_bone(hip_joint,ankle,l1,l2,pole)
        desired['thigh_'+s]=frame(hip_joint,knee);desired['shin_'+s]=frame(knee,ankle)
        desired['foot_'+s]=frame(ankle,ankle+Vector((0,-.16,.16*foot_tilt[s])))
        desired['foot_goal_'+s]=frame(feet[s],feet[s]+Vector((0,0,.12)))
        desired['knee_pole_'+s]=frame(pole,pole+Vector((0,0,.1)))
        desired['hand_goal_'+s]=frame(wrist,wrist+Vector((0,0,.1)))
        desired['elbow_pole_'+s]=frame(elbow_pole,elbow_pole+Vector((0,0,.1)))
        actual_hands[s]=list(wrist+hand_dirs[s]*.6)
    # Convert desired global armature-space matrices into native parent-relative
    # basis transforms using explicit parent goals, avoiding update-order drift.
    for name,pb in arm.pose.bones.items():
        target=desired.get(name,rest_mats[name])
        if pb.parent:
            parent=pb.parent.name
            basis=(desired.get(parent,rest_mats[parent])@rest_mats[parent].inverted()@rest_mats[name]).inverted()@target
        else:basis=rest_mats[name].inverted()@target
        pb.matrix_basis=basis
    arm['current_clip']=clip;arm['current_phase']=t;arm['hand_sockets_current']=json.dumps(actual_hands)
    arm['seat_contact_current']=json.dumps([hip.x,0,hip.z-.105]);arm['hip_control_current']=json.dumps(list(hip));arm['feet_current']=json.dumps({s:list(feet[s]) for s in feet})
    bpy.context.view_layer.update()
    sockets=evaluated_sockets({'armature':arm,'root':builder.root})
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
        'hand_left':('hand_L',Vector(REST['hand_L'][0])+Vector((0,-.007,-.04))),
        'hand_right':('hand_R',Vector(REST['hand_R'][0])+Vector((0,-.007,-.04))),
        'mouth':('head',Vector((0,-.225,1.08))),
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
    root['seat_character_plane']=float(height)/math.cos(math.radians(elevation_degrees))
    character['sockets']['seat_contact']=[0,0,root['seat_character_plane']]
    root['sockets']=json.dumps(character['sockets'])
