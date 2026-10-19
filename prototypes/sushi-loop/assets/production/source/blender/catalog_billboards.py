"""Native camera-facing visual pivots for the five issue 33 catalog effects.

Call ``augment(asset)`` after the effect's native geometry/recipe wrappers have
been assembled. The logical ground root still takes S/E/N/W world rotations;
its new visual child cancels only that root's Z rotation using a native driver.
Existing mesh transforms, animation actions, pose/reset closures and clip names
are unchanged. No rendering, scene deletion or publication happens here.
"""

import bpy
from mathutils import Matrix


BILLBOARD_IDS = frozenset((
    'bubble-preference', 'bubble-happy', 'bubble-puzzled', 'bubble-panic',
    'coin-pop',
))
PART_KEY = 'billboard_visual_root'


def augment(asset):
    """Return ``asset`` with one native counter-rotation visual pivot.

    Invoke only for ``BILLBOARD_IDS``. If production_id is already present it is
    checked; fresh builder results can be augmented before that ID is attached.
    Repeated calls reuse the existing pivot. Children preserve both their local
    transform basis and parent inverse, including any existing action channels.
    """
    root = asset['root']
    asset_id = root.get('production_id')
    if asset_id and asset_id not in BILLBOARD_IDS:
        raise ValueError('Camera-facing catalog effect not allowed: ' + asset_id)

    existing = asset.get(PART_KEY)
    if existing is not None:
        if existing.parent != root:
            raise ValueError('Existing billboard pivot has an unexpected parent')
        return asset

    if PART_KEY in asset['parts']:
        raise ValueError('Billboard pivot part key is already occupied')

    # Capture direct children before linking the new pivot so it cannot parent
    # itself. The parent transform is identical before the driver is installed.
    children = tuple(root.children)
    pivot = bpy.data.objects.new(root.name + '__camera_facing_visual', None)
    asset['collection'].objects.link(pivot)
    pivot.parent = root
    pivot.matrix_parent_inverse = Matrix.Identity(4)
    pivot.matrix_basis = Matrix.Identity(4)
    pivot.rotation_mode = 'XYZ'
    pivot.empty_display_type = 'PLAIN_AXES'
    pivot.empty_display_size = .12
    pivot['role'] = 'camera-facing visual root'

    for child in children:
        local_basis = child.matrix_basis.copy()
        parent_inverse = child.matrix_parent_inverse.copy()
        child.parent = pivot
        child.matrix_parent_inverse = parent_inverse
        child.matrix_basis = local_basis

    curve = pivot.driver_add('rotation_euler', 2)
    driver = curve.driver
    driver.type = 'SCRIPTED'
    variable = driver.variables.new()
    variable.name = 'host_z'
    variable.type = 'SINGLE_PROP'
    variable.targets[0].id = root
    variable.targets[0].data_path = 'rotation_euler[2]'
    driver.expression = '-host_z'

    # Builder pose/reset closures retain their original parts dictionaries.
    # Add the native pivot only to the outward-facing copy.
    asset['parts'] = dict(asset['parts'])
    asset['parts'][PART_KEY] = pivot
    asset[PART_KEY] = pivot
    asset['facingPolicy'] = 'camera-facing'
    root['facingPolicy'] = 'camera-facing'
    root['billboard_visual_root'] = pivot.name
    root['billboard_driver'] = 'visual.rotation_euler[2] = -ground.rotation_euler[2]'
    bpy.context.view_layer.update()
    return asset
