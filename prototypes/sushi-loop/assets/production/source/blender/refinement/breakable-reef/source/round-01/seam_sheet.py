"""Seam-stress sheet: place independently captured pieces at runtime pitch (north row first, west to east) on seabed blue.

    python3 seam_sheet.py FRAMES_DIR OUT.png [native|sprites]

FRAMES_DIR holds <id>.png (native 768x2048) or <id>/static-S.png (sprites 384x1024). '.' is open water.
"""
import sys, subprocess
from pathlib import Path
LAYOUT = [
    'reef-02-a reef-08-b . reef-10-c reef-10-a reef-10-b . reef-04-b . reef-06-b reef-14-c reef-12-a',
    '. . . . . . . reef-01-c . reef-07-a reef-15-b reef-13-c',
    'reef-15-a reef-15-b reef-15-c . reef-05-a . . . . reef-03-c reef-11-a reef-09-b',
    'reef-15-c reef-15-a reef-15-b . reef-05-c . reef-00-b . reef-12-c . .',
    'reef-15-b reef-15-c reef-15-a . reef-01-b . . . reef-03-a reef-09-c . .',
]
d, out, kind = Path(sys.argv[1]), sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else 'native')
s = 1 if kind == 'native' else .5
P, FW, FH = int(512 * s), int(768 * s), int(2048 * s)
rows = [r.split() for r in LAYOUT]; cols = max(map(len, rows))
W, H = (cols - 1) * P + FW, (len(rows) - 1) * P + FH
ins, f, prev, k = [], [f'color=c=0x2387c0:s={W}x{H},format=rgba[b0]'], 'b0', 0
for y, r in enumerate(rows):
    for x, pid in enumerate(r):
        if pid == '.': continue
        ins += ['-i', str(d / f'{pid}.png' if kind == 'native' else d / pid / 'static-S.png')]
        f.append(f'[{prev}][{k}:v]overlay={x * P}:{y * P}[b{k + 1}]'); prev = f'b{k + 1}'; k += 1
top, left = int(1150 * s), int(100 * s)
f.append(f'[{prev}]crop={W - 2 * left}:{H - top - int(100 * s)}:{left}:{top}[o]')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ';'.join(f), '-map', '[o]', '-frames:v', '1', out], check=True)
