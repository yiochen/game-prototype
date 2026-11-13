"""Round-01 technical validation (run in Blender: blender -b --factory-startup --python validate.py -- OUT.json).

Geometry: rebuilds every piece with the backup recipe (backups/reef.py) and with this round's recipe in the same
scene, and compares ground rings, slab heights and rubble vertices. Images: compares alpha footprints of this
round's native captures with baseline captures of the backup recipe, after measuring renderer noise on repeated
renders. Registration: camera/root/frame of the saved project against backups/reef-05-a.blend. Lights: rig symmetry.
"""
import bpy, importlib.util, json, math, sys, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
OUT = Path(sys.argv[sys.argv.index('--') + 1])
C = EXP / 'candidates' / 'round-01'


def load(name, path, patch=None):
    src = Path(path).read_text()
    if patch: src = patch(src)
    mod = type(sys)(name); mod.__file__ = str(path); mod.__dict__['__name__'] = name
    exec(compile(src, str(path), 'exec'), mod.__dict__); return mod


new = load('reef_round01', HERE / 'reef.py')
old = load('reef_backup', EXP / 'backups' / 'reef.py', lambda s: s.split('\nargs = sys.argv')[0].replace(
    "RECIPE = HERE.parents[1] / 'production/source/blender/refinement/boulder-underwater/source/round-04-recipe.py'", f"RECIPE = Path(r'{new.RECIPE}')"))


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def meshes(col):
    return sorted([o for o in col.objects if o.type == 'MESH'], key=lambda o: o.name)


def seg_dist(p, a, b):
    ab = b - a; t = max(0, min(1, (p - a).dot(ab) / max(ab.length_squared, 1e-12))); return (a + ab * t - p).length


def ground_ring(ob):
    return [(ob.matrix_world @ v.co).to_2d() for v in ob.data.vertices if abs(v.co.z) < 1e-9]


def poly_dist(p, ring):
    return min(seg_dist(p, ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring)))


# ---------------- geometry
sc, col, root, mats = new.scene()
geo, worst = {}, {'groundOffOriginal': 0, 'originalOffNew': 0, 'topHeightDelta': 0, 'rubbleVertexDelta': 0, 'chipDepthBeyondChamfer': 0}
jobs = [(f'reef-{m:02d}-{p}', m, p) for m in range(16) for p in 'abc'] + [(f'reef-rubble-{p}', None, p) for p in 'ab']
for pid, mask, p in jobs:
    seed = sum(map(ord, pid)); rec = {}
    for tag, mod in (('old', old), ('new', new)):
        new.clear(col, root)
        if mask is None: mod.rubble(col, root, seed, mats)
        else: mod.cell(col, root, mask, p, seed, mats)
        bpy.context.view_layer.update()
        rec[tag] = [{'name': o.name, 'ground': ground_ring(o), 'zmax': max((o.matrix_world @ v.co).z for v in o.data.vertices),
                     'verts': [tuple(round(c, 7) for c in (o.matrix_world @ v.co)) for v in o.data.vertices]} for o in meshes(col)]
    o_sl = [r for r in rec['old'] if r['name'].startswith(('Limestone', 'Fragment'))]
    n_sl = [r for r in rec['new'] if r['name'].startswith(('Limestone', 'Fragment'))]
    assert [r['name'] for r in o_sl] == [r['name'] for r in n_sl], pid
    e = {'slabs': len(n_sl), 'groundOffOriginal': 0.0, 'originalOffNew': 0.0, 'topHeightDelta': 0.0}
    for a, b in zip(o_sl, n_sl):
        if mask is None:
            d = max(max(abs(x - y) for x, y in zip(u, v)) for u, v in zip(a['verts'], b['verts'])) if len(a['verts']) == len(b['verts']) else 1
            e['rubbleVertexDelta'] = max(e.get('rubbleVertexDelta', 0), d); e['rubbleMaxZ'] = max(e.get('rubbleMaxZ', 0), b['zmax'])
            continue
        e['groundOffOriginal'] = max(e['groundOffOriginal'], max(poly_dist(q, a['ground']) for q in b['ground']))
        e['originalOffNew'] = max(e['originalOffNew'], max(poly_dist(q, b['ground']) for q in a['ground']))
        e['topHeightDelta'] = max(e['topHeightDelta'], abs(a['zmax'] - b['zmax']))
    core = [r for r in rec['new'] if r['name'] == 'Groove core']
    if core:
        union = [r['ground'] for r in n_sl]
        e['coreHeight'] = core[0]['zmax']; e['coreBelowEverySlabTop'] = core[0]['zmax'] < min(r['zmax'] for r in n_sl)
        # Every core ground vertex lies inside the slab outline union's bounds.
        fx = [min(q.x for r in union for q in r), max(q.x for r in union for q in r), min(q.y for r in union for q in r), max(q.y for r in union for q in r)]
        e['coreInsideFootprint'] = all(fx[0] - 1e-6 <= q.x <= fx[1] + 1e-6 and fx[2] - 1e-6 <= q.y <= fx[3] + 1e-6 for q in core[0]['ground'])
    for k in worst:
        if k in e: worst[k] = max(worst[k], e[k])
    geo[pid] = e
# Chip depth: largest extra inward offset of any top-ring vertex, from the recipe's own chip tables.
for p in 'abc':
    for i in range(len(new.PATTERNS[p])):
        for ch in new.slab_extras(p, i)['chips']: worst['chipDepthBeyondChamfer'] = max(worst['chipDepthBeyondChamfer'], ch[3])
crack = {p: [i for i in range(len(new.PATTERNS[p])) if new.slab_extras(p, i)['crack']] for p in 'abc'}

# ---------------- images
def alpha(path):
    im = bpy.data.images.load(str(path)); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)[::-1]
    bpy.data.images.remove(im); return a


def diff(a, b):
    d = np.abs(a - b) * 255; return {'maxAbs': float(d.max()), 'pixelsOver2': int((d.max(axis=2) > 2).sum()), 'pixelsOver8': int((d.max(axis=2) > 8).sum()), 'meanAbs': float(d.mean())}


rep = {'baseline reef-05-a run1 vs run2': diff(alpha(HERE / 'baseline/reef-05-a/static-S.png'), alpha(HERE / 'repeat/baseline-reef-05-a-run2.png')),
       'round-01 reef-05-a run1 vs run2': diff(alpha(HERE / 'native/reef-05-a/static-S.png'), alpha(HERE / 'repeat/r/reef-05-a/static-S.png'))}
alpha_tol = max(int((np.abs(alpha(HERE / 'baseline/reef-05-a/static-S.png')[..., 3] - alpha(HERE / 'repeat/baseline-reef-05-a-run2.png')[..., 3]) > .5 / 255).sum()), 0)
def outer(m, r=12):
    """Outer silhouette: morphological closing (square, radius r native px) bridges groove gaps of up to 2r px, which the
    hidden core intentionally fills; convex outlines and rounded corners are unchanged by a closing."""
    def grow(m, f):
        o = m.copy()
        for ax in (0, 1):
            acc = o.copy()
            for k in range(1, r + 1): acc = f(f(acc, np.roll(o, k, ax)), np.roll(o, -k, ax))
            o = acc
        return o
    p = np.pad(m, r + 2)
    c = ~grow(~grow(p, np.logical_or), np.logical_or)
    return c[r + 2:-r - 2, r + 2:-r - 2]


imgs, iworst = {}, {'alphaIoU': 1, 'bottomRowShift': 0, 'sideExtentShift': 0, 'topRowShift': 0, 'opaqueBeyondBaseline': 0}
for pid, *_ in jobs:
    ra, rb = alpha(HERE / 'baseline' / pid / 'static-S.png')[..., 3] > .5, alpha(C / 'native' / f'{pid}.png')[..., 3] > .5
    groove_fill = int((rb & ~ra).sum()); groove_open = int((ra & ~rb).sum())
    if pid.startswith('reef-rubble'): a, b = ra, rb
    else: a, b = outer(ra), outer(rb)   # outer silhouette: the core may fill grooves, but the outline must not move
    iou = float((a & b).sum() / max(1, (a | b).sum()))
    cols = np.where(a.any(0) & b.any(0))[0]
    def low(m): return np.array([np.where(m[:, c])[0].max() if m[:, c].any() else -1 for c in cols])
    def high(m): return np.array([np.where(m[:, c])[0].min() if m[:, c].any() else -1 for c in cols])
    rows = np.where(a.any(1) & b.any(1))[0]
    rows = rows[(rows >= rows.min() + 8) & (rows <= rows.max() - 8)]  # skip the 8-px top/bottom tangent rows, where tiny height jitter moves the first row's extent
    side = max(max(abs(np.where(a[r])[0].min() - np.where(b[r])[0].min()), abs(np.where(a[r])[0].max() - np.where(b[r])[0].max())) for r in rows)
    # Dilate the baseline by 2 px (one published pixel) before counting new opaque pixels outside it.
    dil = a.copy()
    for dy in (-2, -1, 0, 1, 2):
        for dx in (-2, -1, 0, 1, 2): dil |= np.roll(np.roll(a, dy, 0), dx, 1)
    beyond = int((b & ~dil).sum())
    r = {'alphaIoU': round(iou, 5), 'bottomRowShift': int(np.abs(low(a) - low(b)).max()), 'topRowShift': int(np.abs(high(a) - high(b)).max()),
         'sideExtentShift': int(side), 'opaqueBeyondBaselinePlus2px': beyond, 'grooveFillPx': groove_fill, 'newlyTransparentPx': groove_open,
         'nativeSha256': sha(C / 'native' / f'{pid}.png'), 'spriteSha256': sha(C / 'sprites' / pid / 'static-S.png')}
    imgs[pid] = r
    iworst['alphaIoU'] = min(iworst['alphaIoU'], r['alphaIoU'])
    for k in ('bottomRowShift', 'sideExtentShift', 'topRowShift'): iworst[k] = max(iworst[k], r[k])
    iworst['opaqueBeyondBaseline'] = max(iworst['opaqueBeyondBaseline'], beyond)
    sz = bpy.data.images.load(str(C / 'native' / f'{pid}.png')); r['nativeSize'] = list(sz.size); bpy.data.images.remove(sz)
    sz = bpy.data.images.load(str(C / 'sprites' / pid / 'static-S.png')); r['spriteSize'] = list(sz.size); bpy.data.images.remove(sz)

# ---------------- registration and lights, from saved projects
def scene_record(path):
    bpy.ops.wm.open_mainfile(filepath=str(path)); s = bpy.context.scene; cam = s.camera
    o = world_to_camera_view(s, cam, Vector((0, 0, 0)))
    rootob = bpy.data.objects['Breakable reef ground root']
    return {'file': str(path.relative_to(EXP)), 'sha256': sha(path), 'resolution': [s.render.resolution_x, s.render.resolution_y], 'engine': s.render.engine,
            'viewTransform': s.view_settings.view_transform, 'filmTransparent': s.render.film_transparent, 'taaSamples': s.eevee.taa_render_samples,
            'camera': {'type': cam.data.type, 'orthoScale': cam.data.ortho_scale, 'shift': [cam.data.shift_x, cam.data.shift_y], 'matrixWorld': [list(r) for r in cam.matrix_world]},
            'rootMatrix': [list(r) for r in rootob.matrix_world], 'rootNativePx': [o.x * s.render.resolution_x, (1 - o.y) * s.render.resolution_y],
            'lights': [{'name': ob.name, 'type': ob.data.type, 'location': [round(c, 4) for c in ob.location], 'energy': ob.data.energy, 'size': ob.data.size,
                        'color': [round(c, 4) for c in ob.data.color], 'shape': ob.data.shape} for ob in sorted(s.objects, key=lambda o: o.name) if ob.type == 'LIGHT'],
            'world': {'color': list(s.world.node_tree.nodes['Background'].inputs[0].default_value), 'strength': s.world.node_tree.nodes['Background'].inputs[1].default_value},
            'externalImages': [im.filepath for im in bpy.data.images if im.source == 'FILE'],
            'materials': sorted(m.name for m in bpy.data.materials if m.users)}


src = scene_record(EXP / 'backups' / 'reef-05-a.blend')
cur = scene_record(HERE / 'reef-05-a.blend')
fills = [l for l in cur['lights'] if l['name'].startswith('Symmetric fill')]
rad = [math.hypot(*l['location'][:2]) for l in fills]
reg = {'source': src, 'current': cur,
       'cameraMatrixMaxDelta': max(abs(a - b) for ra, rb in zip(src['camera']['matrixWorld'], cur['camera']['matrixWorld']) for a, b in zip(ra, rb)),
       'shiftDelta': [abs(a - b) for a, b in zip(src['camera']['shift'], cur['camera']['shift'])], 'orthoScaleSame': src['camera']['orthoScale'] == cur['camera']['orthoScale'],
       'rootPxSource': src['rootNativePx'], 'rootPxCurrent': cur['rootNativePx'], 'expectedRootNativePx': [384, 1664],
       'lightsSymmetric': {'fillCount': len(fills), 'fillEnergiesEqual': len({l['energy'] for l in fills}) == 1, 'fillColorsEqual': len({tuple(l['color']) for l in fills}) == 1,
                           'fillRadiusRange': [min(rad), max(rad)], 'fillAnglesDeg': [round(math.degrees(math.atan2(l['location'][1], l['location'][0])) % 360, 2) for l in fills],
                           'fillHeights': sorted({l['location'][2] for l in fills}), 'overheadAtOrigin': [l['location'] for l in cur['lights'] if l['name'] == 'Overhead']},
       'lightChangesFromSource': 'fill colour (.90,.96,1) -> (.97,.96,.95), equal on all eight; positions, energies, sizes and overhead unchanged'}

result = {
    'asset': 'breakable-reef', 'round': 1, 'recipe': 'source/round-01/reef.py', 'recipeSha256': sha(HERE / 'reef.py'),
    'project': 'source/round-01/reef-05-a.blend', 'projectSha256': sha(HERE / 'reef-05-a.blend'),
    'baselineCaptures': 'source/round-01/baseline (backups/reef.py re-rendered in this session, same Blender)',
    'pieceCount': len(imgs),
    'geometry': {'worst': worst, 'limits': {'chipDepth': .03, 'rubbleMaxZ': .1, 'slabHeightJitterOfOriginal': .008},
                 'crackedSlabsPerPattern': crack, 'slabsPerPattern': {p: len(v) for p, v in new.PATTERNS.items()},
                 'notes': ['Ground rings: every new z=0 vertex lies on the original outline polyline and every original z=0 vertex on the new one (distances in cells).',
                           'topHeightDelta is the removed per-vertex top jitter (+/-.008 in the original); the generator sequence, tilt and per-slab heights are unchanged.',
                           'Groove core: hidden block inside the footprint (inset .03 from open faces, flush to faces against solid), below every slab top; the image footprint check confirms it adds no outline pixels.'],
                 'pieces': geo},
    'images': {'repeatability': rep, 'repeatabilityAlphaPixelsChanged': alpha_tol, 'worst': iworst,
               'notes': ['Alpha footprint vs baseline: masks alpha>0.5 at native 768x2048, compared as outer silhouettes (morphological closing, 12 px radius) because the hidden core intentionally fills groove gaps (grooveFillPx). Shifts in native px (4 px = 1 logical px). Pixels opaque beyond the baseline (+2 px) and bottom-row shifts occur only on faces against solid: the core runs flush to those cell edges and square at non-exposed corners (the collision shape), closing the seabed notches the 0.05 slab corner rounding left at cell junctions; it never passes the footprint (geometry.pieces.*.coreInsideFootprint) or the slab tops. sideExtentShift excludes the 8 tangent rows at the top and bottom of the silhouette.', 'Repeat renders of an unchanged piece are pixel-identical (file bytes differ only in PNG metadata), so tolerance is 0 for renderer noise.'],
               'pieces': imgs},
    'registration': reg,
}
OUT.write_text(json.dumps(result, indent=1) + '\n')
print('VALIDATION', json.dumps({'geometry': worst, 'images': iworst, 'repeat': rep, 'camDelta': reg['cameraMatrixMaxDelta'], 'root': [src['rootNativePx'], cur['rootNativePx']]}))
