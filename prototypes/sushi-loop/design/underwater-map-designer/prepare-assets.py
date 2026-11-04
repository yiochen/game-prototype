"""Package exact first frames from the registered atlas, without resizing or repainting."""
from pathlib import Path
import json, hashlib
from PIL import Image
base=Path(__file__).resolve().parent
production=base.parent.parent/'assets/production'
lib=json.loads((production/'library.json').read_text())
ids=['floor-underwater','rock-wall-middle','rock-wall-edge','rock-wall-corner','rock-wall-end','rock-shelf-middle','rock-shelf-edge','rock-shelf-corner','rock-shelf-end','reef-middle','reef-edge','reef-corner','reef-end','wreck-middle','wreck-edge','wreck-corner','wreck-end','rock-half-width','boulder-underwater','column-broken','decor-foreground-rock','decor-foreground-coral','decor-starfish','decor-midground-coral','decor-kelp','decor-ruin-fragment','decor-background-rock','decor-background-wreck','decor-background-fish','decor-bubbles','decor-light-shafts']
objects=[];sources=[]
for ident in ids:
    o=next(o for o in lib['objects'] if o['id']==ident)
    clip=next((c for c in o['clips'] if c['id']=='static'),o['clips'][0])
    layer='floor' if ident=='floor-underwater' else 'decor' if ident.startswith('decor-') else 'obstacles'
    if layer=='floor':group='Seabed'
    elif ident.startswith('rock-wall'):group='Rock wall'
    elif ident.startswith('rock-shelf'):group='Rock shelf'
    elif ident.startswith('reef-'):group='Reef'
    elif ident.startswith('wreck-'):group='Wreck'
    elif layer=='obstacles':group='Loose obstacles'
    elif ident.startswith('decor-background'):group='Background'
    else:group='Decoration'
    entry={'id':ident,'name':o['name'],'layer':layer,'group':group,'directions':{},'footprint':o['footprint']}
    directions={'S':clip['directions']['S']} if layer=='floor' else clip['directions']
    for direction,d in directions.items():
        frame=d.get('frameSize',clip.get('frameSize',o['frameSize']))
        root=d.get('root',clip.get('root',o['root']))
        scale=d.get('sourceScale',clip.get('sourceScale',o.get('sourceScale',1)))
        rect=d.get('rects',[[0,0,frame[0]*scale,frame[1]*scale]])[0]
        source=production/d['image']
        with Image.open(source) as atlas:
            image=atlas.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]))
            path=f'{ident}-{direction}.png'
            image.save(base/'assets'/path,optimize=True)
            entry['directions'][direction]={'image':path,'frameSize':frame,'root':root,'rootCell':o.get('directionRootCells',{}).get(direction,o.get('rootCell',[.5,.5])),'footprint':o.get('directionFootprints',{}).get(direction,o['footprint']),'bounds':list(image.getbbox() or (0,0,image.width,image.height))}
        sources.append({'image':path,'source':d['image'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_rect':rect,'operation':'Exact unscaled first-frame extraction','sha256':hashlib.sha256((base/'assets'/path).read_bytes()).hexdigest()})
    objects.append(entry)
(base/'assets/catalog.json').write_text(json.dumps(objects,indent=2)+'\n')
(base/'assets/provenance.json').write_text(json.dumps({'source':'../../assets/production/library.json','cellSize':128,'sources':sources},indent=2)+'\n')
print(f'{len(objects)} objects, {len(sources)} exact frame exports')
