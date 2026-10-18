"""Shared native support recipe for fresh and existing corner conveyor models.

Only the stationary wooden slab and four legs change. The deck, shader, UVs,
rails, ports, orientation empty, height, ground root and capture frame are not
edited. Geometry is expressed in the canonical N-to-E orientation-parent frame.
"""

import json
import math


LEG_KEYS = tuple('wood_leg_' + str((x, y))
                 for x in (-.28, .28) for y in (-.28, .28))
SLAB_KEY = 'lower_wood_frame'
SUPPORT_VERSION = 1


def geometry():
    """Return the one deterministic, JSON-safe native support mesh recipe."""
    center = (.5, .5)
    inner, outer, bottom, top, segments = .13, .87, .42, .52, 48
    vertices = []
    for station in range(segments + 1):
        angle = math.pi + station / segments * math.pi / 2
        for radius, z in ((inner, bottom), (outer, bottom),
                          (outer, top), (inner, top)):
            vertices.append((center[0] + radius * math.cos(angle),
                             center[1] + radius * math.sin(angle), z))
    faces = []
    for station in range(segments):
        for side in range(4):
            faces.append((station * 4 + side,
                          (station + 1) * 4 + side,
                          (station + 1) * 4 + (side + 1) % 4,
                          station * 4 + (side + 1) % 4))
    faces.extend(((0, 1, 2, 3),
                  tuple(segments * 4 + index for index in (3, 2, 1, 0))))
    legs = []
    for name, (q, radius) in zip(LEG_KEYS, (
            (.18, .24), (.18, .76), (.82, .24), (.82, .76))):
        angle = math.pi + q * math.pi / 2
        legs.append({'part': name, 'arcFraction': q, 'radius': radius,
                     'center': [center[0] + radius * math.cos(angle),
                                center[1] + radius * math.sin(angle), .25],
                     'size': [.10, .10, .50], 'rotationZ': angle})
    return {'vertices': vertices, 'faces': faces, 'legs': legs,
            'layout': {
                'version': SUPPORT_VERSION,
                'kind': 'quarter-annular-wood-support',
                'coordinateFrame': 'canonical N-to-E orientation parent',
                'slab': {'part': SLAB_KEY, 'centerXY': list(center),
                         'innerRadius': inner, 'outerRadius': outer,
                         'angleStart': math.pi, 'angleEnd': math.pi * 1.5,
                         'segments': segments, 'bottomZ': bottom, 'topZ': top,
                         'bevelWidth': .008,
                         'boundsXY': [[-.37, .5], [-.37, .5]]},
                'legs': legs,
                'unchanged': ['deck-path', 'deck-UV', 'deck-material',
                              'shader-phase', 'rails', 'flow-ports',
                              'orientation-parent', 'ground-root',
                              'asset-height', 'capture-frame']}}


def _slab_bevel(obj):
    bevel = next((modifier for modifier in obj.modifiers
                  if modifier.type == 'BEVEL' and
                  modifier.name == 'Small flat bevel'), None)
    if bevel is None:
        bevel = obj.modifiers.new('Small flat bevel', 'BEVEL')
    bevel.width = .008
    bevel.segments = 1
    # Keep the continuous faceted curve; bevel its top/bottom and end edges,
    # rather than treating every 1.875-degree wall join as a separate block.
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = .45


def _record(asset, recipe):
    asset['supportLayout'] = recipe['layout']
    asset['root']['support_layout'] = json.dumps(recipe['layout'],
                                                sort_keys=True)
    return asset


def add(builder, wood, dark_wood):
    """Fresh-build path: add support parts through the existing FB builder."""
    recipe = geometry()
    slab = builder.mesh(SLAB_KEY, recipe['vertices'], recipe['faces'], wood)
    _slab_bevel(slab)
    for leg in recipe['legs']:
        obj = builder.box(leg['part'], leg['center'], leg['size'], dark_wood,
                          .008)
        obj.rotation_euler.z = leg['rotationZ']
    return recipe


def record(asset, recipe=None):
    """Expose the same exact layout on an asset returned by FB.finish()."""
    return _record(asset, recipe or geometry())


def augment(asset):
    """Replace only existing corner support geometry/transforms in-place.

    Object identities, names, parents, materials and the parts dictionary remain
    intact. Root should deliberately rebake that corner's native actions after
    applying this helper, because four static leg transforms have changed.
    """
    parts = asset['parts']
    if 'connected_turn_deck' not in parts:
        raise ValueError('Corner support augmentation requires a turn deck')
    required = (SLAB_KEY,) + LEG_KEYS
    for key in required:
        obj = parts.get(key)
        if obj is None or obj.type != 'MESH':
            raise ValueError('Missing native corner support mesh: ' + key)
        if obj.data.shape_keys is not None:
            raise ValueError('Unexpected animated support shape keys: ' + key)
    recipe = geometry()
    slab = parts[SLAB_KEY]
    slab.data.clear_geometry()
    slab.data.from_pydata(recipe['vertices'], [], recipe['faces'])
    slab.data.update()
    slab.location = (0., 0., 0.)
    slab.rotation_euler = (0., 0., 0.)
    slab.scale = (1., 1., 1.)
    _slab_bevel(slab)
    for leg in recipe['legs']:
        obj = parts[leg['part']]
        obj.location = leg['center']
        obj.rotation_euler = (0., 0., leg['rotationZ'])
        obj.scale = (1., 1., 1.)
    return _record(asset, recipe)
