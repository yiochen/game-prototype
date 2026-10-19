"""Production ID orchestration. Native geometry is authored in Blender MCP.

Rebuilding one ID always uses the same world pitch, support root, camera and
12fps motion contract; belts use24samples over2seconds to preserve travel direction.
The approved concept sheet is never sprite input.
"""
import bpy,sys,math,json,importlib.util
from pathlib import Path

BASE=Path(__file__).parent

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,str(BASE/file))
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def load():
    global P,F,C,X,W,H
    P=module('prop_builders','prop_builders.py')
    F=module('s33fb','food_belt_builders.py')
    C=module('s33chars','character_builders.py')
    X=module('s33fx','creature_fx_builders.py')
    W=module('s33world','world_components.py')
    H=module('s33compose','character_composition.py')

def remap(a,mapping):
    pose=a['pose'];old=a['clips']
    a['clips']={new:dict(old[original]) for new,original in mapping.items()}
    a['pose']=lambda clip,t:pose(mapping[clip],t)
    return a

def attach_food(a):
    meal=F.create_asset('dish-salmon');mr=meal['root']
    for o in list(meal['collection'].objects):
        meal['collection'].objects.unlink(o);a['collection'].objects.link(o)
    bpy.data.collections.remove(meal['collection']);mr.parent=a['root'];mr.location=(0,-.28,1.40);mr.rotation_euler.x=math.radians(65)
    original=a['pose'];base=mr.location.copy();base_scale=mr.scale.copy()
    def pose(clip,t):
        original(clip,t);s=1+.025*math.sin(t*math.tau)
        if clip=='appear':s=max(.025,1-(1-t)**3)+.08*math.sin(t*math.pi*2)*(1-t)
        elif clip=='fade':s=max(.025,1-t*t)
        center=type(base)((0,0,1.42));mr.location=center+(base-center)*s;mr.location.z+=.025*math.sin(t*math.tau);mr.scale=base_scale*s
    a['pose']=pose;a['parts']=dict(a['parts'],native_preference_dish=mr)
    a['sockets']['dishIcon']=[0,-.28,1.40]

def add_static_preview(asset,source_clip='idle'):
    """Explicit frozen source pose in addition to an existing ambient loop."""
    original=asset['pose']
    asset['clips']=dict(asset['clips'],static={'frames':1,'fps':12,'loop':False,'static':True})
    def pose(clip,t):
        original(source_clip,0.0) if clip=='static' else original(clip,t)
    asset['pose']=pose
    asset.setdefault('notes',[]).append('Static preview is the existing idle pose at t=0; ambient motion remains independently inspectable.')
    return asset


def add_equipment_active(asset,asset_id):
    """Presentation-only equipment states with distinct native sampled geometry.
    All motion retracts/stays inside existing modeled clearances, without changing
    capture frames, roots, mechanics, capacity or upgrades.
    """
    original=asset['pose']
    asset['clips']=dict(asset['clips'],active={'frames':12,'fps':12,'loop':asset_id!='sub-harpoon-mount','static':False})
    def pose(clip,t):
        original('idle',0.0)
        if clip!='active':return
        if asset_id=='sub-hull-panels':
            phase=math.tau*t;scale=1+.015*math.sin(phase)
            for obj in asset['parts'].values():
                obj.location.x*=scale;obj.location.y*=scale
                obj.location.z=.18+(obj.location.z-.18)*scale+.008*math.cos(phase)
                obj.scale*=scale
        elif asset_id=='sub-harpoon-mount':
            recoil=.055*math.sin(math.pi*t)*(1-.45*t)+.003*t
            for name,obj in asset['parts'].items():
                if name in ('barrel','muzzle'):obj.location.y+=recoil
        elif asset_id=='sub-collector-inlet':
            phase=math.tau*t
            for index,(name,obj) in enumerate(asset['parts'].items()):
                if name=='dark_mouth':obj.scale.z*=.96+.04*math.sin(phase)
                elif name.startswith('guard_'):obj.rotation_euler.x+=.06*math.sin(phase+index*.45)
    asset['pose']=pose
    asset.setdefault('notes',[]).append('Active state is restrained native panel breathing, barrel recoil or intake pulse only; no simulation, damage, capacity or timing mechanic.')
    return asset



def add_upgraded_variant(a):
    """Baseline/upgraded native assemblies under the same catalog ground root.
    Visibility is an explicit action channel, not a new gameplay object or entry.
    The shared charge light remains controlled by the existing baseline wrapper.
    """
    if a.get('upgraded_native'):
        return a
    if 'P' not in globals():load()
    base_pose=a['pose'];base_clips=list(a['clips'])
    base_parts=dict(a['parts'])
    shared_light=base_parts.get('charge_indicator')
    base_meshes=[obj for obj in base_parts.values() if obj.type in ('MESH','CURVE') and obj!=shared_light]
    upgraded=P.create_asset('submarine_upgraded')
    for obj in list(upgraded['collection'].objects):
        upgraded['collection'].objects.unlink(obj)
        a['collection'].objects.link(obj)
    bpy.data.collections.remove(upgraded['collection'])
    upgraded['root'].parent=a['root']
    upgraded['root']['variant']='upgraded'
    upgraded_meshes=[obj for obj in upgraded['parts'].values() if obj.type in ('MESH','CURVE')]
    # Builder.reset closes over its original parts dictionary; never add names
    # into that dictionary after its baseline transform map has been frozen.
    a['parts']=dict(base_parts)
    a['parts'].update({'upgraded__'+name:obj for name,obj in upgraded['parts'].items()})
    a['clips']=dict(a['clips'])
    for clip in base_clips:a['clips']['upgraded-'+clip]=dict(a['clips'][clip])
    mapping={'idle':'idle','travel':'travel','impact':'impact','protection':'protected','dock-charging':'idle','dock-ready':'idle'}
    if any(clip not in mapping for clip in base_clips):raise ValueError('Unexpected baseline submarine clip set')
    def pose(clip,t):
        show_upgrade=clip.startswith('upgraded-')
        base_clip=clip[len('upgraded-'):] if show_upgrade else clip
        if base_clip not in base_clips:raise KeyError('Unknown submarine variant clip '+clip)
        base_pose(base_clip,t)
        upgraded['pose'](mapping[base_clip],t)
        for obj in base_meshes:obj.hide_render=show_upgrade;obj.hide_viewport=show_upgrade
        for obj in upgraded_meshes:obj.hide_render=not show_upgrade;obj.hide_viewport=not show_upgrade
    a['pose']=pose
    a['reset']=lambda:pose('idle',0.0)
    a['variants']={'baseline':{'clips':base_clips},'upgraded':{'clips':['upgraded-'+clip for clip in base_clips]}}
    a['upgraded_native']={'root':upgraded['root'],'parts':upgraded['parts'],'source':'prop_builders.py','baseBodyObjects':[obj.name for obj in base_meshes],'upgradedBodyObjects':[obj.name for obj in upgraded_meshes],'sharedChargeIndicator':shared_light.name if shared_light else None}
    a['root']['variants']=json.dumps(a['variants'])
    a['root']['animation_recipes']=json.dumps(a['clips'])
    a.setdefault('notes',[]).append('Baseline and upgraded ship use the same logical root, footprint and fixed capture frame. Native armor/harpoon/collector geometry swaps with explicit visibility; shared charge indicator follows the baseline state.')
    pose('idle',0.0)
    return a


def build(aid):
    if 'P' not in globals():load()
    if aid.startswith('chef-') and aid!='chef-blackboard' or aid.startswith('customer-'):
        a=C.create_character(aid.replace('-','_'))
        H.add_held_props(a,F,'dish-salmon' if aid.startswith('chef-') else 'dish-cucumber')
        projection='character-orthographic'
    elif aid.startswith(('floor-','dish-','belt-')):
        a=F.create_asset(aid);projection='character-orthographic' if aid.startswith('dish-') else 'square-top-front-oblique'
        if aid=='floor-underwater':
            waves=[o for n,o in a['parts'].items() if n.startswith('periodic_wave')]
            originals={o.name:[v.co.copy() for v in o.data.vertices] for o in waves}
            def scroll(c,t):
                for o in waves:
                    for v,base in zip(o.data.vertices,originals[o.name]):
                        v.co.y=base.y-.045*math.sin((base.x+.5)*math.tau)+.045*math.sin((base.x+.5+t)*math.tau)
                    o.data.update()
            a['clips']={'scroll':{'frames':12,'fps':12,'loop':True}};a['pose']=scroll
    elif aid in X.SUPPORTED_IDS:
        a=X.create_asset(aid);projection=a['projection']
        if aid=='bubble-preference':attach_food(a)
    elif aid in W.ASSET_IDS or aid in W.PROP_ALIASES:
        a=W.create_asset(aid);projection='square-top-front-oblique'
    elif aid=='submarine-yellow':
        a=P.create_asset('submarine_base');projection='character-orthographic';original=a['pose']
        mapping={'idle':'idle','travel':'travel','impact':'impact','protection':'protected','dock-charging':'idle','dock-ready':'idle'}
        a['clips']={k:dict(frames=12,fps=12,loop=k!='impact') for k in mapping}
        # Real dimensional charge/ready lights, retained on the editable ship.
        builder=P.Builder('sub-charge-indicators')
        light=builder.ico('charge_lamp',(0,.1,1.01),(.065,.065,.045),'cyan')
        for o in list(builder.collection.objects):
            builder.collection.objects.unlink(o);a['collection'].objects.link(o)
        bpy.data.collections.remove(builder.collection);builder.root.parent=a['root'];a['parts']=dict(a['parts'],charge_indicator=light)
        def pose(c,t):
            original(mapping[c],t)
            light.hide_render=c not in ('dock-charging','dock-ready','protection')
            light.scale=(.065,.065,.045)
            if c=='dock-charging':light.scale*=.6+.4*(.5+.5*math.sin(t*math.tau))
            if c=='protection':light.scale*=1+.25*math.sin(t*math.tau)
        a['pose']=pose;a['camera_elevation_degrees']=65;a['footprint']=[1,2]
        a=add_upgraded_variant(a)
    elif aid in ['sub-hull-panels','sub-harpoon-mount','sub-collector-inlet']:
        a=P.create_asset({'sub-hull-panels':'hull_panel','sub-harpoon-mount':'harpoon_mount','sub-collector-inlet':'collector_inlet'}[aid]);projection='square-top-front-oblique'
    elif aid=='salvage-metal':
        a=remap(P.create_asset('salvage_a'),{'shimmer':'idle','attract':'attraction','collect':'collection'});projection='square-top-front-oblique'
    elif aid in ['portal-rim','portal-entry']:
        a=remap(P.create_asset('portal_rim'),{'idle':'idle'} if aid=='portal-rim' else {'enter':'entry'});projection='square-top-front-oblique'
    elif aid=='decor-bubbles':
        b=P.Builder(aid);b.height=1.7
        for i in range(5):b.ico('bubble_'+str(i),((i%3-1)*.20,(i%2-.5)*.24,.12+i*.29),(.06,.06,.07),'cyan')
        def rise(t):
            for i,o in enumerate(b.parts.values()):
                o.location.z=.06+((i*.29+t*1.5)%1.5);o.location.x+=.025*math.sin(t*math.tau+i)
        b.motion['rise']=rise;a=b.finish({'rise':{'frames':12,'fps':12,'loop':True}});projection='square-top-front-oblique'
    else:raise ValueError('No production builder for '+aid)
    if aid in ['plant-angular','column-broken','decor-foreground-coral','decor-ruin-fragment']:
        a=add_static_preview(a,'idle')
    if aid in ['sub-hull-panels','sub-harpoon-mount','sub-collector-inlet']:
        a=add_equipment_active(a,aid)
    for clip,config in a['clips'].items():
        config.update(frames=1 if config.get('static') else 24 if aid.startswith('belt-') else 12,fps=12)
        if config.get('static'):config['loop']=False
    a['root']['production_id']=aid;a['root']['animation_recipes']=json.dumps(a['clips'])
    a['source_script']='production_library.py'
    # Author one frame for the entire object, all poses and all four rotations.
    # Pitch and anchor never change with alpha bounds or an animation sample.
    w,h=a['footprint'];extent=max(w,h);height=a['height']
    if aid.startswith('floor-'):frame=(128,128);root=(64,64)
    elif projection=='character-orthographic' and extent<=2 and height<=2:
        frame=tuple(a.get('frameSize',[192,320]));root=tuple(a.get('frameRoot',[96,248]))
        if extent==2 and frame[0]<320:frame=(320,max(384,frame[1]));root=(160,max(288,root[1]))
    else:
        fw=max(192,int(math.ceil((extent*128+64)/32))*32)
        ry=max(248,int(math.ceil((height*128+extent*64+32)/32))*32)
        fh=max(320,int(math.ceil((ry+extent*64+32)/32))*32)
        frame=(fw,fh);root=(fw//2,ry)
    fixed_frames={
        'creature-eel':((448,512),(224,352)),
        'boost-trail':((448,544),(224,352)),
        'attack-reef-fragments':((320,448),(160,320)),
    }
    if aid in fixed_frames:frame,root=fixed_frames[aid]
    a['frame']=frame;a['anchor']=root;a['projection']=projection;a['scale']=4
    return a

def register(runtime,ids):
    runtime.scene();made=[]
    for aid in ids:
        if aid in runtime.assets:continue
        a=build(aid);runtime.register(aid,a,a['projection'],a['frame'],a['anchor'],a['scale']);made.append(aid)
    return made
