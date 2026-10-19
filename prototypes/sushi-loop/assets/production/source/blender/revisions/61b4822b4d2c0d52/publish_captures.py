"""Publish complete registered Blender captures, preserving prior native attempts.

Native 4x frames are retained byte-for-byte. Runtime atlases use one declared
uniform whole-frame sample (2x by default), with no silhouette fitting. Changed
raw frames/camera/packing options archive the previous pack and trigger repacking.
Run only after a native capture batch is complete; this script does not use MCP.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
from PIL import Image

SKILL=Path('/Users/yiouchen/.codex/skills/generate-blender-characters/scripts')
sys.path.insert(0,str(SKILL))
from pack_captures import pack

HERE=Path(__file__).resolve().parent
DIRECTIONS=['N','E','S','W']
ANGLES={'S':0.,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
ALIASES={'crate':'crate-wood','barrel':'barrel-wood','plant':'plant-angular','potted-plant':'plant-angular','lantern':'lantern-gold','blank-sign':'sign-blank','entrance':'entry-finished','garbage-shelf':'garbage-shelving','submarine-base':'submarine-yellow','hull-panel':'sub-hull-panels','harpoon-mount':'sub-harpoon-mount','collector-inlet':'sub-collector-inlet'}
FX_IDS={'creature-eel','creature-fish','bubble-preference','bubble-happy','bubble-puzzled','bubble-panic','coin-pop','harpoon-projectile','harpoon-cable','route-current','boost-trail','following-strip','attack-reef-fragments','attack-swirl','attack-lateral-current','eel-warning-strip','eel-lightning-symbol','eel-discharge'}
PROP_IDS={'stool-wood','stool-blue','chef-blackboard','plant-angular','barrel-wood','crate-wood','lantern-gold','sign-blank','entry-finished','garbage-sofa','garbage-car','garbage-shelving','column-broken','decor-foreground-rock','decor-foreground-coral','decor-starfish','decor-midground-coral','decor-kelp','decor-ruin-fragment','submarine-yellow','sub-hull-panels','sub-harpoon-mount','sub-collector-inlet','salvage-metal','portal-rim','portal-entry','decor-bubbles'}

CLUSTER_IDS={'restaurant-border-garden-a','restaurant-border-garden-b','restaurant-corner-garden-a','restaurant-corner-garden-b','underwater-reef-garden-a','underwater-reef-garden-b','underwater-coral-garden-a','underwater-coral-garden-b'}


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):digest.update(data)
    return digest.hexdigest()


def json_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def canonical_clip_id(value,recipe,single=False):
    ident=str(value).strip().replace('_','-')
    if not ident:raise ValueError('Empty clip identifier')
    static=bool(recipe.get('static')) or recipe.get('frames')==1
    return 'static' if static and single and ident in ['idle','static'] else ident


def kind_for(asset):
    family=asset.get('family')
    ident=asset['id']
    if family in ['W05','W07']:return 'character'
    if family=='W04' or ident.startswith('belt-'):return 'belt'
    if family=='W01' or ident.startswith('floor-'):return 'floor'
    if family=='W15' or ident=='submarine-yellow':return 'actor'
    if ident in FX_IDS or (family=='W12' and ident in ['decor-bubbles','decor-light-shafts']):return 'effect'
    if family=='W11':return 'terrain'
    return 'prop'


def model_script_for(asset):
    ident=asset['id']
    if asset.get('family') in ['W05','W07']:return 'character_builders.py'
    if ident in {'boulder-underwater','decor-background-rock','decor-foreground-rock','column-broken','decor-ruin-fragment','decor-foreground-coral','decor-midground-coral','decor-kelp'}:return 'catalog_concept_decor.py'
    if ident.startswith(('wall-','rock-wall-','belt-')) or ident in {'plant-angular','barrel-wood','crate-wood','slate-rock','dock-post-rope','chef-blackboard','sign-blank','garbage-sofa','garbage-car','garbage-shelving','dock-cover'}:return 'catalog_art_revision.py'
    if ident in FX_IDS:return 'creature_fx_builders.py'
    if ident in CLUSTER_IDS or ident=='entry-finished':return 'catalog_clusters.py'
    if ident.startswith(('floor-','dish-','belt-')):return 'food_belt_builders.py'
    if ident in PROP_IDS:return 'prop_builders.py'
    return 'world_components.py'


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(value,indent=2)+'\n'
    temp=path.with_name(path.name+'.publishing-tmp')
    temp.write_text(content);os.replace(temp,path)


def copy_changed(source,destination,history=None):
    source,destination=Path(source),Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    incoming=sha(source)
    if destination.exists():
        previous=sha(destination)
        if previous==incoming:return incoming
        if history:
            archived=Path(history)/previous[:16]/destination.name
            archived.parent.mkdir(parents=True,exist_ok=True)
            if not archived.exists():shutil.copy2(destination,archived)
    temporary=destination.with_name(destination.name+'.publishing-tmp')
    shutil.copy2(source,temporary);os.replace(temporary,destination)
    return incoming


def capture_fingerprint(frames,camera_meta,kind,runtime_scale):
    return {'version':2,'sourceFrames':[{'name':p.name,'sha256':sha(p)} for p in frames],
            'cameraSHA256':json_hash(camera_meta),'kind':kind,'columns':6,'gutter':0,
            'runtimeScale':runtime_scale,'packing':'full-authored-frame-uniform-lanczos-v2'}


def pack_matches(packed,fingerprint):
    marker=packed/'capture-fingerprint.json'
    if marker.exists():return json.loads(marker.read_text())==fingerprint
    # Old packs have no camera/configuration proof. Repack them once, retaining
    # the original pack in history rather than assuming cached art is current.
    return False


def archive_pack(packed,history):
    if not packed.exists():return
    marker=packed/'capture-fingerprint.json'
    if marker.exists():identity=json_hash(json.loads(marker.read_text()))
    else:
        guide=packed/'guide.json'
        identity=sha(guide) if guide.exists() else 'unrecorded-'+json_hash(sorted(p.name for p in packed.iterdir()))
    destination=history/identity[:16]
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        # Exact archived data already exists. Validate rather than overwrite it.
        for item in packed.rglob('*'):
            if item.is_file():
                other=destination/item.relative_to(packed)
                if not other.is_file() or sha(item)!=sha(other):
                    raise ValueError('History identity collision at '+str(destination))
        shutil.rmtree(packed)
    else:shutil.move(str(packed),str(destination))


def pack_floor(frames,camera_meta,packed,runtime_scale):
    """Opaque floors deliberately touch their complete authored panel edges."""
    frame=camera_meta['frame'];scale=camera_meta['captureScale']
    width,height=[int(v*runtime_scale) for v in frame]
    columns=min(6,len(frames));rows=math.ceil(len(frames)/columns)
    sheet=Image.new('RGBA',(width*columns,height*rows))
    records=[];cells=[]
    packed.mkdir(parents=True);(packed/'source-captures').mkdir()
    for index,path in enumerate(frames):
        with Image.open(path) as opened:
            image=opened.convert('RGBA')
            if list(image.size)!=[int(v*scale) for v in frame]:
                raise ValueError('Floor dimensions differ from fixed authored capture frame')
            sampled=image.resize((width,height),Image.Resampling.LANCZOS) if image.size!=(width,height) else image.copy()
        x=index%columns*width;y=index//columns*height
        sheet.paste(sampled,(x,y))
        shutil.copy2(path,packed/'source-captures'/path.name)
        records.append({'path':'source-captures/'+path.name,'sha256':sha(path)})
        cells.append({'index':index,'rect':[x,y,x+width,y+height],'durationMs':1000/12})
    sheet.save(packed/'sheet.png')
    guide={'version':1,'kind':'rendered-3d-sheet','assetKind':'floor','frame':frame,
           'anchor':camera_meta['anchor'],'cellSize':128,'captureScale':runtime_scale,
           'sourceCaptureScale':scale,'columns':columns,'rows':rows,'gutter':0,
           'size':[width*columns,height*rows],'cells':cells,'sourceCaptures':records,
           'projection':camera_meta['projection'],'camera':camera_meta.get('camera'),
           'processing':'Uniform complete authored floor canvas only; opaque opposite edges retained; no alpha fitting'}
    write_json(packed/'guide.json',guide)
    return guide


def project_point(point,direction,camera_meta):
    x,y,z=point;c=math.cos(ANGLES[direction]);s=math.sin(ANGLES[direction])
    x,y=c*x-s*y,s*x+c*y
    calibration=camera_meta.get('calibration',{})
    scale=camera_meta.get('captureScale',4)
    X=calibration.get('unitX',[128*scale,0]);D=calibration.get('unitDepth',[0,128*scale]);H=calibration.get('unitHeight',[0,-128*scale])
    return [(X[i]*x-D[i]*y+H[i]*z)/scale for i in (0,1)]


def set_registration(asset,info,camera_meta):
    width,height=info['footprint']
    asset['directionFootprints']={d:([height,width] if d in ['E','W'] else [width,height]) for d in DIRECTIONS}
    asset['directionRootCells']={d:[v/2 for v in asset['directionFootprints'][d]] for d in DIRECTIONS}
    asset['rootCell']=[width/2,height/2]
    full=[[x,y] for y in range(math.ceil(height)) for x in range(math.ceil(width))]
    floating=asset['kind']=='actor' or asset.get('blocking') is False or info.get('nonblocking')
    asset['occupiedCells']=info.get('occupiedCells',full)
    asset['supportCells']=info.get('supportCells',[] if floating or asset['id']=='dock-cover' else full)
    asset['overheadCells']=info.get('overheadCells',full if asset['id']=='dock-cover' else [])
    asset['registration']={'method':'authored-3d-projection','groundAnchorAlignment':'center',
                           'completeFrame':info['frame'],'anchor':info['anchor'],'cellSize':128,
                           'poseFitting':False,'sourceCaptureScale':info.get('scale',4)}
    asset['sockets3D']=info.get('sockets',{})
    asset['sockets']={d:{name:project_point(point,d,camera_meta) for name,point in info.get('sockets',{}).items()} for d in DIRECTIONS}
    asset['socketSpace']='root-relative logical pixels projected from declared native attachment points'
    if 'supportLayout' in info:asset['supportLayout']=info['supportLayout']
    flow=info.get('flow')
    if asset['kind']=='belt' and isinstance(flow,dict):
        asset['portDefinition']={name:flow[name] for name in ('incoming','outgoing') if flow.get(name) in DIRECTIONS}
    raw_ports=info.get('ports')
    asset['portProfiles']={p.get('name',p.get('direction','port-'+str(i))):p['profile'] for i,p in enumerate(raw_ports or []) if isinstance(p,dict) and p.get('profile')}
    if raw_ports:
        ports={p.get('name',p.get('direction','port-'+str(i))):p['position'] for i,p in enumerate(raw_ports) if isinstance(p,dict) and 'position' in p}
    elif asset['kind']=='belt':
        definition=asset.get('portDefinition') or asset.get('ports',{})
        if not isinstance(definition,dict) or any(d in definition for d in DIRECTIONS):definition={}
        asset['portDefinition']=definition
        coordinates={'N':[0,.5,.64],'E':[.5,0,.64],'S':[0,-.5,.64],'W':[-.5,0,.64]}
        ports={name:coordinates[side] for name,side in definition.items() if side in coordinates}
    else:ports={}
    if ports:asset['ports']={d:{name:project_point(point,d,camera_meta) for name,point in ports.items()} for d in DIRECTIONS}



def connected_belt_scene(asset,byid,place,scene,with_dish=False):
    """Use native directed ports; the staged plate follows the actual deck arc."""
    vectors={'N':(0,-1),'E':(1,0),'S':(0,1),'W':(-1,0)}
    opposite={'N':'S','E':'W','S':'N','W':'E'}
    center=(2,2);aid=asset['id'];flow=asset.get('portDefinition',{})
    incoming,outgoing=flow.get('incoming'),flow.get('outgoing')
    if not incoming and not outgoing:raise ValueError(aid+': native belt flow is required')
    def at(side,distance=1):
        dx,dy=vectors[side];return [center[0]+dx*distance,center[1]+dy*distance]
    def belt(ident,point):return place(ident,*point,clip='running')
    corner=bool(incoming and outgoing and opposite[incoming]!=outgoing)
    if corner:
        upstream=opposite[incoming]
        route=[belt('belt-start-'+upstream.lower(),at(incoming,2)),belt('belt-straight-'+upstream.lower(),at(incoming)),belt(aid,center),belt('belt-straight-'+outgoing.lower(),at(outgoing)),belt('belt-end-'+outgoing.lower(),at(outgoing,2))]
        vi,vo=vectors[incoming],vectors[outgoing]
        arc_center=[center[i]+.5*(vi[i]+vo[i]) for i in (0,1)]
        radius=[-.5*vo[i] for i in (0,1)]
        end_radius=[-.5*vi[i] for i in (0,1)]
        turn=math.pi/2 if radius[0]*end_radius[1]-radius[1]*end_radius[0]>0 else -math.pi/2
        angle=math.atan2(radius[1],radius[0])
        arc=[[arc_center[0]+.5*math.cos(angle+turn*step/16),arc_center[1]+.5*math.sin(angle+turn*step/16)] for step in range(17)]
        path=[at(incoming,2),at(incoming)]+arc+[at(outgoing),at(outgoing,2)]
        duration=8
    else:
        forward=outgoing or opposite[incoming]
        backward=opposite[forward]
        if not incoming:
            route=[belt(aid,center),belt('belt-straight-'+forward.lower(),at(forward)),belt('belt-end-'+forward.lower(),at(forward,2))]
            path=[list(center),at(forward),at(forward,2)]
        elif not outgoing:
            route=[belt('belt-start-'+forward.lower(),at(backward,2)),belt('belt-straight-'+forward.lower(),at(backward)),belt(aid,center)]
            path=[at(backward,2),at(backward),list(center)]
        else:
            route=[belt('belt-start-'+forward.lower(),at(backward)),belt(aid,center),belt('belt-end-'+forward.lower(),at(forward))]
            path=[at(backward),list(center),at(forward)]
        duration=4
    for item in route:
        if item['object'] not in byid:raise KeyError('Connected belt fixture references '+item['object'])
    if with_dish:
        sockets=asset.get('sockets',{});deck=sockets.get('S',sockets).get('deck',[0,-57.344])
        # This isolated fixture contains only connected decks at one elevation.
        # Its attached plate must stay above every module as its ground row changes.
        route.append(place('dish-salmon',*path[0],offset=deck,renderPass='foreground',motion={'path':path,'duration':duration,'loop':True}))
    value=scene('Staged dish travel along the connected deck' if with_dish else 'Connected incoming and outgoing modules',route,(5,5),note='Staged review motion follows the deck centerline, including the native quarter-circle turn. Plate travel is independent of slat timing and repeats from the start cap.' if with_dish else 'Open ports meet their matching directed neighbors; caps close the beginning and end of this route.')
    value['connectionReview']={'kind':'directed-belt','object':aid}
    return value


def connected_module_scene(asset,byid,place,scene):
    """Join compatible native loft profiles without reversing asymmetric sections."""
    aid=asset['id']
    if asset['kind']=='floor':
        value=scene('Connected 3 × 3 floor patch',[place(aid,x,y) for y in range(3) for x in range(3)],(3,3),note='Complete authored floor edges touch at one shared tile pitch; no gap or silhouette fitting is applied.')
        value['connectionReview']={'kind':'floor-patch','object':aid}
        return value
    profiles=set(asset.get('portProfiles',{}).values())
    ports=asset.get('ports',{}).get('S',{})
    if len(profiles)!=1 or not ports or any(side not in DIRECTIONS for side in ports):return None
    profile=next(iter(profiles))
    peers=[other for other in byid.values() if set(other.get('portProfiles',{}).values())==profiles and set(other.get('ports',{}).get('S',{}))=={'W','E'}]
    peers.sort(key=lambda other:(not other['id'].endswith('-middle'),other['id']!=aid,other['id']))
    if not peers:raise ValueError(aid+': no matching straight native profile for '+profile)
    peer=peers[0]['id'];center=(2,2);placements=[place(aid,*center)]
    vectors={'N':(0,-1),'E':(1,0),'S':(0,1),'W':(-1,0)}
    directions={'W':'S','E':'S','N':'E','S':'W'}
    for side in DIRECTIONS:
        if side in ports:
            dx,dy=vectors[side];placements.append(place(peer,center[0]+dx,center[1]+dy,directions[side]))
    value=scene('Connected matching-profile modules',placements,(5,5),note='Each reviewed port meets the same native cross-section with its authored handedness. Outside edges remain open so the joins can be inspected.')
    value['connectionReview']={'kind':'profile-join','object':aid,'profile':profile}
    return value


def hydrate_registrations(manifest,target):
    """Read previously captured metadata; never copy or repack image assets."""
    for asset in manifest['objects']:
        source=asset.get('source',{});record=source.get('assetRecord');camera=source.get('camera')
        if not record or not camera:continue
        record_path,camera_path=target/record,target/camera
        if record_path.is_file() and camera_path.is_file():
            set_registration(asset,json.loads(record_path.read_text()),json.loads(camera_path.read_text()))


def refresh_interactions(manifest,ids=None):
    byid={asset['id']:asset for asset in manifest['objects']}
    for aid in ids or byid:
        if aid not in byid:raise KeyError('Unknown object for interaction refresh: '+aid)
        byid[aid]['interactions']=interaction_context(byid[aid],byid)
    return manifest

def interaction_context(asset,byid):
    """Recorded visual fixtures only; does not introduce simulation or mechanics."""
    aid=asset['id'];family=asset.get('family');kind=asset['kind']
    belt='belt-straight-e';dish='dish-salmon';stool='stool-wood';customer='customer-rosa';chef='chef-lena';sub='submarine-yellow';eel='creature-eel'
    def place(ident,x,y,direction='S',clip=None,**extra):
        value={'object':ident,'x':x,'y':y,'direction':direction}
        if clip:value['clip']=clip
        value.update(extra);return value
    def scene(name,placements,grid=(5,4),note=None):
        value={'name':name,'gridSize':list(grid),'placements':placements}
        if note:value['note']=note
        return value
    if aid in CLUSTER_IDS:
        # Keep comparison actors wholly outside each authored multi-cell assembly.
        # Decorative clusters deliberately expose no seam ports or blocking rules.
        width,depth=asset['footprint']
        actor=chef if family=='W02' else sub
        actor_clip='idle' if family=='W02' else 'travel'
        actor_direction='S' if family=='W02' else 'N'
        return [scene('Dense organic assembly and neighboring '+('chef' if family=='W02' else 'submarine'),
          [place(aid,0,1,clip='ambient'),place(actor,width+1,1,actor_direction,actor_clip)],
          (width+4,max(depth+2,4)),
          note='Native multi-cell assembly at its authored capture scale. The neighboring actor occupies separate cells beyond the full cluster footprint; this decorative arrangement has no seam ports or blocking rules.')]
    deck=byid.get(belt,{}).get('sockets',{});deck=deck.get('S',deck).get('deck',[0,-57.344])
    plate=lambda ident,x,y:place(ident,x,y,offset=deck)
    if family=='W05':
        return [scene('Chef faces the neighboring serving belt',[place(aid,1,0,clip='work'),place(belt,1,1,clip='running'),plate(dish,1,1)]),scene('Completed dish and customer scale',[place(aid,0,1,clip='hold'),place(stool,2,1),place(customer,2,1,clip='seated-wait')])]
    if family=='W07':
        return [scene('Separate customer seated on the stool',[place(stool,1,1),place(aid,1,1,clip='seated-wait'),place(belt,1,2,clip='running'),plate(dish,1,2)]),scene('Walking height beside a chef',[place(aid,1,1,clip='walk'),place(chef,3,1,clip='work')])]
    if aid in ['stool-wood','stool-blue']:
        return [scene('Seat, separate customer and serving belt',[place(aid,1,1),place(customer,1,1,clip='seated-wait',offset=[0,-2.688] if aid=='stool-blue' else [0,0]),place(belt,1,2,clip='running'),plate(dish,1,2)],note='Independent customer layer uses the declared blue cushion attachment delta: 0.03 world units × 70% = 2.688 logical pixels above the wood-seat support.' if aid=='stool-blue' else None)]
    if kind=='belt':return [connected_belt_scene(asset,byid,place,scene),connected_belt_scene(asset,byid,place,scene,with_dish=True)]
    connected=connected_module_scene(asset,byid,place,scene)
    if connected:return [connected]
    if aid.startswith('dish-'):
        return [scene('Dish on the running serving surface',[place(belt,1,1,clip='running'),plate(aid,1,1),place(stool,1,2),place(customer,1,2,'N','seated-wait')],(4,4))]
    if aid=='sign-blank':return [scene('Front-edge sign shares a planted tile',[place('plant-angular',1,1),place(aid,1,1,direction='S',renderPass='foreground')],(3,3),note='One blank player-facing sign at the front of the same tile as a plant; no title is baked.')]
    if family=='W06':return [scene('Blank blackboard shares the chef cell',[place(chef,1,1,clip='work'),place(aid,1,1,direction='S',renderPass='foreground'),place(belt,1,2,clip='running')],(4,4),note='Blank player-facing board is physically modeled in the front tile band. It shares the chef ground cell without a fixture translation; dynamic recipe content is added in game.')]
    if family=='W08':
        return [scene('World feedback attached above a customer',[place(stool,1,1),place(customer,1,1,clip='seated-wait'),place(aid,1,1,offset=[0,-90] if aid.startswith('bubble-') else [0,0])],(4,3),note='Bubble attachment is 90 logical pixels above the shared customer ground placement; sale coin effects stay near the meal.' if aid.startswith('bubble-') else None)]
    if family=='W09':
        width,height=asset['footprint']
        return [scene('Whole garbage assembly and human scale',[place(aid,0,0),place(chef,width+1,0,clip='idle')],(width+3,max(3,height+1)))]
    if family=='W10':
        # Use the world_components native dock assembly coordinates. Ground roots
        # stay independent of bounding rectangles and the .23m deck elevation.
        def on_dock(ident,point):
            footprint=byid.get(ident,{}).get('footprint',[1,1])
            x,y,z=point
            return place(ident,1.5+x-footprint[0]/2,1.5-y-footprint[1]/2,offset=[0,-89.6*z])
        placements=[place('dock-floor',0,0),on_dock(sub,[-.70,-.42,.23]),on_dock('workshop-hut',[.78,.35,.23]),on_dock('dock-entry',[0,-1.5,0])]
        if aid=='dock-cover':placements.append(on_dock(aid,[0,0,.23]))
        value=scene('Connected dock entry, shared deck and hut',placements,(4,4),note='The ramp overlaps the dock at its authored native position. The submarine and hut retain the shared deck elevation; the hut stays to the submarine’s right.')
        value['connectionReview']={'kind':'dock-assembly','object':aid}
        return [value]
    if family=='W11':return [scene('Joined terrain beside a ship-sized lane',[place(aid,0,1),place(aid,asset['footprint'][0],1),place(sub,3,0,'N','travel')],(5,4),note='Shared cell pitch and independent support masks. Only compatible declared port profiles form final obstacle joins.')]
    if family=='W12':return [scene('Layered scenery beside the submarine and creature',[place(aid,0,1),place(sub,2,0,'N','travel'),place(eel,4,1,'N','swim')],(6,4))]
    if family=='W13':
        result=[scene('Submarine equipment and creature scale',[place(aid,0,1),place(eel,3,1,'S','swim')]+([] if aid==sub else [place(sub,1,0)]),(5,4))]
        if aid==sub and asset.get('variants'):
            result.append(scene('Baseline and upgraded native assemblies at the same scale',[place(sub,1,1,clip='idle'),place(sub,3,1,clip='upgraded-idle')],(5,4)))
        return result
    if family=='W14':return [scene('Route object beside the traveling submarine',[place(aid,0,1),place(sub,3,0,'N','travel')],(5,4))]
    if family=='W15':return [scene('Creature, submarine and separate cable scale',[place(sub,0,0,'S','travel'),place(aid,2,0,'S','pursuit'),place('harpoon-cable',1,2,'E','taut')],(5,5),note='Presentation comparison. Cable endpoints and hook sockets remain visible through attachment overlays; no capture logic runs.')]
    if family in ['W16','W17']:return [scene('World effect beside submarine and eel',[place(sub,0,0,'N','travel'),place(eel,3,0,'N','pursuit'),place(aid,1,2)],(6,5))]
    return [scene('Shared restaurant scale',[place(aid,1,1),place(chef,3,1,clip='idle')],(5,4))]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--interactions-only',action='store_true',help='Refresh recorded registrations and interaction fixtures from existing source records; do not copy or repack captures')
    parser.add_argument('--ids',nargs='+',default=[],help='Capture IDs; optional capture-id=stable-id mapping. Comma-separated batches accepted.')
    parser.add_argument('--native',type=Path,default=HERE/'export')
    parser.add_argument('--raw-root',type=Path,help='Alternate completed raw-frame root, e.g. raw-belts-v24; metadata/source still come from --native')
    parser.add_argument('--runtime-scale',type=int,choices=[1,2,3,4],default=2)
    args=parser.parse_args()
    native=args.native.resolve();raw_root=args.raw_root.resolve() if args.raw_root else native/'raw-frames';target=args.repo.resolve()/'prototypes/sushi-loop/assets/production'
    source=target/'source';source.mkdir(parents=True,exist_ok=True)
    manifest_path=target/'library.json';manifest=json.loads(manifest_path.read_text())
    byid={asset['id']:asset for asset in manifest['objects']}
    entries=[value for argument in args.ids for value in argument.split(',') if value]
    hydrate_registrations(manifest,target)
    if args.interactions_only:
        ids=[ALIASES.get(entry.split('=')[-1].replace('_','-'),entry.split('=')[-1].replace('_','-')) for entry in entries] or None
        refresh_interactions(manifest,ids)
        write_json(manifest_path,manifest)
        print('Refreshed interaction fixtures for',len(ids or byid),'objects; no captures copied or repacked')
        return
    if not entries:parser.error('--ids is required unless --interactions-only is used')
    models=source/'blender';models.mkdir(parents=True,exist_ok=True)
    # Preserve editable versions and every new sibling native authoring helper.
    native_hashes={}
    blend=native/'source/sushi-loop-world-library.blend'
    if not blend.is_file():raise FileNotFoundError('Save the native library before publishing: '+str(blend))
    native_hashes['sushi-loop-world-library.blend']=copy_changed(blend,models/blend.name,models/'history')
    for script in sorted(HERE.glob('*.py')):
        native_hashes[script.name]=copy_changed(script,models/script.name,models/'history')
    native_revisions={}
    for name,digest in native_hashes.items():
        revision=models/'revisions'/digest[:16]/name
        revision.parent.mkdir(parents=True,exist_ok=True)
        if not revision.exists():
            try:os.link(models/name,revision)
            except OSError:shutil.copy2(models/name,revision)
        elif sha(revision)!=digest:raise ValueError('Immutable native source revision mismatch: '+str(revision))
        native_revisions[name]=str(revision.relative_to(target))
    for entry in entries:
        capture_id,explicit=(entry.split('=',1)+[None])[:2] if '=' in entry else (entry,None)
        normalized=capture_id.replace('_','-');aid=explicit or ALIASES.get(normalized,normalized)
        if aid not in byid:raise KeyError('Capture maps to unknown stable library ID: '+aid)
        record=native/'source'/capture_id
        if not record.is_dir() and (native/'source'/normalized).is_dir():record=native/'source'/normalized;capture_id=normalized
        info=json.loads((record/'asset.json').read_text());camera_meta=json.loads((record/'camera.json').read_text());asset=byid[aid]
        if info['projection']!='character-orthographic':
            info['projection']='top-down-oblique-square-grid';camera_meta['projection']='top-down-oblique-square-grid';camera_meta['name']='square top/front oblique'
        asset.update(status='ready',frameSize=info['frame'],root=info['anchor'],sourceScale=args.runtime_scale,projection=info['projection'],footprint=info['footprint'],height=info['height'],clips=[])
        asset['productionStage']='Native Blender pass · awaiting final art approval'
        if info.get('facingPolicy'):asset['facingPolicy']=info['facingPolicy']
        if info.get('directions')==['S']:asset['facingPolicy']='single-player-facing';asset['directions']=['S']
        asset['artStyle']=info.get('artStyle',{})
        if info.get('locomotion'):asset['locomotion']=info['locomotion']
        if info.get('conceptReference'):asset['conceptReference']=info['conceptReference']
        if info.get('squareFooting'):asset['projection']='height-dependent-35-square-footing'
        if info.get('variants'):asset['variants']={name:{**value,'clips':[canonical_clip_id(c,info['clips'][c],len(info['clips'])==1) for c in value.get('clips',[])]} for name,value in info['variants'].items()}
        asset['kind']=kind_for(asset)
        asset['layer']=0 if asset['kind']=='floor' or aid=='dock-floor' else 1 if asset['kind']=='belt' else 3 if aid.startswith('dish-') else 2
        if aid.startswith('decor-background-') or aid=='decor-light-shafts':asset['layer']=1
        if aid.startswith('decor-foreground-') or aid=='decor-starfish':asset['layer']=4
        if aid=='dock-cover':asset['layer']=5
        if info.get('composition_context'):asset['compositionContext']=info['composition_context']
        source_record=source/'records'/aid;source_record.mkdir(parents=True,exist_ok=True)
        for name,value in [('camera.json',camera_meta),('asset.json',info)]:
            destination=source_record/name
            if destination.exists() and json.loads(destination.read_text())!=value:
                archive=source/'records-history'/aid/sha(destination)[:16]/name;archive.parent.mkdir(parents=True,exist_ok=True)
                if not archive.exists():shutil.copy2(destination,archive)
            write_json(destination,value)
        camera_path=source_record/'camera.json';guides=[];raw_records=[];clip_ids=set()
        for source_clip,recipe in info['clips'].items():
            count=recipe['frames'];static=bool(recipe.get('static')) or count==1
            if recipe.get('fps',12)!=12:raise ValueError(aid+'/'+source_clip+': expected native 12 fps')
            export_clip=canonical_clip_id(source_clip,recipe,len(info['clips'])==1)
            if export_clip in clip_ids:raise ValueError('Canonical clip ID collision: '+aid+'/'+export_clip)
            clip_ids.add(export_clip)
            clip={'id':export_clip,'sourceClipId':source_clip,'name':export_clip.replace('-',' ').title(),'frames':count,'fps':12,'static':static,'loop':False if static else recipe.get('loop',True),'frameOrder':list(range(count)),'directions':{}}
            for direction in info.get('directions',DIRECTIONS):
                raw=raw_root/capture_id/(source_clip+'-'+direction);frames=[raw/(f'{index:03d}.png') for index in range(count) if (raw/(f'{index:03d}.png')).is_file()]
                if len(frames)!=count:raise ValueError(f'{aid}/{source_clip}/{direction}: {len(frames)} != {count}; capture batch incomplete')
                fingerprint=capture_fingerprint(frames,camera_meta,'floor' if asset['kind']=='floor' else 'object' if static else 'animation',args.runtime_scale)
                packed=source/'registered'/aid/(export_clip+'-'+direction)
                if packed.exists() and not pack_matches(packed,fingerprint):archive_pack(packed,source/'registered-history'/aid/(export_clip+'-'+direction))
                if not packed.exists():
                    if asset['kind']=='floor':guide=pack_floor(frames,camera_meta,packed,args.runtime_scale)
                    else:guide=pack(raw,camera_path,packed,kind='object' if static else 'animation',columns=6,gutter=0,sheet_scale=args.runtime_scale)
                    write_json(packed/'capture-fingerprint.json',fingerprint)
                else:guide=json.loads((packed/'guide.json').read_text())
                runtime=target/'sprites'/aid;runtime.mkdir(parents=True,exist_ok=True)
                filename=export_clip+'-'+direction+'.png';copy_changed(packed/'sheet.png',runtime/filename)
                cells=guide['cells']
                rects=[[r[0],r[1],r[2]-r[0],r[3]-r[1]] for r in [cell['rect'] for cell in cells]]
                clip['directions'][direction]={'image':f'sprites/{aid}/{filename}','columns':guide['columns'],'rows':guide['rows'],'atlasSize':guide['size'],'rects':rects}
                guides.append(str((packed/'guide.json').relative_to(target)))
                raw_records.extend({'image':str((packed/item['path']).relative_to(target)),'sha256':item['sha256'],'clip':export_clip,'direction':direction,'index':index} for index,item in enumerate(guide['sourceCaptures']))
            asset['clips'].append(clip)
        set_registration(asset,info,camera_meta)
        source_info={'blend':native_revisions['sushi-loop-world-library.blend'],'modelScript':native_revisions[model_script_for(asset)],'camera':str(camera_path.relative_to(target)),'guide':guides[0],'guides':guides,'assetRecord':str((source_record/'asset.json').relative_to(target)),'rawFrames':raw_records,'nativeScripts':{name:native_revisions[name] for name in native_hashes if name.endswith('.py')},'hashes':{native_revisions[name]:digest for name,digest in native_hashes.items()}}
        rig=record/'rig.json'
        if rig.exists():
            copy_changed(rig,source_record/'rig.json',source/'records-history'/aid)
            source_info['rig']=str((source_record/'rig.json').relative_to(target))
            asset.setdefault('validation',{})['rigEvidence']='exported; independent visual review pending'
        elif asset['kind']=='character' or asset.get('family')=='W15':
            asset.setdefault('validation',{})['rigEvidence']='not-exported-yet'
        asset['source']=source_info
        asset['interactions']=interaction_context(asset,byid)
        asset['captureFingerprint']=json_hash({'asset':info,'camera':camera_meta,'rawFrames':raw_records})
        print(aid,[(clip['id'],clip['frames']) for clip in asset['clips']])
    manifest['approval']={'concept':'approved','finalAssets':'pending','issue':33}
    manifest['production']={'pipeline':'Blender MCP native source and registered 2D captures','captureScale':4,'runtimeSourceScale':args.runtime_scale,'fps':12,'editableProject':'source/blender/sushi-loop-world-library.blend','visualApproval':'pending-user-review','nativeSourceSHA256':native_hashes}
    write_json(manifest_path,manifest)


if __name__=='__main__':main()
