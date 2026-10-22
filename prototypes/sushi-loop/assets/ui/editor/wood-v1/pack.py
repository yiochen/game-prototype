#!/usr/bin/env python3
"""Extract unresized ImageGen pixels; only registered plain spans may stretch."""
from pathlib import Path
import hashlib
import json
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RUNTIME = ROOT / 'godot/assets/ui/editor-wood'
SOURCES = {
    'board': [28, 18, 1930, 330],
    'tab-idle': [75, 360, 500, 205],
    'tab-active': [590, 360, 510, 178],
    'shop': [1125, 360, 510, 205],
    'badge': [1680, 360, 220, 215],
    'waves': [24, 575, 1935, 207],
    'join': [800, 170, 24, 24],
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    source = HERE / 'raw/surfaces.png'
    image = Image.open(source).convert('RGBA')
    atlas = Image.new('RGBA', (2048, 1024))
    styles, icons, entries = {}, {}, {}
    x = y = row = 0
    for name, (sx, sy, w, h) in SOURCES.items():
        if x + w + 8 > 2048:
            x, y, row = 0, y + row, 0
        region = [x + 4, y + 4, w, h]
        atlas.paste(image.crop((sx, sy, sx + w, sy + h)), (x + 4, y + 4))
        entries[name] = {'source_region': [sx, sy, w, h], 'region': region}
        entry = {'region': region}
        if name in ('board', 'tab-idle', 'tab-active', 'shop'):
            slices, edges = ([88] * 4, [40] * 4) if name == 'shop' else ([48] * 4, [24] * 4)
            entry.update(slice_px=slices, edge=edges, content=[10] * 4,
                         face_px=[8, 8, w - 16, h - 16],
                         stretch='Only plain central maple/walnut grain and straight edge spans stretch; all four corner strips retain one uniform source-to-logical scale.',
                         states={'pressed': {'tint': 'efdfcaff'}, 'disabled': {'tint': 'b5afa6aa'}})
            if name == 'shop':
                entry['minimum_height'] = 100
            styles[name] = entry
        else:
            icons[name] = entry
        x += w + 8
        row = max(row, h + 8)
    target = RUNTIME / 'skin.png'
    atlas.crop((0, 0, 2048, y + row)).save(target)
    refs = ['design/inventory-tray-concepts/v5-connected-tabs/full-screen.png',
            'design/art-directions/restaurant-item-catalog.png']
    record = {'mode': 'builtin-image_gen-edit', 'transparent': True,
              'prompt': (HERE / 'surfaces-prompt.txt').read_text(),
              'source': 'assets/ui/editor/wood-v1/raw/surfaces.png',
              'source_sha256': sha(source), 'dimensions': list(image.size),
              'references': {p: sha(ROOT / p) for p in refs}, 'entries': entries,
              'packing': 'Exact RGBA crops with 4-pixel transparent gutters; no repaint, masking or resampling.',
              'connected_joint': 'The active cap excludes its generated lower edge. The board joint is covered with the registered plain maple join crop. It is decorative only.',
              'state_inventory': ['normal', 'pressed', 'disabled', 'selected', 'focus', 'quantity badge', 'safe-area waves']}
    (HERE / 'imagegen.json').write_text(json.dumps(record, indent=2) + '\n')
    manifest = {'version': 1, 'atlas': 'skin.png', 'atlas_sha256': sha(target),
                'source_record': 'assets/ui/editor/wood-v1/imagegen.json',
                'source_record_sha256': sha(HERE / 'imagegen.json'),
                'packing_script_sha256': sha(Path(__file__)), 'styles': styles, 'icons': icons}
    (RUNTIME / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Packed coordinated wood family:', target)

if __name__ == '__main__':
    main()
