#!/usr/bin/env python3
"""Read-only audit of issue-33 library.json and native source/capture evidence.

Canonical runtime schema: library.objects[].{id,status,family,frameSize,root,
sourceScale,footprint,projection,clips:[{id,fps,loop,frames,directions:{N:{image,
columns,rows},E:...,S:...,W:...}}],interactions:[{placements:[{object,...}]}]}.
Source evidence may be shared in library.source and extended per object.source:
{blend,modelScript,camera,rig,guide,rawFrames:[path...],hashes:{path:sha256}}.
Camera/rig/guide may be records or JSON paths. This script never modifies rasters,
models, metadata or the manifest. It writes only the explicitly requested report.
A structural pass does not establish visual/model/rig/animation quality.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

try:
    from PIL import Image
except ImportError:
    Image = None

DIRECTIONS = ['N', 'E', 'S', 'W']
READY = {'ready', 'published', 'user-approved'}
STATIC_STATES = {'static'}


_HASH_CACHE = {}


def sha256(path):
    path = Path(path)
    key = (str(path), path.stat().st_size, path.stat().st_mtime_ns)
    if key not in _HASH_CACHE:
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        _HASH_CACHE[key] = digest.hexdigest()
    return _HASH_CACHE[key]


def png_size(path):
    with path.open('rb') as stream:
        data = stream.read(24)
    if len(data) != 24 or data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
        raise ValueError('Not a PNG with an IHDR header')
    return struct.unpack('>II', data[16:24])


def finite_pair(value, positive=False):
    return (isinstance(value, list) and len(value) == 2 and
            all(isinstance(x, (int, float)) and math.isfinite(x) and
                (not positive or x > 0) for x in value))


def matrix_valid(value):
    return (isinstance(value, list) and len(value) == 4 and
            all(isinstance(row, list) and len(row) == 4 and
                all(isinstance(x, (int, float)) and math.isfinite(x) for x in row)
                for row in value))


def validate_variant_clips(variants, clips):
    """Bind each declared appearance to actual canonical runtime clip IDs.

    Native source names may contain underscores, but public variant references
    must already use normalized hyphens so a runtime lookup works without repair.
    This checks metadata integrity only; it does not grade variant appearance.
    """
    if not isinstance(variants, dict):
        return {}, []
    available = {clip.get('id') for clip in clips if isinstance(clip.get('id'), str)}
    records, errors = {}, []
    for variant, entry in variants.items():
        item = {'referencedClipIds': [], 'resolvedClipIds': [], 'errors': []}
        records[variant] = item
        references = entry.get('clips') if isinstance(entry, dict) else None
        if not isinstance(references, list) or not references:
            item['errors'].append('requires a nonempty clips list bound to actual runtime exports')
        else:
            for reference in references:
                if not isinstance(reference, str) or not reference:
                    item['errors'].append('clip reference must be a nonempty string')
                    continue
                item['referencedClipIds'].append(reference)
                normalized = reference.replace('_', '-')
                if reference != normalized:
                    item['errors'].append(f'clip reference {reference!r} is not normalized; use {normalized!r}')
                if normalized not in available:
                    item['errors'].append(f'references missing normalized runtime clip {normalized!r}')
                else:
                    item['resolvedClipIds'].append(normalized)
        item['valid'] = not item['errors']
        errors.extend(f'Variant {variant}: {error}' for error in item['errors'])
    return records, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--asset-root', type=Path)
    parser.add_argument('--coverage-plan', type=Path,
                        default=Path('/private/tmp/sushi33-production/coverage-plan.json'))
    parser.add_argument('--report', type=Path)
    parser.add_argument('--strict', action='store_true',
                        help='Exit 1 if any ready object fails or any planned coverage remains missing.')
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    asset_root = (args.asset_root or manifest_path.parent).resolve()
    manifest = json.loads(manifest_path.read_text())
    plan = json.loads(args.coverage_plan.read_text()) if args.coverage_plan.exists() else {'objects': []}
    expected = {o['id']: o for o in plan.get('objects', [])}
    objects = manifest.get('objects', [])
    object_ids = [o.get('id') for o in objects]
    by_id = {o.get('id'): o for o in objects}
    report = {'version': 1, 'mode': 'read-only-structural-audit',
              'manifest': str(manifest_path), 'manifestSHA256': sha256(manifest_path),
              'assetRoot': str(asset_root), 'visualReview': 'not-established-by-this-audit',
              'pngCropInspection': bool(Image), 'globalErrors': [], 'objects': [],
              'missingObjectIds': sorted(set(expected) - set(object_ids)),
              'unplannedObjectIds': sorted(set(object_ids) - set(expected))}
    if len(set(object_ids)) != len(object_ids):
        report['globalErrors'].append('Duplicate object IDs')
    if manifest.get('cellSize') != 128:
        report['globalErrors'].append('Expected shared logical cellSize=128')
    if not objects:
        report['globalErrors'].append('No objects in library')

    def file_path(value):
        if not isinstance(value, str) or not value:
            raise ValueError('Expected a nonempty source/image path')
        p = Path(value)
        return p.resolve() if p.is_absolute() else (asset_root / p).resolve()

    def load_record(value):
        if isinstance(value, dict):
            return value
        return json.loads(file_path(value).read_text())

    for obj in objects:
        oid = obj.get('id')
        result = {'id': oid, 'status': obj.get('status'), 'errors': [], 'warnings': [],
                  'clips': [], 'sourceFiles': [], 'coverage': {}}
        report['objects'].append(result)
        errors, warnings = result['errors'], result['warnings']
        planned = expected.get(oid, {})
        if not isinstance(oid, str) or not oid:
            errors.append('Missing stable object ID')
        if obj.get('status') not in READY:
            result['auditStatus'] = 'pending-production'
            continue
        size, root, scale = obj.get('frameSize'), obj.get('root'), obj.get('sourceScale', 1)
        if not finite_pair(size, True):
            errors.append('frameSize must contain two positive finite values')
            size = [192, 320]
        if not finite_pair(root):
            errors.append('root must contain two finite values')
            root = [96, 248]
        if not (0 <= root[0] <= size[0] and 0 <= root[1] <= size[1]):
            errors.append('Authored root lies outside complete frame')
        if not isinstance(scale, (int, float)) or not math.isfinite(scale) or scale <= 0:
            errors.append('sourceScale must be positive finite')
            scale = 1
        footprint = obj.get('footprint')
        if not finite_pair(footprint, True):
            errors.append('Explicit footprint is missing')
        elif any(int(v) != v for v in footprint):
            warnings.append('Non-integer bounding footprint: declare explicit integer occupied/support cells independently')
        projection = obj.get('projection')
        if projection not in {'square-top-front-oblique', 'top-down-oblique-square-grid',
                              'character-orthographic'}:
            errors.append('Undeclared/unsupported projection')
        if planned.get('projection') == 'character-orthographic' and projection != 'character-orthographic':
            errors.append('Character/rounded actor requires declared ordinary orthographic art camera')
        source = {}
        if isinstance(manifest.get('source'), dict):
            source.update(manifest['source'])
        if isinstance(obj.get('source'), dict):
            source.update(obj['source'])
        for key in ['blend', 'modelScript']:
            value = source.get(key)
            if not value:
                errors.append(f'Missing native source.{key}')
                continue
            try:
                p = file_path(value)
                if not p.is_file():
                    raise ValueError('file is absent')
                if key == 'blend':
                    with p.open('rb') as stream:
                        signature = stream.read(12)
                    # Native uncompressed, gzip-compressed, and Blender 3.x+ zstd-compressed files.
                    if not (signature.startswith(b'BLENDER') or signature.startswith(b'\x1f\x8b') or
                            signature.startswith(b'\x28\xb5\x2f\xfd')):
                        raise ValueError('invalid Blender file signature')
                result['sourceFiles'].append({'role': key, 'path': str(p), 'sha256': sha256(p)})
            except Exception as exc:
                errors.append(f'Invalid {key}: {exc}')
        camera = None
        if not source.get('camera'):
            errors.append('Missing source.camera actual fixed-camera record')
        else:
            try:
                camera = load_record(source['camera'])
                cam = camera.get('camera', camera)
                if not matrix_valid(cam.get('worldMatrix')) or not matrix_valid(cam.get('projectionMatrix')):
                    errors.append('Camera needs actual finite 4x4 world/projection matrices')
                if cam.get('type') not in {'orthographic', 'ORTHO'}:
                    errors.append('Camera must be orthographic')
                if camera.get('root', camera.get('anchor', root)) != root:
                    errors.append('Camera root/anchor differs from manifest root')
                if camera.get('frame', size) != size:
                    errors.append('Camera full frame differs from manifest frameSize')
            except Exception as exc:
                errors.append(f'Invalid camera record: {exc}')
        if (obj.get('kind') == 'character' or obj.get('family') == 'W15') and not source.get('rig'):
            errors.append('Character is missing source.rig evidence')
        if not source.get('guide'):
            errors.append('Missing authored registration source.guide')
        if not source.get('rawFrames'):
            warnings.append('No raw capture frame list supplied: native frame provenance not independently traversed')
        for value in source.get('rawFrames', []):
            try:
                p = file_path(value['image'] if isinstance(value, dict) else value)
                actual = png_size(p)
                raw_scale = (camera or {}).get('captureScale', obj.get('registration', {}).get('sourceCaptureScale', scale))
                if actual != (int(size[0] * raw_scale), int(size[1] * raw_scale)):
                    errors.append(f'Raw frame {p.name} differs from complete declared native capture frame: {actual}')
                if isinstance(value, dict) and value.get('sha256') and sha256(p) != value['sha256']:
                    errors.append(f'Raw source capture hash mismatch: {p.name}')
            except Exception as exc:
                errors.append(f'Invalid raw frame: {exc}')
        for value, digest in source.get('hashes', {}).items():
            try:
                if sha256(file_path(value)) != digest:
                    errors.append(f'Source hash mismatch: {value}')
            except Exception as exc:
                errors.append(f'Source hash unavailable for {value}: {exc}')

        requirements = obj.get('requirements', {})
        required_states = requirements.get('states', planned.get('states', []))
        required_dirs = requirements.get('directions', planned.get('directions', DIRECTIONS))
        clips = obj.get('clips', [])
        seen_states = set()
        for clip in clips:
            cid = clip.get('id')
            state = clip.get('state', cid)
            seen_states.add(state)
            frames = clip.get('frames')
            clip_result = {'id': cid, 'directions': {}, 'errors': []}
            result['clips'].append(clip_result)
            ce = clip_result['errors']
            is_static = bool(clip.get('static')) or state in STATIC_STATES
            if not isinstance(frames, int) or frames < 1:
                ce.append('frames must be a positive integer')
                frames = 0
            if clip.get('fps') != 12:
                ce.append('Authoritative timing must be exactly 12 fps')
            if not is_static and frames < 6:
                ce.append('Animated clip has fewer than six sampled frames')
            if clip.get('frameOrder') is not None and clip['frameOrder'] != list(range(frames)):
                ce.append('Explicit frameOrder does not match sequential complete panel order')
            direction_map = clip.get('directions', {})
            missing_dirs = sorted(set(required_dirs) - set(direction_map))
            if missing_dirs:
                ce.append('Missing directions: ' + ', '.join(missing_dirs))
            for direction, panel in direction_map.items():
                dr = {'errors': []}
                clip_result['directions'][direction] = dr
                de = dr['errors']
                try:
                    image_path = file_path(panel.get('image'))
                    width, height = png_size(image_path)
                    columns, rows = panel.get('columns'), panel.get('rows', 1)
                    if not isinstance(columns, int) or not isinstance(rows, int) or columns < 1 or rows < 1:
                        raise ValueError('positive integer columns and rows required')
                    if columns * rows < frames:
                        de.append('Atlas panel count smaller than clip frames')
                    cell = (int(size[0] * scale), int(size[1] * scale))
                    if (width, height) != (cell[0] * columns, cell[1] * rows):
                        de.append(f'Atlas {width}x{height} differs from complete panel grid {cell[0]*columns}x{cell[1]*rows}')
                    dr.update(image=str(image_path), pngSize=[width, height], panelSize=list(cell), sha256=sha256(image_path))
                    if Image and not de:
                        signatures = []
                        with Image.open(image_path) as im:
                            rgba = im.convert('RGBA')
                            for index in range(frames):
                                x, y = (index % columns) * cell[0], (index // columns) * cell[1]
                                crop = rgba.crop((x, y, x + cell[0], y + cell[1]))
                                if crop.getchannel('A').getbbox() is None:
                                    de.append(f'Frame {index} is completely transparent')
                                signatures.append(hashlib.sha256(crop.tobytes()).hexdigest())
                        unique = len(set(signatures))
                        dr['uniquePixelFrames'] = unique
                        dr['frameSHA256'] = signatures
                        if not is_static and unique < 6:
                            de.append(f'Only {unique} unique PNG frame drawings; need at least six')
                        if not is_static and frames > 1 and signatures[0] == signatures[-1]:
                            warnings.append(f'{cid}/{direction}: first/last pixel frames equal; inspect duplicate closing pose')
                    elif not Image:
                        warnings.append(f'{cid}/{direction}: Pillow absent; unique crop pixels not inspected')
                except Exception as exc:
                    de.append(str(exc))
                if de:
                    ce.extend(f'{direction}: {e}' for e in de)
            if ce:
                errors.extend(f'{cid}: {e}' for e in ce)
        missing_states = sorted(set(required_states) - seen_states)
        result['coverage'].update(requiredStates=required_states, seenStates=sorted(seen_states), missingStates=missing_states)
        if missing_states:
            errors.append('Missing required states: ' + ', '.join(missing_states))
        required_variants = requirements.get('variants', planned.get('variants', ['default']))
        declared_variants = obj.get('variants', [])
        variant_records, variant_errors = validate_variant_clips(declared_variants, clips)
        result['coverage']['variantClipBindings'] = variant_records
        errors.extend(variant_errors)
        if isinstance(declared_variants, dict):
            declared_variants = list(declared_variants)
        available_variants = {v.get('id') if isinstance(v, dict) else v for v in declared_variants}
        available_variants.update(clip.get('variant') for clip in clips if clip.get('variant'))
        available_variants.update(clip.get('id') for clip in clips)
        missing_variants = sorted(set(required_variants) - available_variants - {'default'})
        result['coverage']['missingVariants'] = missing_variants
        if missing_variants:
            errors.append('Missing explicit required variant coverage: ' + ', '.join(missing_variants))
        if not clips:
            errors.append('Ready object has no reusable sprites/clips')
        interactions = obj.get('interactions', [])
        if not interactions:
            errors.append('Ready object has no explicit interaction size-comparison composition')
        for scene in interactions:
            placements = scene.get('placements', [])
            ids = [p.get('object') for p in placements]
            if oid not in ids:
                errors.append('Interaction composition does not include reviewed object: ' + str(scene.get('name')))
            for target in ids:
                if target not in by_id:
                    errors.append('Interaction references unknown object: ' + str(target))
                elif by_id[target].get('status') not in READY:
                    warnings.append('Interaction target not produced yet: ' + str(target))
        if planned.get('family') == 'W04':
            if obj.get('portDefinition', obj.get('ports')) != planned.get('ports'):
                errors.append('Directed conveyor incoming/outgoing ports differ from planned module')
            if not source.get('connectedSystem'):
                warnings.append('No explicit connected belt source-system reference; visual seam/transport review still required')
        if not source.get('poseSignatures'):
            warnings.append('No native pose signatures supplied; pixel uniqueness is not rig proof')
        result['auditStatus'] = 'structural-fail' if errors else 'structural-pass-visual-review-pending'

    statuses = [o['auditStatus'] for o in report['objects']]
    report['summary'] = {'objects': len(objects), 'readyAudited': sum(s != 'pending-production' for s in statuses),
                         'pendingProduction': statuses.count('pending-production'),
                         'structuralFailures': statuses.count('structural-fail'),
                         'structuralPasses': statuses.count('structural-pass-visual-review-pending'),
                         'errors': len(report['globalErrors']) + sum(len(o['errors']) for o in report['objects']),
                         'warnings': sum(len(o['warnings']) for o in report['objects']),
                         'fullCoverageComplete': (not report['missingObjectIds'] and
                                                  all(s == 'structural-pass-visual-review-pending' for s in statuses) and
                                                  bool(statuses))}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary'], indent=2))
    if args.strict and (report['summary']['errors'] or not report['summary']['fullCoverageComplete']):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
