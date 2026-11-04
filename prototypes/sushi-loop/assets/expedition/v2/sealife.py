"""Issue #21 sea-life pieces: ocean props that replace the restaurant crate and plank wreck.

Run from the repository root:

    blender -b --factory-startup --python prototypes/sushi-loop/assets/expedition/v2/sealife.py [-- id,id]

Uses the ruin kit (ruins.py, decor-ruin-fragment round-03 vocabulary): the same
material model, cobalt reef footing, light rig, 35° orthographic camera and
capture-only square footing. Edge pieces stand on a reef footing at a rock edge
and block their cell; floor pieces are small seabed scatter without footing.
"""
import importlib.util, json, math, random, sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ruins', HERE / 'ruins.py')
ruins = importlib.util.module_from_spec(spec); spec.loader.exec_module(ruins)
Kit, setup_capture, capture, NATIVE = ruins.Kit, ruins.setup_capture, ruins.capture, ruins.NATIVE
OUT = HERE / 'native' / 'sealife'


def ribbed(o, amp, freq, axis='y', lift=0.0):
    """Push vertices along their normals with a cosine rib pattern (shell flutes)."""
    for v in o.data.vertices:
        t = getattr(v.co, axis)
        weight = max(0.0, min(1.0, (v.co.z + lift) / max(.001, o.dimensions.z)))
        v.co += v.normal * amp * math.cos(t * freq) * (.35 + .65 * weight)
    o.data.update()


def cone(k, name, base, direction, length, radius, mat):
    bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=radius, radius2=0, depth=length, location=base + direction * length / 2)
    o = k.adopt(bpy.context.object, name, mat)
    o.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return o


def fibonacci(n, min_z=-.2):
    pts = []
    for i in range(n * 2):
        z = 1 - (i + .5) / n
        if z < min_z: break
        r = math.sqrt(max(0, 1 - z * z)); a = i * math.pi * (3 - math.sqrt(5))
        pts.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))
    return pts


def urchin(k, center, radius, rng, body, spine, spines=34):
    k.ellipsoid('Urchin test', center, (radius, radius, radius * .78), body, 16, 10)
    for d in fibonacci(spines, -.15):
        d = (d + Vector((rng.uniform(-.12, .12), rng.uniform(-.12, .12), rng.uniform(-.05, .1)))).normalized()
        cone(k, 'Urchin spine', Vector(center) + d * radius * .82, d, radius * rng.uniform(.95, 1.25), radius * .085, spine)


# ------------------------------------------------------------------ edge pieces (on reef footing)

def clam_giant(k):
    rng = random.Random(21)
    m = k.material
    shell, rim = m('Pale ridged clam shell', 'EDE2C8', .62, .03), m('Clam shell lip', 'D9C7AA', .7, .02)
    mantle, spots, edge = m('Teal clam mantle', '1C9BB8', .42, .04), m('Mantle glow spots', 'A8ECF5', .4, 0), m('Violet mantle rim', '6448A6', .5, .02)
    k.footing('Reef footing', 0, 0, .98, .96, .24, 7)
    k.sprouts(.38, .26, .23, rng, 2)
    for side in (-1, 1):
        v = k.ellipsoid('Clam valve', (side * .15, 0, .44), (.19, .42, .24), shell, 28, 14)
        ribbed(v, .03, 2 * math.pi * 3.5 / .42, 'y', .1)
        v.rotation_euler = (0, side * .38, 0)
        k.ellipsoid('Valve lip', (side * .24, 0, .58), (.05, .4, .05), rim, 20, 8).rotation_euler = (0, side * .5, 0)
    k.ellipsoid('Mantle rim', (0, 0, .6), (.17, .39, .06), edge, 28, 10)
    man = k.ellipsoid('Mantle', (0, 0, .64), (.14, .35, .06), mantle, 28, 10)
    ribbed(man, .018, 2 * math.pi * 5 / .35, 'y')
    for i in range(9):
        k.ellipsoid('Mantle spot', (rng.uniform(-.08, .08), -.3 + i * .075, .7), (.022, .022, .012), spots, 8, 6)
    k.moss_cap('Footing moss', -.32, -.3, .26, .13, .1, rng)


def urchin_cluster(k):
    rng = random.Random(22)
    m = k.material
    body, spine = m('Urchin test plum', '4A1D57', .6, .02), m('Urchin spines magenta', '8A3486', .5, .02)
    k.footing('Reef footing', 0, 0, .98, .96, .26, 8)
    k.sprouts(-.38, -.24, .25, rng, 2)
    for c, r in (((-.17, .1, .38), .17), ((.2, -.02, .36), .14), ((-.02, -.26, .33), .11), ((.24, .28, .34), .09)):
        urchin(k, c, r, rng, body, spine)
    k.moss_cap('Footing moss', .3, -.32, .27, .12, .1, rng)


def anemone(k):
    rng = random.Random(23)
    m = k.material
    column, disc = m('Anemone column coral orange', 'E2704A', .55, .03), m('Anemone oral disc', 'F7A27B', .5, .02)
    tentacle, tip, mouth = m('Anemone tentacles', 'FF8E62', .45, .02), m('Anemone tentacle tips', 'FFE3C4', .4, 0), m('Anemone mouth', 'B23D2B', .6, 0)
    k.footing('Reef footing', 0, 0, .98, .96, .26, 9)
    k.ellipsoid('Anemone column', (0, 0, .4), (.24, .24, .2), column, 24, 12)
    k.ellipsoid('Oral disc', (0, 0, .58), (.24, .24, .05), disc, 24, 8)
    k.ellipsoid('Mouth', (0, 0, .62), (.05, .07, .02), mouth, 12, 6)
    for ring, (count, radius, length, lean) in enumerate(((16, .22, .3, .95), (11, .13, .26, .55))):
        for i in range(count):
            a = i * math.tau / count + ring * .2 + rng.uniform(-.08, .08)
            base = Vector((math.cos(a) * radius, math.sin(a) * radius, .6))
            d = Vector((math.cos(a) * lean, math.sin(a) * lean, 1)).normalized()
            L = length * rng.uniform(.85, 1.1)
            mid = base + d * L / 2
            t = k.ellipsoid('Tentacle', tuple(mid), (.034, .034, L / 2), tentacle, 10, 6)
            t.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
            k.ellipsoid('Tentacle tip', tuple(base + d * L * .98), (.036, .036, .036), tip, 8, 6)
    k.sprouts(.38, .28, .25, rng, 2)


# ------------------------------------------------------------------ seabed scatter (no footing)

def shell_conch(k):
    m = k.material
    body, knob, lip = m('Conch shell cream', 'F0D3AE', .55, .03), m('Conch knobs', 'DDB48A', .6, .02), m('Conch pink lip', 'F2939A', .4, .01)
    k.ellipsoid('Conch body', (0, .02, .16), (.2, .3, .16), body, 24, 12).rotation_euler = (0, .25, 0)
    for i in range(5):
        t = i / 4
        k.ellipsoid('Spire whorl', (-.04 * t, .28 + t * .2, .16 + t * .03), (.14 * (1 - t * .7), .07, .12 * (1 - t * .6)), body, 16, 8)
    for i in range(6):
        a = -.6 + i * .32
        k.ellipsoid('Shoulder knob', (math.sin(a) * .2, .1 + math.cos(a) * .05, .28), (.04, .04, .05), knob, 8, 6)
    k.ellipsoid('Flared lip', (.12, -.08, .12), (.13, .26, .1), lip, 20, 10).rotation_euler = (0, .7, -.15)


def scallop(k, x, y, size, turn, shell, rib, ear):
    """Fan valve: a flat disc with raised ribs radiating from the hinge."""
    hinge = Vector((x, y, 0)) + Vector((0, .27, 0)).copy() * size
    k.ellipsoid('Scallop valve', (x, y, .01), (.3 * size, .27 * size, .05 * size), shell, 40, 10)
    for i in range(9):
        a = math.radians(-64 + i * 16) + turn
        d = Vector((math.sin(a), -math.cos(a), 0))
        L = .5 * size * (1 - abs(i - 4) * .05)
        c = hinge + d * L * .5
        o = k.ellipsoid('Scallop rib', (c.x, c.y, .045 * size), (.035 * size, L * .5, .035 * size), rib, 10, 6)
        o.rotation_euler = (0, 0, a)
    for side in (-1, 1):
        k.block('Scallop ear', (hinge.x + side * .08 * size, hinge.y, .03 * size), (.13 * size, .08 * size, .05 * size), ear, .015, (0, 0, side * .3))


def shell_scallop(k):
    m = k.material
    shell, rib, ear = m('Scallop shell coral pink', 'EE9C86', .55, .03), m('Scallop ribs', 'F7B9A1', .5, .02), m('Scallop ears', 'D9826E', .6, .02)
    scallop(k, -.04, -.04, 1, 0, shell, rib, ear)
    scallop(k, .3, .3, .5, 0, shell, rib, ear)


def urchin_small(k):
    rng = random.Random(24)
    m = k.material
    urchin(k, (0, 0, .14), .15, rng, m('Urchin test plum', '4A1D57', .6, .02), m('Urchin spines magenta', '8A3486', .5, .02), 30)


PIECES = {
    'clam-giant': (clam_giant, 'sealife-edge'), 'urchin-cluster': (urchin_cluster, 'sealife-edge'), 'anemone': (anemone, 'sealife-edge'),
    'shell-conch': (shell_conch, 'sealife-floor'), 'shell-scallop': (shell_scallop, 'sealife-floor'), 'urchin-small': (urchin_small, 'sealife-floor'),
}


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = set(args[0].split(',')) if args else None
    manifest = OUT / 'pieces.json'
    records = json.loads(manifest.read_text())['pieces'] if manifest.exists() else {}
    directions = [('N', 180), ('E', 90), ('S', 0), ('W', -90)]
    for pid, (fn, family) in PIECES.items():
        if only and pid not in only:
            continue
        out = OUT / pid; out.mkdir(parents=True, exist_ok=True)
        for direction in directions:
            k = Kit(pid); fn(k); frame_w = setup_capture(k, 1)
            if direction == directions[0]:
                bpy.ops.wm.save_as_mainfile(filepath=str(out / 'project.blend'), compress=True)
            capture(k, out, [direction])
        records[pid] = {'footprint': [1, 1], 'frame': [frame_w, 512], 'root': [frame_w / 2, 416], 'directions': [d for d, _ in directions],
                        'family': family, 'solidCells': [[0, 0]] if family == 'sealife-edge' else []}
    OUT.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({'style': 'decor-ruin-fragment round-03 kit', 'nativeScale': NATIVE, 'pieces': records}, indent=1) + '\n')


if __name__ == '__main__':
    main()
