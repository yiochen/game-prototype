#!/usr/bin/env python3
"""Verify the approved B ImageGen family, exact atlas pixels and nine-patch calibration.

The release gate intentionally uses only the Python standard library. Native
captures are still required to judge appearance; provenance alone is not approval.
"""
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import math
import re
import struct
import zlib

REFERENCE = 'design/art-directions/restaurant-item-catalog.png'
WORLD_REFERENCE = 'design/art-directions/restaurant-concept.png'
COMPOSITION = 'assets/ui/editor/v4/raw/b-indigo-ceramic.png'
SOURCE_RECORD = 'assets/ui/editor/v6/imagegen.json'
HISTORICAL_SOURCE_RECORD = 'assets/ui/editor/v5/imagegen.json'
HISTORICAL_RECORD_SHA256 = 'c0893a19e487376002d6941d8ac2d3eaa7ca12e13189f7f29acd9268f22ebc26'
ATLAS = 'skin.png'
GUTTER = 4
# Exact coverage is filled by the coordinated packer contract, not inferred from
# whichever images happen to be present in the runtime directory.
STYLES = {'control-wood', 'control-pressed', 'control-green', 'control-green-pressed',
          'control-slate', 'slot-paper', 'slot-selected', 'container-tray',
          'container-modal', 'toast-error', 'noren-rail', 'context-bubble',
          'stock-badge', 'tab-active', 'tab-idle', 'coin-panel', 'context-action',
          'noren-rod', 'noren-dock'}
ICONS = {'people', 'layout', 'floor', 'shop', 'rotate', 'remove', 'caret-left',
         'caret-right', 'coin', 'close', 'retry', 'warning', 'play', 'pointer',
         'edit', 'check'}
PILL_STYLES = {'control-wood', 'control-pressed', 'control-green',
               'control-green-pressed', 'control-slate', 'coin-panel',
               'context-bubble', 'toast-error'}
PILL_MINIMUM_HEIGHT = 100


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def _path(root, relative, label):
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), f'Invalid editor UI {label} path')
    path = (root / relative).resolve()
    require(path.is_relative_to(root), f'Editor UI {label} escapes its source root')
    return path


def _numbers(value, count, label, integer=False, positive=False):
    require(isinstance(value, list) and len(value) == count and all(
        type(v) is int if integer else type(v) in (int, float) and math.isfinite(v)
        for v in value), f'Invalid editor UI {label}')
    require(all(v > 0 if positive else v >= 0 for v in value), f'Invalid editor UI {label}')
    return value


def _region(value, dimensions, label):
    x, y, width, height = _numbers(value, 4, label, integer=True)
    require(width > 0 and height > 0 and x + width <= dimensions[0] and y + height <= dimensions[1], f'Editor UI {label} lies outside its sheet')
    return x, y, width, height


@lru_cache(maxsize=6)
def _decode_png(data):
    """Decode noninterlaced 8-bit RGBA PNGs for an independent crop-pixel proof."""
    require(data[:8] == b'\x89PNG\r\n\x1a\n', 'Expected editor UI PNG')
    position, compressed, dimensions = 8, bytearray(), None
    ended = False
    while position < len(data):
        length = struct.unpack_from('>I', data, position)[0]
        kind = data[position + 4:position + 8]
        payload = data[position + 8:position + 8 + length]
        crc = struct.unpack_from('>I', data, position + 8 + length)[0]
        require(zlib.crc32(kind + payload) & 0xffffffff == crc, 'Editor UI PNG checksum changed')
        if kind == b'IHDR':
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', payload)
            require(depth == 8 and color == 6 and compression == filtering == interlace == 0, 'Expected editor UI noninterlaced 8-bit RGBA PNG')
            require(0 < width <= 8192 and 0 < height <= 8192, 'Invalid editor UI PNG dimensions')
            dimensions = [width, height]
        elif kind == b'IDAT':
            compressed.extend(payload)
        elif kind == b'IEND':
            ended = True
            require(position + length + 12 == len(data), 'Unexpected editor UI PNG trailing bytes')
            break
        position += length + 12
    require(dimensions and ended, 'Incomplete editor UI PNG')
    stride = dimensions[0] * 4
    filtered = zlib.decompress(compressed)
    require(len(filtered) == (stride + 1) * dimensions[1], 'Invalid editor UI PNG scanlines')
    pixels, previous = bytearray(), bytearray(stride)
    for y in range(dimensions[1]):
        offset = y * (stride + 1)
        method = filtered[offset]
        row = bytearray(filtered[offset + 1:offset + 1 + stride])
        require(method <= 4, 'Invalid editor UI PNG filter')
        if method == 1:
            for i in range(4, stride):
                row[i] = (row[i] + row[i - 4]) & 255
        elif method == 2:
            for i in range(stride):
                row[i] = (row[i] + previous[i]) & 255
        elif method == 3:
            for i in range(stride):
                row[i] = (row[i] + ((row[i - 4] if i >= 4 else 0) + previous[i]) // 2) & 255
        elif method == 4:
            for i in range(stride):
                left, up = row[i - 4] if i >= 4 else 0, previous[i]
                upper_left = previous[i - 4] if i >= 4 else 0
                p = left + up - upper_left
                a, b, c = abs(p - left), abs(p - up), abs(p - upper_left)
                prediction = left if a <= b and a <= c else up if b <= c else upper_left
                row[i] = (row[i] + prediction) & 255
        pixels.extend(row)
        previous = row
    return dimensions, bytes(pixels)


def _crop(pixels, dimensions, region):
    x, y, width, height = region
    stride = dimensions[0] * 4
    return b''.join(pixels[(y + row) * stride + x * 4:(y + row) * stride + (x + width) * 4] for row in range(height))


def _calibration(identity, entry, region):
    slices = _numbers(entry['slice_px'], 4, f'source slices: {identity}', integer=True)
    edges = _numbers(entry['edge'], 4, f'logical edges: {identity}')
    content = _numbers(entry['content'], 4, f'content margins: {identity}')
    for values, label in ((slices, 'source slices'), (edges, 'logical edges'), (content, 'content margins')):
        require(values[0] == values[2] and values[1] == values[3], f'Editor UI asymmetric {label}: {identity}')
    require(slices[0] + slices[2] < region[2] and slices[1] + slices[3] < region[3], f'Editor UI has no plain stretch spans: {identity}')
    if any(slices):
        require(all(slices) and all(edges), f'Editor UI fixed corner calibration is incomplete: {identity}')
        ratios = [edges[index] / slices[index] for index in range(4)]
        require(all(math.isclose(ratio, ratios[0], abs_tol=1e-9) for ratio in ratios), f'Editor UI corner scale is distorted: {identity}')
    else:
        require(identity == 'context-action' and not any(edges), f'Editor UI framed surface lacks fixed corners: {identity}')
    if identity in PILL_STYLES or 'minimum_height' in entry:
        minimum_height = entry.get('minimum_height')
        require(type(minimum_height) in (int, float) and math.isfinite(minimum_height) and minimum_height > 0, f'Editor UI minimum height is missing or invalid: {identity}')
        if identity in PILL_STYLES:
            require(minimum_height >= PILL_MINIMUM_HEIGHT, f'Editor UI pill minimum height is below {PILL_MINIMUM_HEIGHT}: {identity}')
        natural_height = region[3] * ratios[0] if any(slices) else 0
        require(minimum_height >= natural_height or math.isclose(minimum_height, natural_height, abs_tol=1e-9), f'Editor UI minimum height is below its uniformly scaled source height: {identity}')
    require(isinstance(entry.get('stretch'), str) and len(entry['stretch']) > 30, f'Editor UI plain stretch span documentation is missing: {identity}')
    require(type(entry.get('draw_center', True)) is bool, f'Invalid editor UI centre drawing: {identity}')
    require(isinstance(entry.get('tint', 'ffffffff'), str) and re.fullmatch(r'(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})', entry.get('tint', 'ffffffff')), f'Invalid editor UI tint: {identity}')


def _verify(project, source_project):
    prototype = source_project.parent
    runtime = project / 'assets/ui/editor'
    manifest = json.loads((runtime / 'manifest.json').read_text())
    require(manifest.get('version') == 3, 'Editor UI requires the current B amendment manifest version 3')
    require(manifest.get('reference') == REFERENCE and sha(prototype / REFERENCE) == manifest['reference_sha256'], 'Editor UI catalog reference changed')
    require(manifest.get('source_record') == SOURCE_RECORD, 'Editor UI requires the current B v6 source record')
    source_record = _path(prototype, manifest['source_record'], 'ImageGen record')
    require(sha(source_record) == manifest['source_record_sha256'], 'Editor ImageGen prompt record changed')
    require(sha(source_record.parent / 'pack.py') == manifest['packing_script_sha256'], 'Editor UI packing procedure changed')
    require(sha(source_record.parent / 'authoring.json') == manifest['authoring_sha256'], 'Editor UI authored calibration and states changed')
    generation = json.loads(source_record.read_text())
    require(generation.get('version') == 3, 'Editor UI generation record version changed')
    accepted = generation['accepted_composition']
    require(accepted['path'] == COMPOSITION and sha(prototype / COMPOSITION) == accepted['sha256'], 'Editor UI accepted B composition changed')
    latest = generation['latest_composition']
    latest_path = _path(prototype, latest['path'], 'latest B composition')
    require(latest_path.is_relative_to(source_record.parent) and sha(latest_path) == latest['sha256'], 'Editor UI latest B amendment composition changed')
    historical_path = _path(prototype, HISTORICAL_SOURCE_RECORD, 'historical ImageGen record')
    require(sha(historical_path) == HISTORICAL_RECORD_SHA256, 'Editor UI historical v5 record changed')
    historical = json.loads(historical_path.read_text())
    historical_generations = {record['id']: record for record in historical['generations']}
    references = generation['references']
    require(isinstance(references, list) and len({r['path'] for r in references}) == len(references), 'Editor UI reference set is invalid')
    referenced = {entry['path']: entry for entry in references}
    require({REFERENCE, WORLD_REFERENCE, COMPOSITION, latest['path']} <= set(referenced), 'Editor UI catalog, world and B amendment references are incomplete')
    for relative, entry in referenced.items():
        path = _path(prototype, relative, 'reference')
        require(sha(path) == entry['sha256'] and isinstance(entry.get('role'), str) and entry['role'].strip(), f'Editor UI reference changed or lacks its role: {relative}')
    composition = generation['composition_generation']
    require(composition.get('mode') in {'builtin-image_gen', 'builtin-image_gen-edit'} and isinstance(composition.get('prompt'), str) and len(composition['prompt']) > 100, 'Editor UI complete-screen generation provenance is missing')
    composition_path = _path(source_record.parent, composition['raw'], 'complete-screen generated output')
    require(composition_path == latest_path and composition.get('raw_sha256') == latest['sha256'], 'Editor UI complete-screen output registration changed')
    composition_data = composition_path.read_bytes()
    require(composition_data[:8] == b'\x89PNG\r\n\x1a\n' and list(struct.unpack_from('>II', composition_data, 16)) == composition['dimensions'] and min(composition['dimensions']) >= 768, 'Editor UI full complete-screen output resolution changed')
    require(COMPOSITION in composition['reference_paths'] and set(composition['reference_sha256']) == set(composition['reference_paths']), 'Editor UI complete-screen B reference is missing')
    for reference in composition['reference_paths']:
        require(reference in referenced and composition['reference_sha256'][reference] == referenced[reference]['sha256'], 'Editor UI complete-screen generation reference hash changed')
    require(manifest.get('atlas') == ATLAS, 'Invalid editor UI atlas path')
    atlas = runtime / ATLAS
    atlas_data = atlas.read_bytes()
    require(hashlib.sha256(atlas_data).hexdigest() == manifest['atlas_sha256'] and len(atlas_data) == manifest['atlas_bytes'], 'Editor UI pixels changed: atlas')
    dimensions, atlas_pixels = _decode_png(atlas_data)
    require(dimensions == manifest['atlas_dimensions'], 'Editor UI atlas dimensions changed')
    styles, icons = manifest['styles'], manifest['icons']
    require(isinstance(styles, dict) and isinstance(icons, dict) and set(styles) == STYLES and set(icons) == ICONS, 'Editor UI active/passive surface or icon coverage is incomplete')
    require(not set(styles) & set(icons), 'Editor UI style/icon identities overlap')
    identities = set(styles) | set(icons)
    require(set(generation['entries']) == identities, 'Editor UI source region coverage is incomplete')
    require(isinstance(generation['surface_inventory'], list) and set(generation['surface_inventory']) == identities and len(generation['surface_inventory']) == len(identities), 'Editor UI full-screen surface inventory is incomplete')
    sources = {}
    generation_ids = set()
    new_sources = inherited_sources = 0
    for record in generation['generations']:
        require(isinstance(record.get('id'), str) and record['id'] and record['id'] not in generation_ids and record.get('mode') == 'builtin-image_gen', 'Editor UI ImageGen generation identity/mode is invalid')
        generation_ids.add(record['id'])
        relative = str((source_record.parent / record['raw']).relative_to(prototype))
        source = _path(source_record.parent, record['raw'], 'generated sheet')
        require(source.is_relative_to(source_record.parent / 'raw') and relative not in sources, 'Editor UI generated source identity is invalid')
        require(record.get('transparent') is True and isinstance(record.get('prompt'), str) and len(record['prompt']) > 100, 'Editor UI coordinated ImageGen prompt is missing')
        require(set(record['reference_sha256']) == set(record['reference_paths']), 'Editor UI coordinated generation references are incomplete')
        if 'inherits' in record:
            require(record['inherits'] == {'source_record': HISTORICAL_SOURCE_RECORD, 'generation': 'icons'}, 'Editor UI inherited sheet identity changed')
            original = historical_generations['icons']
            require(all(record.get(key) == original[key] for key in ('mode', 'prompt', 'transparent', 'reference_paths', 'reference_sha256', 'raw_sha256', 'dimensions')), 'Editor UI inherited v5 generation provenance changed')
            inherited_sources += 1
        else:
            require(set(record['reference_paths']) >= {REFERENCE, latest['path']}, 'Editor UI new generation does not use the latest B amendment composition')
            new_sources += 1
        for reference in record['reference_paths']:
            require(reference in referenced and record['reference_sha256'][reference] == referenced[reference]['sha256'], 'Editor UI generation reference hash changed')
        data = source.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        require(digest == record['raw_sha256'], f'Editor UI source changed: {relative}')
        source_dimensions, pixels = _decode_png(data)
        require(source_dimensions == record['dimensions'] and min(source_dimensions) >= 768, f'Editor UI full source resolution changed: {relative}')
        require(any(pixels[i] == 0 for i in range(3, len(pixels), 4)) and any(pixels[i] == 255 for i in range(3, len(pixels), 4)), f'Editor UI source lacks clean transparency: {relative}')
        sources[relative] = (digest, source_dimensions, pixels, record['id'])
    require(len(sources) == 3 and new_sources == 2 and inherited_sources == 1, 'Editor UI requires two coordinated v6 ImageGen sheets and the unchanged inherited v5 icon sheet')
    occupied = []
    used_sources = set()
    for identity in sorted(identities):
        entry = (styles | icons)[identity]
        record = generation['entries'][identity]
        kind = 'style' if identity in styles else 'icon'
        require(record['kind'] == kind and record['source'] in sources, f'Editor UI region source is missing: {identity}')
        digest, source_dimensions, pixels, generation_id = sources[record['source']]
        require(record.get('generation') == generation_id, f'Editor UI generation region identity changed: {identity}')
        require(record['source_sha256'] == digest, f'Editor UI region source hash changed: {identity}')
        region = _region(entry['region'], dimensions, f'atlas region: {identity}')
        require(record['region'] == entry['region'], f'Editor UI region registration changed: {identity}')
        source_region = _region(record['source_region'], source_dimensions, f'source region: {identity}')
        require(region[2:] == (source_region[2] + GUTTER * 2, source_region[3] + GUTTER * 2), f'Editor UI source crop was rescaled: {identity}')
        interior = [region[0] + GUTTER, region[1] + GUTTER, source_region[2], source_region[3]]
        require(_crop(atlas_pixels, dimensions, interior) == _crop(pixels, source_dimensions, source_region), f'Editor UI atlas pixels differ from the ImageGen source crop: {identity}')
        if identity == 'floor':
            original = historical['entries']['floor']
            original_source = _path(prototype, original['source'], 'historical Floor icon source')
            require(sha(original_source) == original['source_sha256'], 'Editor UI historical Floor icon source changed')
            original_dimensions, original_pixels = _decode_png(original_source.read_bytes())
            require(tuple(original['source_region'][2:]) == source_region[2:] and _crop(pixels, source_dimensions, source_region) == _crop(original_pixels, original_dimensions, original['source_region']), 'Editor UI approved Floor icon pixels changed')
        gutter_pixels = _crop(atlas_pixels, dimensions, region)
        row_stride = region[2] * 4
        clear_gutter = not any(gutter_pixels[3:GUTTER * row_stride:4]) and not any(gutter_pixels[(region[3] - GUTTER) * row_stride + 3::4])
        for row in range(GUTTER, region[3] - GUTTER):
            start = row * row_stride
            clear_gutter = clear_gutter and not any(gutter_pixels[start + 3:start + GUTTER * 4:4]) and not any(gutter_pixels[start + row_stride - GUTTER * 4 + 3:start + row_stride:4])
        require(clear_gutter, f'Editor UI sampling gutter is not transparent: {identity}')
        for other in occupied:
            require(region[0] + region[2] <= other[0] or other[0] + other[2] <= region[0] or region[1] + region[3] <= other[1] or other[1] + other[3] <= region[1], f'Editor UI atlas regions overlap: {identity}')
        occupied.append(region)
        used_sources.add(record['source'])
        require('image' not in entry, f'Editor UI bypasses the coordinated atlas: {identity}')
        if kind == 'style':
            _calibration(identity, entry, region)
            require(all(record.get(key) == entry[key] for key in ('slice_px', 'edge', 'content', 'stretch')), f'Editor UI calibration differs from its packing record: {identity}')
            require(record.get('minimum_height') == entry.get('minimum_height'), f'Editor UI minimum height differs from its packing record: {identity}')
            require(isinstance(entry.get('states', {}), dict), f'Invalid editor UI states: {identity}')
            for state, treatment in entry.get('states', {}).items():
                require(state in {'normal', 'pressed', 'disabled', 'selected', 'focus'}, f'Unknown editor UI state: {identity}')
                require((isinstance(treatment, str) and treatment in styles) or (isinstance(treatment, dict) and set(treatment) <= {'tint', 'draw_center'} and treatment), f'Editor UI state bypasses calibrated framing: {identity}')
                if isinstance(treatment, dict):
                    require(type(treatment.get('draw_center', True)) is bool and isinstance(treatment.get('tint', 'ffffffff'), str) and re.fullmatch(r'(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})', treatment.get('tint', 'ffffffff')), f'Invalid editor UI state treatment: {identity}')
    require(used_sources == set(sources), 'Editor UI generated sheets are unused')
    require({p.relative_to(runtime).as_posix() for p in runtime.rglob('*.png')} == {ATLAS}, 'Unexpected editor UI image payload')
    return {'images': 1, 'imagegen_sources': len(sources), 'styles': len(styles), 'icons': len(icons),
            'pill_styles': len(PILL_STYLES), 'pill_minimum_height': min(styles[identity]['minimum_height'] for identity in PILL_STYLES),
            'png_bytes': len(atlas_data), 'reference_sha256': manifest['reference_sha256'], 'runtime_images': [ATLAS]}


def verify_editor_ui(project: Path, source_project: Path | None = None) -> dict:
    project = Path(project).resolve()
    try:
        return _verify(project, Path(source_project or project).resolve())
    except ValueError:
        raise
    except (OSError, KeyError, TypeError, AttributeError, IndexError, struct.error, zlib.error) as error:
        raise ValueError(f'Invalid editor UI provenance: {error}') from error


if __name__ == '__main__':
    print(json.dumps(verify_editor_ui(Path(__file__).resolve().parents[1]), indent=2))
