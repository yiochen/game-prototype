"""Assemble published reef sprites at runtime pitch (256 px per cell at 2x) into one snapshot page.

    python3 inputs/assemble_snapshot.py SPRITES_DIR OUT.html

A 6x6 patch with a winding breach; outside the patch counts as open water, so outer corners round too.
Masks use the seabed bed bits (N=1, E=2, S=4, W=8; set = solid neighbour). Patterns follow the cell hash.
"""
import sys
from pathlib import Path

PATCH = ['RR..RR', 'RR.RRR', 'R..RRR', 'R.RRRR', 'R..RRR', 'RR..RR']
CELL, ROOT, FRAME, PAD = 256, (192, 832), (384, 1024), 160
sprites, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
solid = lambda x, y: 0 <= y < 6 and 0 <= x < 6 and PATCH[y][x] == 'R'
imgs = []
for y in range(6):
    for x in range(6):
        cx, cy = PAD + (x + .5) * CELL, PAD + (y + .5) * CELL
        if solid(x, y):
            mask = (solid(x, y - 1) and 1) | (solid(x + 1, y) and 2) | (solid(x, y + 1) and 4) | (solid(x - 1, y) and 8)
            pid = f'reef-{mask:02d}-{"abc"[(x * 7 + y * 13) % 3]}'
        else:
            pid = f'reef-rubble-{"ab"[(x + y) % 2]}'
        imgs.append((y, 0 if pid.startswith('reef-rubble') else 1, f'<img src="{sprites / pid / "static-S.png"}" style="left:{cx - ROOT[0]}px;top:{cy - ROOT[1]}px">'))
# Rubble first, then reef in row order, as the runtime draws them.
imgs.sort(key=lambda t: (t[1], t[0]))
W = H = 6 * CELL + 2 * PAD
out.write_text(f'''<!doctype html><meta charset="utf-8"><style>body{{margin:0}}#p{{position:relative;width:{W}px;height:{H}px;background:#2387c0;overflow:hidden}}
img{{position:absolute;width:{FRAME[0]}px;height:{FRAME[1]}px}}</style><div id="p">{''.join(i[2] for i in imgs)}</div>''')
print(W, H)
