"""Issue #76 breakable reef blocks and rubble, built with the approved boulder-underwater capture recipe.

Run from the repository root:

    blender -b --factory-startup --python prototypes/sushi-loop/assets/expedition/v2/reef.py [-- id,id]

Like rocks.py, the production recipe (boulder-underwater round-04) is imported unchanged for its stone
material, registered 35 degree camera, nine-light rig and capture-only square footing. Only the geometry is new.

Brittle reef is a connected mass, so each cell is drawn by its neighbour mask, with the same bits as the
seabed beds (N=1, E=2, S=4, W=8; a set bit means the neighbour is solid: intact reef or rock). Its ground
footprint is the #24 collision shape: open faces inset by `INSET`, faces against solid flat to the cell
edge, and every exposed corner (both neighbours open) rounded by `CORNER`. So when the parrotfish breaks a
cell, its neighbours switch to masks whose exposed corners are round and the breach looks as wide as it
flies (user, 2026-11-13).

Each cell is two or three pale limestone slabs with narrow grooves between them (patterns a, b, c), so repeats
don't tile visibly; cell edges against reef meet flush, so the bevels draw the only seam. Nothing grows on top: coral and kelp grow from
the seabed between rocks (#21 art direction). Rubble (a, b) is the low scatter left on a broken cell.
Native captures are 4x, south only (terrain is drawn by mask, never rotated); publish.mjs downsamples 2x.
"""
import bpy, importlib.util, json, math, random, sys
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
RECIPE = HERE.parents[1] / 'production/source/blender/refinement/boulder-underwater/source/round-04-recipe.py'
spec = importlib.util.spec_from_file_location('boulder_recipe', RECIPE)
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)  # `__main__` guard: defines functions only.
OUT = HERE / 'native' / 'reef'

# Collision contract (godot/content/expedition.json): rock_inset and rock_corner_radius, in cells.
INSET, CORNER = .08, .35
HEIGHT = .32        # slab height in cells, before per-slab variation (low: a reef bed to break through, not pillars)
BEVEL = .045        # chamfer round each slab's top
GROOVE = .012       # half-gap between slabs inside a cell; cell edges against reef have none, so the mass reads as one
# Limestone: (top, side, groove) as hex; warmer and yellower than the ivory ruins.
TOP, SIDE, DEEP = 'E8DCBC', 'CBB386', 'A08A60'
N, E, S, W = 1, 2, 4, 8

# Slab layouts in unit-cell coordinates (x0, y0, x1, y1), before the footprint is applied.
PATTERNS = {
    'a': [(-.5, -.5, .06, .5), (.06, -.5, .5, .5)],
    'b': [(-.5, -.5, .5, -.02), (-.5, -.02, .5, .5)],
    'c': [(-.5, -.5, -.04, .14), (-.04, -.5, .5, .14), (-.5, .14, .5, .5)],
}


def outline(x0, y0, x1, y1, radii, seg=4):
    """Rounded rectangle, counter-clockwise from the south-west; radii per corner (sw, se, ne, nw)."""
    pts = []
    for (cx, cy, sx, sy, a0), r in zip([(x0, y0, 1, 1, math.pi), (x1, y0, -1, 1, 1.5 * math.pi), (x1, y1, -1, -1, 0), (x0, y1, 1, -1, .5 * math.pi)], radii):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        if r < 1e-4:
            pts.append((cx, cy)); continue
        ox, oy = cx + sx * r, cy + sy * r
        for k in range(seg + 1):
            a = a0 + k * (math.pi / 2) / seg
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return pts


def slab(col, root, name, box, radii, height, rng, mats):
    """A limestone slab: footprint outline, straight sides, a chamfered and slightly uneven top."""
    x0, y0, x1, y1 = box
    base = outline(x0, y0, x1, y1, radii)
    b = min(BEVEL, (x1 - x0) / 3, (y1 - y0) / 3)
    top = outline(x0 + b, y0 + b, x1 - b, y1 - b, [max(0, r - b) for r in radii])
    n, m = len(base), len(top)
    # Resample the top ring to the base ring's vertex count so quads join (both start at the same corner).
    top = [top[round(i * m / n) % m] for i in range(n)]
    tilt = (rng.uniform(-.03, .03), rng.uniform(-.03, .03))
    lift = lambda x, y: height + tilt[0] * x + tilt[1] * y
    verts = [(x, y, 0) for x, y in base] + [(x, y, lift(x, y) - b) for x, y in base] + [(x, y, lift(x, y) + rng.uniform(-.008, .008)) for x, y in top]
    faces = [tuple(reversed(range(n)))]
    mids = [2]
    for ring in (0, 1):
        for i in range(n):
            j = (i + 1) % n
            faces.append((ring * n + i, ring * n + j, (ring + 1) * n + j, (ring + 1) * n + i)); mids.append(1)
    faces.append(tuple(range(2 * n, 3 * n))); mids.append(0)
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me); col.objects.link(ob); ob.parent = root
    for mat in mats: me.materials.append(mat)
    for p, mi in zip(me.polygons, mids): p.material_index = mi; p.use_smooth = False
    # The chamfer ring shares the side material but faces up: give it the top material.
    for p in me.polygons:
        if p.material_index == 1 and p.normal.z > .45: p.material_index = 0
    return ob


def cell(col, root, mask, pattern, seed, mats):
    rng = random.Random(seed)
    fx0 = -.5 + (0 if mask & W else INSET); fx1 = .5 - (0 if mask & E else INSET)
    fy0 = -.5 + (0 if mask & S else INSET); fy1 = .5 - (0 if mask & N else INSET)
    # Exposed corners (both neighbours open) take the collision radius.
    corner = {'sw': not mask & S and not mask & W, 'se': not mask & S and not mask & E, 'ne': not mask & N and not mask & E, 'nw': not mask & N and not mask & W}
    for i, (sx0, sy0, sx1, sy1) in enumerate(PATTERNS[pattern]):
        # Slab box inside the footprint, with grooves on interior edges only.
        bx0 = fx0 if sx0 <= -.5 else sx0 + GROOVE; bx1 = fx1 if sx1 >= .5 else sx1 - GROOVE
        by0 = fy0 if sy0 <= -.5 else sy0 + GROOVE; by1 = fy1 if sy1 >= .5 else sy1 - GROOVE
        small = .05
        radii = [CORNER if corner['sw'] and sx0 <= -.5 and sy0 <= -.5 else small, CORNER if corner['se'] and sx1 >= .5 and sy0 <= -.5 else small,
                 CORNER if corner['ne'] and sx1 >= .5 and sy1 >= .5 else small, CORNER if corner['nw'] and sx0 <= -.5 and sy1 >= .5 else small]
        slab(col, root, f'Limestone slab {i}', (bx0, by0, bx1, by1), radii, HEIGHT * rng.uniform(.88, 1.1), rng, mats)


def rubble(col, root, seed, mats):
    """Low fragments scattered over a broken cell's seabed; none taller than a hull's keel."""
    rng = random.Random(seed)
    # Jittered 3x3 grid, a few cells skipped, so fragments spread over the whole cell.
    spots = [(gx * .27 + rng.uniform(-.08, .08), gy * .27 + rng.uniform(-.08, .08)) for gx in (-1, 0, 1) for gy in (-1, 0, 1)]
    for i, (cx, cy) in enumerate(rng.sample(spots, rng.randint(6, 8))):
        w, d, h = rng.uniform(.05, .11), rng.uniform(.04, .09), rng.uniform(.03, .07)
        a = rng.uniform(0, math.pi)
        corners = [(-w, -d), (w, -d * rng.uniform(.6, 1)), (w * rng.uniform(.6, 1), d), (-w * rng.uniform(.5, 1), d)]
        base = [(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)) for x, y in corners]
        tip = (sum(p[0] for p in base) / 4 + rng.uniform(-.02, .02), sum(p[1] for p in base) / 4 + rng.uniform(-.02, .02))
        top = [(tip[0] + (x - tip[0]) * .55, tip[1] + (y - tip[1]) * .55) for x, y in base]
        verts = [(x, y, 0) for x, y in base] + [(x, y, h * rng.uniform(.8, 1.1)) for x, y in top]
        faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        me = bpy.data.meshes.new(f'Fragment {i}'); me.from_pydata(verts, [], faces); me.update()
        ob = bpy.data.objects.new(f'Fragment {i}', me); col.objects.link(ob); ob.parent = root
        for mat in mats: me.materials.append(mat)
        for p in me.polygons: p.material_index = 0 if p.normal.z > .45 else 1; p.use_smooth = False


def scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.name = 'Breakable Reef Native'
    col = bpy.data.collections.new('Breakable reef'); sc.collection.children.link(col)
    root = bpy.data.objects.new('Breakable reef ground root', None); col.objects.link(root)
    # The recipe's height ramp is calibrated to 2.3-cell boulders; these slabs sit low on it, so lift the gain.
    mats = [R.material('Limestone top', TOP, 1.18), R.material('Limestone side', SIDE, 1.16), R.material('Limestone underside', DEEP, 1.1)]
    cam = bpy.data.objects.new('Registered 35 degree camera', bpy.data.cameras.new('Registered 35 degree camera'))
    sc.collection.objects.link(cam); sc.camera = cam
    R.configure(sc)
    roles = [('Overhead', (0, 0, 5), 185, 4.5, (1, .95, .88))]
    for i in range(8):
        a = i * math.tau / 8; roles.append(('Symmetric fill ' + str(i), (3.5 * math.cos(a), 3.5 * math.sin(a), 2.3), 34, 5, (.90, .96, 1)))
    for name, pos, power, size, color in roles:
        ld = bpy.data.lights.new(name, 'AREA'); ob = bpy.data.objects.new(name, ld); sc.collection.objects.link(ob)
        ob.location = pos; ob.rotation_euler = (Vector((0, 0, 1)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
        ld.energy = power; ld.shape = 'DISK'; ld.size = size; ld.color = color
    sc.world = bpy.data.worlds.new('Balanced blue stone studio'); sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value = (.72, .80, 1, 1); bg.inputs['Strength'].default_value = .12
    return sc, col, root, mats


def capture(sc, col, out):
    out.mkdir(parents=True, exist_ok=True)
    with R.square_footing(col):
        sc.render.filepath = str(out / 'static-S.png'); bpy.ops.render.render(write_still=True)


def clear(col, root):
    for ob in list(col.objects):
        if ob is not root: me = ob.data; bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(args[0].split(',')) if args else None
sc, col, root, mats = scene()
pieces = {}
jobs = [(f'reef-{mask:02d}-{p}', ('cell', mask, p)) for mask in range(16) for p in PATTERNS] + [(f'reef-rubble-{p}', ('rubble', None, p)) for p in 'ab']
for pid, (kind, mask, p) in jobs:
    if only and pid not in only: continue
    clear(col, root)
    seed = sum(map(ord, pid))
    if kind == 'cell': cell(col, root, mask, p, seed, mats)
    else: rubble(col, root, seed, mats)
    capture(sc, col, OUT / pid)
    pieces[pid] = {'kind': kind, 'mask': mask, 'pattern': p}
    if pid == 'reef-05-a': bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'reef-05-a' / 'project.blend'), compress=True)
(OUT / 'pieces.json').write_text(json.dumps({'recipe': str(RECIPE.relative_to(HERE.parents[2])), 'frame': [192, 512], 'root': [96, 416], 'nativeScale': 4,
                                            'maskBits': {'N': N, 'E': E, 'S': S, 'W': W}, 'collision': {'inset': INSET, 'cornerRadius': CORNER}, 'pieces': pieces}, indent=1) + '\n')
