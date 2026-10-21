#!/usr/bin/env python3
"""Verify native Blender editor previews and unchanged atlas render pixels."""
from pathlib import Path
import json
import math
import re
import struct
import zlib

from verify_editor_ui import _crop, _decode_png, _path, _region, require, sha

SOURCE_ROOT = 'assets/ui/editor/goods-v1'
PRODUCTION_BLEND = 'assets/production/source/blender/sushi-loop-world-library.blend'
PRODUCTION_BLEND_SHA256 = 'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
SPRITES = {'belt-straight-e', 'stool-wood', 'plant-angular', 'crate-wood',
           'barrel-wood', 'floor-cream'}
ATLAS = 'atlas.png'
FRAME_SIZE = [384, 384]
GUTTER = 4
METHOD = 'Blender MCP native render'


def _camera(camera):
    require(isinstance(camera, dict) and isinstance(camera.get('id'), str) and camera['id'], 'Editor goods camera identity is missing')
    require(camera.get('projection') == 'ordinary-orthographic-three-quarter', 'Editor goods require the three-quarter UI camera')
    require(camera.get('pixel_aspect') == [1, 1], 'Editor goods pixel aspect changed')
    require(camera.get('elevation_degrees') == 35 and camera.get('azimuth_degrees') == 35, 'Editor goods camera angle changed')


def _alpha_bounds(pixels, dimensions):
    width, height = dimensions
    occupied = [(index % width, index // width) for index, alpha in enumerate(pixels[3::4]) if alpha]
    require(occupied, 'Editor goods render is empty')
    left = min(x for x, _ in occupied)
    top = min(y for _, y in occupied)
    return [left, top, max(x for x, _ in occupied) + 1, max(y for _, y in occupied) + 1]


def _verify(project, source_project):
    prototype = source_project.parent
    runtime = project / 'assets/ui/editor-goods'
    manifest = json.loads((runtime / 'manifest.json').read_text())
    require(type(manifest.get('schema_version')) is int and manifest['schema_version'] == 1 and set(manifest.get('sprites', {})) == SPRITES, 'Editor goods identity coverage/version changed')
    require(manifest.get('atlas') == ATLAS, 'Editor goods atlas path changed')
    require(manifest.get('padding') == GUTTER and manifest.get('native_render_size') == FRAME_SIZE, 'Editor goods native render/sampling size changed')
    provenance = manifest['provenance']
    require(provenance.get('source_root') == SOURCE_ROOT and provenance.get('method') == METHOD, 'Editor goods require the native Blender source contract')
    source = _path(prototype, SOURCE_ROOT, 'goods source root')
    require(provenance.get('production_blend') == PRODUCTION_BLEND, 'Editor goods approved production source changed')
    require(sha(_path(prototype, PRODUCTION_BLEND, 'production Blender source')) == provenance['production_blend_sha256'] == PRODUCTION_BLEND_SHA256, 'Editor goods production Blender source hash changed')
    for field in ('blend', 'recipe', 'packing_recipe', 'records'):
        require(sha(_path(source, provenance[field], f'goods {field}')) == provenance[f'{field}_sha256'], f'Editor goods {field} source hash changed')
    records = json.loads(_path(source, provenance['records'], 'goods capture record').read_text())
    require(type(records.get('schema_version')) is int and records['schema_version'] == 1 and records.get('method') == METHOD, 'Editor goods native capture receipt changed')
    require(records.get('main_file_preserved') is True and records.get('original_scene_restored') is True, 'Editor goods native source preservation receipt is incomplete')
    for field in ('production_blend', 'blend', 'recipe'):
        require(records.get(field) == provenance[field] and records.get(f'{field}_sha256') == provenance[f'{field}_sha256'], f'Editor goods capture {field} registration changed')
    require(set(records.get('sprites', {})) == SPRITES, 'Editor goods capture coverage is incomplete')
    camera = manifest['camera']
    _camera(camera)
    atlas = runtime / ATLAS
    data = atlas.read_bytes()
    require(sha(atlas) == manifest['atlas_sha256'] and len(data) == manifest['atlas_bytes'], 'Editor goods atlas pixels changed')
    dimensions, pixels = _decode_png(data)
    require(dimensions == manifest['atlas_size'], 'Editor goods atlas dimensions changed')
    occupied = []
    for identity, entry in sorted(manifest['sprites'].items()):
        record = records['sprites'][identity]
        require(record.get('art_id') == identity and record.get('source_production_sha256') == provenance['production_blend_sha256'], f'Editor goods native identity/source changed: {identity}')
        require(record.get('source_collection') == entry.get('source_collection') and isinstance(entry.get('source_collection'), str) and entry['source_collection'], f'Editor goods native collection changed: {identity}')
        require(isinstance(record.get('native_objects'), list) and record['native_objects'] and isinstance(record.get('geometry_origin'), str) and record['geometry_origin'], f'Editor goods editable geometry receipt is missing: {identity}')
        require(isinstance(entry.get('geometry_sha256'), str) and re.fullmatch(r'[a-f0-9]{64}', entry['geometry_sha256']) and record.get('geometry_sha256') == entry['geometry_sha256'], f'Editor goods geometry registration changed: {identity}')
        _camera(record['camera'])
        require(all(record['camera'].get(key) == camera[key] for key in ('id', 'projection', 'elevation_degrees', 'azimuth_degrees', 'pixel_aspect')), f'Editor goods capture camera changed: {identity}')
        require(entry.get('camera') == record['camera'], f'Editor goods native camera registration changed: {identity}')
        require(entry.get('native_collection') == record.get('native_collection') and isinstance(entry.get('native_collection'), str) and entry['native_collection'], f'Editor goods editable native collection changed: {identity}')
        require(record['camera'].get('resolution') == FRAME_SIZE and entry.get('camera_id') == camera['id'], f'Editor goods native capture dimensions/camera changed: {identity}')
        require(entry.get('source_render') == record.get('source_render'), f'Editor goods source render registration changed: {identity}')
        render = _path(source, entry['source_render'], 'goods source render')
        require(render.is_relative_to(source / 'renders'), f'Editor goods render escapes the source render folder: {identity}')
        require(sha(render) == entry['source_sha256'] == record['source_sha256'], f'Editor goods native render hash changed: {identity}')
        render_dimensions, render_pixels = _decode_png(render.read_bytes())
        require(render_dimensions == FRAME_SIZE and any(alpha == 0 for alpha in render_pixels[3::4]) and any(alpha == 255 for alpha in render_pixels[3::4]), f'Editor goods render dimensions/transparency changed: {identity}')
        require(entry.get('alpha_bounds') == _alpha_bounds(render_pixels, render_dimensions), f'Editor goods render alpha bounds changed: {identity}')
        region = _region(entry['region'], dimensions, f'goods atlas region: {identity}')
        require(list(region[2:]) == FRAME_SIZE, f'Editor goods native render was rescaled: {identity}')
        require(_crop(pixels, dimensions, region) == render_pixels, f'Editor goods atlas pixels differ from the native Blender render: {identity}')
        padded = _region([region[0] - GUTTER, region[1] - GUTTER, region[2] + GUTTER * 2, region[3] + GUTTER * 2], dimensions, f'goods sampling gutter: {identity}')
        padding = _crop(pixels, dimensions, padded)
        stride = padded[2] * 4
        require(not any(padding[3:GUTTER * stride:4]) and not any(padding[(padded[3] - GUTTER) * stride + 3::4]), f'Editor goods sampling gutter is not transparent: {identity}')
        for row in range(GUTTER, padded[3] - GUTTER):
            start = row * stride
            require(not any(padding[start + 3:start + GUTTER * 4:4]) and not any(padding[start + stride - GUTTER * 4 + 3:start + stride:4]), f'Editor goods sampling gutter is not transparent: {identity}')
        for other in occupied:
            require(padded[0] + padded[2] <= other[0] or other[0] + other[2] <= padded[0] or padded[1] + padded[3] <= other[1] or other[1] + other[3] <= padded[1], f'Editor goods atlas regions overlap: {identity}')
        occupied.append(padded)
        if identity == 'floor-cream':
            thickness = entry.get('floor_thickness')
            require(type(thickness) in (int, float) and math.isfinite(thickness) and thickness > 0 and thickness == record.get('floor_thickness'), 'Editor goods floor tile has no physical thickness')
    require({path.relative_to(runtime).as_posix() for path in runtime.rglob('*.png')} == {ATLAS}, 'Unexpected editor goods image payload')
    return {'images': 1, 'sprites': len(SPRITES), 'png_bytes': len(data), 'source_root': SOURCE_ROOT,
            'source_blend_sha256': provenance['blend_sha256'], 'runtime_images': [ATLAS]}


def verify_editor_goods(project: Path, source_project: Path | None = None) -> dict:
    project = Path(project).resolve()
    try:
        return _verify(project, Path(source_project or project).resolve())
    except ValueError:
        raise
    except (OSError, KeyError, TypeError, AttributeError, IndexError, struct.error, zlib.error) as error:
        raise ValueError(f'Invalid editor goods provenance: {error}') from error


if __name__ == '__main__':
    print(json.dumps(verify_editor_goods(Path(__file__).resolve().parents[1]), indent=2))
