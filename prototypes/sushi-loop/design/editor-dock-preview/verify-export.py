"""Validate and package the CSS-rendered Godot asset set (requires Pillow)."""
from hashlib import sha256
from pathlib import Path
import json
import zipfile

from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[3]
OUTPUT = HERE.parents[1] / 'assets/ui/editor/html-export-v1'
manifest = json.loads((OUTPUT / 'manifest.json').read_text())
checks = []


def require(condition, message):
    if not condition:
        raise AssertionError(message)


for path, expected in manifest['source']['files'].items():
    require(sha256((REPOSITORY / path).read_bytes()).hexdigest() == expected,
            f'Source changed since export: {path}')
checks.append('All recorded source hashes match current files.')

require(len(manifest['assets']) == 26, 'Incomplete component set')
png_count = 0
for name, asset in manifest['assets'].items():
    for scale_name, variant in asset['variants'].items():
        scale = int(scale_name.removesuffix('x'))
        path = OUTPUT / variant['path']
        require(sha256(path.read_bytes()).hexdigest() == variant['sha256'], f'Hash: {name}')
        image = Image.open(path)
        require(image.mode == 'RGBA', f'No RGBA transparency: {path}')
        w, h = image.size
        require([w, h] == variant['size'] == [n * scale for n in asset['logical_size']],
                f'Incorrect resolution: {path}')
        alpha = image.getchannel('A')
        require(alpha.getbbox() is not None, f'Empty image: {path}')
        borders = [(0, 0, w, 1), (0, h - 1, w, h), (0, 0, 1, h), (w - 1, 0, w, h)]
        require(all(alpha.crop(box).getextrema()[1] == 0 for box in borders),
                f'Shadow or artwork clipped at outer edge: {path}')
        if 'nine_patch_margins_ltrb' in variant:
            l, t, r, b = variant['nine_patch_margins_ltrb']
            require(min(l, t, r, b) >= 0 and l + r < w and t + b < h,
                    f'Overlapping nine-patch cuts: {path}')
            if asset['resize'] == 'horizontal_only_tile_center':
                require(t == b == 0, f'Capsule end caps must remain complete: {path}')
        if asset['kind'] == 'icon':
            for channel in image.split()[:3]:
                tinted = ImageChops.multiply(ImageChops.invert(channel), alpha)
                require(tinted.getbbox() is None, f'Icon is not white/modulatable: {path}')
        png_count += 1

checks.extend([
    f'{png_count} nonempty RGBA PNGs have exact 1x/2x dimensions and matching hashes.',
    'Every outer pixel is transparent; pressed shadows fit inside the gutters.',
    'All slicing margins leave a nonzero center; capsule cuts retain complete end caps.',
    'All eight icon pairs use white artwork suitable for native tinting.',
])
for prefix in ['tab', 'shop', 'hud-cream', 'hud-live']:
    for scale in ['1x', '2x']:
        a = manifest['assets'][f'{prefix}-normal']['variants'][scale]['sha256']
        b = manifest['assets'][f'{prefix}-pressed']['variants'][scale]['sha256']
        require(a != b, f'Missing press state: {prefix}/{scale}')
checks.append('All four normal/pressed surface pairs differ at both resolutions.')
for texture in manifest['textures'].values():
    require(sha256((OUTPUT / texture['path']).read_bytes()).hexdigest() == texture['sha256'],
            f'Original texture hash mismatch: {texture["path"]}')
checks.append('Both original background textures match their source hashes.')

cell_w, cell_h, columns = 320, 188, 4
rows = (len(manifest['assets']) + columns - 1) // columns
sheet = Image.new('RGB', (cell_w * columns, cell_h * rows), '#132d40')
draw = ImageDraw.Draw(sheet)
for i, (name, asset) in enumerate(manifest['assets'].items()):
    x, y = (i % columns) * cell_w, (i // columns) * cell_h
    draw.text((x + 12, y + 8), name, fill='#fff2d5')
    draw.text((x + 12, y + 24), f'{asset["logical_size"][0]} x {asset["logical_size"][1]} px @1x', fill='#a8bbc6')
    for by in range(y + 44, y + cell_h - 8, 12):
        for bx in range(x + 8, x + cell_w - 8, 12):
            color = '#244254' if ((bx - x) // 12 + (by - y) // 12) % 2 else '#1b3548'
            draw.rectangle((bx, by, min(bx + 11, x + cell_w - 9), min(by + 11, y + cell_h - 9)), fill=color)
    image = Image.open(OUTPUT / asset['variants']['1x']['path'])
    image.thumbnail((cell_w - 24, cell_h - 54), Image.Resampling.LANCZOS)
    sheet.paste(image, (x + (cell_w - image.width) // 2, y + 44 + (cell_h - 52 - image.height) // 2), image)
sheet.save(OUTPUT / 'preview.png')
report = {'status': 'PASS', 'assets': len(manifest['assets']), 'png_files': png_count, 'checks': checks}
(OUTPUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')

archive = OUTPUT.with_suffix('.zip')
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
    for path in sorted(OUTPUT.rglob('*')):
        if path.is_file():
            bundle.write(path, path.relative_to(OUTPUT.parent))
print(f'PASS: {png_count} PNGs; package: {archive.relative_to(REPOSITORY)}')
