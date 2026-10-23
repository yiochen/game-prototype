"""Issue33 independent world components and exactly joined environment modules.
Native Blender geometry authoring only; no camera/render/publish/scene deletion.
Depends on sibling prop_builders.py. One world unit per logical square tile.
"""
import bpy
import math
import json
import importlib.util
import pathlib
import sys
from mathutils import Vector
try:
    import prop_builders as P
except ModuleNotFoundError:
    _path=pathlib.Path(globals().get('__file__','/private/tmp/sushi33-production/world_components.py')).with_name('prop_builders.py')
    _spec=importlib.util.spec_from_file_location('prop_builders',str(_path))
    P=importlib.util.module_from_spec(_spec);sys.modules['prop_builders']=P;_spec.loader.exec_module(P)

STATIC={'static':{'frames':1,'fps':12,'loop':False,'static':True}}
DIRECTION_POINTS={'W':(-.5,0,0),'E':(.5,0,0),'N':(0,.5,0),'S':(0,-.5,0)}


def finish(b,ports=None,clips=None,nonblocking=False,layer='world',context=None):
    ports=ports or []
    b.root['ports']=json.dumps(ports);b.root['nonblocking']=bool(nonblocking);b.root['depth_layer']=layer
    b.root['support_cells']=json.dumps([] if nonblocking else [[x,y] for y in range(b.footprint[1]) for x in range(b.footprint[0])])
    if context:b.root['composition_context']=json.dumps(context)
    result=b.finish(clips or STATIC)
    result.update(ports=ports,nonblocking=nonblocking,depth_layer=layer,composition_context=context or {})
    return result


def port(direction,profile,height=0):
    x,y,z=DIRECTION_POINTS[direction]
    return {'direction':direction,'position':[x,y,z+height],'profile':profile,'normal':{'W':[-1,0,0],'E':[1,0,0],'N':[0,1,0],'S':[0,-1,0]}[direction]}


def _loft(b,name,centers,profile,color='rock',variation=0):
    """Extrude one real connected watertight mesh along a declared centerline.
    Start/end ring coordinates equal the shared profile exactly. Intermediate
    ring detail is permitted only between the cell ports, never at the seam.
    """
    verts=[];count=len(profile)
    for i,p in enumerate(centers):
        p=Vector(p)
        tangent=Vector(centers[min(i+1,len(centers)-1)])-Vector(centers[max(i-1,0)])
        tangent.z=0;tangent.normalize();normal=Vector((-tangent.y,tangent.x,0))
        for j,(width,z) in enumerate(profile):
            dz=(variation*math.sin(j*1.7+i*.9) if 1<i<len(centers)-2 and z>.05 else 0)
            verts.append(tuple(p+normal*width+Vector((0,0,z+dz))))
    faces=[tuple(reversed(range(count))),tuple((len(centers)-1)*count+j for j in range(count))]
    for ring in range(len(centers)-1):
        for j in range(count):faces.append((ring*count+j,ring*count+(j+1)%count,(ring+1)*count+(j+1)%count,(ring+1)*count+j))
    o=b.mesh(name,verts,faces,color)
    tones={'wood':('wood_light','wood_dark'),'wood_light':('wood_end','wood'),'wood_dark':('wood','wood_dark'),'blue':('blue_light','blue_dark'),'blue_dark':('blue','blue_dark'),'metal_dark':('metal','metal_dark')}
    light,dark=tones.get(color,('rock_light','rock_dark'))
    o.data.materials.append(P.mat(light));o.data.materials.append(P.mat(dark))
    for face in o.data.polygons:
        if face.index>1:face.material_index=(1 if face.normal.z>.4 else 2 if (face.index-2)%count in (0,count-1) else 0)
    return o


def _path(variant):
    if variant=='corner':return [(-.5,0,0),(-.25,0,0),(0,0,0),(0,.25,0),(0,.5,0)]
    if variant=='end':return [(-.5,0,0),(-.2,0,0),(.14,0,0),(.34,0,0)]
    return [(-.5,0,0),(-.35,0,0),(-.10,0,0),(.10,0,0),(.35,0,0),(.5,0,0)]


def _ports(variant,profile):
    return [port('W',profile)]+([port('N',profile)] if variant=='corner' else [] if variant=='end' else [port('E',profile)])


def build_wall(b,variant):
    b.height=1.02;profile='restaurant-wall-wood-blue-v1'
    path=_path('corner' if 'corner' in variant else 'end' if variant=='end' else 'middle')
    if variant=='outer-corner':path=[(-.5,0,0),(-.25,0,0),(0,0,0),(0,-.25,0),(0,-.5,0)]
    # Exact continuous lower wall; separate horizontal boards, top coping and trim.
    _loft(b,'wall_panel',path,[(-.105,.07),(.105,.07),(.105,.89),(-.105,.89)],'wood_light')
    for j,z in enumerate((.12,.34,.56,.78)):
        _loft(b,'horizontal_board_'+str(j),[(x,y,z) for x,y,_ in path],[(-.115,0),(.115,0),(.115,.025),(-.115,.025)],'wood')
    _loft(b,'wood_cap',[(x,y,.86) for x,y,_ in path],[(-.15,0),(.15,0),(.15,.075),(-.15,.075)],'wood_dark')
    _loft(b,'blue_coping',[(x,y,.93) for x,y,_ in path],[(-.18,0),(.18,0),(.18,.04),(.12,.08),(-.12,.08),(-.18,.04)],'blue')
    for y in (-.12,.12):b.box('center_upright_'+str(y),(0,y,.48),(.065,.025,.78),'wood_dark',.005)
    if variant=='end':b.box('finished_end_post',(.34,0,.51),(.14,.30,1.02),'wood',.015)
    if variant=='inner-corner':
        b.box('inside_corner_tenon',(0,0,.48),(.19,.19,.81),'wood_dark',.01)
    ports=_ports('corner' if 'corner' in variant else 'end' if variant=='end' else 'middle',profile)
    if variant=='outer-corner':ports=[port('W',profile),port('S',profile)]
    b.notes.append('Perimeter-only dressing. Top coping and panel rings meet the exact shared port cross-section; no access mechanic.')
    return finish(b,ports)


def build_post_rope(b):
    b.height=.72
    # Genuine half posts stop exactly on each cell boundary. Repeated modules
    # reconstruct one full post, rather than overlapping two full cylinders.
    def half_post(name,x,r,z0,z1,color):
        angles=[-math.pi/2+i*math.pi/4 for i in range(5)] if x<0 else [math.pi/2+i*math.pi/4 for i in range(5)]
        ring=[(x+r*math.cos(a),r*math.sin(a)) for a in angles]
        verts=[(vx,vy,z0) for vx,vy in ring]+[(vx,vy,z1) for vx,vy in ring]
        faces=[tuple(reversed(range(5))),tuple(range(5,10))]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
        b.mesh(name,verts,faces,color)
    for x in (-.5,.5):
        half_post('half_post_'+str(x),x,.10,0,.68,'wood_end')
        for z in (.49,.57):half_post('rope_binding_'+str(x)+str(z),x,.108,z-.0125,z+.0125,'cream')
        half_post('post_cap_'+str(x),x,.115,.68,.715,'wood_light')
    for i in range(8):
        x0=-.5+i*.125;x1=x0+.125
        z0=.53-.12*(1-(x0/.5)**2);z1=.53-.12*(1-(x1/.5)**2)
        b.beam('sag_rope_'+str(i),(x0,0,z0),(x1,0,z1),.042,'cream')
    return finish(b,[port('W','dock-rope-v1',.53),port('E','dock-rope-v1',.53)])


def build_dock_floor(b):
    b.footprint=(3,3);b.height=.25
    for i in range(12):b.box('full_plank_'+str(i),(-1.375+i*.25,0,.13),(.238,3.,.18),'wood_light' if i%3==0 else 'wood',.008)
    for x in (-1.17,1.17):b.box('under_joist_'+str(x),(x,0,.035),(.18,3.,.07),'wood_dark',.008)
    for x in (-1.375,-.375,.625,1.375):
        for y in (-1.28,1.28):b.cyl('nail_'+str(x)+str(y),(x,y,.224),.014,.008,'metal_dark',6)
    return finish(b,context={'layoutCells':[3,3],'workshopRoot':[.78,.35,.23],'submarineRoot':[-.70,-.42,.23],'entryRoot':[0,-1.5,0]})


def build_dock_entry(b):
    b.height=.49
    for i in range(4):
        z=.04+i*.045
        b.box('step_plank_'+str(i),(0,-.375+i*.25,z),(.96,.24,.10),'wood_light' if i%2 else 'wood',.012)
    for x in (-.43,.43):
        b.box('short_post_'+str(x),(x,.28,.22),(.10,.10,.44),'wood_dark',.01)
        b.box('post_cap_'+str(x),(x,.28,.455),(.16,.16,.055),'wood_light',.01)
    b.socket('entry',(0,-.5,0));b.socket('dock',(0,.5,.23))
    return finish(b,context={'layoutCells':[3,3],'compositionOffset':[0,-1.5,0]})


def build_hut(b):
    b.height=1.81
    b.box('body',(0,0,.64),(.82,.86,1.20),'wood',.025)
    for i in range(5):b.box('front_plank_'+str(i),(-.32+i*.16,-.442,.64),(.15,.035,1.16),'wood_light' if i%3==0 else 'wood',.005)
    for x in (-.40,.40):b.box('corner_'+str(x),(x,0,.65),(.075,.90,1.25),'wood_dark',.008)
    b.box('door_frame',(-.12,-.48,.52),(.43,.10,.99),'wood_dark',.012)
    b.box('door',(-.12,-.54,.50),(.32,.035,.91),'wood_light',.01)
    b.cyl('door_knob',(-.01,-.565,.48),.024,.028,'gold',8,(math.pi/2,0,0))
    b.box('window_frame',(.25,-.478,.85),(.22,.075,.30),'wood_dark',.008)
    b.box('window_glass',(.25,-.520,.85),(.16,.015,.23),'yellow_light',.004)
    b.box('window_bar',(.25,-.532,.85),(.022,.015,.24),'wood',.002)
    b.box('window_cross',(.25,-.532,.85),(.17,.015,.022),'wood',.002)
    P._roof(b,0,0,1.25,1.06,1.13,'workshop_roof','aqua')
    b.box('chimney',(.25,.19,1.56),(.16,.16,.40),'rock_dark',.01)
    b.box('chimney_cap',(.25,.19,1.77),(.20,.20,.07),'rock',.01)
    b.socket('door',(-.12,-.56,0));b.notes.append('Independent workshop. In shared3x3 dock composition place to RIGHT of yellow submarine.')
    return finish(b,context={'layoutCells':[3,3],'compositionOffset':[.78,.35,.23],'submarineRoot':[-.70,-.42,.23]})


def build_dock_cover(b):
    b.footprint=(3,3);b.height=1.87
    xs=[-1.45+i*(2.9/6) for i in range(7)];ys=[-1.26,-.63,0,.63,1.26]
    # Stitched pitched tarp patches remain independent editable cloth panels.
    for iy in range(4):
        for ix in range(6):
            if iy==0 and ix in (1,2):continue # retained genuine peek opening
            x0,x1=xs[ix],xs[ix+1];y0,y1=ys[iy],ys[iy+1]
            z0=1.82-.52*abs(y0)/1.26;z1=1.82-.52*abs(y1)/1.26
            c=['sand','teal','sand','cream','blue_dark','sand'][(ix+iy*2)%6]
            b.mesh('tarp_patch_'+str(ix)+'_'+str(iy),[(x0,y0,z0),(x1,y0,z0),(x1,y1,z1),(x0,y1,z1)],[(0,1,2,3)],c)
            b.beam('stitched_seam_'+str(ix)+'_'+str(iy),(x0,y0,z0+.007),(x1,y0,z0+.007),.014,'wood_light')
    for x in (-1.45,1.45):
        b.beam('tie_rope_'+str(x),(x,-1.26,.24),(x,-1.26,1.30),.025,'cream')
    def covered(t):
        for n,o in b.parts.items():
            if n.startswith('tarp_patch'):o.location.z+=.007*math.sin(math.tau*t+o.name.count('1'))
    def uncover(t):
        u=t*t*(3-2*t)
        for n,o in b.parts.items():
            if not n.startswith('tie_rope'):
                o.scale.y*=1-.96*u;o.location.y+=1.24*u;o.location.z+=.10*math.sin(math.pi*u)
            else:o.scale.z*=1-.65*u
    b.motion.update(covered=covered,uncover=uncover)
    b.notes.append('Separate3x3 overhead patchwork cover. Genuine omitted front panels provide peek holes. Root and source geometry stay fixed while cover folds toward rear.')
    return finish(b,clips={'covered':{'frames':24,'fps':12,'loop':True},'uncover':{'frames':24,'fps':12,'loop':False}},nonblocking=True,layer='overhead',context={'layoutCells':[3,3],'compositionOffset':[0,0,.23],'workshopRoot':[.78,.35,.23],'submarineRoot':[-.70,-.42,.23]})


PROFILES={
 'rock-wall':[(-.34,0),(.34,0),(.34,.63),(.26,.94),(.12,1.10),(-.12,1.10),(-.27,.91),(-.34,.61)],
 'rock-shelf':[(-.45,0),(.45,0),(.45,.28),(.39,.43),(-.39,.43),(-.45,.28)],
 'reef':[(-.38,0),(.38,0),(.38,.20),(.25,.40),(.08,.44),(-.14,.35),(-.30,.40),(-.38,.20)],
 'rock-half-width':[(-.17,0),(.17,0),(.17,.64),(.12,.93),(-.12,.93),(-.17,.64)],
}


def build_terrain(b,family,variant):
    profile=PROFILES[family];path=_path(variant);pid=family+'-section-v1'
    b.height=.68 if family=='reef' else max(z for _,z in profile)+.02
    _loft(b,family+'_continuous_core',path,profile,'rock_dark' if family=='reef' else 'rock',.018 if family=='rock-wall' else .012)
    # Detail stays away from ports. Every incoming/outgoing cross-section remains
    # byte-for-byte the authored profile, including material/height at the seam.
    if family=='rock-wall':
        for i,(x,y,z,w,h) in enumerate([(-.21,-.343,.39,.27,.27),(.18,-.343,.62,.25,.33),(0,.341,.30,.35,.22)]):
            b.box('faceted_wall_inset_'+str(i),(x,y,z),(w,.018,h),'rock_dark' if i%2 else 'rock_light',.012)
        if variant=='edge':
            b.ico('weathered_edge_shard',(.05,-.37,.11),(.27,.12,.15),'rock_dark')
        elif variant=='end':
            b.box('end_face_strata',(.35,0,.47),(.025,.46,.035),'rock_dark',.005)
    elif family=='rock-shelf':
        # This is an actual broad low shelf, not a compressed wall copy.
        for i in range(3):
            x=-.25+i*.25
            b.box('top_crack_'+str(i),(x,-.04,.446),(.013,.48,.006),'rock_dark',0,rot=(0,0,.10*(-1 if i%2 else 1)))
        if variant=='edge':b.ico('shelf_flake',(0,-.39,.19),(.27,.14,.17),'rock')
        if variant=='end':b.box('exposed_shelf_end',(.35,0,.25),(.018,.73,.025),'rock_dark',0)
    elif family=='reef':
        for i,(x,y,z) in enumerate([(-.21,-.12,.52),(.03,.10,.59),(.23,-.10,.50)]):
            b.cyl('reef_coral_stem_'+str(i),(x,y,z-.11),.044,.23,'teal' if i%2 else 'purple',7)
            b.ico('reef_coral_tip_'+str(i),(x,y,z),(.06,.055,.07),'teal' if i%2 else 'purple')
        b.ico('reef_polyp',(.04,-.26,.30),(.12,.08,.08),'coral')
    if variant=='corner':
        # Keep trim off bent ports. Center dressing follows the real90deg turn.
        for n,o in b.parts.items():
            if n.startswith(('faceted_wall_inset','top_crack')):o.hide_render=True
    b.notes.append('Continuous native loft. Endpoint profile is exact; intermediate facets/detail never alter the seam. Match only identical profile IDs.')
    return finish(b,_ports(variant,pid))


def _rect_profile(width,z,height):return [(-width/2,z),(width/2,z),(width/2,z+height),(-width/2,z+height)]


def build_wreck(b,variant):
    path=_path(variant);b.height=.78;pid='wreck-frame-section-v1'
    # Open structure: three continuous beams, with actual space between rails.
    _loft(b,'lower_hull_rail',path,_rect_profile(.36,.04,.16),'blue_dark')
    _loft(b,'upper_hull_rail',path,_rect_profile(.18,.60,.14),'blue_dark')
    _loft(b,'back_hull_lip',path,[(.20,.16),(.26,.16),(.26,.35),(.20,.35)],'metal_dark')
    for i,(x,y) in enumerate([(-.22,0),(.22,0)] if variant!='corner' else [(-.23,0),(0,.23)]):
        if variant=='corner' and i==1:
            b.box('iron_rib_'+str(i),(x,y,.40),(.39,.075,.63),'rock_dark',.012)
            b.box('rib_plate_'+str(i),(x+.21,y,.41),(.025,.17,.19),'metal_dark',.006)
            for z in (.36,.46):b.cyl('rib_rivet_'+str(i)+str(z),(x+.228,y,z),.016,.018,'metal',6,(0,math.pi/2,0))
        else:
            b.box('iron_rib_'+str(i),(x,y,.40),(.075,.39,.63),'rock_dark',.012)
            b.box('rib_plate_'+str(i),(x,y-.21,.41),(.17,.025,.19),'metal_dark',.006)
            for z in (.36,.46):b.cyl('rib_rivet_'+str(i)+str(z),(x,y-.228,z),.016,.018,'metal',6,(math.pi/2,0,0))
    if variant=='edge':
        b.box('broken_sheet',(0,-.25,.20),(.55,.25,.04),'metal_dark',.008,rot=(.12,.13,.06))
    elif variant=='end':
        b.box('finished_cross_rib',(.34,0,.4),(.08,.43,.72),'rock_dark',.012)
    b.notes.append('Open old hull framing with continuous lower/top rails. No new barrier or gate mechanic.')
    return finish(b,_ports(variant,pid))


def build_slate_rock(b):
    b.height=.46
    for i,(x,y,scale) in enumerate([(-.18,.08,(.27,.24,.33)),(.20,.05,(.23,.22,.27)),(-.02,-.23,(.24,.20,.20))]):
        b.ico('slate_'+str(i),(x,y,scale[2]*.53),scale,'metal_dark' if i%2 else 'rock_dark')
    return finish(b,nonblocking=True,layer='perimeter')


def build_boulder(b):
    b.height=.86
    # Separate1cell design, not a scaled version of the older2x2 boulder.
    b.ico('main_boulder',(-.10,.07,.36),(.37,.34,.43),'rock')
    b.ico('flat_fore_stone',(.18,-.21,.17),(.28,.22,.22),'rock_dark')
    b.ico('rear_ridge',(.22,.22,.36),(.24,.22,.39),'rock')
    b.box('stone_fissure',(-.11,-.28,.36),(.016,.012,.29),'rock_dark',0,rot=(0,-.18,0))
    return finish(b)


def _extruded_silhouette(b,name,outline,depth,color):
    count=len(outline)
    verts=[(x,-depth/2,z) for x,z in outline]+[(x,depth/2,z) for x,z in outline]
    faces=[tuple(reversed(range(count))),tuple(range(count,count*2))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    return b.mesh(name,verts,faces,color)


def build_background_rock(b):
    b.height=.86
    # Quiet shallow faceted silhouette; intentionally no high contrast coral.
    for i,(x,w,h) in enumerate([(-.32,.27,.48),(-.08,.34,.84),(.23,.31,.65)]):
        outline=[(x-w/2,0),(x+w/2,0),(x+w/2,h*.8),(x+w*.2,h),(x-w*.32,h*.97),(x-w/2,h*.7)]
        _extruded_silhouette(b,'distant_rock_'+str(i),outline,.12,'356E91' if i%2 else '3D7A9B')
        b.mesh('distant_facet_'+str(i),[(x,-.061,.04),(x+w*.2,-.061,h),(x+w/2,-.061,h*.8),(x+w/2,-.061,0)],[(0,1,2,3)],'326684')
    return finish(b,nonblocking=True,layer='background')


def build_background_wreck(b):
    b.height=.75
    outline=[(-.49,.11),(.39,.07),(.49,.30),(.32,.36),(-.43,.36)]
    _extruded_silhouette(b,'distant_hull',outline,.12,'356E91')
    b.box('mast',(-.06,0,.51),(.045,.025,.47),'326684',.002,rot=(0,-.1,0))
    b.box('crossbar',(-.06,-.015,.63),(.47,.027,.035),'326684',.002,rot=(0,.05,0))
    b.box('cabin',(.20,.015,.43),(.21,.03,.16),'3D7A9B',.005)
    return finish(b,nonblocking=True,layer='background')


def _school_fish(b,name,pos,size):
    x,y,z=pos
    b.ico(name+'_body',(x,y,z),(size*.60,.018,size*.30),'3D87A8')
    tail=b.mesh(name+'_tail',[(-size*.44,0,0),(-size*.88,0,size*.30),(-size*.88,0,-size*.30)],[(0,1,2)],'3D87A8')
    tail.location=(x,y,z)
    b.mesh(name+'_fin',[(x-size*.05,y-.003,z+size*.15),(x+size*.16,y-.003,z+size*.37),(x+size*.28,y-.003,z+size*.17)],[(0,1,2)],'3D87A8')
    return tail


def build_background_fish(b):
    b.height=.79;tails=[]
    for i,(x,z,s) in enumerate([(-.22,.29,.25),(.23,.45,.30),(-.17,.66,.20)]):tails.append(_school_fish(b,'fish_'+str(i),(x,0,z),s))
    def swim(t):
        for i,o in enumerate(tails):o.rotation_euler.z=.13*math.sin(math.tau*t*2+i*.8)
        for o in b.parts.values():o.location.x+=.025*math.sin(math.tau*t)
    b.motion['swim']=swim
    return finish(b,clips={'swim':{'frames':24,'fps':12,'loop':True}},nonblocking=True,layer='background')


def build_light_shafts(b):
    b.height=1.65
    pale=P.mat('shaft_translucent','A3E5E2')
    principled=next(n for n in pale.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    principled.inputs['Alpha'].default_value=.12;pale.diffuse_color=(*pale.diffuse_color[:3],.12)
    if hasattr(pale,'surface_render_method'):pale.surface_render_method='DITHERED'
    elif hasattr(pale,'blend_method'):pale.blend_method='BLEND'
    for i,(x,w) in enumerate([(-.27,.16),(.17,.21)]):
        o=b.mesh('light_ribbon_'+str(i),[(x-w*.85,0,.03),(x+w*.85,0,.03),(x+w*.23,.01,1.65),(x-w*.23,.01,1.65)],[(0,1,2,3)],'cyan')
        o.data.materials.clear();o.data.materials.append(pale)
        cross=b.mesh('light_cross_ribbon_'+str(i),[(0,x-w*.85,.03),(0,x+w*.85,.03),(.01,x+w*.23,1.65),(.01,x-w*.23,1.65)],[(0,1,2,3)],'cyan')
        cross.data.materials.clear();cross.data.materials.append(pale)
    def ambient(t):
        for i,o in enumerate(b.parts.values()):o.location.x+=.015*math.sin(math.tau*t+i);o.scale.x*=1+.05*math.sin(math.tau*t+i)
    b.motion['ambient']=ambient
    return finish(b,clips={'ambient':{'frames':24,'fps':12,'loop':True}},nonblocking=True,layer='background-light')


def build_safe_passage(b):
    b.height=.53
    # One nonblocking flank-decoration module. Stage flanks3cells apart to leave
    # the continuous ship-sized clear lane required by the encounter concept.
    b.ico('quiet_flank_stone',(-.35,.16,.13),(.16,.23,.18),'rock')
    b.ico('quiet_base_stone',(-.23,-.19,.07),(.14,.13,.10),'rock_dark')
    leaves=P._kelp(b,(-.38,.23,.02),.45,'passage_kelp',3)
    for i,y in enumerate((-.31,-.02,.27)):
        b.box('safe_floor_inlay_'+str(i),(.26,y,.015),(.12,.04,.012),'aqua',.004)
    b.motion['ambient']=lambda t:P._kelp_sway(leaves,t,.045)
    b.notes.append('Nonblocking flank scenery, not an arch/gate. Compose left/right flanks3cells apart; empty centerlane remains free. No collision, timer or access rule.')
    return finish(b,clips={'ambient':{'frames':24,'fps':12,'loop':True}},nonblocking=True,layer='midground',context={'role':'passage-flank','minimumClearLaneCells':3,'mirroredFlankRoot':[3,0,0]})


ASSET_IDS=[
 'wall-middle','wall-inner-corner','wall-outer-corner','wall-end','dock-post-rope','dock-floor','dock-entry','workshop-hut','dock-cover',
 'slate-rock','rock-wall-middle','rock-wall-edge','rock-wall-corner','rock-wall-end',
 'rock-shelf-middle','rock-shelf-edge','rock-shelf-corner','rock-shelf-end',
 'reef-middle','reef-edge','reef-corner','reef-end','wreck-middle','wreck-edge','wreck-corner','wreck-end',
 'rock-half-width','boulder-underwater','decor-background-rock','decor-background-wreck','decor-background-fish','decor-light-shafts','safe-passage'
]
# Remaining stable entries delegate to distinct already-authored native props.
PROP_ALIASES={
 'plant-angular':'potted_plant','barrel-wood':'barrel','crate-wood':'crate','lantern-gold':'lantern','sign-blank':'blank_sign',
 'stool-wood':'stool_wood','stool-blue':'stool_blue','chef-blackboard':'chef_blackboard','garbage-sofa':'garbage_sofa','garbage-car':'garbage_car','garbage-shelving':'garbage_shelf',
 'column-broken':'ruin_column','decor-foreground-rock':'rubble','decor-foreground-coral':'coral_branch','decor-starfish':'starfish','decor-midground-coral':'coral_tubes','decor-kelp':'kelp_group','decor-ruin-fragment':'ruin_column',
}


def create_asset(asset_id):
    """Stable coverage IDs. Each new object has its own independent collection."""
    ident=asset_id.replace('_','-')
    if ident in PROP_ALIASES:return P.create_asset(PROP_ALIASES[ident])
    if ident not in ASSET_IDS:raise ValueError('Unknown world component '+asset_id)
    b=P.Builder(ident)
    if ident.startswith('wall-'):return build_wall(b,ident[5:])
    if ident=='dock-post-rope':return build_post_rope(b)
    if ident=='dock-floor':return build_dock_floor(b)
    if ident=='dock-entry':return build_dock_entry(b)
    if ident=='workshop-hut':return build_hut(b)
    if ident=='dock-cover':return build_dock_cover(b)
    if ident=='slate-rock':return build_slate_rock(b)
    if ident=='rock-half-width':return build_terrain(b,'rock-half-width','middle')
    if ident=='boulder-underwater':return build_boulder(b)
    if ident.startswith(('rock-wall-','rock-shelf-','reef-')):
        family,variant=ident.rsplit('-',1);return build_terrain(b,family,variant)
    if ident.startswith('wreck-'):return build_wreck(b,ident[6:])
    if ident=='decor-background-rock':return build_background_rock(b)
    if ident=='decor-background-wreck':return build_background_wreck(b)
    if ident=='decor-background-fish':return build_background_fish(b)
    if ident=='decor-light-shafts':return build_light_shafts(b)
    if ident=='safe-passage':return build_safe_passage(b)
    raise ValueError(ident)
