"""Compose a ship from ship-layout.json (same math as app.js composeShip) for previews."""
import json, sys
from PIL import Image
A = 'assets/'
L = json.load(open(A + 'ship-layout.json'))
K = L['compose']

def compose(h, p, c):
    hull, harp, col = L['hull'][h - 1], L['harpoon'][p - 1], L['collector'][c - 1]
    layers = []
    # Hull centred at origin.
    hx, hy = -hull['size'][0] / 2, -hull['size'][1] / 2
    s = K['harpoon_scale']; layers.append(('harpoon', hull['nose'][0] + hx - harp['base'][0] * s, hull['nose'][1] + hy - harp['base'][1] * s, s, False, harp, 2))
    cs = K['collector_scale']; ov = K['collector_overlap']
    lx = hull['left'][0] + hx + ov - col['bracket'][0] * cs; ly = hull['left'][1] + hy - col['bracket'][1] * cs
    layers.append(('collector', lx, ly, cs, False, col, 0))
    rx = hull['right'][0] + hx - ov + col['bracket'][0] * cs - col['size'][0] * cs
    layers.append(('collector', rx, ly, cs, True, col, 0))
    layers.append(('hull', hx, hy, 1.0, False, hull, 1))
    return layers

def render(h, p, c, scale=0.5):
    layers = sorted(compose(h, p, c), key=lambda l: l[6])
    canvas = Image.new('RGBA', (900, 1100), (233, 214, 180, 255))
    ox, oy = 450, 640
    for name, x, y, s, flip, part, _ in layers:
        im = Image.open(A + part['file']).convert('RGBA')
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        canvas.alpha_composite(im, (round(ox + x), round(oy + y)))
    return canvas.resize((round(900 * scale), round(1100 * scale)), Image.LANCZOS)

if __name__ == '__main__':
    out = Image.new('RGBA', (1350, 550))
    for i, t in enumerate([(1, 1, 1), (2, 2, 2), (3, 3, 3)]):
        out.alpha_composite(render(*t), (i * 450, 0))
    out.save(sys.argv[1])
