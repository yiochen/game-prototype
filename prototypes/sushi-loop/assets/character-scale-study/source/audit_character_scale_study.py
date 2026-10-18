#!/usr/bin/env python3
"""Read-only independent audit of native B/C character proportion captures.

Checks real evaluated mesh vertices and native camera matrices. Does not render,
change meshes, scale bitmaps, crop sprites, or assign artistic approval.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import struct

try:
    from PIL import Image
except ImportError:
    Image = None

SCALES = {'100': 1.0, '125': 1.25, '150': 1.5}
ANGLES = {'S': 0.0, 'E': math.pi / 2, 'N': math.pi, 'W': -math.pi / 2}
TOLERANCE = 0.08  # Logical rendered pixels; comfortably below one source pixel.


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def matrix(value):
    if len(value) != 4 or any(len(row) != 4 for row in value):
        raise ValueError('Expected 4×4 row-major matrix')
    result = [[float(x) for x in row] for row in value]
    if any(not math.isfinite(x) for row in result for x in row):
        raise ValueError('Nonfinite matrix')
    return result


def inverse(value):
    value = matrix(value)
    rows = [row[:] + [float(i == j) for j in range(4)] for i, row in enumerate(value)]
    for column in range(4):
        pivot = max(range(column, 4), key=lambda i: abs(rows[i][column]))
        if abs(rows[pivot][column]) < 1e-12:
            raise ValueError('Singular matrix')
        rows[column], rows[pivot] = rows[pivot], rows[column]
        factor = rows[column][column]
        rows[column] = [x / factor for x in rows[column]]
        for i in range(4):
            if i != column:
                factor = rows[i][column]
                rows[i] = [a - factor * b for a, b in zip(rows[i], rows[column])]
    return [row[4:] for row in rows]


def mul(value, vector):
    return [sum(a * b for a, b in zip(row, vector)) for row in value]


def transform(value, point):
    result = mul(value, [*point, 1.0])
    return [v / result[3] for v in result[:3]]


def distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def bounds(points):
    if not points:
        raise ValueError('No evaluated vertices')
    return [[min(point[i] for point in points) for i in range(len(points[0]))],
            [max(point[i] for point in points) for i in range(len(points[0]))]]


def dimensions(value):
    return [b - a for a, b in zip(*value)]


def resolve(base, value):
    path = Path(value)
    return path if path.is_absolute() else Path(base) / path


def record(base, value):
    if isinstance(value, dict):
        return value, None
    path = resolve(base, value)
    return json.loads(path.read_text()), path


def png_size(path):
    with Path(path).open('rb') as stream:
        data = stream.read(24)
    if data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
        raise ValueError('Invalid PNG signature/IHDR')
    return list(struct.unpack('>II', data[16:24]))


def root_matrix(scale, facing):
    angle = ANGLES[facing]
    c, s = math.cos(angle) * scale, math.sin(angle) * scale
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, scale, 0], [0, 0, 0, 1]]


def camera_measure(receipt):
    camera = receipt['camera']
    world = matrix(camera['worldMatrix'])
    projection = matrix(camera['projectionMatrix'])
    view = inverse(world)
    scale = receipt.get('sourceScale', receipt.get('captureScale'))
    frame = receipt.get('frameSize', receipt.get('frame'))
    width, height = [value * scale for value in frame]

    def project(point):
        clip = mul(projection, mul(view, [*point, 1.0]))
        return [(clip[0] / clip[3] + 1) * width / 2,
                (1 - clip[1] / clip[3]) * height / 2]

    origin = project([0, 0, 0])
    vectors = {name: [(b - a) / scale for a, b in zip(origin, project(point))]
               for name, point in {'unitX': [1, 0, 0], 'unitDepth': [0, -1, 0],
                                   'unitHeight': [0, 0, 1]}.items()}
    back = [world[i][2] for i in range(3)]
    elevation = math.degrees(math.atan2(back[2], math.hypot(back[0], back[1])))
    return {'root': [v / scale for v in origin], 'vectors': vectors,
            'elevationDegrees': elevation}, project


def audit_camera(receipt, frame, root, source_scale, cell_size):
    errors = []
    measured, project = camera_measure(receipt)
    actual_frame = receipt.get('frameSize', receipt.get('frame'))
    actual_root = receipt.get('root', receipt.get('anchor'))
    camera = receipt['camera']
    if list(actual_frame) != list(frame):
        errors.append('Native frame differs from fixed comparison frame')
    if list(actual_root) != list(root):
        errors.append('Native root differs from fixed comparison root')
    if receipt.get('sourceScale', receipt.get('captureScale')) != source_scale:
        errors.append('Native source scale differs from retained PNG pixel scale')
    if distance(measured['root'], root) > TOLERANCE:
        errors.append('Actual matrix-projected origin misses the common ground root')
    if camera.get('type') not in ['ORTHO', 'orthographic']:
        errors.append('Character camera is not orthographic')
    if camera.get('sensorFit') != 'HORIZONTAL':
        errors.append('Character camera does not use fixed horizontal sensor fit')
    if abs(camera.get('orthoScale', -999) - frame[0] / cell_size) > 1e-5:
        errors.append('Camera ortho scale changed from fixed world pitch')
    aspect = camera.get('pixelAspect', [])
    if len(aspect) != 2 or aspect[0] != aspect[1]:
        errors.append('Character capture pixels are not square')
    if abs(measured['elevationDegrees'] - 35) > 1e-3:
        errors.append('Actual camera is not the ordinary 35 degree projection')
    expected = {'unitX': [cell_size, 0],
                'unitDepth': [0, cell_size * math.sin(math.radians(35))],
                'unitHeight': [0, -cell_size * math.cos(math.radians(35))]}
    for name, value in expected.items():
        if distance(measured['vectors'][name], value) > TOLERANCE:
            errors.append('Actual camera calibration differs from fixed ordinary 35 degree ' + name)
    measured['expectedLogicalVectors'] = expected
    return errors, measured, project


def evaluated_geometry(geometry):
    objects = geometry['objects']
    if not objects:
        raise ValueError('Native geometry receipt has no evaluated mesh objects')
    points, canonical, anatomy, errors = [], {}, {}, []
    for obj in objects:
        object_id = obj.get('objectID', obj.get('id', obj.get('name')))
        if object_id is None or object_id in canonical:
            raise ValueError('Evaluated object identity missing or duplicate')
        world_matrix = matrix(obj.get('objectWorldMatrix', obj.get('worldMatrix')))
        local = obj['localVertices']
        world = obj['worldVertices']
        if not local or len(local) != len(world):
            raise ValueError('Evaluated local/world vertex arrays differ in length')
        recomputed = [transform(world_matrix, point) for point in local]
        maximum_error = max(distance(a, b) for a, b in zip(recomputed, world))
        if maximum_error > 2e-6:
            errors.append('Recorded world vertices disagree with evaluated mesh+matrix for ' + object_id)
        points.extend(world)
        canonical[object_id] = {'localVertices': local, 'faces': obj.get('faces')}
        anatomy[object_id] = {'role': obj.get('role'), 'bounds': bounds(world)}
    return points, canonical, anatomy, errors


def alpha_measure(path, source_scale):
    if Image is None:
        raise ValueError('Pillow required for independent alpha/cropping inspection')
    with Image.open(path) as opened:
        opened.load()
        alpha = opened.convert('RGBA').getchannel('A')
        bbox = alpha.getbbox()
        # Threshold avoids treating negligible transparent-filter ringing as body volume.
        visible = alpha.point(lambda value: 255 if value >= 16 else 0).getbbox()
        mode = opened.mode
    if not bbox or not visible:
        raise ValueError('Empty rendered sprite alpha')
    width, height = png_size(path)
    return {'mode': mode, 'boundsRaw': list(bbox),
            'boundsLogical': [v / source_scale for v in bbox],
            'visibleBoundsLogical': [v / source_scale for v in visible],
            'widthLogical': (bbox[2] - bbox[0]) / source_scale,
            'visibleWidthLogical': (visible[2] - visible[0]) / source_scale,
            'transparentMarginLogical': min(bbox[0], bbox[1], width - bbox[2], height - bbox[3]) / source_scale,
            'touchesFrame': bbox[0] == 0 or bbox[1] == 0 or bbox[2] == width or bbox[3] == height}


def source_guard(study, base):
    result = {'ok': True, 'errors': []}
    for key in ['nativeProject', 'nativeProjectSHA256']:
        if not study.get(key):
            result['errors'].append('Missing ' + key)
    if study.get('nativeProject'):
        path = resolve(base, study['nativeProject'])
        digest = sha_file(path)
        result['nativeProjectSHA256'] = digest
        if digest != study.get('nativeProjectSHA256'):
            result['errors'].append('Editable native study project differs from retained capture identity')
    before = study.get('productionPresentationHashBefore')
    after = study.get('productionPresentationHashAfter')
    if not before or not after or before != after:
        result['errors'].append('Production presentation pre/post preservation guard missing or changed')
    result['productionPresentationRestored'] = bool(before and before == after)
    result['ok'] = not result['errors']
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study')
    parser.add_argument('--asset-root')
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    study_path = Path(args.study)
    base = Path(args.asset_root) if args.asset_root else study_path.parent
    study = json.loads(study_path.read_text())
    # Manifest adapters below are completed against the native capture schema.
    report = audit(study, base)
    report.update(createdAtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  manifest=str(study_path), manifestSHA256=sha_file(study_path))
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp-' + str(os.getpid()))
    temporary.write_text(json.dumps(report, indent=2) + '\n')
    os.replace(temporary, path)
    print(json.dumps({'ok': report['ok'], 'captures': len(report.get('captures', [])),
                      'errors': report['errors'], 'report': str(path)}))
    raise SystemExit(0 if report['ok'] else 1)


def audit(study, base):
    report = {'version': 1, 'mode': 'read-only-independent-native-character-study-audit',
              'ok': False, 'errors': [], 'captures': [], 'designs': [],
              'artApproval': 'Not established by structural audit; visual review remains required.'}
    cell_size = study.get('cellSize')
    source_scale = study.get('sourceScale')
    frame, root = study.get('frameSize'), study.get('root')
    if cell_size != 128 or source_scale != 4:
        report['errors'].append('Study must retain native 4× images at 128 logical pixels per cell')
    if {str(row['id']): row['factor'] for row in study.get('scales', [])} != SCALES:
        report['errors'].append('Study must contain exactly 100/125/150 percent true world scales')
    if set(study.get('directions', [])) != set(ANGLES):
        report['errors'].append('Study must contain all four cardinal facings')
    if {v['id'] for v in study.get('variants', [])} != {'B', 'C'}:
        report['errors'].append('Study must contain B Playful and C Chunky')
    guard = source_guard(study, base)
    report['sourcePreservation'] = guard
    report['errors'].extend(guard['errors'])
    shared_camera = None
    for variant in study.get('variants', []):
        design = {'id': variant['id'], 'ok': False, 'errors': [], 'measurements': {},
                  'anatomyAt100South': {}}
        canonical_baseline = None
        for scale_id, factor in SCALES.items():
            scale_record = variant['scales'][scale_id]
            if scale_record['factor'] != factor:
                design['errors'].append('Advertised ' + scale_id + ' factor differs from requested world scale')
            for facing in ANGLES:
                sample = {'id': variant['id'] + '/' + scale_id + '/' + facing,
                          'variant': variant['id'], 'scale': scale_id, 'factor': factor,
                          'facing': facing, 'ok': False, 'errors': []}
                try:
                    receipt, receipt_path = record(base, scale_record['cameras'][facing])
                    geometry, geometry_path = record(base, scale_record['geometry'][facing])
                    if receipt.get('variantId') != variant['id'] or geometry.get('variantId') != variant['id']:
                        sample['errors'].append('Native receipt identifies another variant')
                    for value in [receipt, geometry]:
                        if value.get('direction') != facing or value.get('factor') != factor or value.get('scaleId') != scale_id:
                            sample['errors'].append('Native receipt identifies another direction/scale')
                    if variant['frameSize'] != frame or variant['root'] != root:
                        sample['errors'].append('B/C samples do not share one fixed frame and ground root')
                    errors, measured, project = audit_camera(receipt, frame, root, source_scale, cell_size)
                    sample['errors'].extend(errors)
                    sample['camera'] = measured
                    camera_identity = {'frame': receipt['frameSize'], 'root': receipt['root'],
                                       'camera': receipt['camera']}
                    if shared_camera is None:
                        shared_camera = camera_identity
                    elif camera_identity != shared_camera:
                        sample['errors'].append('Actual camera changed between samples; comparison may contain fitting')
                    points, canonical, anatomy, errors = evaluated_geometry(geometry)
                    sample['errors'].extend(errors)
                    actual_root = matrix(geometry['rootWorldMatrix'])
                    expected_root = root_matrix(factor, facing)
                    if max(abs(a - b) for row1, row2 in zip(actual_root, expected_root) for a, b in zip(row1, row2)) > 2e-6:
                        sample['errors'].append('Native root is not the requested uniform scale and cardinal facing')
                    actual_world_bounds = bounds(points)
                    actual_dimensions = dimensions(actual_world_bounds)
                    sample['evaluatedWorldBounds'] = actual_world_bounds
                    sample['evaluatedWorldDimensions'] = actual_dimensions
                    if min(actual_world_bounds[0][:2]) < -.5 - 2e-6 or max(actual_world_bounds[1][:2]) > .5 + 2e-6:
                        sample['errors'].append('Full evaluated geometry crosses its one-cell XY footprint')
                    if max(actual_dimensions[:2]) > 1 + 2e-6:
                        sample['errors'].append('Full evaluated geometry is wider/deeper than one cell')
                    projected = [[v / source_scale for v in project(point)] for point in points]
                    projected_bounds = bounds(projected)
                    projected_dimensions = dimensions(projected_bounds)
                    sample['projectedBoundsLogical'] = projected_bounds
                    sample['projectedDimensionsLogical'] = projected_dimensions
                    sample['heightTilesIncludingHat'] = projected_dimensions[1] / cell_size
                    sample['widthTiles'] = projected_dimensions[0] / cell_size
                    if projected_bounds[0][0] < root[0] - cell_size / 2 - TOLERANCE or projected_bounds[1][0] > root[0] + cell_size / 2 + TOLERANCE:
                        sample['errors'].append('Full projected geometry crosses one tile horizontally')
                    # Independently normalize all evaluated world vertices, preserving their native order.
                    inverse_root = inverse(actual_root)
                    normalized = {obj['id']: [transform(inverse_root, p) for p in obj['worldVertices']]
                                  for obj in geometry['objects']}
                    if canonical_baseline is None:
                        canonical_baseline = normalized
                    if set(normalized) != set(canonical_baseline):
                        sample['errors'].append('Native object set changes between scales/facings')
                    else:
                        maximum_error = 0.0
                        for object_id, vertices in normalized.items():
                            baseline = canonical_baseline[object_id]
                            if len(vertices) != len(baseline):
                                sample['errors'].append('Native evaluated mesh topology changes for ' + object_id)
                                continue
                            maximum_error = max(maximum_error, max(distance(a, b) for a, b in zip(vertices, baseline)))
                        sample['maximumNormalizedVertexDifferenceCells'] = maximum_error
                        if maximum_error > 3e-5:
                            sample['errors'].append('Actual native anatomy differs after removing requested scale/facing')
                    recomputed_geometry_hash = json_hash([{'id': obj['id'], 'vertices': obj['localVertices'], 'faces': obj['faces']}
                                                          for obj in geometry['objects']])
                    recomputed_placements_hash = json_hash([{'id': obj['id'], 'worldMatrix': obj['worldMatrix']}
                                                            for obj in geometry['objects']])
                    if recomputed_geometry_hash != geometry['geometryHash'] or geometry['geometryHash'] != variant['source']['geometryHash']:
                        sample['errors'].append('Evaluated local mesh identity changed between native captures')
                    if recomputed_placements_hash != geometry['placementsHash']:
                        sample['errors'].append('Native placement hash disagrees with independently hashed actual matrices')
                    for key in ['geometryHash', 'placementsHash', 'materialsHash']:
                        if receipt[key] != geometry[key]:
                            sample['errors'].append('Camera and native geometry receipts disagree: ' + key)
                    if geometry['materialsHash'] != variant['source']['materialsHash']:
                        sample['errors'].append('Materials differ between native captures')
                    if receipt['nativeProjectSHA256'] != study['nativeProjectSHA256']:
                        sample['errors'].append('Capture came from another editable native project')
                    if receipt['geometry']['sha256'] != sha_file(geometry_path):
                        sample['errors'].append('Retained evaluated geometry differs from native camera receipt')
                    if scale_id == '100' and facing == 'S':
                        for role in ['head', 'torso', 'hair', 'hat', 'leg', 'shoe']:
                            role_points = [p for obj in geometry['objects'] if obj.get('role') == role for p in obj['worldVertices']]
                            if role_points:
                                rb = bounds(role_points)
                                design['anatomyAt100South'][role] = {'bounds': rb, 'dimensions': dimensions(rb)}
                        core = next((obj for obj in geometry['objects'] if obj['id'].endswith('__head')), None)
                        if core:
                            hb = bounds(core['worldVertices'])
                            design['anatomyAt100South']['headCore'] = {'bounds': hb, 'dimensions': dimensions(hb)}
                    image_path = resolve(base, scale_record['images'][facing])
                    actual_png_size = png_size(image_path)
                    actual_png_hash = sha_file(image_path)
                    if actual_png_size != [int(v * source_scale) for v in frame]:
                        sample['errors'].append('Actual PNG dimensions differ from fixed native 4× frame')
                    if actual_png_hash != receipt['png']['sha256'] or actual_png_size != receipt['png']['dimensions']:
                        sample['errors'].append('PNG differs byte-for-byte from native output receipt')
                    alpha = alpha_measure(image_path, source_scale)
                    sample['alpha'] = alpha
                    if alpha['touchesFrame'] or alpha['transparentMarginLogical'] < 1:
                        sample['errors'].append('Native rendered alpha approaches capture border; possible crop')
                    # Native antialiasing adds at most a source-pixel fringe outside mesh vertices.
                    if alpha['visibleBoundsLogical'][0] < root[0] - cell_size / 2 - .5 or alpha['visibleBoundsLogical'][2] > root[0] + cell_size / 2 + .5:
                        sample['errors'].append('Rendered character silhouette exceeds one tile horizontally')
                    sample.update(geometryReceiptSHA256=sha_file(geometry_path),
                                  cameraReceiptSHA256=sha_file(receipt_path),
                                  imageSHA256=actual_png_hash, imageDimensions=actual_png_size,
                                  evaluatedVertexCount=len(points), evaluatedObjectCount=len(geometry['objects']))
                    design['measurements'].setdefault(scale_id, {})[facing] = {
                        'worldWidth': actual_dimensions[0], 'worldDepth': actual_dimensions[1],
                        'worldHeight': actual_dimensions[2], 'screenWidthTiles': sample['widthTiles'],
                        'screenHeightTilesIncludingHat': sample['heightTilesIncludingHat'],
                        'alphaHeightTilesIncludingHat': (alpha['boundsLogical'][3] - alpha['boundsLogical'][1]) / cell_size}
                except Exception as exc:
                    sample['errors'].append(type(exc).__name__ + ': ' + str(exc))
                sample['ok'] = not sample['errors']
                report['captures'].append(sample)
                if not sample['ok']:
                    design['errors'].append(sample['id'] + ': ' + '; '.join(sample['errors']))
        design['ok'] = not design['errors']
        report['designs'].append(design)
        report['errors'].extend(design['errors'])
    if len(report['captures']) != 24:
        report['errors'].append('Exactly 24 native static captures must be audited')
    try:
        b, c = [next(d for d in report['designs'] if d['id'] == ident) for ident in ['B', 'C']]
        bd, cd = b['anatomyAt100South'], c['anatomyAt100South']
        report['sideVolumeComparison'] = {
            'B': {key: bd[key]['dimensions'] for key in ['headCore', 'torso', 'hair']},
            'C': {key: cd[key]['dimensions'] for key in ['headCore', 'torso', 'hair']},
            'C_headCoreDepthIncreasePercent': (cd['headCore']['dimensions'][1] / bd['headCore']['dimensions'][1] - 1) * 100,
            'C_torsoDepthIncreasePercent': (cd['torso']['dimensions'][1] / bd['torso']['dimensions'][1] - 1) * 100,
            'meaning': 'Actual native core geometry depth; not nose/hat enlargement or bitmap scaling.'}
    except Exception as exc:
        report['errors'].append('Could not independently establish side-volume comparison: ' + str(exc))
    report['ok'] = not report['errors']
    return report


if __name__ == '__main__':
    main()
