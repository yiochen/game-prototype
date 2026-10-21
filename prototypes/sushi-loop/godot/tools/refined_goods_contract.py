"""Verify five approved native inventory captures and the unchanged cream floor."""
from pathlib import Path

from refinement_contract import contained, read, verified_packet
from verify_editor_ui import _crop, _decode_png, require, sha

IDS = ['belt-straight-e', 'stool-wood', 'plant-angular',
       'crate-wood', 'barrel-wood', 'floor-cream']
METHOD = 'Approved per-object Blender native captures'
LEGACY_ROOT = 'assets/ui/editor/goods-v1'
RECORD_SHA = '1fa232581710958ea1a7dddf0bcd5b7715371fe4135d1dac6199550ab1930406'
FLOOR_SHA = '6ded9330f3106d1d4941ac84e94c3e54436f098d261f5f36436d7115af239177'
FLOOR_RGBA_SHA = '1cee44c04199f35fd17b2774d667dfa7ed95656ad2b8f88f16df628d2d8a1ce1'
CAMERA = {'id': 'goods-three-quarter-35',
          'projection': 'ordinary-orthographic-three-quarter',
          'elevation_degrees': 35, 'azimuth_degrees': 35,
          'pixel_aspect': [1, 1], 'exception_scope': 'UI merchandise presentation only'}


def approved_goods(prototype):
    prototype = Path(prototype).resolve()
    legacy = prototype / LEGACY_ROOT
    records_path = legacy / 'records/captures.json'
    require(sha(records_path) == RECORD_SHA, 'Original inventory camera/floor receipt changed')
    records = read(records_path)
    for key, root in [('production_blend', prototype), ('blend', legacy), ('recipe', legacy)]:
        require(sha(contained(prototype, root / records[key])) == records[key + '_sha256'],
                f'Original inventory source changed: {key}')
    entries, provenance, renders = {}, {}, {}
    for index, asset in enumerate(IDS):
        record = records['sprites'][asset]
        if asset == 'floor-cream':
            render = legacy / record['source_render']
            require(sha(render) == record['source_sha256'] == FLOOR_SHA,
                    'Excluded cream floor render changed')
            approval = {'legacyCaptureRecord': LEGACY_ROOT + '/records/captures.json',
                        'legacyCaptureRecordSHA256': RECORD_SHA}
        else:
            relative = f'assets/refinement/objects/{asset}/supplements/editor-goods/final/approval.json'
            receipt_path = prototype / relative
            receipt = read(receipt_path)
            require(receipt.get('asset') == asset and receipt.get('status') == 'exact-approved-bytes-saved'
                    and isinstance(receipt.get('editor'), str) and receipt['editor']
                    and isinstance(receipt.get('judge'), str) and receipt['judge']
                    and receipt['editor'] != receipt['judge'], f'Invalid native inventory approval: {asset}')
            packet_path = contained(prototype, receipt_path.parent / receipt['packet'])
            review_path = contained(prototype, receipt_path.parent / receipt['review'])
            packet, bound = verified_packet(prototype, packet_path, receipt['packetSHA256'],
                                            review_path, receipt['reviewSHA256'], asset)
            capture = packet['capture']
            require(capture['frame'] == [384, 384] and capture['views'] == ['goods']
                    and capture['projection'] == CAMERA['projection']
                    and capture['pixelAspect'] == [1, 1]
                    and capture['elevationDegrees'] == capture['azimuthDegrees'] == 35,
                    f'Approved native inventory capture contract changed: {asset}')
            native = contained(prototype, receipt_path.parent / receipt['editableSource'])
            render = contained(prototype, receipt_path.parent / receipt['image'])
            require(bound.get(native) == receipt['editableSourceSHA256'] == sha(native),
                    f'Inventory editable native source changed: {asset}')
            require(sha(render) == receipt['imageSHA256']
                    and any(value == receipt['imageSHA256'] for value in bound.values()),
                    f'Inventory image is not an approved native capture: {asset}')
            require(packet['candidateRenders']['goods']['sha256'] == receipt['imageSHA256'],
                    f'Inventory image does not match the reviewed goods view: {asset}')
            approval = {'receipt': relative, 'receiptSHA256': sha(receipt_path),
                        'packetSHA256': receipt['packetSHA256'],
                        'reviewSHA256': receipt['reviewSHA256'],
                        'editableSourceSHA256': receipt['editableSourceSHA256']}
        dimensions, pixels = _decode_png(render.read_bytes())
        require(dimensions == [384, 384] and 0 in pixels[3::4] and 255 in pixels[3::4],
                f'Native inventory canvas/alpha changed: {asset}')
        occupied = [(i % 384, i // 384) for i, alpha in enumerate(pixels[3::4]) if alpha]
        bounds = [min(x for x, _ in occupied), min(y for _, y in occupied),
                  max(x for x, _ in occupied) + 1, max(y for _, y in occupied) + 1]
        entries[asset] = {'region': [index % 3 * 392 + 4, index // 3 * 392 + 4, 384, 384],
                          'source_render': render.relative_to(prototype).as_posix(),
                          'source_sha256': sha(render), 'camera_id': CAMERA['id'],
                          'camera': record['camera'], 'alpha_bounds': bounds}
        if asset == 'floor-cream':
            entries[asset]['floor_thickness'] = record['floor_thickness']
            entries[asset]['floor_bevel'] = record['floor_bevel']
        renders[asset] = render
        provenance[asset] = approval
    metadata = {'schema_version': 2, 'atlas': 'atlas.png', 'atlas_size': [1176, 784],
                'padding': 4, 'native_render_size': [384, 384], 'camera': CAMERA,
                'provenance': {'method': METHOD, 'native_renders_unresized': True,
                               'approvals': provenance}, 'sprites': entries}
    return metadata, renders


def verify_refined_goods(project, source_project):
    import hashlib
    project, source_project = Path(project).resolve(), Path(source_project).resolve()
    metadata, renders = approved_goods(source_project.parent)
    runtime = project / 'assets/ui/editor-goods'
    manifest = read(runtime / 'manifest.json')
    target = runtime / 'atlas.png'
    atlas_bytes = target.read_bytes()
    expected = {**metadata, 'atlas_sha256': sha(target), 'atlas_bytes': len(atlas_bytes)}
    require(manifest == expected, 'Refined inventory metadata, source approval or registration changed')
    dimensions, pixels = _decode_png(atlas_bytes)
    require(dimensions == metadata['atlas_size'], 'Refined inventory atlas dimensions changed')
    # Every nonzero-alpha pixel must belong to one fixed 384px cell. This
    # independently checks every border/gutter, including the outer perimeter.
    coverage = bytearray(dimensions[0] * dimensions[1])
    for asset, entry in metadata['sprites'].items():
        region = entry['region']
        native_dimensions, native_pixels = _decode_png(renders[asset].read_bytes())
        require(native_dimensions == [384, 384] and _crop(pixels, dimensions, region) == native_pixels,
                f'Inventory atlas changed/resized approved native pixels: {asset}')
        if asset == 'floor-cream':
            require(hashlib.sha256(native_pixels).hexdigest() == FLOOR_RGBA_SHA,
                    'Excluded cream floor atlas crop changed')
        x, y, width, height = region
        for row in range(y, y + height):
            start = row * dimensions[0] + x
            require(not any(coverage[start:start + width]), 'Inventory atlas regions overlap')
            coverage[start:start + width] = b'\x01' * width
    require(all(inside or not alpha for inside, alpha in zip(coverage, pixels[3::4])),
            'Inventory atlas sampling gutter is not transparent')
    require({path.relative_to(runtime).as_posix() for path in runtime.rglob('*.png')} == {'atlas.png'},
            'Unexpected refined inventory image payload')
    return {'images': 1, 'sprites': 6, 'png_bytes': len(atlas_bytes),
            'source_root': 'assets/refinement/objects', 'runtime_images': ['atlas.png'],
            'approved_native_captures': 5, 'unchanged_floor': True}
