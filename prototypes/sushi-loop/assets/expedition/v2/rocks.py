"""Issue #21 rock variants built with the approved boulder-underwater recipe.

Run from the repository root:

    blender -b --factory-startup --python prototypes/sushi-loop/assets/expedition/v2/rocks.py

The production recipe (assets/production/source/blender/refinement/
boulder-underwater/source/round-04-recipe.py) is imported unchanged: its
hand-shaped `rock()` geometry, stone material, registered 35° camera
calibration, nine-light rig and capture-only square footing. Only the mass
layout, total height and palette vary. Native captures are 4x; `publish.sh`
downsamples them 2x with Lanczos to the published atlas scale, like the
production delivery.
"""
import bpy, importlib.util, json, math, sys
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
RECIPE = HERE.parents[1] / 'production/source/blender/refinement/boulder-underwater/source/round-04-recipe.py'
spec = importlib.util.spec_from_file_location('boulder_recipe', RECIPE)
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)  # `__main__` guard: defines functions only.
OUT = HERE / 'native' / 'rocks'

# Palettes: (body, crown, secondary, facet). The first is the production set.
PALETTES = {
    'cobalt': ('2479D8', '2C8DDD', '236FD1', '2A7FD9'),
    'deep': ('1B4FB0', '2160BE', '1A47A2', '1F58B4'),
    'indigo': ('3352C4', '3D63D2', '2E48B4', '3759C9'),
    'teal': ('1F86C9', '27A0D6', '1C78BC', '2391CF'),
    'sky': ('3A92E6', '52A9EE', '3486DB', '449DE9'),
}

# Mass layouts in the recipe's own vocabulary: (name, cx, cy, w, d, relative height, angle).
LAYOUTS = {
    'crag': [('Dominant crown', .035, .075, .83, .82, 1.0, -.06), ('Rear left shoulder', -.275, .255, .51, .51, .67, .1),
             ('Front right shoulder', .285, -.19, .47, .54, .61, -.14), ('Low front boulder', -.22, -.32, .55, .46, .38, .08)],
    'pair': [('Left mass', -.2, .05, .62, .7, 1.0, .12), ('Right mass', .27, -.06, .56, .62, .78, -.1),
             ('Front pebble', .05, -.36, .4, .32, .32, .3)],
    'mound': [('Broad mound', 0, 0, .92, .9, 1.0, .04), ('Side lump', .33, .26, .4, .42, .55, -.2), ('Front lump', -.3, -.3, .42, .38, .45, .15)],
    'spire': [('Spire', .02, .08, .58, .58, 1.0, -.08), ('Shoulder', -.26, -.18, .5, .5, .5, .1), ('Rear foot', .3, .28, .4, .4, .4, -.12)],
}

VARIANTS = [
    # (id, layout, palette, total height in cells)
    ('rock-crag-low-cobalt', 'crag', 'cobalt', .75), ('rock-crag-mid-deep', 'crag', 'deep', 1.35),
    ('rock-crag-tall-indigo', 'crag', 'indigo', 1.9), ('rock-pair-low-teal', 'pair', 'teal', .65),
    ('rock-pair-mid-cobalt', 'pair', 'cobalt', 1.15), ('rock-pair-mid-indigo', 'pair', 'indigo', 1.25),
    ('rock-mound-low-deep', 'mound', 'deep', .55), ('rock-mound-low-sky', 'mound', 'sky', .7),
    ('rock-mound-mid-teal', 'mound', 'teal', 1.0), ('rock-spire-tall-deep', 'spire', 'deep', 2.2),
    ('rock-spire-mid-sky', 'spire', 'sky', 1.6), ('rock-spire-tall-teal', 'spire', 'teal', 2.0),
]


def normalize(col, height):
    """Fit the cluster to the full 1x1 footprint and the requested height (cells)."""
    pts = [v.co for o in col.objects if o.type == 'MESH' for v in o.data.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
    for o in col.objects:
        if o.type != 'MESH':
            continue
        for v in o.data.vertices:
            v.co.x = (v.co.x - lo[0]) / (hi[0] - lo[0]) * .96 - .48
            v.co.y = (v.co.y - lo[1]) / (hi[1] - lo[1]) * .96 - .48
            v.co.z = (v.co.z - lo[2]) / (hi[2] - lo[2]) * height
        o.data.update()


def build(layout, palette, height):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.name = R.SCENE
    col = bpy.data.collections.new(R.COL_NAME); sc.collection.children.link(col)
    root = bpy.data.objects.new(R.ROOT_NAME, None); col.objects.link(root)
    body, crown, secondary, facet = PALETTES[palette]
    R.MATS = [R.material('Blue stone body', body), R.material('Cyan blue crown', crown),
              R.material('Blue stone secondary', secondary), R.material('Blue stone facet', facet)]
    for i, (name, cx, cy, w, d, rel, angle) in enumerate(LAYOUTS[layout]):
        # The recipe's bevel width keys off absolute height, so build at the
        # production scale and normalise afterwards.
        R.rock(col, root, name, cx, cy, w, d, 2.325 * rel, angle, i)
    normalize(col, height)
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
    return sc, col, root


def capture(sc, col, root, out):
    for direction, angle in R.DIRS.items():
        root.rotation_euler = (0, 0, angle); bpy.context.view_layer.update()
        with R.square_footing(col):
            sc.render.filepath = str(out / f'static-{direction}.png'); bpy.ops.render.render(write_still=True)
    root.rotation_euler = (0, 0, 0)


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(args[0].split(',')) if args else None
records = {}
for vid, layout, palette, height in VARIANTS:
    if only and vid not in only:
        continue
    sc, col, root = build(layout, palette, height)
    out = OUT / vid; out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'project.blend'), compress=True)
    capture(sc, col, root, out)
    records[vid] = {'layout': layout, 'palette': palette, 'height': height}
(OUT / 'variants.json').write_text(json.dumps({'recipe': str(RECIPE.relative_to(HERE.parents[2])), 'frame': [192, 512], 'root': [96, 416],
                                              'nativeScale': 4, 'variants': records}, indent=1) + '\n')
