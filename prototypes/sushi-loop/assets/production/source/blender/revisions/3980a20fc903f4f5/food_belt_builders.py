"""Native food, seamless tile floors and directed conveyor authoring for issue33.
All dimensions in world cells; X right, -Y screen depth, Z up.
"""
import bpy, math, importlib.util
from pathlib import Path
from mathutils import Vector

# Load beside this source so fresh builds and in-place native corner fixes use
# exactly the same stationary support recipe, including when loaded via MCP.
_support_spec=importlib.util.spec_from_file_location('s33_corner_supports',str(Path(__file__).with_name('catalog_corner_supports.py')))
_corner_supports=importlib.util.module_from_spec(_support_spec);_support_spec.loader.exec_module(_corner_supports)

def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def mat(name,color):
    key='S33_FB_'+name;m=bpy.data.materials.get(key)
    if m:return m
    rgb=tuple(linear(int(color[i:i+2],16)/255) for i in (0,2,4));m=bpy.data.materials.new(key);m.use_nodes=True;m.diffuse_color=(*rgb,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.85
    return m
M={k:mat(k,c) for k,c in {'red':'E3493F','red_dark':'A32E31','wood':'B77B3C','wood_dark':'77512F','cream':'F6E0B4','white':'FFF5DF','rice':'FFF4D7','salmon':'F87B42','salmon_light':'FFC09A','nori':'253A3B','cucumber':'79C953','cucumber_light':'B8E381','eel':'914A23','eel_sauce':'CF853A','blue':'66BAD7','blue_dark':'4AA0C5','water':'21B8CD','water_dark':'19AEC9','deck':'38414B','metal':'68757B'}.items()}

class B:
    def __init__(self,aid):
        self.aid=aid;self.parts={};self.collection=bpy.data.collections.new('S33_FB_'+aid);bpy.context.scene.collection.children.link(self.collection)
        self.root=bpy.data.objects.new(aid+'__root',None);self.collection.objects.link(self.root);self.sockets={};self.footprint=[1,1]
    def add(self,o,name,material=None):
        o.name=self.aid+'__'+name
        for c in list(o.users_collection):c.objects.unlink(o)
        self.collection.objects.link(o);o.parent=self.root;self.parts[name]=o
        if material:o.data.materials.append(material)
        return o
    def box(self,n,p,s,m,bevel=.015):
        bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=self.add(bpy.context.object,n,m);o.dimensions=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        if bevel:mod=o.modifiers.new('Small flat bevel','BEVEL');mod.width=bevel;mod.segments=1
        return o
    def cyl(self,n,p,r,d,m,vertices=16):
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=d,location=p);return self.add(bpy.context.object,n,m)
    def mesh(self,n,verts,faces,m,uv=None):
        mesh=bpy.data.meshes.new(self.aid+'__'+n);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(self.aid+'__'+n,mesh);self.collection.objects.link(o);o.parent=self.root;o.data.materials.append(m);self.parts[n]=o
        if uv:
            layer=mesh.uv_layers.new(name='Flow')
            for poly in mesh.polygons:
                for li in poly.loop_indices:layer.data[li].uv=uv[mesh.loops[li].vertex_index]
        return o
    def finish(self,height,clips=None,pose=None):
        clips=clips or {'static':{'frames':1,'fps':12,'loop':False,'static':True}}
        def reset():return None
        return {'root':self.root,'collection':self.collection,'parts':self.parts,'footprint':self.footprint,'height':height,'sockets':self.sockets,'directions':['N','E','S','W'],'clips':clips,'pose':pose or (lambda c,t:None),'reset':reset}

def food(aid):
    b=B(aid)
    # Thin faceted porcelain rim and inset keep all three recipes recognizable.
    b.cyl('plate_foot',(0,0,.018),.22,.036,M['cream'],20)
    b.cyl('porcelain_plate',(0,0,.045),.285,.032,M['white'],24)
    if aid=='dish-salmon':
        b.box('rice_mound',(0,0,.12),(.37,.27,.14),M['rice'],.045)
        b.box('salmon_fillet',(0,-.012,.214),(.405,.29,.075),M['salmon'],.025)
        for i,x in enumerate([-.13,-.035,.06,.15]):
            stripe=b.box('salmon_fat_'+str(i),(x,-.013,.254),(.016,.285,.003),M['salmon_light'],.001);stripe.rotation_euler.z=-.20
    elif aid=='dish-cucumber':
        b.cyl('nori',(0,0,.16),.183,.218,M['nori'],16)
        b.cyl('rice_center',(0,0,.271),.151,.009,M['rice'],16)
        for i,(x,y) in enumerate([(-.045,-.025),(.044,-.028),(.0,.048)]):b.box('cucumber_'+str(i),(x,y,.283),(.075,.075,.023),M['cucumber' if i%2==0 else 'cucumber_light'],.008)
    else:
        b.box('eel_rice',(0,0,.122),(.36,.28,.145),M['rice'],.035)
        b.box('eel_roll_nori',(0,0,.16),(.38,.294,.075),M['nori'],.008)
        b.box('eel_fillet',(0,0,.235),(.395,.29,.095),M['eel'],.026)
        for i in range(4):b.box('glaze_'+str(i),(-.145+i*.097,0,.287),(.023,.27,.006),M['eel_sauce'],.003)
        for i,(x,y) in enumerate([(-.12,-.09),(-.06,.06),(.02,-.04),(.09,.09),(.14,-.07)]):b.box('sesame_'+str(i),(x,y,.292),(.025,.012,.004),M['white'],.001)
    b.sockets['plate_center']=[0,0,.05]
    # Deliberate anatomy-relative scale, shared by world/held/bubble instances.
    # A plate is 0.342 cells wide, about three quarters of a character head.
    b.root.scale=(.6,.6,.6)
    return b.finish(.186)

def floor(aid):
    b=B(aid)
    material=M['water'] if aid=='floor-underwater' else M['cream']
    b.mesh('full_square',[(-.501,-.501,0),(.501,-.501,0),(.501,.501,0),(-.501,.501,0)],[(0,1,2,3)],material)
    if aid=='floor-checker':
        for x,y in [(-.25,-.25),(.25,.25)]:b.box('quiet_checker'+str(x),(x,y,.001),(.5,.5,.001),M['white'],0)
    if aid in ['floor-blue-wave','floor-underwater']:
        # Periodic sine bands meet opposite edges exactly; no raised front wall.
        for row in range(3 if aid=='floor-blue-wave' else 2):
            verts=[]
            center=-.5+(row+.5)/(3 if aid=='floor-blue-wave' else 2)
            for i in range(65):
                x=-.501+i*1.002/64;y=center+.045*math.sin((x+.5)*math.tau)
                verts.extend([(x,y-.055,.002),(x,y+.055,.002)])
            faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(64)]
            b.mesh('periodic_wave_'+str(row),verts,faces,M['blue'] if aid=='floor-blue-wave' else M['water_dark'])
    return b.finish(.002)

def deck_material(aid):
    m=bpy.data.materials.new('S33_'+aid+'_moving_deck');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links
    shader=next(x for x in n if x.type=='BSDF_PRINCIPLED');shader.inputs['Roughness'].default_value=.82
    uv=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],sep.inputs[0])
    mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=7;l.new(sep.outputs[0],mul.inputs[0])
    phase=n.new('ShaderNodeValue');phase.label='Deck travel phase';phase.outputs[0].default_value=0
    add=n.new('ShaderNodeMath');add.operation='ADD';l.new(mul.outputs[0],add.inputs[0]);l.new(phase.outputs[0],add.inputs[1])
    frac=n.new('ShaderNodeMath');frac.operation='FRACT';l.new(add.outputs[0],frac.inputs[0])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='CONSTANT'
    for el in list(ramp.color_ramp.elements)[2:]:ramp.color_ramp.elements.remove(el)
    ramp.color_ramp.elements[0].position=0;ramp.color_ramp.elements[0].color=(.039,.052,.064,1)
    ramp.color_ramp.elements[1].position=.13;ramp.color_ramp.elements[1].color=(.066,.080,.094,1)
    rim=ramp.color_ramp.elements.new(.18);rim.color=(.087,.105,.116,1)
    main=ramp.color_ramp.elements.new(.23);main.color=(.066,.080,.094,1)
    l.new(frac.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],shader.inputs['Base Color'])
    return m,phase

def belt(aid):
    b=B(aid);z=.64;deck,phase=deck_material(aid)
    # Build in a canonical straight (N->S) or N->E quarter turn then rotate
    # the actual geometry's orientation empty, retaining a separate ground root.
    corner='corner' in aid
    if corner:
        verts=[];uv=[];segments=48;L=math.pi*.25
        for i in range(segments+1):
            q=i/segments;angle=math.pi+q*math.pi/2
            # Gradually fan slats on the turn while matching derivative at ports.
            s=q*L;u=s+(1-L)*(3*q*q-2*q*q*q)
            for radius in [.15,.85]:verts.append((.5+radius*math.cos(angle),.5+radius*math.sin(angle),z));uv.append((u,0 if radius==.15 else 1))
        faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(segments)]
        b.mesh('connected_turn_deck',verts,faces,deck,uv)
        for label,r0,r1 in [('inside',.065,.15),('outside',.85,.935)]:
            vs=[]
            for i in range(segments+1):
                a=math.pi+i/segments*math.pi/2
                for rr,zz in [(r0,z-.10),(r1,z-.10),(r1,z+.035),(r0,z+.035)]:vs.append((.5+rr*math.cos(a),.5+rr*math.sin(a),zz))
            fs=[]
            for i in range(segments):
                for k in range(4):fs.append((4*i+k,4*i+(k+1)%4,4*(i+1)+(k+1)%4,4*(i+1)+k))
            b.mesh('stationary_'+label+'_rail',vs,fs,M['red'])
        parts=aid.split('-');inp,out=parts[-2].upper(),parts[-1].upper()
        quarter={frozenset(['N','E']):0,frozenset(['E','S']):-math.pi/2,frozenset(['S','W']):math.pi,frozenset(['W','N']):math.pi/2}[frozenset([inp,out])]
        canonical={'N':'N','E':'E'}
        # A corner's ports rotate with its actual geometry. Reverse flow uses -u.
        base_in={0:'N',-math.pi/2:'E',math.pi:'S',math.pi/2:'W'}[quarter]
        reverse=inp!=base_in
    else:
        verts=[(-.35,.5,z),(.35,.5,z),(.35,-.5,z),(-.35,-.5,z)]
        b.mesh('connected_straight_deck',verts,[(0,1,2,3)],deck,[(0,0),(0,1),(1,1),(1,0)])
        for x in [-.3925,.3925]:b.box('stationary_rail_'+str(x),(x,0,z-.033),(.085,1,.135),M['red'],0)
        suffix=aid.split('-')[-1].upper();quarter={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[suffix];reverse=False
        inp={'N':'S','E':'W','S':'N','W':'E'}[suffix];out=suffix
        if 'start' in aid:b.box('start_cap',(0,.46,z-.015),(.87,.08,.16),M['red'],.01);inp=None
        if 'end' in aid:b.box('end_cap',(0,-.46,z-.015),(.87,.08,.16),M['red'],.01);out=None
    # No outline or cap at connecting ports. Corner supports follow the same
    # arc as the deck; straight/start/end supports retain their original shape.
    support_recipe=None
    if corner:
        support_recipe=_corner_supports.add(b,M['wood'],M['wood_dark'])
    else:
        for x in [-.28,.28]:
            for y in [-.28,.28]:b.box('wood_leg_'+str((x,y)),(x,y,.25),(.10,.10,.50),M['wood_dark'],.008)
        b.box('lower_wood_frame',(0,0,.47),(.74,.74,.10),M['wood'],.015)
    orient=bpy.data.objects.new(aid+'__orientation',None);b.collection.objects.link(orient);orient.parent=b.root
    for part in b.parts.values():part.parent=orient
    orient.rotation_euler.z=quarter
    def pose(clip,t):phase.outputs[0].default_value=(7*t if reverse else -7*t)
    result=b.finish(.68,{'running':{'frames':24,'fps':12,'loop':True}},pose)
    if support_recipe:_corner_supports.record(result,support_recipe)
    result['flow']={'incoming':inp,'outgoing':out,'deckHeight':z,'periodCells':1/7,'durationSeconds':2,'speedCellsPerSecond':.5,'turnPhaseMapping':'endpoint derivative matched, compressed radially inside turn'}
    b.sockets['deck']=[0,0,z]
    result['phaseNode']=phase
    return result

def create_asset(aid):
    if aid.startswith('dish-'):return food(aid)
    if aid.startswith('floor-'):return floor(aid)
    if aid.startswith('belt-'):return belt(aid)
    raise ValueError(aid)
