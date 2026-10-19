"""Reproducible 2D atlas packing and manifest merger; run after the native publisher.

Only generated input cutouts are trimmed once. Every animation retains one fixed
logical canvas/root. No view-specific cropping, perspective rotation or lighting.
"""
from pathlib import Path
import argparse, copy, hashlib, json, math
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PRODUCTION = HERE.parent.parent
DIRECTIONS = ['N', 'E', 'S', 'W']
DELETED = {f'{base}-{suffix}' for base in ['restaurant-border-garden', 'restaurant-corner-garden', 'underwater-reef-garden', 'underwater-coral-garden'] for suffix in ['a', 'b']}
GENERATED = ['dish-salmon', 'dish-cucumber', 'dish-eel', 'bubble-preference', 'bubble-happy', 'bubble-puzzled', 'bubble-panic', 'decor-bubbles']
PROCEDURAL = ['attack-swirl', 'attack-lateral-current', 'eel-warning-strip', 'eel-lightning-symbol', 'eel-discharge']
SCALE = 2

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def cutout(ident, width):
    im = Image.open(HERE / 'generated' / f'{ident}.png').convert('RGBA')
    bounds = im.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox()
    im = im.crop(bounds)
    return im.resize((round(width*SCALE), round(im.height / im.width * width*SCALE)), Image.Resampling.LANCZOS)

def paste_center(canvas, image, center, opacity=1):
    if opacity < 1:
        image = image.copy(); image.putalpha(image.getchannel('A').point(lambda v: round(v*max(0,opacity))))
    canvas.alpha_composite(image, (round(center[0]*SCALE-image.width/2), round(center[1]*SCALE-image.height/2)))

def generated_frame(obj, clip, index):
    ident = obj['id']; size = obj['frameSize']; root = obj['root']
    canvas = Image.new('RGBA', tuple(v*SCALE for v in size))
    t = index/12; phase = t*math.tau
    if ident.startswith('dish-'):
        paste_center(canvas,cutout(ident,66),root)
        return canvas
    width = 82 if ident != 'decor-bubbles' else 72
    image = cutout(ident,width)
    alpha = 1
    if 'appear' in clip['id']:
        scale = .5 + .5*math.sin((index+1)/12*math.pi/2)
        image = image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.LANCZOS)
        alpha = (index+1)/12
    elif 'fade' in clip['id']: alpha = 1-index/12
    elif clip['id']=='happy-transition':
        scale=1+.12*math.sin(phase)
        image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.LANCZOS)
    center=[root[0],root[1]-52-3*math.sin(phase)]
    if ident=='decor-bubbles': center=[root[0],root[1]-70-index*3];alpha=.5+.5*math.sin((index+1)/13*math.pi)
    paste_center(canvas,image,center,alpha)
    if ident=='bubble-preference':
        dish = 'dish-cucumber' if clip['id'].startswith('cucumber') else 'dish-eel' if clip['id'].startswith('eel') else 'dish-salmon'
        dish_image=cutout(dish,40)
        if 'appear' in clip['id']: dish_image=dish_image.resize((round(dish_image.width*scale),round(dish_image.height*scale)),Image.Resampling.LANCZOS)
        paste_center(canvas,dish_image,[center[0],center[1]-5],alpha)
    return canvas

def procedural_frame(obj, clip, index, direction):
    size=obj['frameSize'];root=obj['root']; ident=obj['id']; t=index/12
    canvas=Image.new('RGBA',tuple(v*SCALE for v in size)); draw=ImageDraw.Draw(canvas)
    alpha=1 if clip['id']=='active' else .25+.65*t if clip['id']=='windup' else 1-.9*t
    aqua=(155,245,255,round(255*alpha));amber=(255,169,31,round(255*alpha))
    angle={'N':math.pi,'E':-math.pi/2,'S':0,'W':math.pi/2}[direction]
    def point(p):
        x,y=p;return ((root[0]+x*math.cos(angle)-y*math.sin(angle))*SCALE,(root[1]+x*math.sin(angle)+y*math.cos(angle))*SCALE)
    def line(p,color=aqua,width=3):draw.line([point(q) for q in p],fill=color,width=width*SCALE,joint='curve')
    if ident=='eel-warning-strip':
        # Full strip fits the complete registered capture even for E/W.
        half=155
        draw.polygon([point(p)for p in [(-27,-half),(27,-half),(27,half),(-27,half)]],fill=(255,142,20,round(35*alpha)))
        for j in range(12):
            y=-half+4+j*25+t*4;line([(-26,y),(26,y+20)],amber,3)
        line([(-28,-half),(-28,half)],amber,2);line([(28,-half),(28,half)],amber,2)
    elif ident=='eel-lightning-symbol':
        draw.polygon([point(p) for p in [(3,-48),(-27,5),(-3,2),(-12,48),(31,-13),(9,-9)]],fill=amber)
        line([(3,-48),(-27,5),(-3,2),(-12,48),(31,-13),(9,-9),(3,-48)],(255,226,104,round((150+80*math.sin(t*math.tau))*alpha)),2)
    elif ident=='eel-discharge':
        for j in range(7):
            a=j*math.tau/7+t*.13;r=(math.cos(a),math.sin(a));s=(-r[1],r[0]);l=62+math.sin(t*math.tau+j)*8
            line([(r[0]*12,r[1]*12),(r[0]*30+s[0]*9,r[1]*30+s[1]*9),(r[0]*41-s[0]*8,r[1]*41-s[1]*8),(r[0]*l,r[1]*l)],aqua,4)
    elif ident=='attack-lateral-current':
        for j in range(5):
            y=-40+j*20;x=-90+t*50
            line([(x,y+4),(x+40,y-3),(x+90,y),(x+140,y-4)],aqua,3+j%2)
            line([(x+122,y-17),(x+140,y-4),(x+120,y+8)],aqua,4)
    else:
        for strand in range(3):
            points=[]
            for step in range(60):
                u=step/59;a=u*math.tau*1.4+t*math.tau+strand*math.tau/3;r=12+u*(49+strand*4)
                points.append((math.cos(a)*r,math.sin(a)*r*.55))
            line(points,aqua,3)
    return canvas

def export_object(obj):
    ident=obj['id']; generated=ident in GENERATED
    # Preserve fixed source registration; full warning stripe must fit every view.
    if ident=='eel-warning-strip': obj.update(frameSize=[448,512],root=[224,256])
    obj.update(sourceScale=SCALE, projection='screen-space-2d',facingPolicy='camera-facing' if generated else 'directional-2d',productionStage='ImageGen 2D artwork · awaiting art approval' if generated else 'Procedural 2D cue · Godot draw source · awaiting art approval')
    obj['source']={'pipeline':'imagegen-2d' if generated else 'procedural-2d','modelScript':'source/2d/publish_2d.py','prompts':'source/2d/prompts.json'}
    if generated: obj['source']['artwork']=f'source/2d/generated/{ident}.png';obj['source']['sha256']=sha(HERE/'generated'/f'{ident}.png')
    else: obj['source']['godot']='source/2d/world_effects.gd'
    obj['artStyle']={'lowerShading':'painted into 2D artwork' if generated else 'not applicable: flat gameplay cue','worldDirectionalLight':False,'contrast':'painted source palette; no additional Blender/CSS grade'}
    obj.pop('sockets',None); obj.pop('ports',None)
    for clip in obj['clips']:
        frames=clip['frames']; columns=min(6,frames);rows=math.ceil(frames/columns)
        clip.update(fps=12,frameOrder=list(range(frames)))
        clip['directions']={}
        for direction in (['S'] if generated else DIRECTIONS):
            atlas=Image.new('RGBA',(obj['frameSize'][0]*SCALE*columns,obj['frameSize'][1]*SCALE*rows))
            unique=[]
            for i in range(frames):
                im=generated_frame(obj,clip,i) if generated else procedural_frame(obj,clip,i,direction)
                unique.append(hashlib.sha256(im.tobytes()).hexdigest())
                atlas.alpha_composite(im,((i%columns)*im.width,(i//columns)*im.height))
            path=PRODUCTION/'sprites'/ident/f'2d-{clip["id"]}-{direction}.png';path.parent.mkdir(parents=True,exist_ok=True);atlas.save(path,optimize=True)
            entry={'image':str(path.relative_to(PRODUCTION)),'columns':columns,'rows':rows,'atlasSize':list(atlas.size),'rects':[[i%columns*obj['frameSize'][0]*SCALE,i//columns*obj['frameSize'][1]*SCALE,obj['frameSize'][0]*SCALE,obj['frameSize'][1]*SCALE] for i in range(frames)],'uniqueFrames':len(set(unique))}
            if frames>1 and len(set(unique))<6:raise ValueError(f'{ident}/{clip["id"]}: fewer than6unique frames')
            clip['directions'][direction]=entry
        if generated:
            for direction in DIRECTIONS: clip['directions'][direction]=copy.deepcopy(clip['directions']['S'])
    return obj

def merge(manifest):
    overrides=json.loads((HERE/'overrides.json').read_text())
    objects=[]
    for obj in manifest['objects']:
        if obj['id'] in DELETED: continue
        if obj['id'] in overrides:
            changed=copy.deepcopy(overrides[obj['id']]);changed['interactions']=obj.get('interactions',changed.get('interactions',[]));obj=changed
        if obj['id'] in ['chef-blackboard','sign-blank']:
            obj['facingPolicy']='single-player-facing'
            obj['renderPass']='foreground'
            obj['requirements']['directions']=['S']
            if obj['id']=='chef-blackboard':
                obj['clips']=[c for c in obj['clips'] if c['id'] in ['idle','selected','recipe-change']]
                obj['requirements']['states']=['idle','selected','recipe-change']
            for clip in obj['clips']:clip['directions']={'S':clip['directions']['S']}
            obj['reviewNote']='Blank player-facing surface at the front of its tile; shares the same tile with another object. Content is drawn dynamically in Godot.'
            if obj['id']=='chef-blackboard':obj['interactions']=[{'name':'Chef and blank board share one tile','gridSize':[3,2],'placements':[{'object':'chef-lena','x':1,'y':0,'direction':'E','clip':'work'},{'object':'chef-blackboard','x':1,'y':0,'direction':'S','clip':'idle','renderPass':'foreground'}],'note':obj['reviewNote']}]
            else:obj['interactions']=[{'name':'Front-edge sign with a plant behind it','gridSize':[3,2],'placements':[{'object':'plant-angular','x':1,'y':0,'direction':'S','clip':'static'},{'object':'sign-blank','x':1,'y':0,'direction':'S','clip':'static','renderPass':'foreground'}],'note':obj['reviewNote']}]
        for scene in obj.get('interactions',[]):
            scene['placements']=[p for p in scene.get('placements',[]) if p['object'] not in DELETED]
            for p in scene['placements']:
                if p['object'] in ['chef-blackboard','sign-blank']:p['direction']='S';p['renderPass']='foreground';p['clip']={'cucumber-selected':'selected','eel-selected':'selected','cucumber-idle':'idle','eel-idle':'idle'}.get(p.get('clip'),p.get('clip'))
        objects.append(obj)
    manifest['objects']=objects
    manifest.setdefault('production',{})['twoDimensionalAssets']={'count':len(overrides),'source':'source/2d/prompts.json','effects':'source/2d/world_effects.gd','deletedLargeClusters':sorted(DELETED)}
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--merge-only',action='store_true');args=parser.parse_args()
    manifest_path=PRODUCTION/'library.json';manifest=json.loads(manifest_path.read_text())
    if not args.merge_only:
        overrides={obj['id']:export_object(copy.deepcopy(obj)) for obj in manifest['objects'] if obj['id'] in GENERATED+PROCEDURAL}
        (HERE/'overrides.json').write_text(json.dumps(overrides,indent=2)+'\n')
        print(f'Packed {len(overrides)} 2D objects; full fixed-frame12fps atlases.')
    if args.apply:
        result=merge(manifest);manifest_path.write_text(json.dumps(result,indent=2)+'\n');print(f'Merged {len(result["objects"])} active objects.')
