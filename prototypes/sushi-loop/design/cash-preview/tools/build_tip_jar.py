"""#61 tip jar on a pedestal: native Blender model in the approved world-prop style.

Run (the library project is opened read-only; nothing is saved over it):
  blender --background prototypes/sushi-loop/assets/production/source/blender/sushi-loop-world-library.blend \
    --python prototypes/sushi-loop/design/cash-preview/tools/build_tip_jar.py -- --out <dir>

Uses the production prop builder (prop_builders.py), the approved Faceted finish and
lower-height ramp (catalog_style.py) and the production capture camera
(capture_runtime.configure_camera: square grid, 70% height, 2x of a 128 px cell).
Canonical axes: X = x, depth = -Y, height = Z; one unit per cell; root at the tile centre.
One south view only (the jar never rotates). Five fill states share one model:
note objects are shown up to each state's level.
Writes <dir>/jar-<state>.png, <dir>/camera.json and <dir>/tip-jar.blend (jar data only).
"""
import bpy
import bmesh
import importlib.util
import json
import math
import random
import sys
from pathlib import Path

BLENDER_SOURCE = Path(__file__).resolve().parents[3] / 'assets/production/source/blender'
ASSET_ID = 'tip-jar'
FRAME, ANCHOR, SCALE = (192, 384), (96, 288), 2      # same registration as lantern-gold
JAR_BASE, JAR_TOP, JAR_R = .5, 1.3, .26
STATES = {'empty': None, 'quarter': .6, 'half': .82, 'most': 1.1, 'full': 'overflow'}


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, BLENDER_SOURCE / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def output_dir():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out = Path(argv[argv.index('--out') + 1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    return out


def lathe(b, name, profile, color, segments=32, cap_bottom=True):
    """Revolve (radius, z) points around Z; open at the top."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for a in (i * math.tau / segments for i in range(segments))])
    for lower, upper in zip(rings, rings[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new((lower[i], lower[j], upper[j], upper[i]))
    if cap_bottom:
        bm.faces.new(list(reversed(rings[0])))
    me = bpy.data.meshes.new(ASSET_ID + '__' + name)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new(name, me)
    b.collection.objects.link(obj)
    obj.parent = b.root
    obj.name = ASSET_ID + '__' + name
    obj.data.materials.append(color)
    b.parts[name] = obj
    return obj


def glass(props, name, hex_color, alpha):
    m = props.mat(name, hex_color)
    shader = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    shader.inputs['Alpha'].default_value = alpha
    if hasattr(m, 'surface_render_method'):
        m.surface_render_method = 'BLENDED'
    m.use_backface_culling = False
    return m


def note_mesh(props):
    """One banknote: green slab with a pale printed frame on both faces."""
    w, d, t, f = .15, .075, .012, .008
    verts, faces, mats = [], [], []

    def quad(a, b, c, e, material):
        base = len(verts)
        verts.extend([a, b, c, e])
        faces.append((base, base + 1, base + 2, base + 3))
        mats.append(material)

    hx, hy, hz = w / 2, d / 2, t / 2
    corners = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    for z, flip in ((hz, False), (-hz, True)):
        ring = [(x, y, z) for x, y in corners]
        quad(*(reversed(ring) if flip else ring), 0)
    for i in range(4):
        (x0, y0), (x1, y1) = corners[i], corners[(i + 1) % 4]
        quad((x0, y0, -hz), (x1, y1, -hz), (x1, y1, hz), (x0, y0, hz), 0)
    # Printed frame: four thin strips floating just off each face.
    ix, iy = hx - .018, hy - .016
    for z in (hz + .0012, -hz - .0012):
        for (x0, y0, x1, y1) in ((-ix, -iy, ix, -iy + f), (-ix, iy - f, ix, iy), (-ix, -iy, -ix + f, iy), (ix - f, -iy, ix, iy)):
            ring = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
            quad(*(ring if z > 0 else list(reversed(ring))), 1)
        s = .02
        ring = [(-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z)]
        quad(*(ring if z > 0 else list(reversed(ring))), 1)
    me = bpy.data.meshes.new(ASSET_ID + '__note')
    me.from_pydata(verts, [], faces)
    me.materials.append(props.mat('cash_green', '35A35C'))
    me.materials.append(props.mat('cash_print', '9EDCA4'))
    for poly, material in zip(me.polygons, mats):
        poly.material_index = material
    me.update()
    return me


def build(props):
    b = props.Builder(ASSET_ID)
    b.height = 1.38
    # Pedestal: square, matte maple with a darker plinth, true-shape top and front faces.
    b.box('plinth', (0, 0, .035), (.76, .76, .07), 'wood_dark', .015)
    b.box('body', (0, 0, .26), (.64, .64, .4), 'wood', .02)
    b.box('cap', (0, 0, .47), (.74, .74, .06), 'wood_light', .015)
    b.box('plaque', (0, -.325, .27), (.28, .02, .18), 'cream', .006)
    b.box('plaque_note', (0, -.337, .27), (.18, .008, .09), props.PALETTE['green'], .002)
    # Glass jar (open mouth) with a rolled rim, twine and a paper tag.
    glass_body = glass(props, 'jar_glass', 'D7F1FA', .26)
    glass_rim = props.mat('jar_rim', 'BFE2EE')
    lathe(b, 'glass', [(JAR_R - .02, JAR_BASE), (JAR_R, JAR_BASE + .03), (JAR_R, JAR_TOP - .12), (JAR_R - .02, JAR_TOP - .07), (JAR_R - .05, JAR_TOP - .04), (JAR_R - .055, JAR_TOP)], glass_body)
    lathe(b, 'rim', [(JAR_R - .057, JAR_TOP - .01), (JAR_R - .035, JAR_TOP), (JAR_R - .035, JAR_TOP + .03), (JAR_R - .057, JAR_TOP + .035)], glass_rim, cap_bottom=False)
    highlight = glass(props, 'jar_highlight', 'FFFFFF', .55)
    for name, angle, z, height, width in (('shine_a', -2.25, .86, .5, .05), ('shine_b', -2.0, .76, .18, .024), ('shine_c', -.75, .86, .4, .022)):
        strip = b.box(name, ((JAR_R + .005) * math.cos(angle), (JAR_R + .005) * math.sin(angle), z), (width, .006, height), 'white', 0)
        strip.data.materials.clear()
        strip.data.materials.append(highlight)
        strip.rotation_euler = (0, 0, angle + math.pi / 2)
    b.box('tag_string', (.1, -.205, 1.16), (.008, .008, .1), 'wood', 0, (0, .5, 0))
    b.box('tag', (.13, -.268, 1.04), (.12, .01, .13), 'chalk', .006, (0, .18, 0))
    b.box('tag_note', (.13, -.275, 1.04), (.08, .006, .04), props.PALETTE['green'], .001, (0, .18, 0))
    # Cash: packed crumpled notes in layers, then overflow notes standing out of the mouth.
    me = note_mesh(props)
    random_state = random.Random(61)
    notes = []
    z = JAR_BASE + .015
    while z < JAR_TOP - .04:
        for _ in range(9):
            r = (JAR_R - .1) * math.sqrt(random_state.random())
            a = random_state.random() * math.tau
            obj = bpy.data.objects.new(ASSET_ID + '__note_%03d' % len(notes), me)
            b.collection.objects.link(obj)
            obj.parent = b.root
            obj.location = (r * math.cos(a), r * math.sin(a), z + random_state.random() * .015)
            obj.rotation_euler = (random_state.uniform(-.6, .6), random_state.uniform(-.6, .6), random_state.random() * math.tau)
            notes.append(obj)
        z += .022
    overflow = []
    for i in range(7):
        a = i * math.tau / 7 + random_state.random() * .4
        obj = bpy.data.objects.new(ASSET_ID + '__overflow_%d' % i, me)
        b.collection.objects.link(obj)
        obj.parent = b.root
        obj.location = (.07 * math.cos(a), .07 * math.sin(a), JAR_TOP + .03 + random_state.random() * .04)
        obj.rotation_euler = (random_state.uniform(.7, 1.1) * (1 if i % 2 else -1), random_state.uniform(-.4, .4), a + math.pi / 2)
        overflow.append(obj)
    asset = b.finish()
    asset['notes_objects'], asset['overflow_objects'] = notes, overflow
    return asset


def show_state(asset, level):
    for obj in asset['notes_objects']:
        obj.hide_render = level is None or (level != 'overflow' and obj.location.z > level)
    for obj in asset['overflow_objects']:
        obj.hide_render = level != 'overflow'


def main():
    out = output_dir()
    worker = load('tipjar_capture_worker', 'capture_worker.py')
    props = load('tipjar_prop_builders', 'prop_builders.py')
    style = load('tipjar_catalog_style', 'catalog_style.py')
    runtime = load('tipjar_capture_runtime', 'capture_runtime.py')
    scene = worker.native_scene()
    with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0]):
        asset = build(props)
        style.apply(asset, ASSET_ID)
        for name in ('jar_glass', 'jar_highlight'):
            for m in bpy.data.materials:
                if m.name.endswith(name) and hasattr(m, 'surface_render_method'):
                    m.surface_render_method = 'BLENDED'
        worker.show_only(scene, asset)
        runtime.scene = lambda: scene
        runtime.SCENE_NAME = scene.name
        camera = runtime.configure_camera('top-down-oblique-square-grid', FRAME, ANCHOR, SCALE)
        scene.eevee.taa_render_samples = 64
        for state, level in STATES.items():
            show_state(asset, level)
            scene.render.filepath = str(out / ('jar-%s.png' % state))
            bpy.ops.render.render(write_still=True, scene=scene.name)
        (out / 'camera.json').write_text(json.dumps({'assetId': ASSET_ID, 'frame': FRAME, 'anchor': ANCHOR, 'scale': SCALE, 'cellSize': 128, 'projection': 'top-down-oblique-square-grid', 'axes': {'x': 'X', 'depth': '-Y', 'height': 'Z'}, 'direction': 'S', 'states': {k: v for k, v in STATES.items()}, 'camera': camera}, indent=1, default=str))
        blocks = {asset['collection'], *asset['collection'].all_objects}
        blocks |= {o.data for o in asset['collection'].all_objects if o.data}
        blocks |= {s.material for o in asset['collection'].all_objects if o.type == 'MESH' for s in o.material_slots if s.material}
        bpy.data.libraries.write(str(out / 'tip-jar.blend'), blocks, fake_user=True)
    print('TIPJAR_DONE', out)


main()
