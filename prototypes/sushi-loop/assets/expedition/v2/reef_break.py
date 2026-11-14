"""Issue #76 breakable reef: crack and break animation for every reef piece, from the same cells as reef.py.

Run from the repository root:

    blender -b --factory-startup --python prototypes/sushi-loop/assets/expedition/v2/reef_break.py [-- id,id] [--out DIR]

Replaces the preview's code-drawn hairlines (user, 2026-11-13). Each piece `reef-MM-p` (neighbour mask, slab pattern)
gets nine native frames, captured like its static sprite (same camera, lights, materials and square footing):

  crack-1..3  the intact cell while the parrotfish closes in: fractures run from the impact point on the south edge
              (where the nose arrives) across every slab, longer and wider each stage. Shown over `crack_seconds`.
  break-1..6  12 fps: the slabs split along those fractures, the chunks burst up and away from the impact (biased
              north, the way the fish is pushing), tumble, and land as low fragments. break-6 is the rubble the cell
              keeps afterwards, so the cell never pops to a different scatter.

The fracture is one set of vertical planes per piece (three radial from the impact, two across); the cracks drawn in
crack-1..3 lie on those planes, so the chunks come apart exactly where the cracks were. Fracture lines are seeded by
mask and pattern; the cell geometry and surface are reef.py's, built with the same seed as the static sprite.
"""
import bmesh, bpy, importlib.util, json, math, random, sys
from pathlib import Path
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('reef', HERE / 'reef.py')
reef = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reef)
reef.SEGS = 28          # room for the fracture cracks after each slab's own hairlines (unused segments draw nothing)

STAGES = [(.34, .9), (.66, 1.3), (1.3, 1.9)]   # crack stages: reach from the impact (cells), width scale
CRACK_W = .0068         # fracture crack width at the impact end, before the stage scale
BREAK_FRAMES = 6
FRESH = 'F7E6C6'        # freshly broken limestone inside the slabs: paler than the weathered top


def fracture_lines(mask, pattern):
    rng = random.Random(f'reef-break-{mask}-{pattern}')
    impact = Vector((rng.uniform(-.14, .14), -.5))
    lines = [(impact, math.radians(a)) for a in (rng.uniform(48, 68), rng.uniform(82, 98), rng.uniform(112, 132))]
    lines.append((Vector((rng.uniform(-.1, .1), rng.uniform(-.24, -.1))), math.radians(rng.uniform(-14, 14))))
    lines.append((Vector((rng.uniform(-.1, .1), rng.uniform(.1, .26))), math.radians(rng.uniform(-14, 14))))
    return impact, [(p, Vector((math.cos(a), math.sin(a)))) for p, a in lines]


def clip(p, d, lo, hi):
    """The part of the infinite line p + t d inside the box, as (t0, t1), or None."""
    t0, t1 = -9.0, 9.0
    for i in range(2):
        if abs(d[i]) < 1e-9:
            if not lo[i] <= p[i] <= hi[i]: return None
            continue
        a, b = (lo[i] - p[i]) / d[i], (hi[i] - p[i]) / d[i]
        t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
    return (t0, t1) if t1 - t0 > .02 else None


def crack_segments(ob, impact, lines, reach, scale, rng_key):
    """Fracture cracks on one slab's top for a stage: each line clipped to the slab, cut into short jittered segments,
    revealed out to `reach` from the impact, tapering away from it."""
    xs = [v.co.x for v in ob.data.vertices]; ys = [v.co.y for v in ob.data.vertices]
    lo, hi = Vector((min(xs) + .03, min(ys) + .03)), Vector((max(xs) - .03, max(ys) - .03))
    segs = []
    for li, (p, d) in enumerate(lines):
        span = clip(p, d, lo, hi)
        if not span: continue
        rng = random.Random(f'{rng_key}-{li}')
        n = max(2, round((span[1] - span[0]) / .045))
        normal = Vector((-d.y, d.x))
        pts = [p + d * (span[0] + (span[1] - span[0]) * k / n) + normal * (0 if k in (0, n) else rng.uniform(-.014, .014)) for k in range(n + 1)]
        for a, b in zip(pts, pts[1:]):
            ra, rb = (a - impact).length, (b - impact).length
            if min(ra, rb) > reach: continue
            if max(ra, rb) > reach:   # the crack tip, part way along this segment
                near, far = (a, b) if ra < rb else (b, a)
                t = (reach - min(ra, rb)) / max(abs(rb - ra), 1e-6); far = near + (far - near) * t
                a, b = near, far; ra, rb = (a - impact).length, (b - impact).length
            w = lambda r: CRACK_W * scale * max(.35, 1 - r / 1.4) * (1 - .55 * min(1, max(0, (r - reach * .7) / max(reach * .3, 1e-6))))
            segs.append((a.x, a.y, w(ra), b.x, b.y, w(rb)))
    return segs


def set_cracks(ob, own, extra):
    segs = (own + extra)[:reef.SEGS]
    for i in range(reef.SEGS):
        a = segs[i] if i < len(segs) else (0, 0, 0, 0, 0, 0)
        ob[f'seg{i}_a'] = (a[0], a[1], a[2]); ob[f'seg{i}_b'] = (a[3], a[4], a[5])


def own_cracks(ob):
    out = []
    for i in range(reef.SEGS):
        a, b = ob.get(f'seg{i}_a'), ob.get(f'seg{i}_b')
        if a is None or a[2] <= 0: break
        out.append((a[0], a[1], a[2], b[0], b[1], b[2]))
    return out


def split(ob, lines, mat_index):
    """Cut a slab mesh by the vertical fracture planes; returns a list of bmeshes (closed chunks)."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    pieces = [bm]
    for p, d in lines:
        co, no = Vector((p.x, p.y, 0)), Vector((-d.y, d.x, 0))
        nxt = []
        for piece in pieces:
            for keep in ('inner', 'outer'):
                c = piece.copy()
                bmesh.ops.bisect_plane(c, geom=c.verts[:] + c.edges[:] + c.faces[:], dist=1e-6, plane_co=co, plane_no=no,
                                       clear_inner=keep == 'outer', clear_outer=keep == 'inner')
                edges = [e for e in c.edges if e.is_boundary]
                if edges:
                    made = bmesh.ops.holes_fill(c, edges=edges, sides=0)['faces']
                    for f in made: f.material_index = mat_index; f.smooth = False
                if len(c.faces) >= 4 and len(c.verts) >= 6: nxt.append(c)
                else: c.free()
            piece.free()
        pieces = nxt
    return pieces


def chunk_objects(col, root, slabs, lines, mats):
    obs = []
    for s in slabs:
        idx = len(s.data.materials)
        s.data.materials.append(mats['fresh'])
        for k, bm in enumerate(split(s, lines, idx)):
            me = bpy.data.meshes.new(f'{s.name} chunk {k}'); bm.to_mesh(me); bm.free()
            for m in s.data.materials: me.materials.append(m)
            size = [max(v.co[i] for v in me.vertices) - min(v.co[i] for v in me.vertices) for i in range(2)]
            check = bmesh.new(); check.from_mesh(me); vol = abs(check.calc_volume()); check.free()
            if min(size) < .045 or vol < .0016:   # a sliver or spike between close cuts: it crumbles to dust
                bpy.data.meshes.remove(me); continue
            if 'custom_normal' in me.attributes: me.attributes.remove(me.attributes['custom_normal'])
            c = sum((v.co for v in me.vertices), Vector()) / len(me.vertices)
            me.transform(Matrix.Translation(-c))
            for p in me.polygons: p.use_smooth = p.material_index == 2
            me.set_sharp_from_angle(angle=math.radians(32))
            o = bpy.data.objects.new(me.name, me); col.objects.link(o); o.parent = root; o.location = c
            for key in s.keys():
                if key.startswith('seg') or key in ('tone', 'seed', 'box_lo', 'box_hi', 'top_h'): o[key] = s[key]
            obs.append(o)
    return obs


def flights(chunks, impact, seed):
    """Per chunk: start, travel, hop, final spin and scale. Away from the impact, biased north, inside the frame."""
    rng = random.Random(seed); out = []
    for o in chunks:
        c = o.location.copy()
        away = Vector((c.x - impact.x, c.y - impact.y))
        away = (away.normalized() if away.length > 1e-4 else Vector((0, 1))) + Vector((0, .7))
        away.normalize()
        dist = rng.uniform(.14, .34)
        end = Vector((max(-.62, min(.62, c.x + away.x * dist)), max(-.6, min(1.1, c.y + away.y * dist))))
        axis = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-.3, .3))).normalized()
        out.append({'ob': o, 'start': c, 'end': end, 'hop': rng.uniform(.14, .32), 'axis': axis,
                    'spin': rng.uniform(1.0, 2.2) * rng.choice((-1, 1)), 'scale': rng.uniform(.5, .62), 'flat': rng.uniform(.4, .55)})
    return out


def pose(f, t):
    """Chunk transform at t in (0, 1]; the last frame is the settled rubble."""
    o = f['ob']; k = min(1, t / .82); e = 1 - (1 - k) ** 2   # fast burst, easing into the landing
    s = 1 + (f['scale'] - 1) * e
    rot = Matrix.Rotation(f['spin'] * e, 4, f['axis'])
    flat = Matrix.Diagonal((1, 1, 1 + (f['flat'] - 1) * e, 1))
    o.matrix_basis = Matrix.Translation(Vector((0, 0, 0))) @ flat @ rot @ Matrix.Diagonal((s, s, s, 1))
    bpy.context.view_layer.update()
    low = min((o.matrix_world @ v.co).z for v in o.data.vertices) - o.matrix_world.translation.z
    z_land = -low   # resting on the seabed
    z = f['start'].z + (z_land - f['start'].z) * e + 4 * f['hop'] * k * (1 - k)
    xy = f['start'].xy.lerp(f['end'], e)
    o.matrix_basis = Matrix.Translation(Vector((xy.x, xy.y, max(z, z_land)))) @ flat @ rot @ Matrix.Diagonal((s, s, s, 1))
    bpy.context.view_layer.update()


def shoot(sc, col, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with reef.R.square_footing(col):
        sc.render.filepath = str(path); bpy.ops.render.render(write_still=True)


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out = HERE / 'native' / 'reef-break'
    if '--out' in args: i = args.index('--out'); out = Path(args[i + 1]).resolve(); del args[i:i + 2]
    only = set(args[0].split(',')) if args else None
    sc, col, root, mats = reef.scene()
    saved = reef.RIM; reef.RIM = FRESH
    fresh = reef.limestone('Limestone fresh break', 'rim'); reef.RIM = saved
    pieces = {}
    for mask in range(16):
        for p in reef.PATTERNS:
            pid = f'reef-{mask:02d}-{p}'
            if only and pid not in only: continue
            reef.clear(col, root)
            reef.cell(col, root, mask, p, sum(map(ord, pid)), mats)
            reef.bake_rest(col)
            impact, lines = fracture_lines(mask, p)
            slabs = [o for o in col.objects if o.name.startswith('Limestone slab')]
            core = next(o for o in col.objects if o.name.startswith('Groove core'))
            own = {o.name: own_cracks(o) for o in slabs}
            for k, (reach, scale) in enumerate(STAGES, 1):
                for o in slabs: set_cracks(o, own[o.name], crack_segments(o, impact, lines, reach, scale, f'{pid}-{o.name}'))
                shoot(sc, col, out / pid / f'crack-{k}.png')
            chunks = chunk_objects(col, root, slabs, lines, {'fresh': fresh})
            for o in slabs + [core]: o.hide_render = True
            for o in slabs: o.parent = None; col.objects.unlink(o)
            core.parent = None; col.objects.unlink(core)
            fl = flights(chunks, impact, f'{pid}-flight')
            for k in range(1, BREAK_FRAMES + 1):
                for f in fl: pose(f, k / BREAK_FRAMES)
                shoot(sc, col, out / pid / f'break-{k}.png')
            if pid == 'reef-05-a': bpy.ops.wm.save_as_mainfile(filepath=str(out / pid / 'project.blend'), compress=True)
            pieces[pid] = {'mask': mask, 'pattern': p, 'impact': list(impact), 'chunks': len(chunks),
                           'lines': [[list(a), list(d)] for a, d in lines]}
    if not only:
        (out / 'pieces.json').write_text(json.dumps({'frame': [192, 512], 'root': [96, 416], 'nativeScale': 4, 'fps': 12,
            'frames': [f'crack-{k}' for k in range(1, 4)] + [f'break-{k}' for k in range(1, BREAK_FRAMES + 1)],
            'crackStages': [{'reach': r, 'width': w} for r, w in STAGES], 'pieces': pieces}, indent=1) + '\n')


if __name__ == '__main__':
    main()
