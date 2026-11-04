"""Issue #22 bonus-passage portal: a sunken ring of pale ruin stones.

Run from the repository root:

    blender -b --factory-startup --python prototypes/sushi-loop/assets/expedition/v3/portal.py

Reuses the v2 ruin kit (decor-ruin-fragment round-03 materials, helpers, light
rig and 35° registered camera) so the ring matches the approved arches. The
centre is left open: the game draws the animated whirlpool under the stones.
Writes native/portal-ring/static-S.png (4x) and native/pieces.json.
"""
import json, math, random, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'v2'))
import ruins  # noqa: E402  (Kit, setup_capture, capture)

OUT = HERE / 'native'


def portal_ring(k):
    rng = random.Random(22)
    count, radius = 11, .4
    for i in range(count):
        a = i * math.tau / count + rng.uniform(-.05, .05)
        x, y = math.cos(a) * radius, math.sin(a) * radius
        h = rng.uniform(.13, .2) + (.05 if i in (2, 7) else 0)
        stone = k.wornstone('Ring stone ' + str(i), (x, y, h / 2), (.22, .17, h), rng.choice([k.stone, k.side, k.chip]),
                            top=[rng.uniform(-.02, .02) for _ in range(8)], cuts=(.16, .14, .18, .12), bevel=.012)
        stone.rotation_euler.z = a + math.pi / 2
        # A carved groove on every other stone, facing the whirlpool.
        if i % 2 == 0:
            k.block('Inner groove ' + str(i), (x * .8, y * .8, h * .6), (.03, .1, .04), k.recess, .006, (0, 0, a + math.pi / 2))
    for i in (1, 5, 8):
        a = i * math.tau / count
        k.moss_cap('Ring moss ' + str(i), math.cos(a) * radius, math.sin(a) * radius, .18, .16, .14, rng)
    for i in (3, 9):
        a = i * math.tau / count
        k.sprouts(math.cos(a) * (radius + .1), math.sin(a) * (radius + .1), .02, rng, 2)


def main():
    pid = 'portal-ring'
    out = OUT / pid; out.mkdir(parents=True, exist_ok=True)
    k = ruins.Kit(pid); portal_ring(k); frame_w = ruins.setup_capture(k, 1)
    ruins.bpy.ops.wm.save_as_mainfile(filepath=str(out / 'project.blend'), compress=True)
    ruins.capture(k, out, [('S', 0)])
    record = {'footprint': [1, 1], 'frame': [frame_w, 512], 'root': [frame_w / 2, 416], 'directions': ['S'], 'solidCells': []}
    (OUT / 'pieces.json').write_text(json.dumps({'style': 'decor-ruin-fragment round-03', 'nativeScale': ruins.NATIVE, 'pieces': {pid: record}}, indent=1) + '\n')


if __name__ == '__main__':
    main()
