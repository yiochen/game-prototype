#!/usr/bin/env python3
"""Pack measured ImageGen source rectangles without repainting or rescaling.

Each atlas item retains the exact source RGBA crop and a four-pixel transparent
sampling gutter. Source-pixel and logical nine-patch calibration remain separate.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image

HERE = Path(__file__).resolve().parent
PROTOTYPE = HERE.parents[3]
GUTTER = 4
WIDTH = 2048


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    config = json.loads((HERE / 'authoring.json').read_text())
    runtime = PROTOTYPE / config['runtime']
    runtime.mkdir(parents=True, exist_ok=True)
    record = {key: value for key, value in config.items() if key not in ('assets', 'runtime', 'reference')}
    record['accepted_composition']['sha256'] = sha(PROTOTYPE / record['accepted_composition']['path'])
    record['latest_composition']['sha256'] = sha(PROTOTYPE / record['latest_composition']['path'])
    composition = record['composition_generation']
    composition_path = HERE / composition['raw']
    composition['raw_sha256'] = sha(composition_path)
    composition['dimensions'] = list(Image.open(composition_path).size)
    composition['reference_sha256'] = {path: sha(PROTOTYPE / path) for path in composition['reference_paths']}
    for reference in record['references']:
        reference['sha256'] = sha(PROTOTYPE / reference['path'])
    images = {}
    for generation in record['generations']:
        source = HERE / generation['raw']
        images[generation['raw']] = Image.open(source).convert('RGBA')
        generation['raw_sha256'] = sha(source)
        generation['dimensions'] = list(images[generation['raw']].size)
        generation['reference_sha256'] = {path: sha(PROTOTYPE / path) for path in generation['reference_paths']}
    rows, x, y, height = [], 0, 0, 0
    for asset in config['assets']:
        sx, sy, sw, sh = asset['source_region']
        width, item_height = sw + GUTTER * 2, sh + GUTTER * 2
        if x + width > WIDTH:
            x, y, height = 0, y + height, 0
        region = [x, y, width, item_height]
        rows.append((asset, region))
        x += width
        height = max(height, item_height)
    atlas_height = ((y + height + 63) // 64) * 64
    atlas = Image.new('RGBA', (WIDTH, atlas_height), (0, 0, 0, 0))
    styles, icons, entries = {}, {}, {}
    for asset, region in rows:
        sx, sy, sw, sh = asset['source_region']
        crop = images[asset['source']].crop((sx, sy, sx + sw, sy + sh))
        # No mask/compositing: preserve even invisible RGB and all original alpha.
        atlas.paste(crop, (region[0] + GUTTER, region[1] + GUTTER))
        identity = asset['id']
        entry = {'region': region}
        registration = {'kind': asset['kind'], 'generation': asset['generation'],
                        'source': str((HERE / asset['source']).relative_to(PROTOTYPE)),
                        'source_sha256': sha(HERE / asset['source']),
                        'source_region': asset['source_region'], 'region': region}
        if asset['kind'] == 'style':
            for key in ('slice_px', 'edge', 'content', 'stretch'):
                entry[key] = asset[key]
                registration[key] = asset[key]
            for key in ('states', 'draw_center', 'tint', 'minimum_height'):
                if key in asset:
                    entry[key] = asset[key]
                    if key == 'minimum_height':
                        registration[key] = asset[key]
            styles[identity] = entry
        else:
            icons[identity] = entry
        entries[identity] = registration
    record['entries'] = entries
    (HERE / 'imagegen.json').write_text(json.dumps(record, indent=2) + '\n')
    target = runtime / 'skin.png'
    atlas.save(target, optimize=True)
    # Remove only superseded runtime UI PNGs; originals remain in v1/raw.
    for previous in runtime.glob('*.png'):
        if previous.name != target.name:
            previous.unlink()
    manifest = {'version': 3, 'reference': config['reference'],
                'reference_sha256': sha(PROTOTYPE / config['reference']),
                'source_record': str((HERE / 'imagegen.json').relative_to(PROTOTYPE)),
                'source_record_sha256': sha(HERE / 'imagegen.json'),
                'authoring_sha256': sha(HERE / 'authoring.json'),
                'packing_script_sha256': sha(Path(__file__)),
                'atlas': target.name, 'atlas_sha256': sha(target),
                'atlas_bytes': target.stat().st_size, 'atlas_dimensions': list(atlas.size),
                'styles': styles, 'icons': icons}
    (runtime / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'styles': len(styles), 'icons': len(icons), 'atlas': list(atlas.size), 'bytes': target.stat().st_size}))


if __name__ == '__main__':
    main()
