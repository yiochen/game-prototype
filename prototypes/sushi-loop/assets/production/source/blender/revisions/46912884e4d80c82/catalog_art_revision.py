"""Issue 33 approved prop silhouette revision, native modeling only.

Call ``augment(asset, production_id)`` after the legacy variant wrappers and
before computing capture bounds / baking actions. Replacement assets discard
only the supplied asset's own collection. No scene, camera, render, capture,
publication, or live Blender selection is modified by importing this module.

World coordinates are cells: X right, -Y toward the player, Z up. Grade and
height-based shading are deliberately supplied by the shared capture pipeline.
"""
import importlib.util
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


def _sibling(name, filename):
    spec = importlib.util.spec_from_file_location(name, str(Path(__file__).with_name(filename)))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


P = _sibling('s33_art_revision_props', 'prop_builders.py')
W = _sibling('s33_art_revision_world', 'world_components.py')
REVISION = 'approved-art-rollout-2026-10-19-v1'
SINGLE_FACING = ('chef-blackboard', 'sign-blank')
REPLACEMENT_IDS = (
    'wall-middle', 'wall-inner-corner', 'wall-outer-corner', 'wall-end',
    'plant-angular', 'barrel-wood', 'crate-wood', 'slate-rock',
    'dock-post-rope', 'chef-blackboard', 'sign-blank',
    'garbage-sofa', 'garbage-car', 'garbage-shelving', 'dock-cover',
    'rock-wall-middle', 'rock-wall-edge', 'rock-wall-corner', 'rock-wall-end',
)


def _remove_owned(asset):
    """Release exactly this builder collection, never the rest of the project."""
    collection = asset['collection']
    objects = list(collection.all_objects)
    for obj in objects:
        foreign = [c for c in obj.users_collection if c != collection]
        if foreign:
            raise ValueError('Refusing to replace shared object ' + obj.name)
    for obj in objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def _record(asset, changes):
    asset.setdefault('notes', []).extend(changes)
    asset['root']['art_revision'] = REVISION
    asset['root']['art_revision_changes'] = json.dumps(changes)
    asset['source_script'] = 'catalog_art_revision.py'
    return asset


def _plan(variant, half_width):
    """The exact union of two perpendicular strips, with a square miter.

    Every endpoint is on the same +/- .5 tile boundary as the straight module.
    A diagonal center ring is inappropriate here: it pinches the inside corner
    and gives the coping an apparent offset relative to its straight neighbor.
    """
    h = half_width
    if variant in ('inner-corner', 'outer-corner', 'corner'):
        points = [(-.5, -h), (h, -h), (h, .5), (-h, .5), (-h, h), (-.5, h)]
        if variant == 'outer-corner':
            points = list(reversed([(x, -y) for x, y in points]))
        return points
    end = .34 if variant == 'end' else .5
    return [(-.5, -h), (end, -h), (end, h), (-.5, h)]


def _tier(builder, name, variant, width_z, color):
    rings = [_plan(variant, width) for width, _ in width_z]
    count = len(rings[0])
    vertices = [(x, y, z) for ring, (_, z) in zip(rings, width_z) for x, y in ring]
    faces = [tuple(reversed(range(count))), tuple((len(rings) - 1) * count + i for i in range(count))]
    for ring in range(len(rings) - 1):
        for i in range(count):
            faces.append((ring * count + i, ring * count + (i + 1) % count,
                          (ring + 1) * count + (i + 1) % count, (ring + 1) * count + i))
    return builder.mesh(name, vertices, faces, color)


def _wall(aid):
    b = P.Builder(aid)
    b.height = 1.02
    variant = aid.removeprefix('wall-')
    _tier(b, 'wall_panel', variant, [(.105, .07), (.105, .89)], 'wood_light')
    for i, z in enumerate((.12, .34, .56, .78)):
        _tier(b, 'horizontal_board_' + str(i), variant, [(.115, z), (.115, z + .025)], 'wood')
    _tier(b, 'wood_cap', variant, [(.15, .86), (.15, .935)], 'wood_dark')
    _tier(b, 'blue_coping', variant, [(.18, .93), (.18, .97), (.12, 1.01)], 'blue')
    if variant == 'end':
        b.box('finished_end_post', (.34, 0, .51), (.14, .30, 1.02), 'wood', .015)
    ports = [W.port('W', 'restaurant-wall-wood-blue-v2')]
    if variant != 'end':
        ports.append(W.port({'middle': 'E', 'inner-corner': 'N', 'outer-corner': 'S'}[variant],
                            'restaurant-wall-wood-blue-v2'))
    asset = W.finish(b, ports)
    return _record(asset, ['Square-miter native panel, boards and coping share exact straight/corner end sections. No extra corner table/post masks the joint.'])


def _leaf(b, name, base, tip, width, color):
    """Broad folded angular leaf, rather than a thin cylindrical frond."""
    start, end = Vector(base), Vector(tip)
    delta = end - start
    across = Vector((-delta.y, delta.x, 0))
    if across.length < 1e-6:
        across = Vector((1, 0, 0))
    across.normalize()
    shoulder = start + delta * .52
    ridge = shoulder + Vector((0, 0, width * .18))
    vertices = [tuple(start), tuple(shoulder - across * width * .5), tuple(end),
                tuple(shoulder + across * width * .5), tuple(ridge)]
    obj = b.mesh(name, vertices, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], color)
    return obj


def _plant(aid):
    b = P.Builder(aid)
    b.height = 1.48
    # Broad pot and a deliberately arranged two-tier leafy crown. The wide
    # diagonals are authored to remain within one cell, including sway.
    lower = [(-.27, -.27, .015), (.27, -.27, .015), (.27, .27, .015), (-.27, .27, .015)]
    upper = [(-.38, -.38, .43), (.38, -.38, .43), (.38, .38, .43), (-.38, .38, .43)]
    b.mesh('broad_tapered_pot', lower + upper,
           [(0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], 'wood')
    for x in (-.385, .385):
        b.box('pot_rim_x_' + str(x), (x, 0, .43), (.055, .82, .075), 'wood_light', .01)
    for y in (-.385, .385):
        b.box('pot_rim_y_' + str(y), (0, y, .43), (.82, .055, .075), 'wood_light', .01)
    b.box('soil', (0, 0, .428), (.72, .72, .025), 'wood_dark', .005)
    # The silhouette touches all four cell edges without a separate rubble pad.
    leaves = []
    tips = [(-.47, -.14, .96), (-.32, -.46, 1.03), (.12, -.48, .91),
            (.46, -.27, 1.02), (.48, .13, 1.13), (.23, .47, 1.01),
            (-.20, .48, 1.10), (-.47, .27, 1.07),
            (-.24, -.05, 1.33), (.22, -.12, 1.39), (.15, .25, 1.46), (-.17, .20, 1.40)]
    for i, tip in enumerate(tips):
        base = (0, 0, .48 if i < 8 else .80)
        b.beam('plant_stem_' + str(i), (0, 0, .44),
               (tip[0] * .48, tip[1] * .48, tip[2] - .18), .035, 'green')
        leaves.append(_leaf(b, 'full_crown_leaf_' + str(i), base, tip,
                            .34 if i < 8 else .30, 'leaf_light' if i % 3 == 0 else 'leaf'))
    def sway(t):
        # Moving only the leaf ridge retains the declared XY footprint exactly.
        for i, obj in enumerate(leaves):
            obj.data.vertices[4].co.z = sum(obj.data.vertices[j].co.z for j in (1, 3)) / 2 + (.34 if i < 8 else .30) * .18 + .012 * math.sin(t * math.tau + i * .6)
        for obj in leaves:
            obj.data.update()
    b.motion['idle'] = sway
    asset = b.finish({'idle': {'frames': 24, 'fps': 12, 'loop': True},
                      'static': {'frames': 1, 'fps': 12, 'loop': False, 'static': True}})
    return _record(asset, ['Broad one-cell pot and layered angular foliage span the tile width/depth; leaf-only native sway preserves the XY envelope.'])


def _barrel(aid):
    b = P.Builder(aid)
    b.height = .85
    rings = ((.025, .335), (.18, .398), (.425, .435), (.67, .398), (.81, .335))
    for i in range(14):
        angle = i * math.tau / 14
        half = math.pi / 14 - .006
        vertices = [(radius * math.cos(angle + side * half), radius * math.sin(angle + side * half), z)
                    for z, radius in rings for side in (-1, 1)]
        faces = [(2 * r, 2 * r + 1, 2 * r + 3, 2 * r + 2) for r in range(len(rings) - 1)]
        b.mesh('bulging_stave_' + str(i), vertices, faces, 'wood_light' if i % 3 == 0 else 'wood')
    for z in (.18, .67):
        b.cyl('iron_band_' + str(z), (0, 0, z), .407, .06, 'blue_dark', 14)
    b.cyl('lid', (0, 0, .817), .339, .032, 'wood_end', 14)
    b.cyl('bottom', (0, 0, .026), .335, .025, 'wood_dark', 14)
    for x in (-.17, -.055, .075, .19):
        length = 2 * math.sqrt(max(0, .328 ** 2 - x * x))
        b.box('lid_seam_' + str(x), (x, 0, .835), (.009, length, .006), 'wood', 0)
    return _record(b.finish(), ['Coopered barrel has a .87-cell rounded middle and .67-cell ends, with five real stave rings rather than a cylindrical middle.'])


def _crate(aid):
    b = P.Builder(aid)
    b.height = .925
    P._crate(b, size=.90)
    # The helper's diagonal braces have bevel-width depth, so their complete
    # assembly is slightly deeper than the cube. Author the intended .979-cell
    # world-depth for the whole assembly before Builder freezes its pose map.
    points = [obj.matrix_basis @ vertex.co for obj in b.parts.values() for vertex in obj.data.vertices]
    depth = max(p.y for p in points) - min(p.y for p in points)
    factor = .979 / depth
    for obj in b.parts.values():
        inverse = obj.matrix_basis.inverted()
        for vertex in obj.data.vertices:
            point = obj.matrix_basis @ vertex.co
            point.y *= factor
            vertex.co = inverse @ point
        obj.data.update()
    return _record(b.finish(), ['Crate body, braces and end rails occupy .979 × .979 cells; authored dimensions, no sprite fitting.'])


def _slate(aid):
    b = P.Builder(aid)
    b.height = .48
    outline = [(-.50, -.32), (-.32, -.50), (.35, -.50), (.50, -.30),
               (.50, .35), (.30, .50), (-.35, .50), (-.50, .30)]
    base = [(x, y, 0) for x, y in outline]
    top = [(x * .91, y * .90, z) for (x, y), z in zip(outline, (.29, .34, .32, .37, .42, .48, .43, .36))]
    vertices = base + top + [(-.04, .04, .43)]
    faces = [tuple(reversed(range(8)))]
    for i in range(8):
        faces.extend([(i, (i + 1) % 8, (i + 1) % 8 + 8, i + 8), (i + 8, (i + 1) % 8 + 8, 16)])
    b.mesh('full_cell_slate_mass', vertices, faces, '586777')
    b.box('shallow_top_fissure', (-.06, .08, .438), (.018, .43, .008), '3A495A', .002, rot=(0, .03, -.24))
    return _record(W.finish(b, nonblocking=True, layer='perimeter'), ['Broad uneven slate crown has a one-cell ground envelope and reaches the front edge; no sparse pebble stamp or platform underneath.'])


def _post_rope(aid):
    b = P.Builder(aid)
    b.height = .78
    def half_post(name, x, radius, bottom, top, color):
        angles = [-math.pi / 2 + i * math.pi / 6 for i in range(7)] if x < 0 else [math.pi / 2 + i * math.pi / 6 for i in range(7)]
        ring = [(x + radius * math.cos(a), radius * math.sin(a)) for a in angles]
        vertices = [(vx, vy, bottom) for vx, vy in ring] + [(vx, vy, top) for vx, vy in ring]
        faces = [tuple(reversed(range(7))), tuple(range(7, 14))]
        faces += [(i, (i + 1) % 7, (i + 1) % 7 + 7, i + 7) for i in range(7)]
        b.mesh(name, vertices, faces, color)
    for x in (-.5, .5):
        half_post('half_post_' + str(x), x, .153, 0, .73, 'wood_end')
        for z in (.53, .62):
            half_post('rope_binding_' + str(x) + '_' + str(z), x, .164, z - .022, z + .022, 'cream')
        half_post('post_cap_' + str(x), x, .175, .73, .777, 'wood_light')
    for i in range(12):
        x0 = -.5 + i / 12
        x1 = x0 + 1 / 12
        z0 = .575 - .13 * (1 - (x0 / .5) ** 2)
        z1 = .575 - .13 * (1 - (x1 / .5) ** 2)
        b.beam('thick_sag_rope_' + str(i), (x0, 0, z0), (x1, 0, z1), .072, 'cream')
    # Saw each end flush to its exact tile port plane. The pitched beam's
    # rectangular cap would otherwise project a few hundredths past the post.
    for name, obj in b.parts.items():
        if name.startswith('thick_sag_rope_'):
            inverse = obj.matrix_basis.inverted()
            for vertex in obj.data.vertices:
                point = obj.matrix_basis @ vertex.co
                point.x = max(-.5, min(.5, point.x))
                vertex.co = inverse @ point
            obj.data.update()
    asset = W.finish(b, [W.port('W', 'dock-rope-v2', .575), W.port('E', 'dock-rope-v2', .575)])
    return _record(asset, ['Dock posts are .306-cell thick and rope is .072-cell thick. Native half-post seams reconstruct one full post at tile boundaries.'])


def _front_facing(asset, face_socket):
    asset['directions'] = ['S']
    asset['root']['directions'] = json.dumps(['S'])
    asset['player_facing'] = True
    asset['front_of_tile'] = True
    asset['shared_tile'] = True
    asset['composition_context'] = {'role': 'front-edge-player-facing-overlay', 'allowCoOccupancy': True,
                                    'displayDirection': 'S', 'groundBandY': [-.5, -.27]}
    asset['root']['composition_context'] = json.dumps(asset['composition_context'])
    asset['sockets']['display_face'] = list(face_socket)
    asset['root']['sockets'] = json.dumps(asset['sockets'])
    return asset


def _blackboard(aid):
    b = P.Builder(aid)
    b.height = 1.0
    # This is a counter-height front board, leaving the chef's center free.
    for x in (-.33, .33):
        b.box('front_post_' + str(x), (x, -.355, .49), (.085, .11, .98), 'wood', .012)
        b.box('short_foot_' + str(x), (x, -.375, .035), (.13, .21, .07), 'wood_dark', .01)
    b.box('blank_dynamic_face', (0, -.400, .61), (.62, .055, .57), 'board', .006)
    for x in (-.35, .35):
        b.box('frame_side_' + str(x), (x, -.41, .61), (.075, .10, .72), 'wood_light', .012)
    for z in (.275, .945):
        b.box('frame_end_' + str(z), (0, -.41, z), (.77, .10, .075), 'wood_light', .012)
    b.box('chalk_ledge', (0, -.445, .275), (.77, .10, .055), 'wood', .008)
    b.socket('recipe_face', (0, -.434, .61))
    def selected(t):
        for name, obj in b.parts.items():
            if name.startswith('frame_'):
                obj.location.z += .005 * math.sin(t * math.tau)
    def recipe_change(t):
        for obj in b.parts.values():
            obj.location.z += .012 * math.sin(t * math.pi) * math.sin(t * math.tau)
    b.motion.update(selected=selected, recipe_change=recipe_change)
    clips = {'idle': {'frames': 1, 'fps': 12, 'loop': False, 'static': True},
             'selected': {'frames': 12, 'fps': 12, 'loop': True},
             'recipe_change': {'frames': 12, 'fps': 12, 'loop': False}}
    asset = _front_facing(b.finish(clips), (0, -.434, .61))
    return _record(asset, ['Single player-facing blank blackboard lives in front .23-cell band, sharing one tile with the chef. Recipe content is a later dynamic 2D overlay; no food/chalk tokens are baked.'])


def _sign(aid):
    b = P.Builder(aid)
    b.height = 1.12
    for x in (-.29, .29):
        b.box('rear_post_' + str(x), (x, -.345, .53), (.10, .10, 1.06), 'wood_dark', .012)
    for i in range(3):
        b.box('blank_plank_' + str(i), (0, -.41, .64 + i * .13), (.90, .10, .125), 'wood_light' if i % 2 else 'wood', .012)
    for x in (-.34, .34):
        for z in (.66, .90):
            b.cyl('nail_' + str(x) + '_' + str(z), (x, -.468, z), .014, .012, 'metal_dark', 6, (math.pi / 2, 0, 0))
    b.socket('sign_face', (0, -.472, .77))
    asset = _front_facing(b.finish(), (0, -.472, .77))
    return _record(asset, ['Single player-facing blank sign is on the front tile edge. Its supporting posts leave the central tile free for another object. No title is baked.'])


def _debris(b, entries):
    # Designed, repeatable positions remain inside the declared idle support.
    for i, (x, y, z, width) in enumerate(entries):
        b.box('loose_debris_' + str(i), (x, y, z), (width, width * .64, .07), '776F63', .008, rot=(0, .06 * (i % 3 - 1), .18 * (i % 3 - 1)))


def _sofa(aid):
    b = P.Builder(aid)
    b.footprint = (2, 2)
    b.height = 1.08
    b.box('base', (0, 0, .27), (1.86, 1.08, .25), '65584F', .04)
    for x in (-.75, .75):
        for y in (-.39, .39):
            b.box('foot_' + str(x) + '_' + str(y), (x, y, .10), (.16, .16, .20), '77654F', .015)
    b.box('old_back', (0, .42, .72), (1.90, .29, .71), '927875', .06, rot=(.065, 0, .012))
    for x in (-.84, .84):
        b.box('old_arm_' + str(x), (x, -.04, .58), (.29, 1.16, .52), '927875', .045)
    for i, x in enumerate((-.49, 0, .49)):
        b.box('sagging_seat_' + str(i), (x, -.17, .46), (.47, .79, .20), 'A49185' if i == 1 else '927875', .05, rot=(0, .025 * i, .025 * (i - 1)))
        b.box('old_back_cushion_' + str(i), (x, .19, .80), (.48, .25, .43), '9B827D', .045, rot=(.08, 0, .035 * (i - 1)))
    b.box('torn_fabric', (-.47, -.28, .568), (.19, .15, .012), '65584F', .004, rot=(0, 0, -.23))
    b.box('exposed_stuffing', (-.47, -.28, .574), (.09, .09, .014), 'C0AA87', .008)
    b.beam('exposed_spring', (.31, -.35, .57), (.44, -.22, .65), .025, 'metal_dark')
    _debris(b, [(-.83, -.79, .07, .18), (.74, -.78, .08, .21), (-.65, .80, .06, .16)])
    asset = b.finish(P._clearance_motion(b, list(b.parts.values())))
    return _record(asset, ['Whole faded sofa has a 1.97-cell main body, dull worn upholstery, a torn seat and visible stuffing; its 2×2 support is preserved.'])


def _broken_window(b, name, x0, x1, y):
    """Dark real cabin opening plus jagged retained shards in its frame."""
    sign = 1 if y > 0 else -1
    z0, z1 = .77, 1.115
    # Keep every point exactly on the same sloping side-window surface.
    def pt(x, z, offset=0):
        u = (z - z0) / (z1 - z0)
        return (x, y * (1 - .17 * u) + sign * offset, z)
    b.mesh(name + '_dark_opening', [pt(x0, z0, -.004), pt(x1, z0, -.004), pt(x1 * .78, z1, -.004), pt(x0 * .78, z1, -.004)], [(0, 1, 2, 3)], '263A43')
    center = (x0 + x1) * .5
    left = [pt(x0, z0, .004), pt(x0 + .14, z0 + .025, .004), pt(x0 + .09, z0 + .13, .004),
            pt(x0 + .18, z0 + .21, .004), pt(x0 * .78 + .035, z1 - .055, .004), pt(x0 * .78, z1, .004)]
    right = [pt(x1, z0, .006), pt(x1 * .78, z1, .006), pt(center + .03, z1 - .025, .006),
             pt(center + .10, z1 - .12, .006), pt(x1 - .04, z0 + .11, .006), pt(x1 - .11, z0 + .025, .006)]
    b.mesh(name + '_jagged_left_glass', left, [tuple(range(len(left)))], '698E95')
    b.mesh(name + '_jagged_right_glass', right, [tuple(range(len(right)))], '8BA9AA')
    for i, (a, c) in enumerate(zip([pt(x0, z0, .012), pt(x1, z0, .012), pt(x1 * .78, z1, .012), pt(x0 * .78, z1, .012)],
                                  [pt(x1, z0, .012), pt(x1 * .78, z1, .012), pt(x0 * .78, z1, .012), pt(x0, z0, .012)])):
        b.beam(name + '_metal_frame_' + str(i), a, c, .027, '60747A')


def _car(aid):
    b = P.Builder(aid)
    b.footprint = (3, 2)
    b.height = 1.32
    b.box('chassis', (0, 0, .28), (2.75, 1.40, .24), '48535A', .055)
    b.box('dull_dented_body', (0, 0, .52), (2.80, 1.47, .45), '6F858C', .07)
    b.box('dark_cabin_interior', (.02, 0, .77), (1.35, 1.17, .15), '263A43', .025)
    # Separate rear/front body panels leave the side openings genuinely dark.
    b.mesh('cabin_front', [(-.72, -.72, .70), (-.48, -.58, 1.17), (-.48, .58, 1.17), (-.72, .72, .70)], [(0, 1, 2, 3)], '5C707A')
    b.mesh('cabin_back', [(.87, -.72, .70), (.55, -.58, 1.17), (.55, .58, 1.17), (.87, .72, .70)], [(0, 1, 2, 3)], '566B75')
    for y in (-.728, .728):
        _broken_window(b, 'broken_side_window_' + str(y) + '_rear', -.55, -.04, y)
        _broken_window(b, 'broken_side_window_' + str(y) + '_front', .06, .68, y)
        b.beam('side_center_pillar_' + str(y), (0, y, .72), (0, y * .83, 1.17), .075, '6F858C')
        b.box('old_handle_' + str(y), (.30, y, .64), (.20, .028, .04), '7A8787', .008)
        b.box('rust_sill_' + str(y), (-.74, y, .44), (.46, .015, .08), '8A6F56', .005)
    b.box('dented_roof', (.025, 0, 1.19), (1.13, 1.22, .11), '849399', .02, rot=(.012, .025, .01))
    for x in (-.94, .94):
        for y in (-.75, .75):
            b.cyl('old_tire_' + str(x) + '_' + str(y), (x, y, .28), .29, .21, '3F484B', 12, (math.pi / 2, 0, 0))
            b.cyl('rust_hub_' + str(x) + '_' + str(y), (x, y + math.copysign(.113, y), .28), .13, .025, '7F7669', 8, (math.pi / 2, 0, 0))
    for y in (-.45, .45):
        b.box('cloudy_headlamp_' + str(y), (-1.412, y, .58), (.026, .24, .14), 'B9B9A0', .012)
    b.box('bent_front_bumper', (-1.42, 0, .31), (.12, 1.38, .11), '6E7A79', .014, rot=(0, .055, -.035))
    b.box('bent_broken_hood', (-1.08, 0, .79), (.60, 1.34, .075), '849399', .02, rot=(0, -.12, .04))
    b.box('loose_number_plate', (1.29, -.45, .15), (.28, .26, .035), '8C9591', .006, rot=(0, .30, .18))
    _debris(b, [(-1.29, -.77, .08, .18), (1.30, .77, .07, .18), (.86, -.84, .08, .17)])
    asset = b.finish(P._clearance_motion(b, list(b.parts.values())))
    return _record(asset, ['Muted blue-gray wrecked car has jagged broken glass around real dark cabin openings, rust, a bent hood/bumper, and a broad 3×2 body.'])


def _shelf(aid):
    b = P.Builder(aid)
    b.footprint = (2, 2)
    b.height = 1.68
    for x in (-.88, .88):
        for y in (-.36, .36):
            b.beam('old_upright_' + str(x) + '_' + str(y), (x - .03, y, .02), (x + .03, y, 1.58), .105, '6C5945')
    for i, z in enumerate((.18, .69, 1.20, 1.57)):
        b.box('warped_shelf_' + str(i), (0, 0, z), (1.97, .95, .095), '927650', .015, rot=(0, .02 * (-1 if i % 2 else 1), 0))
    b.beam('back_brace', (-.84, .42, .13), (.89, .42, 1.54), .065, 'A68B5E')
    for i, (x, z) in enumerate([(-.60, .38), (-.03, .38), (.57, .38), (-.48, .90), (.16, .90), (.63, 1.40)]):
        b.box('stored_box_' + str(i), (x, -.02, z), (.38, .48, .31), 'A38D67' if i % 2 else 'BAA57A', .015, rot=(0, .035 * (i % 2), .06 * (i % 3 - 1)))
    b.box('fallen_board', (0, -.72, .12), (1.76, .30, .075), 'A38D67', .012, rot=(0, .08, .10))
    _debris(b, [(-.81, -.84, .06, .16), (.74, -.79, .07, .17)])
    asset = b.finish(P._clearance_motion(b, list(b.parts.values())))
    return _record(asset, ['Collapsed shelf spans the full two-cell declared width with native shelves/uprights and broad fallen boards.'])


def _rock_wall(aid):
    b = P.Builder(aid)
    b.height = 1.17
    variant = aid.removeprefix('rock-wall-')
    # End modules finish at +.5 as well: full-cell depth/width is never traded
    # for an empty front. Endpoint rings remain identical at matching ports.
    path = W._path('corner' if variant == 'corner' else 'middle')
    profile = [(-.5, 0), (.5, 0), (.5, .67), (.45, 1.04), (.31, 1.15),
               (-.31, 1.15), (-.45, 1.04), (-.5, .67)]
    W._loft(b, 'full_width_continuous_crag', path, profile, 'rock', .018)
    # Low squared shoulder prevents a broad rock face hovering behind a strip
    # of empty front-floor. It stays below the shared .67-cell seam tier.
    _tier(b, 'broad_contact_shoulder', 'middle', [(.5, .001), (.5, .10), (.44, .21)], 'rock_dark')
    if variant != 'corner':
        for i, (x, y, z, w, h) in enumerate([(-.21, -.505, .40, .28, .27), (.18, -.505, .70, .25, .30), (.03, .505, .33, .35, .22)]):
            b.box('broad_strata_facet_' + str(i), (x, y, z), (w, .012, h), 'rock_dark' if i % 2 else 'rock_light', .008)
    if variant in ('edge', 'end'):
        b.box('finished_end_strata', (.505, 0, .47), (.012, .83, .035), 'rock_dark', .003)
    ports = [W.port('W', 'rock-wall-full-cell-v2')]
    if variant != 'end':
        ports.append(W.port('N' if variant == 'corner' else 'E', 'rock-wall-full-cell-v2'))
    return _record(W.finish(b, ports), ['Cobalt canyon has a one-cell-wide/deep contact mass and a broad uneven crown. All wall-family port sections share the same native profile.'])


def _dock_cover(aid):
    b = P.Builder(aid)
    b.footprint = (3, 3)
    b.height = 1.87
    cloth = []
    seams = []
    # Large, quiet cloth panels, an obvious ridge/hem, and tied front corners
    # clarify that this is an overhead weather tarp rather than a floor tile.
    xs = [-1.45, -.72, 0, .72, 1.45]
    ys = [-1.26, -.63, 0, .63, 1.26]
    for iy in range(4):
        for ix in range(4):
            if iy == 0 and ix == 1:
                continue  # intentional peek opening, not a missing texture
            x0, x1 = xs[ix:ix + 2]
            y0, y1 = ys[iy:iy + 2]
            z0, z1 = 1.82 - .52 * abs(y0) / 1.26, 1.82 - .52 * abs(y1) / 1.26
            color = ('C9AE79', 'DBCA9D', '6A9C96', 'C9AE79')[(ix + 2 * iy) % 4]
            cloth.append(b.mesh('weather_tarp_panel_' + str(ix) + '_' + str(iy), [(x0, y0, z0), (x1, y0, z0), (x1, y1, z1), (x0, y1, z1)], [(0, 1, 2, 3)], color))
            seams.append(b.beam('thick_stitched_seam_' + str(ix) + '_' + str(iy), (x0, y0, z0 + .012), (x1, y0, z0 + .012), .025, '806D4F'))
    for y in (-1.26, 1.26):
        # Separate front hem sections retain the opening.
        spans = [(-1.45, -.72), (0, 1.45)] if y < 0 else [(-1.45, 1.45)]
        for i, (x0, x1) in enumerate(spans):
            seams.append(b.beam('rolled_cloth_hem_' + str(y) + '_' + str(i), (x0, y, 1.30), (x1, y, 1.30), .055, 'A58A5C'))
    b.beam('permanent_ridge_support', (-1.45, 0, 1.80), (1.45, 0, 1.80), .065, 'wood_dark')
    for x in (-1.45, 1.45):
        for y in (-1.26, 1.26):
            b.beam('corner_tie_rope_' + str(x) + '_' + str(y), (x, y, .24), (x, y, 1.30), .047, 'cream')
            b.cyl('tie_knot_' + str(x) + '_' + str(y), (x, y, 1.28), .049, .075, 'cream', 8)
    folding = cloth + seams
    def covered(t):
        for i, obj in enumerate(cloth):
            obj.location.z += .008 * math.sin(math.tau * t + i * .37)
    def uncover(t):
        u = t * t * (3 - 2 * t)
        for obj in folding:
            obj.scale.y *= 1 - .96 * u
            obj.location.y += 1.24 * u
            obj.location.z += .10 * math.sin(math.pi * u)
    b.motion.update(covered=covered, uncover=uncover)
    b.socket('dock_floor', (0, 0, 0))
    context = {'role': 'dock-overhead-weather-tarp', 'layoutCells': [3, 3], 'compositionOffset': [0, 0, .23],
               'workshopRoot': [.78, .35, .23], 'submarineRoot': [-.70, -.42, .23],
               'explanation': 'Patchwork weather tarp covering the docked submarine and workshop; folds to the back when the dock is uncovered.'}
    asset = W.finish(b, clips={'covered': {'frames': 24, 'fps': 12, 'loop': True}, 'uncover': {'frames': 24, 'fps': 12, 'loop': False}},
                     nonblocking=True, layer='overhead', context=context)
    return _record(asset, ['Recognizable 3×3 overhead dock weather tarp: stitched patchwork cloth, ridge, rolled hems, ties and an intentional peek opening. Preview over its dock/submarine/workshop composition; never stamp it as a floor.'])


def _belt(asset, aid):
    """Thicken stationary structure; do not touch moving deck / UV / phase."""
    if asset['root'].get('belt_structure_revision') == REVISION:
        return asset
    parts = asset['parts']
    corner = 'connected_turn_deck' in parts
    changed = []
    for name, obj in parts.items():
        if obj.type != 'MESH':
            continue
        if corner and name.startswith('stationary_') and name.endswith('_rail'):
            inner = 'inside' in name
            old_lo, old_hi = (.065, .15) if inner else (.85, .935)
            new_lo, new_hi = (.02, .15) if inner else (.85, .98)
            for vertex in obj.data.vertices:
                dx, dy = vertex.co.x - .5, vertex.co.y - .5
                radius = math.hypot(dx, dy)
                new_radius = new_lo + (radius - old_lo) / (old_hi - old_lo) * (new_hi - new_lo)
                vertex.co.x = .5 + dx / radius * new_radius
                vertex.co.y = .5 + dy / radius * new_radius
                vertex.co.z = .505 + (vertex.co.z - .54) / .135 * .19
            changed.append(name)
        elif not corner and name.startswith('stationary_rail_'):
            for vertex in obj.data.vertices:
                vertex.co.x *= .13 / .085
                vertex.co.z *= .19 / .135
            obj.location.x = math.copysign(.415, obj.location.x)
            obj.location.z = .600
            changed.append(name)
        elif name.startswith('wood_leg_'):
            width = max(vertex.co.x for vertex in obj.data.vertices) - min(vertex.co.x for vertex in obj.data.vertices)
            depth = max(vertex.co.y for vertex in obj.data.vertices) - min(vertex.co.y for vertex in obj.data.vertices)
            for vertex in obj.data.vertices:
                vertex.co.x *= .16 / width
                vertex.co.y *= .16 / depth
            changed.append(name)
        elif name in ('start_cap', 'end_cap'):
            for vertex in obj.data.vertices:
                vertex.co.x *= .96 / .87
                vertex.co.z *= 1.18
            changed.append(name)
        if name in changed:
            obj.data.update()
    if corner:
        layout = dict(asset.get('supportLayout', {}))
        layout['version'] = 2
        layout['legs'] = [dict(leg, size=[.16, .16, .50]) for leg in layout.get('legs', [])]
        asset['supportLayout'] = layout
        asset['root']['support_layout'] = json.dumps(layout, sort_keys=True)
    asset['root']['belt_structure_revision'] = REVISION
    asset['root']['belt_structure_dimensions'] = json.dumps({'railWidth': .13, 'railHeight': .19, 'legSection': [.16, .16], 'deckWidth': .70, 'deckHeight': .64})
    asset['height'] = max(asset['height'], .695)
    return _record(asset, ['Stationary red rails are .13 cells wide × .19 high; legs are .16 × .16. Corner legs remain under the curve. Deck mesh, UVs, phase, speed, ports and orientation are untouched.'])


BUILDERS = {'plant-angular': _plant, 'barrel-wood': _barrel, 'crate-wood': _crate,
            'slate-rock': _slate, 'dock-post-rope': _post_rope,
            'chef-blackboard': _blackboard, 'sign-blank': _sign,
            'garbage-sofa': _sofa, 'garbage-car': _car, 'garbage-shelving': _shelf,
            'dock-cover': _dock_cover}


def augment(asset, aid):
    """Return the revised asset, retaining the same production ID and ground root."""
    if asset['root'].get('art_revision') == REVISION:
        return asset
    if aid.startswith('belt-'):
        return _belt(asset, aid)
    builder = _wall if aid.startswith('wall-') else _rock_wall if aid.startswith('rock-wall-') else BUILDERS.get(aid)
    if builder is None:
        return asset
    _remove_owned(asset)
    revised = builder(aid)
    if aid in ('garbage-sofa', 'garbage-car', 'garbage-shelving'):
        revised['variants'] = {'normal': {'clips': ['idle']}, 'highlighted': {'clips': ['highlighted']}, 'clearance': {'clips': ['clearance']}}
        revised['root']['variants'] = json.dumps(revised['variants'])
    return revised


def repair_existing_rollout(asset, aid):
    """Bring an already-created, not-yet-baked rollout model to final geometry.

    This is an explicit bridge for a Blender session which imported the recipe
    before its final support calibration. A clean build does not need it. The
    operation is idempotent and never edits conveyor decks, UVs or phase nodes.
    """
    if aid.startswith('belt-') and 'connected_turn_deck' in asset['parts']:
        supports = _sibling('s33_art_revision_support_calibration', 'catalog_corner_supports.py')
        recipe = supports.geometry()
        for leg in recipe['legs']:
            obj = asset['parts'][leg['part']]
            width = max(v.co.x for v in obj.data.vertices) - min(v.co.x for v in obj.data.vertices)
            depth = max(v.co.y for v in obj.data.vertices) - min(v.co.y for v in obj.data.vertices)
            for vertex in obj.data.vertices:
                vertex.co.x *= .16 / width
                vertex.co.y *= .16 / depth
            obj.location = leg['center']
            obj.rotation_euler = (0, 0, leg['rotationZ'])
            obj.data.update()
        supports.record(asset, recipe)
    elif aid == 'crate-wood':
        parts = [obj for obj in asset['parts'].values() if obj.type == 'MESH']
        points = [obj.matrix_basis @ vertex.co for obj in parts for vertex in obj.data.vertices]
        center = (max(p.y for p in points) + min(p.y for p in points)) / 2
        factor = .979 / (max(p.y for p in points) - min(p.y for p in points))
        for obj in parts:
            inverse = obj.matrix_basis.inverted()
            for vertex in obj.data.vertices:
                point = obj.matrix_basis @ vertex.co
                point.y = center + (point.y - center) * factor
                vertex.co = inverse @ point
            obj.data.update()
    elif aid == 'plant-angular':
        asset['clips'].setdefault('static', {'frames': 1, 'fps': 12, 'loop': False, 'static': True})
        asset['root']['animation_recipes'] = json.dumps(asset['clips'])
    elif aid == 'dock-cover':
        for name, obj in asset['parts'].items():
            if name.startswith('tie_knot_'):
                radius = max(abs(v.co.x) for v in obj.data.vertices)
                if radius > 1e-8:
                    for vertex in obj.data.vertices:
                        vertex.co.x *= .049 / radius
                        vertex.co.y *= .049 / radius
                    obj.data.update()
    elif aid == 'dock-post-rope':
        for name, obj in asset['parts'].items():
            if name.startswith('thick_sag_rope_'):
                inverse = obj.matrix_basis.inverted()
                for vertex in obj.data.vertices:
                    point = obj.matrix_basis @ vertex.co
                    point.x = max(-.5, min(.5, point.x))
                    vertex.co = inverse @ point
                obj.data.update()
    return asset
