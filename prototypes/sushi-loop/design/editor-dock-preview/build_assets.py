#!/usr/bin/env python3
"""Extract unchanged RGBA crops for the HTML assembly, recording every source."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ASSETS = HERE / 'assets'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ASSETS.mkdir(exist_ok=True)
    records = {}
    def extract(name, source, region=None, trim=False):
        image = Image.open(source).convert('RGBA')
        x, y, w, h = region or [0, 0, image.width, image.height]
        crop = image.crop((x, y, x + w, y + h))
        if trim:
            bounds = crop.getbbox()
            if bounds:
                crop = crop.crop(bounds)
                x, y, w, h = x + bounds[0], y + bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1]
        target = ASSETS / (name + '.png')
        crop.save(target)
        records[name] = {'source': str(source.relative_to(ROOT)), 'source_sha256': sha(source),
                         'source_region': [x, y, w, h], 'sha256': sha(target), 'resampled': False}
    record = json.loads((ROOT / 'assets/ui/editor/wood-v1/imagegen.json').read_text())
    extract('waves', ROOT / record['source'], record['entries']['waves']['source_region'])
    # Plain center only: tile at one scale so the fine horizontal grain cannot
    # become vertical streaks when the panel grows beyond its corner strips.
    bx, by, bw, bh = record['entries']['board']['source_region']
    extract('wood-grain', ROOT / record['source'], [bx + 112, by + 112, bw - 224, bh - 224])
    for name in ['belt-straight-e', 'stool-wood', 'plant-angular', 'crate-wood', 'barrel-wood', 'floor-cream']:
        extract(name, ROOT / 'assets/ui/editor/goods-v1/renders' / (name + '.png'), trim=True)
    catalog = json.loads((ROOT / 'godot/assets/catalog/manifest.json').read_text())
    for name in ['chef-lena', 'chef-omar']:
        frame = catalog['objects'][name]['clips']['idle']['directions']['S']
        extract(name, ROOT / 'godot/assets/catalog' / frame['image'], frame['rects'][0], trim=True)
    extract('restaurant-sky', ROOT / 'design/inventory-tray-concepts/v5-connected-tabs/full-screen.png', [0, 0, 840, 143])
    extract('restaurant-wall', ROOT / 'design/inventory-tray-concepts/v5-connected-tabs/full-screen.png', [0, 268, 840, 211])
    extract('restaurant-floor', ROOT / 'design/inventory-tray-concepts/v5-connected-tabs/full-screen.png', [0, 479, 840, 865])
    font = ROOT / 'godot/assets/fonts/Nunito.ttf'
    shutil.copy2(font, ASSETS / 'Nunito.ttf')
    records['font'] = {'source': str(font.relative_to(ROOT)), 'sha256': sha(font)}
    # Remove only outputs produced by earlier versions of this extractor.
    # Original generated sheets and historical review artifacts stay intact.
    for name in ['board','tab-idle','tab-active','shop','badge','join',
                 'icon-people','icon-layout','icon-floor','icon-shop','icon-caret-left',
                 'restaurant-reference','restaurant-upper']:
        (ASSETS / (name + '.png')).unlink(missing_ok=True)
    (ASSETS / 'provenance.json').write_text(json.dumps(records, indent=2) + '\n')
    # Mocklens deliberately renders from file://, where module imports are
    # blocked. Generate independent review states with the same inline source.
    script = (HERE / 'app.js').read_text().replace(
        "const asset = name => new URL(`./assets/${name}.png`, import.meta.url).href;",
        "const asset = name => new URL(`../assets/${name}.png`, location.href).href;")
    for state in ['layout', 'people', 'floor', 'out-of-stock', 'shop', 'live']:
        (HERE / 'screens' / f'{state}.phone.html').write_text(
            '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            '<meta name="mocklens:form-factor" content="phone"><meta name="mocklens:primary-device" content="phone">'
            '<meta name="mocklens:target-devices" content="phone,narrow,landscape,review-browser"><meta name="mocklens:viewport" content="390x844">'
            f'<title>Sushi Loop · {state}</title><link rel="stylesheet" href="../shared.css"></head>'
            f'<body data-state="{state}"><main class="scene" aria-label="Sushi Loop editor assembly"></main><script>\n{script}\n</script></body></html>')
    print('Extracted', len(records), 'local assets without resampling.')

if __name__ == '__main__': main()
