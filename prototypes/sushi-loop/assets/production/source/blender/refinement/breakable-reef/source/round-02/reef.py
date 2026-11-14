"""Issue #76 breakable reef blocks and rubble, built with the approved boulder-underwater capture recipe.

Run from the repository root:

    blender -b --factory-startup --python prototypes/sushi-loop/assets/expedition/v2/reef.py [-- id,id] [--out DIR]

Like rocks.py, the production recipe (boulder-underwater round-04) is imported unchanged for its registered
35 degree camera (configure), nine-light rig values and capture-only square footing. Only the geometry and the
limestone surface are new.

Brittle reef is a connected mass, so each cell is drawn by its neighbour mask, with the same bits as the
seabed beds (N=1, E=2, S=4, W=8; a set bit means the neighbour is solid: intact reef or rock). Its ground
footprint is the #24 collision shape: open faces inset by `INSET`, faces against solid flat to the cell
edge, and every exposed corner (both neighbours open) rounded by `CORNER`. So when the parrotfish breaks a
cell, its neighbours switch to masks whose exposed corners are round and the breach looks as wide as it
flies (user, 2026-11-13).

Each cell is two or three pale limestone slabs with narrow grooves between them (patterns a, b, c), so repeats
don't tile visibly; cell edges against reef meet flush, so the bevels draw the only seam. A low hidden core
under the slabs fills the groove floors so no seabed shows inside a cell. Nothing grows on top: coral and kelp
grow from the seabed between rocks (#21 art direction). Rubble (a, b) is the low scatter left on a broken cell.

Limestone surface (breakable-reef refinement round 01, surface only; shape and height approved 2026-11-13):
peach-cream tops with per-slab tone, a warm chamfer highlight, deeper tan fronts with soft strata driven by
world height, hairline cracks on one slab per cell, sparse pores and small chips on groove-side top edges.
Every surface detail is a function of pre-footing world position (the `rest` attribute) and of per-slab values
seeded by pattern and slab index, never by the mask; the only field that crosses slabs repeats once per cell,
so any mask joins any other without a tone step. Cracks, pores and chips stay inside their slab, away from
cell edges. Native captures are 4x, south only (terrain is drawn by mask, never rotated); publish.mjs
downsamples 2x.
"""
import bpy, importlib.util, json, math, random, sys
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
RECIPE_REL = 'production/source/blender/refinement/boulder-underwater/source/round-04-recipe.py'


def find_recipe():
    for p in [HERE, *HERE.parents]:
        if (p / RECIPE_REL).exists(): return p / RECIPE_REL
        if (p / 'prototypes/sushi-loop/assets' / RECIPE_REL).exists(): return p / 'prototypes/sushi-loop/assets' / RECIPE_REL
    raise FileNotFoundError(RECIPE_REL)


RECIPE = find_recipe()
ASSETS = RECIPE.parents[len(Path(RECIPE_REL).parts) - 1]
spec = importlib.util.spec_from_file_location('boulder_recipe', RECIPE)
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)  # `__main__` guard: defines functions only.

# Collision contract (godot/content/expedition.json): rock_inset and rock_corner_radius, in cells.
INSET, CORNER = .08, .35
HEIGHT = .32        # slab height in cells, before per-slab variation (low: a reef bed to break through, not pillars)
BEVEL = .045        # chamfer round each slab's top
GROOVE = .012       # half-gap between slabs inside a cell; cell edges against reef have none, so the mass reads as one
SMALL = .05         # the backup recipe's radius for non-exposed corners (kept only to replay its random sequence)
TIGHT = .015        # corner radius where a slab is not on an exposed corner: grooves and seams read as thin lines
CHIP = .028         # deepest chip bite into the top, measured inward from the chamfer's top edge (locked limit .03)
CORE = .03, .58     # hidden groove-floor core: inset from the footprint, height as a share of HEIGHT
# Limestone, sRGB hex: top, chamfer highlight, front, groove core.
TOP, RIM, SIDE, DEEP = 'F4D19C', 'FDDDAA', 'C38D55', 'A07448'
N, E, S, W = 1, 2, 4, 8

# Slab layouts in unit-cell coordinates (x0, y0, x1, y1), before the footprint is applied.
PATTERNS = {
    'a': [(-.5, -.5, .06, .5), (.06, -.5, .5, .5)],
    'b': [(-.5, -.5, .5, -.02), (-.5, -.02, .5, .5)],
    'c': [(-.5, -.5, -.04, .14), (-.04, -.5, .5, .14), (-.5, .14, .5, .5)],
}
# Which slab of each pattern carries the cell's cracks (a half, a half and a third of slabs; two cracks each).
CRACKED = {'a': 1, 'b': 1, 'c': 2}


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


def dense_outline(x0, y0, x1, y1, radii, cuts, seg=4, step=.06):
    """The same rounded rectangle as `outline` (identical corner arcs), with straight edges subdivided collinearly
    so chips can bite the top edge. Returns (x, y, outward normal x, y, edge) per vertex; edge is 's', 'e', 'n',
    'w' on straight edges and (corner x, y, sign x, y, radius) on arcs. `cuts` holds extra positions per edge."""
    corners = [(x0, y0, 1, 1, math.pi), (x1, y0, -1, 1, 1.5 * math.pi), (x1, y1, -1, -1, 0), (x0, y1, 1, -1, .5 * math.pi)]
    arcs = []
    for (cx, cy, sx, sy, a0), r in zip(corners, radii):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        ox, oy = cx + sx * r, cy + sy * r
        arcs.append([(ox + r * math.cos(a0 + k * math.pi / 2 / seg), oy + r * math.sin(a0 + k * math.pi / 2 / seg),
                      math.cos(a0 + k * math.pi / 2 / seg), math.sin(a0 + k * math.pi / 2 / seg), (cx, cy, sx, sy, r)) for k in range(seg + 1)])
    pts = []
    for i, edge in enumerate('senw'):
        pts += arcs[i]
        (ax, ay, *_), (bx, by, *_) = arcs[i][-1], arcs[(i + 1) % 4][0]
        nx, ny = {'s': (0, -1), 'e': (1, 0), 'n': (0, 1), 'w': (-1, 0)}[edge]
        length = math.hypot(bx - ax, by - ay)
        ts = {k / max(1, round(length / step)) for k in range(1, max(1, round(length / step)))}
        for c in cuts.get(edge, []):
            t = ((c - ax) / (bx - ax)) if edge in 'sn' else ((c - ay) / (by - ay))
            if .001 < t < .999: ts.add(t)
        for t in sorted(ts):
            pts.append((ax + (bx - ax) * t, ay + (by - ay) * t, nx, ny, edge))
    return pts


def slab_extras(pattern, index):
    """Per-slab look, seeded by pattern and slab index only (never the mask), in the slab's nominal box: the
    pattern box clipped to the smallest footprint any mask gives it, so the same marks land in every mask.
    Chip candidates are listed here; `slab` keeps only those the cell's mask allows (never on a flush seam)."""
    sx0, sy0, sx1, sy1 = PATTERNS[pattern][index]
    rng = random.Random(f'reef-surface-{pattern}-{index}-r2')
    lo = (max(sx0 + GROOVE, -.5 + INSET), max(sy0 + GROOVE, -.5 + INSET))
    hi = (min(sx1 - GROOVE, .5 - INSET), min(sy1 - GROOVE, .5 - INSET))
    ex = {'tone': rng.random(), 'seed': rng.uniform(0, 50), 'lo': lo, 'hi': hi, 'chips': [], 'cracks': []}
    # Corner chips: the slab's four corners in a fixed random order; the first one the mask allows is chipped.
    corners = ['sw', 'se', 'ne', 'nw']; rng.shuffle(corners)
    ex['chips'] += [('corner', k, rng.uniform(.024, CHIP), rng.uniform(.006, .014), rng.uniform(.022, .034)) for k in corners]
    # One nick on a groove edge (an edge that is never a cell edge), away from its corners.
    grooves = [e for e, inner in (('w', sx0 > -.5), ('e', sx1 < .5), ('s', sy0 > -.5), ('n', sy1 < .5)) if inner]
    e = rng.choice(grooves)
    a, b = (lo[1], hi[1]) if e in 'we' else (lo[0], hi[0])
    w = rng.uniform(.04, .055); margin = .065 + w + .03
    if b - a > 2 * margin: ex['chips'].append(('edge', e, rng.uniform(a + margin, b - margin), w, rng.uniform(.018, CHIP)))
    if CRACKED[pattern] == index:
        m = .06
        cx0, cy0, cx1, cy1 = lo[0] + m, lo[1] + m, hi[0] - m, hi[1] - m
        for branch in (True, False):
            for _ in range(500):
                # Steep cracks: the 35 degree view squashes the depth axis, so near-horizontal hairlines thin out.
                th = math.radians(rng.uniform(40, 140)); d = (math.cos(th), math.sin(th))
                c = (rng.uniform(cx0, cx1), rng.uniform(cy0, cy1)); L = rng.uniform(.09, .2) if branch else rng.uniform(.06, .12)
                ends = [(c[0] + s * L * d[0], c[1] + s * L * d[1]) for s in (-1, 1)]
                u = rng.uniform(-.35, .35) * L; p = (c[0] + u * d[0], c[1] + u * d[1])
                bt = th + rng.choice((-1, 1)) * rng.uniform(.6, 1.0); bd = (math.cos(bt), math.sin(bt)); bl = rng.uniform(.05, .09) if branch else 0
                ends.append((p[0] + bl * bd[0], p[1] + bl * bd[1]))
                far = all(math.hypot(c[0] - k['c'][0], c[1] - k['c'][1]) > .14 for k in ex['cracks'])
                if far and all(cx0 <= x <= cx1 and cy0 <= y <= cy1 for x, y in ends):
                    ex['cracks'].append({'c': c, 'd': d, 'L': L, 'p': p, 'bd': bd, 'bl': bl}); break
    return ex


def slab(col, root, name, box, radii, height, rng, mats, ex, sides, old_radii):
    """A limestone slab: footprint outline, straight sides, a chamfered planar top with small chips on its groove side.
    `sides` gives each edge's kind ('groove', 'open' or 'flush' against a solid neighbour)."""
    x0, y0, x1, y1 = box
    b = min(BEVEL, (x1 - x0) / 3, (y1 - y0) / 3)
    tilt = (rng.uniform(-.03, .03), rng.uniform(-.03, .03))
    # The approved heights of later slabs come from this generator: draw the backup recipe's per-vertex top jitter
    # so the sequence is unchanged, but keep the top planar (the jitter drew faint triangulation lines across tops).
    for _ in outline(x0, y0, x1, y1, old_radii): rng.uniform(-.008, .008)
    # Chips. A corner chip breaks off one top corner whose two edges are groove or open, at least one a groove (never a
    # flush seam, never an exposed rounded corner): the top loses a triangle `w` deep along each edge and the corner
    # point drops `dz` and moves `d` inward, leaving lit/shaded broken facets. A nick is a shallow V on a groove edge.
    sgn = {'sw': (1, 1), 'se': (-1, 1), 'ne': (-1, -1), 'nw': (1, -1)}
    pos = {'sw': (x0, y0), 'se': (x1, y0), 'ne': (x1, y1), 'nw': (x0, y1)}
    corner_chip, nicks, cuts = None, [], {}
    for spec in ex['chips']:
        if spec[0] == 'corner' and corner_chip is None:
            k, w, d, dz = spec[1:]
            kinds = [sides[e] for e in k]
            if 'flush' in kinds or 'groove' not in kinds: continue
            (px, py), (sx, sy) = pos[k], sgn[k]
            corner_chip = (k, px + sx * b, py + sy * b, sx, sy, w, d, dz)
            cuts.setdefault(k[0], []).append(px + sx * (b + w)); cuts.setdefault(k[1], []).append(py + sy * (b + w))
        elif spec[0] == 'edge':
            e, c, w, d = spec[1:]
            if sides[e] != 'groove': continue
            px, py = (c, y1 if e == 'n' else y0) if e in 'sn' else (x1 if e == 'e' else x0, c)
            nicks.append((px, py, w, d)); cuts.setdefault(e, []).extend([c - w, c, c + w])
    ex['placedChips'] = {'corner': corner_chip and {'corner': corner_chip[0], 'w': corner_chip[5], 'd': corner_chip[6], 'dz': corner_chip[7]},
                         'nicks': [{'w': w, 'd': d} for *_, w, d in nicks]}
    ring = dense_outline(x0, y0, x1, y1, radii, cuts)
    lift = lambda x, y: height + tilt[0] * x + tilt[1] * y

    def nick(x, y):
        return max([d * max(0, 1 - math.hypot(x - px, y - py) / w) for px, py, w, d in nicks] + [0])
    n = len(ring)
    top, chipped = [], []
    for x, y, nx, ny, e in ring:
        # Inset by the chamfer, clamped to the inset rectangle (a corner tighter than the chamfer becomes a point).
        tx, ty = min(max(x - nx * b, x0 + b), x1 - b), min(max(y - ny * b, y0 + b), y1 - b)
        k = nick(x, y); tx, ty = tx - nx * k, ty - ny * k
        z, inside = lift(tx, ty), False
        if corner_chip:
            _, cx, cy, sx, sy, w, d, dz = corner_chip
            if (tx - cx) * sx < w - 1e-6 and (ty - cy) * sy < w - 1e-6:
                inside = True; tx, ty = cx + sx * d, cy + sy * d; z = lift(tx, ty) - dz
        top.append((tx, ty, z)); chipped.append(inside)
    verts = [(x, y, 0) for x, y, *_ in ring] + [(x, y, lift(x, y) - b) for x, y, *_ in ring] + top
    # Coincident top points (a tight corner's point, the chip's broken corner) share one vertex, so the planar top
    # polygon has no duplicate corners to mis-triangulate and the chamfer there closes with triangles.
    tid = []
    for i, t in enumerate(top):
        tid.append(tid[-1] if i and math.dist(t, top[i - 1]) < 1e-7 else 2 * n + i)
    if len(tid) > 1 and math.dist(top[-1], top[0]) < 1e-7:
        last = tid[-1]; tid = [tid[0] if t == last else t for t in tid]
    chip_v = next((tid[i] for i in range(n) if chipped[i]), None)

    def face(*idx):
        out = [v for k, v in enumerate(idx) if v != idx[k - 1]]
        return tuple(out) if len(out) >= 3 else None
    faces, mids, smooth = [tuple(reversed(range(n)))], [3], [False]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i)); mids.append(2); smooth.append(True)
        q = (n + i, n + j, tid[j], tid[i])
        if max(nick(*ring[i][:2]), nick(*ring[j][:2])) > 1e-9 or chip_v in (tid[i], tid[j]):
            for f in (face(*q[:3]), face(q[0], q[2], q[3])):   # chipped facets: explicit planar triangles
                if f: faces.append(f); mids.append(1); smooth.append(False)
        elif face(*q):
            faces.append(face(*q)); mids.append(1); smooth.append(True)
    ring_top = [t for k, t in enumerate(tid) if t != tid[k - 1]] or tid[:1]
    if chip_v is not None:
        # The broken corner leaves the top polygon; one facet spans the break between its neighbours on the top.
        at = ring_top.index(chip_v)
        faces.append((ring_top[at - 1], chip_v, ring_top[(at + 1) % len(ring_top)])); mids.append(1); smooth.append(False)
        ring_top = [t for t in ring_top if t != chip_v]
    faces.append(tuple(ring_top)); mids.append(0); smooth.append(False)
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me); col.objects.link(ob); ob.parent = root
    for mat in mats: me.materials.append(mat)
    for p, mi in zip(me.polygons, mids): p.material_index = mi; p.use_smooth = True
    # Exact per-corner normals: the outline's own outward normal on sides (flat on straight runs, turning only round
    # the corner arcs), a 45 degree normal on the chamfer only round its arcs (straight chamfer runs keep their true,
    # tilted face normal: a mismatch there drew shadow speckle), face normals on tops, bottoms and chips.
    side_n = [Vector((nx, ny, 0)) for _, _, nx, ny, _ in ring]
    rim_n = [Vector((nx, ny, 1)).normalized() for _, _, nx, ny, _ in ring]
    loops = [None] * len(me.loops)
    for p, sm in zip(me.polygons, smooth):
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            if sm and p.material_index == 2: loops[li] = side_n[vi % n]
            elif sm and p.material_index == 1 and isinstance(ring[vi % n][4], tuple): loops[li] = rim_n[vi % n]   # round the arcs
            else: loops[li] = p.normal.copy()
    me.normals_split_custom_set(loops)
    ex['top_h'] = lift((x0 + x1) / 2, (y0 + y1) / 2) - b
    look(ob, ex)
    return ob


def look(ob, ex):
    """Per-slab surface values the shaders read as object attributes."""
    ob['tone'] = ex['tone']; ob['seed'] = ex['seed']
    ob['box_lo'] = (*ex['lo'], 0.0); ob['box_hi'] = (*ex['hi'], 0.0)
    ob['top_h'] = ex.get('top_h', 1.0)
    cracks = ex.get('cracks', [])
    for i in range(2):
        k = cracks[i] if i < len(cracks) else None
        if k:
            ob[f'crack{i}_c'] = (k['c'][0], k['c'][1], k['L']); ob[f'crack{i}_d'] = (k['d'][0], k['d'][1], 1.0)
            ob[f'branch{i}_p'] = (k['p'][0], k['p'][1], k['bl']); ob[f'branch{i}_d'] = (k['bd'][0], k['bd'][1], 1.0 if k['bl'] else 0.0)
        else:
            for key in ('crack{}_c', 'crack{}_d', 'branch{}_p', 'branch{}_d'): ob[key.format(i)] = (0.0, 0.0, 0.0)


def core(col, root, fx, open_, radii, mats):
    """Hidden low core under the slabs: inset from open faces, flush to faces against solid (so the slab corners that meet
    at a cell edge close over it), so groove floors read as warm shadow, never seabed."""
    x0, y0, x1, y1 = (fx[0] + CORE[0] * open_[0], fx[1] + CORE[0] * open_[1], fx[2] - CORE[0] * open_[2], fx[3] - CORE[0] * open_[3])
    base = outline(x0, y0, x1, y1, [max(0, r - CORE[0]) for r in radii])
    n, h = len(base), HEIGHT * CORE[1]
    verts = [(x, y, 0) for x, y in base] + [(x, y, h) for x, y in base]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    me = bpy.data.meshes.new('Groove core'); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new('Groove core', me); col.objects.link(ob); ob.parent = root
    for mat in mats: me.materials.append(mat)
    for p in me.polygons: p.material_index = 3; p.use_smooth = False
    look(ob, {'tone': .5, 'seed': 0, 'lo': (0, 0), 'hi': (0, 0)})


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
        exposed = [corner['sw'] and sx0 <= -.5 and sy0 <= -.5, corner['se'] and sx1 >= .5 and sy0 <= -.5,
                   corner['ne'] and sx1 >= .5 and sy1 >= .5, corner['nw'] and sx0 <= -.5 and sy1 >= .5]
        radii = [CORNER if x else TIGHT for x in exposed]
        old = [CORNER if x else SMALL for x in exposed]
        edge = lambda inner, bit: 'groove' if inner else ('flush' if mask & bit else 'open')
        sides = {'s': edge(sy0 > -.5, S), 'e': edge(sx1 < .5, E), 'n': edge(sy1 < .5, N), 'w': edge(sx0 > -.5, W)}
        slab(col, root, f'Limestone slab {i}', (bx0, by0, bx1, by1), radii, HEIGHT * rng.uniform(.88, 1.1), rng, mats, slab_extras(pattern, i), sides, old)
    core(col, root, (fx0, fy0, fx1, fy1), (not mask & W, not mask & S, not mask & E, not mask & N), [CORNER if corner[k] else 0 for k in ('sw', 'se', 'ne', 'nw')], mats)


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
        for p in me.polygons: p.material_index = 0 if p.normal.z > .45 else 2; p.use_smooth = False
        look(ob, {'tone': (i * .37) % 1, 'seed': i * 7.0, 'lo': (0, 0), 'hi': (0, 0)})


# ---------------------------------------------------------------------------------------------------------------
# Limestone shader: a local copy of the production material pattern (Principled, rough, low specular, a modest
# emission fill of the base colour), with procedural limestone detail on pre-footing world position.

class Graph:
    def __init__(self, mat):
        self.nt = mat.node_tree; self.n = self.nt.nodes; self.l = self.nt.links

    def math(self, op, a, b=None, c=None):
        k = self.n.new('ShaderNodeMath'); k.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): k.inputs[i].default_value = v
            else: self.l.new(v, k.inputs[i])
        return k.outputs[0]

    def attr(self, name, kind='OBJECT'):
        a = self.n.new('ShaderNodeAttribute'); a.attribute_type = kind; a.attribute_name = name; return a

    def sep(self, v):
        s = self.n.new('ShaderNodeSeparateXYZ'); self.l.new(v, s.inputs[0]); return s.outputs

    def comb(self, x, y, z):
        c = self.n.new('ShaderNodeCombineXYZ')
        for i, v in enumerate((x, y, z)):
            if isinstance(v, (int, float)): c.inputs[i].default_value = v
            else: self.l.new(v, c.inputs[i])
        return c.outputs[0]

    def noise(self, vec, w, scale, detail=1.0, rough=.5):
        t = self.n.new('ShaderNodeTexNoise'); t.noise_dimensions = '4D'
        t.inputs['Scale'].default_value = scale; t.inputs['Detail'].default_value = detail; t.inputs['Roughness'].default_value = rough
        self.l.new(vec, t.inputs['Vector'])
        if isinstance(w, (int, float)): t.inputs['W'].default_value = w
        else: self.l.new(w, t.inputs['W'])
        return t.outputs['Fac']

    def mix(self, fac, a, b):
        m = self.n.new('ShaderNodeMix'); m.data_type = 'RGBA'; m.clamp_factor = True
        for sock, v in ((m.inputs['Factor'], fac), (m.inputs['A'], a), (m.inputs['B'], b)):
            if isinstance(v, (int, float)): sock.default_value = v
            elif isinstance(v, tuple): sock.default_value = v
            else: self.l.new(v, sock)
        return m.outputs['Result']

    def scale_rgb(self, col, k):
        m = self.n.new('ShaderNodeMix'); m.data_type = 'RGBA'; m.blend_type = 'MULTIPLY'; m.inputs['Factor'].default_value = 1
        self.l.new(col, m.inputs['A']) if not isinstance(col, tuple) else None
        if isinstance(col, tuple): m.inputs['A'].default_value = col
        g = self.comb(k, k, k) if not isinstance(k, (int, float)) else None
        if g is None: m.inputs['B'].default_value = (k, k, k, 1)
        else: self.l.new(g, m.inputs['B'])
        return m.outputs['Result']

    def _smooth(self, lo, hi, x):
        k = self.n.new('ShaderNodeMapRange'); k.interpolation_type = 'SMOOTHSTEP'; k.clamp = True
        k.inputs['From Min'].default_value = lo; k.inputs['From Max'].default_value = hi
        self.l.new(x, k.inputs['Value']); return k.outputs['Result']


def lin(h): return tuple(R.lin(h)) + (1,)


def limestone(name, kind):
    """kind: top, rim, side or deep."""
    m = bpy.data.materials.new(name); m.use_nodes = True; g = Graph(m); g.n.clear()
    out = g.n.new('ShaderNodeOutputMaterial'); bs = g.n.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Roughness'].default_value = .72 if kind == 'rim' else .86
    bs.inputs['Specular IOR Level'].default_value = .1; bs.inputs['IOR'].default_value = 1.45
    rest = g.sep(g.attr('rest', 'GEOMETRY').outputs['Vector']); x, y, z = rest
    tone = g.attr('tone').outputs['Fac']; seed = g.attr('seed').outputs['Fac']
    ax, ay = g.math('MULTIPLY', x, math.tau), g.math('MULTIPLY', y, math.tau)
    # Broad tone, periodic over exactly one cell in x and y (a torus in 4D), so any cell edge meets any other.
    torus = g.comb(g.math('MULTIPLY', g.math('COSINE', ax), .4), g.math('MULTIPLY', g.math('SINE', ax), .4), g.math('MULTIPLY', g.math('COSINE', ay), .4))
    tw = g.math('MULTIPLY', g.math('SINE', ay), .4)
    ring_x = g.comb(g.math('MULTIPLY', g.math('COSINE', ax), .6), g.math('MULTIPLY', g.math('SINE', ax), .6), 0)   # x-only period, for fronts
    base = {'top': TOP, 'rim': RIM, 'side': SIDE, 'deep': DEEP}[kind]
    col = lin(base)
    # Per-slab tone: a few warmer/peachier, a few paler and greyer.
    t = g.math('SUBTRACT', tone, .5)
    warm = g.mix(g.math('MULTIPLY', g.math('MAXIMUM', t, 0), 1.6), col, lin('F9CF98' if kind != 'side' else 'C88E55'))
    col = g.mix(g.math('MULTIPLY', g.math('MAXIMUM', g.math('MULTIPLY', t, -1), 0), 1.0), warm, lin('EFDDC0' if kind != 'side' else 'BE9D78'))
    if kind in ('top', 'rim'):
        broad = g.noise(torus, tw, 1.2, 2)
        col = g.scale_rgb(col, g.math('ADD', .97, g.math('MULTIPLY', g.math('SUBTRACT', broad, .5), .12)))
    if kind == 'side':
        broad = g.noise(ring_x, 0.0, 1.0, 2)
        wav = g.math('MULTIPLY', g.math('SUBTRACT', g.noise(ring_x, 3.0, 1.4, 0), .5), .03)
        zz = g.math('ADD', z, wav)
        # Strata at world heights (rows line up across every seam): three bands per slab height, each a slightly
        # different tone, parted by a thin crisp line; no line within the top .03 below the chamfer foot.
        P = .09
        u = g.math('DIVIDE', zz, P); f = g.math('FRACT', u); kb = g.math('FLOOR', u)
        hsh = g.math('FRACT', g.math('MULTIPLY', g.math('SINE', g.math('MULTIPLY', g.math('ADD', kb, 3.7), 12.9898)), 43758.5453))
        band = g.math('ADD', .955, g.math('MULTIPLY', hsh, .09))
        edge_d = g.math('MULTIPLY', g.math('MINIMUM', f, g.math('SUBTRACT', 1, f)), P)
        line_ = g._smooth(.0042, .0018, edge_d)
        clean = g.math('MINIMUM', g.math('MAXIMUM', g.math('DIVIDE', g.math('SUBTRACT', g.math('SUBTRACT', g.attr('top_h').outputs['Fac'], .03), z), .015), 0), 1)
        grad = g.math('ADD', .74, g.math('MULTIPLY', g.math('MINIMUM', g.math('DIVIDE', z, .3), 1), .26))
        k = g.math('MULTIPLY', g.math('MULTIPLY', band, grad), g.math('ADD', .97, g.math('MULTIPLY', broad, .06)))
        k = g.math('MULTIPLY', k, g.math('SUBTRACT', 1, g.math('MULTIPLY', g.math('MULTIPLY', line_, clean), .14)))
        col = g.scale_rgb(col, k)
    if kind == 'deep':
        col = g.scale_rgb(col, g.math('ADD', .8, g.math('MULTIPLY', g.math('MINIMUM', g.math('DIVIDE', z, .2), 1), .2)))
    if kind == 'top':
        lo = g.sep(g.attr('box_lo').outputs['Vector']); hi = g.sep(g.attr('box_hi').outputs['Vector'])
        # Sparse pores: a few small pits per slab, whole dots only, kept inside the slab's mask-independent box.
        vor = g.n.new('ShaderNodeTexVoronoi'); vor.voronoi_dimensions = '2D'; vor.feature = 'F1'; vor.inputs['Scale'].default_value = 13
        vor.inputs['Randomness'].default_value = .9
        # 2D, offset per slab (4D distances never reach zero, so dots would vanish); Position is in input units.
        g.l.new(g.comb(g.math('ADD', x, seed), g.math('ADD', y, g.math('MULTIPLY', seed, 1.37)), 0), vor.inputs['Vector'])
        pv = g.sep(vor.outputs['Position']); pp = (g.math('SUBTRACT', pv[0], seed), g.math('SUBTRACT', pv[1], g.math('MULTIPLY', seed, 1.37)))
        inside = g.math('MULTIPLY', g.math('MULTIPLY', g.math('GREATER_THAN', pp[0], g.math('ADD', lo[0], .04)), g.math('LESS_THAN', pp[0], g.math('SUBTRACT', hi[0], .04))),
                        g.math('MULTIPLY', g.math('GREATER_THAN', pp[1], g.math('ADD', lo[1], .04)), g.math('LESS_THAN', pp[1], g.math('SUBTRACT', hi[1], .04))))
        pick = g.math('GREATER_THAN', g.sep(vor.outputs['Color'])[0], .86)
        radius = g.math('MULTIPLY', g.math('ADD', .0055, g.math('MULTIPLY', g.sep(vor.outputs['Color'])[1], .004)), 13)  # Voronoi distance is in scaled units
        dot = g._smooth(.016, 0, g.math('SUBTRACT', vor.outputs['Distance'], radius))
        rim_ = g._smooth(.045, 0, g.math('ABSOLUTE', g.math('SUBTRACT', vor.outputs['Distance'], g.math('ADD', radius, .03))))
        pore = g.math('MULTIPLY', g.math('MULTIPLY', inside, pick), dot)
        col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', g.math('MULTIPLY', inside, pick), rim_), .35), col, lin('FFE9C4'))
        col = g.mix(g.math('MULTIPLY', pore, .75), col, lin('B98D5E'))
        # Cracks: up to two gently wandering lines per slab, one with a short branch, tapered to points, inside the
        # slab. A dark core with a pale lip on both sides, wide enough to survive the 2x publish downsample.
        wob = g.math('MULTIPLY', g.math('SUBTRACT', g.noise(g.comb(x, y, 0), seed, 9.0, 2, .55), .5), .04)

        def line(px, py, dx, dy, length, one_sided, width):
            rx, ry = g.math('SUBTRACT', x, px), g.math('SUBTRACT', y, py)
            u = g.math('ADD', g.math('MULTIPLY', rx, dx), g.math('MULTIPLY', ry, dy))
            v = g.math('ABSOLUTE', g.math('ADD', g.math('SUBTRACT', g.math('MULTIPLY', ry, dx), g.math('MULTIPLY', rx, dy)), wob))
            s_ = g.math('DIVIDE', u, g.math('MAXIMUM', length, .001))
            if one_sided: taper = g.math('MULTIPLY', g.math('GREATER_THAN', s_, 0), g.math('SUBTRACT', 1, g.math('POWER', g.math('MAXIMUM', s_, 0), 2)))
            else: taper = g.math('SUBTRACT', 1, g.math('POWER', g.math('ABSOLUTE', s_), 3))
            w_ = g.math('MULTIPLY', g.math('MAXIMUM', taper, 0), width)
            live = g.math('GREATER_THAN', w_, 1e-5)
            core_ = g.math('MULTIPLY', g.math('SUBTRACT', 1, g._smooth(.55, 1, g.math('DIVIDE', v, g.math('MAXIMUM', w_, 1e-5)))), live)
            lip_ = g.math('MULTIPLY', g._smooth(.003, .0012, g.math('ABSOLUTE', g.math('SUBTRACT', v, g.math('ADD', w_, .0032)))), live)
            return core_, lip_
        cores, lips = [], []
        for i in range(2):
            cc = g.sep(g.attr(f'crack{i}_c').outputs['Vector']); cd = g.sep(g.attr(f'crack{i}_d').outputs['Vector'])
            bp = g.sep(g.attr(f'branch{i}_p').outputs['Vector']); bd = g.sep(g.attr(f'branch{i}_d').outputs['Vector'])
            c1, l1 = line(cc[0], cc[1], cd[0], cd[1], cc[2], False, .0075 if i == 0 else .0062)
            c2, l2 = line(bp[0], bp[1], bd[0], bd[1], bp[2], True, .0058)
            cores += [g.math('MULTIPLY', c1, cd[2]), g.math('MULTIPLY', c2, bd[2])]
            lips += [g.math('MULTIPLY', l1, cd[2]), g.math('MULTIPLY', l2, bd[2])]
        crack = g.math('MAXIMUM', g.math('MAXIMUM', cores[0], cores[1]), g.math('MAXIMUM', cores[2], cores[3]))
        lipm = g.math('MULTIPLY', g.math('MAXIMUM', g.math('MAXIMUM', lips[0], lips[1]), g.math('MAXIMUM', lips[2], lips[3])), g.math('SUBTRACT', 1, crack))
        col = g.mix(g.math('MULTIPLY', lipm, .7), col, lin('FFF4DE'))
        col = g.mix(crack, col, lin('8C6038'))
    g.l.new(col, bs.inputs['Base Color']); g.l.new(col, bs.inputs['Emission Color'])
    bs.inputs['Emission Strength'].default_value = {'top': .10, 'rim': .16, 'side': .10, 'deep': .14}[kind]
    g.l.new(bs.outputs[0], out.inputs['Surface'])
    m.diffuse_color = lin(base)
    m['nativeSurface'] = 'warm limestone; pre-footing world/per-slab procedural detail; no raster textures'
    return m


def scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.name = 'Breakable Reef Native'
    col = bpy.data.collections.new('Breakable reef'); sc.collection.children.link(col)
    root = bpy.data.objects.new('Breakable reef ground root', None); col.objects.link(root)
    mats = [limestone('Limestone top', 'top'), limestone('Limestone chamfer', 'rim'), limestone('Limestone side', 'side'), limestone('Limestone groove core', 'deep')]
    cam = bpy.data.objects.new('Registered 35 degree camera', bpy.data.cameras.new('Registered 35 degree camera'))
    sc.collection.objects.link(cam); sc.camera = cam
    R.configure(sc)
    roles = [('Overhead', (0, 0, 5), 185, 4.5, (1, .95, .88))]
    for i in range(8):
        a = i * math.tau / 8; roles.append(('Symmetric fill ' + str(i), (3.5 * math.cos(a), 3.5 * math.sin(a), 2.3), 34, 5, (.97, .96, .95)))
    for name, pos, power, size, color in roles:
        ld = bpy.data.lights.new(name, 'AREA'); ob = bpy.data.objects.new(name, ld); sc.collection.objects.link(ob)
        ob.location = pos; ob.rotation_euler = (Vector((0, 0, 1)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
        ld.energy = power; ld.shape = 'DISK'; ld.size = size; ld.color = color
        # Soft shadows resolved over the 64 TAA samples instead of one noisy shadow-map tap (speckle in grooves).
        ld.use_shadow_jitter = True; ld.shadow_filter_radius = 2.0
    sc.eevee.shadow_ray_count = 4; sc.eevee.shadow_step_count = 16
    sc.world = bpy.data.worlds.new('Balanced blue stone studio'); sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value = (.72, .80, 1, 1); bg.inputs['Strength'].default_value = .12
    return sc, col, root, mats


def bake_rest(col):
    """Store pre-footing world positions: the capture squash moves vertices, the stone pattern must not move."""
    for ob in col.objects:
        if ob.type != 'MESH': continue
        a = ob.data.attributes.get('rest') or ob.data.attributes.new('rest', 'FLOAT_VECTOR', 'POINT')
        for v in ob.data.vertices: a.data[v.index].vector = ob.matrix_world @ v.co


def capture(sc, col, out):
    out.mkdir(parents=True, exist_ok=True)
    bake_rest(col)
    with R.square_footing(col):
        sc.render.filepath = str(out / 'static-S.png'); bpy.ops.render.render(write_still=True)


def clear(col, root):
    for ob in list(col.objects):
        if ob is not root: me = ob.data; bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out = HERE / 'native' / 'reef'
    if '--out' in args: i = args.index('--out'); out = Path(args[i + 1]).resolve(); del args[i:i + 2]
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
        capture(sc, col, out / pid)
        pieces[pid] = {'kind': kind, 'mask': mask, 'pattern': p}
        if pid == 'reef-05-a': bpy.ops.wm.save_as_mainfile(filepath=str(out / 'reef-05-a' / 'project.blend'), compress=True)
    if not only:
        (out / 'pieces.json').write_text(json.dumps({'recipe': str(RECIPE.relative_to(ASSETS)), 'frame': [192, 512], 'root': [96, 416], 'nativeScale': 4,
                                                     'maskBits': {'N': N, 'E': E, 'S': S, 'W': W}, 'collision': {'inset': INSET, 'cornerRadius': CORNER}, 'pieces': pieces}, indent=1) + '\n')


if __name__ == '__main__':
    main()
