"""Judge-only contact evidence; never publishes or modifies source artwork."""
from pathlib import Path
from PIL import Image, ImageDraw
import json
import hashlib

BASE = Path(__file__).resolve().parents[1]
PROTOTYPE = BASE.parents[3]
REVIEW = BASE / 'reviews'
catalog = json.loads((BASE / 'inputs/catalog-object.json').read_text())
variant = json.loads((BASE / 'inputs/runtime-variants/smile/original-manifest.json').read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
backgrounds = {'light': (248, 247, 241, 255), 'gray': (128, 128, 128, 255), 'dark': (31, 34, 37, 255)}
records = []
for kind, clips in [('heart', catalog['clips']), ('smile', list(variant['objects']['bubble-happy']['clips'].values()))]:
    sheets = {name: Image.new('RGBA', (1360, 544), color) for name, color in backgrounds.items()}
    for row, clip in enumerate(clips):
        entry = clip['directions']['S']
        path = PROTOTYPE / 'assets/production' / entry['image'] if kind == 'heart' else BASE / 'inputs/runtime-variants/smile/original-atlases' / Path(entry['image']).name
        atlas = Image.open(path).convert('RGBA')
        pixels, bounds = [], []
        for index, (x, y, width, height) in enumerate(entry['rects']):
            frame = atlas.crop((x, y, x + width, y + height))
            pixels.append(hashlib.sha256(frame.tobytes()).hexdigest())
            bounds.append(frame.getchannel('A').getbbox())
            logical = frame.resize((192, 320), Image.Resampling.LANCZOS)
            viewport = logical.crop((40, 136, 152, 256))
            for name, sheet in sheets.items():
                sheet.alpha_composite(viewport, (8 + index * 112, 16 + row * 132))
                ImageDraw.Draw(sheet).text((10 + index * 112, 2 + row * 132), f'{clip["id"]} {index}', fill=(255,255,255) if name == 'dark' else (0,0,0))
        records.append({'kind': kind, 'clip': clip['id'], 'atlas': str(path), 'sha256': sha(path), 'size': list(atlas.size), 'frames': 12, 'uniquePixelFrames': len(set(pixels)), 'aliases': ['S','N','E','W'] if kind == 'heart' else ['S'], 'bounds': bounds})
    for name, sheet in sheets.items():
        sheet.convert('RGB').save(REVIEW / f'baseline-{kind}-{name}.png')

sheet = Image.new('RGBA', (672, 372))
inputs = [('original heart', PROTOTYPE/'assets/production/source/2d/generated/bubble-happy.png'), ('target heart', BASE/'inputs/target.png'), ('original smile', BASE/'inputs/runtime-variants/smile/original-source/bubble-happy-smile.png'), ('target smile', BASE/'inputs/runtime-variants/smile/target.png')]
sources = []
for row, (label, path) in enumerate(inputs):
    image = Image.open(path).convert('RGBA')
    rectangle = image.getchannel('A').point(lambda value: 255 if value > 8 else 0).getbbox()
    cutout = image.crop(rectangle)
    cutout = cutout.resize((82, round(cutout.height / cutout.width * 82)), Image.Resampling.LANCZOS)
    sources.append({'label': label, 'path': str(path), 'sha256': sha(path), 'size': list(image.size), 'alphaRange': list(image.getchannel('A').getextrema()), 'alpha8Rectangle': rectangle, 'logicalNormalizedSize': list(cutout.size)})
    for column, (name, color) in enumerate(backgrounds.items()):
        tile = Image.new('RGBA', (224, 93), color)
        tile.alpha_composite(cutout, (132, (93-cutout.height)//2))
        ImageDraw.Draw(tile).text((6,36), label, fill=(255,255,255) if name == 'dark' else (0,0,0))
        sheet.alpha_composite(tile, (column*224,row*93))
sheet.convert('RGB').save(REVIEW / 'baseline-targets-logical.png')
(REVIEW/'baseline-contract-audit.json').write_text(json.dumps({'schemaVersion':1, 'evidence':'Original384x640 frames uniformly downscaled to192x320 and fixed viewport [40,136,152,256]. Target comparison: one alpha>8rectangle and uniform82logicalwidth. Inspection only; no asset publication.', 'sources': sources, 'atlases': records}, indent=2)+'\n')
print(json.dumps({'atlasCount':len(records), 'mainAliasSlots':192, 'smileActualFrames':48, 'allActualFrames':96, 'evidenceDirectory':str(REVIEW)},indent=2))
