"""Translate a measured native camera record without changing approved art."""
import math


def normalize_measured(camera, asset, catalog, validation):
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    require(validation.get('allChecksPassed') is True
            and validation.get('camera') == camera,
            'Measured camera must match the passing native validation')
    frame, anchor, scale = asset.get('frame'), asset.get('anchor'), asset.get('scale')
    require(asset.get('id') == catalog['id'] and frame == catalog['frameSize']
            and anchor == catalog['root'] and scale == catalog['sourceScale'],
            'Measured camera asset registration differs from the catalog')
    require(type(scale) is int and scale > 0
            and camera.get('nativeFrame') == [v * scale for v in frame],
            'Measured native frame differs from registered capture scale')
    root = camera.get('rootPx')
    require(isinstance(root, list) and len(root) == 2
            and all(math.isfinite(v) and abs(v - a * scale) <= .001
                    for v, a in zip(root, anchor)),
            'Measured native ground root differs from registration')
    matrix, shift, ortho = camera.get('matrix'), camera.get('shift'), camera.get('orthoScale')
    require(isinstance(matrix, list) and len(matrix) == 4
            and all(isinstance(row, list) and len(row) == 4
                    and all(math.isfinite(v) for v in row) for row in matrix)
            and isinstance(shift, list) and len(shift) == 2
            and all(math.isfinite(v) for v in shift)
            and isinstance(ortho, (int, float)) and math.isfinite(ortho) and ortho > 0,
            'Measured native camera transform is incomplete')
    return {'projection': asset['projection'], 'frame': frame, 'anchor': anchor,
            'captureScale': scale, 'fps': camera['fps'],
            'camera': {'type': 'orthographic', 'worldMatrix': matrix,
                       'orthoScale': ortho, 'shift': shift},
            'calibration': {'root': root}, 'artStyle': asset.get('artStyle'),
            'nativeMeasurement': camera,
            'normalization': 'Metadata translation only; exact approved native fields retained'}
