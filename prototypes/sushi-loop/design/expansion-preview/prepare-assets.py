"""Extract exact production first frames; retain fixed world roots and preview bounds."""
import json, hashlib
from pathlib import Path
from PIL import Image

here = Path(__file__).resolve().parent
root = here.parents[1]
library = json.loads((root / 'assets/production/library.json').read_text())
names = ['garbage-sofa', 'garbage-car', 'garbage-shelving', 'dock-floor', 'dock-cover',
         'submarine-yellow', 'workshop-hut', 'wall-middle', 'wall-middle-e', 'plant-angular', 'barrel-wood',
         'crate-wood', 'lantern-gold', 'sign-blank', 'slate-rock', 'stool-wood',
         'belt-straight-e', 'chef-lena', 'chef-omar', 'floor-cream']
records = {}
rotatable = {'garbage-sofa','garbage-car','garbage-shelving','plant-angular','barrel-wood','crate-wood','slate-rock','lantern-gold','sign-blank'}
for name in names:
    obj = next(o for o in library['objects'] if o['id'] == ('wall-middle' if name == 'wall-middle-e' else name))
    direction = obj['clips'][0]['directions']['E' if name == 'wall-middle-e' else 'S']
    x, y, w, h = direction['rects'][0]
    source = root / 'assets/production' / direction['image']
    destination = here / f'assets/{name}.png'
    im = Image.open(source).crop((x, y, x+w, y+h))
    im.save(destination)
    b = im.getbbox()
    records[name] = dict(source=str(source.relative_to(root)),
                         source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                         crop_xywh=[x,y,w,h], frame_size=obj['frameSize'], root=obj['root'],
                         footprint=obj['footprint'], destination=str(destination.relative_to(here)),
                         sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                         visible_bounds=[b[0],b[1],b[2]-b[0],b[3]-b[1]])
# Extract exact native facings, including source metadata for rotated occupancy.
for name in rotatable:
    obj = next(o for o in library['objects'] if o['id'] == name)
    for facing, direction in obj['clips'][0]['directions'].items():
        x,y,w,h = direction['rects'][0]
        source = root / 'assets/production' / direction['image']
        destination = here / f'assets/{name}-{facing}.png'
        im = Image.open(source).crop((x,y,x+w,y+h)); im.save(destination); b = im.getbbox()
        records[f'{name}-{facing}'] = dict(source=str(source.relative_to(root)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),crop_xywh=[x,y,w,h],frame_size=obj['frameSize'],root=obj['root'],footprint=obj['footprint'],facing=facing,destination=str(destination.relative_to(here)),sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),visible_bounds=[b[0],b[1],b[2]-b[0],b[3]-b[1]])
# Approved experiment variants are copied without re-rendering; retain their records.
old=json.loads((here/'world-registration.json').read_text())
records.update({n:r for n,r in old.items() if r.get('approved_experiment')})
(here / 'world-registration.json').write_text(json.dumps(records, indent=2) + '\n')
