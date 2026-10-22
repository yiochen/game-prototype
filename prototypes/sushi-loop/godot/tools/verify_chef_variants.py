#!/usr/bin/env python3
"""Stdlib release verification for the isolated issue11 native chef variants."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import zlib

IDS = ['chef-omar']
CLIPS = ['hold-cucumber', 'load-cucumber']
DIRECTIONS = ['N', 'E', 'S', 'W']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise ValueError(f'Missing or invalid chef variant metadata: {path}') from error


def _verify_chef_variants(project: Path, source_project: Path | None = None) -> dict:
    project = Path(project).resolve()
    source_project = Path(source_project or project).resolve()
    prototype = source_project.parent
    author = prototype / 'assets/production/source/variants/chef-cucumber'
    runtime = project / 'assets/chef-variants'
    manifest = read(runtime / 'manifest.json')
    if 'refinement' in manifest:
        from refined_actor_variants import verify_refined_actor_variants
        return verify_refined_actor_variants(project, source_project, 'chef')
    publication = read(author / 'publication.json')
    authorship = read(author / 'authorship.json')
    native_audit = read(author / 'native-audit.json')
    editable = read(author / 'finalized-project.json')
    base = read(source_project / 'assets/catalog/manifest.json')
    require(manifest.get('version') == 1, 'Unsupported chef manifest version')
    require(manifest.get('baseLibrarySha256') == sha(prototype / 'assets/production/library.json'), 'Chef variants refer to a stale approved library')
    require(set(manifest.get('objects', {})) == set(IDS), 'Chef variant chef identity coverage is incomplete')
    require(authorship.get('bodyGeometryUnchanged') is True and not authorship.get('foreignObjects'), 'Native chef body/isolation audit did not pass')
    require(authorship['captureContract'] == {'frameSize': [192, 320], 'root': [96, 248], 'sourceScale': 4, 'runtimeScale': 2, 'frames': 12, 'fps': 12, 'directions': DIRECTIONS}, 'Native capture registration changed')
    require(authorship['derivativeBlend']['sha256'] == sha(author / 'chef-cucumber.blend') == publication['sourceBlendSha256'], 'Chef captures are stale relative to editable Blender source')
    require(native_audit.get('passed') is True and native_audit.get('poseFacingSamples') == 96 and native_audit.get('sourceBlendSha256') == publication['sourceBlendSha256'] and native_audit.get('approvedCucumberPackedBytesMatch') is True, 'Native food/visibility/geometry audit did not pass')
    require(editable['captureSource']['sha256'] == publication['sourceBlendSha256'] and editable.get('geometryOrAnimationEdits') is False and editable['editableProject']['sha256'] == sha(author / editable['editableProject']['file']), 'Editable chef project is stale or modified after capture')
    require(authorship['authorScriptSha256'] == sha(author / 'author_chef.py'), 'Chef authoring script changed after native authorship')
    require(authorship['approvedFood']['sha256'] == sha(prototype / authorship['approvedFood']['path']), 'Approved ImageGen cucumber source changed')
    require(authorship['baseBlend']['sha256'] == sha(prototype / authorship['baseBlend']['path']), 'Approved native base project changed')
    files = manifest.get('sourceFiles', {})
    require(isinstance(files, dict) and len(files) >= 20, 'Chef source provenance is incomplete')
    for relative, expected in files.items():
        path = (prototype / relative).resolve()
        require(path.is_relative_to(prototype), 'Chef source path escapes the prototype')
        require(path.is_file() and sha(path) == expected, f'Chef source metadata or helper changed: {relative}')
    frame_count = 0
    expected_files = set()
    for identity in IDS:
        obj = manifest['objects'][identity]
        expected = base['objects'][identity]
        for key in ['frameSize', 'root', 'sourceScale', 'projection']:
            require(obj.get(key) == expected[key], f'Chef variant changed fixed {key}: {identity}')
        require(set(obj.get('clips', {})) == set(CLIPS), f'Incorrect chef variants for {identity}')
        edit = authorship['edits'][identity]
        require(edit['foodSourceSha256'] == authorship['approvedFood']['sha256'] and len(edit['unchangedActions']) == 12, f'Incorrect food/visibility native edit: {identity}')
        for clip in CLIPS:
            action = obj['clips'][clip]
            require(action['id'] == clip and action['frames'] == 12 and action['fps'] == 12 and action['loop'] is (clip != 'load-cucumber') and action['frameOrder'] == list(range(12)), f'Incorrect authored timing: {identity}/{clip}')
            require(set(action.get('directions', {})) == set(DIRECTIONS), f'Missing chef facing: {identity}/{clip}')
            for direction in DIRECTIONS:
                entry = action['directions'][direction]
                relative = f'sprites/{identity}/{clip}-{direction}.png'
                require(entry['image'] == relative, 'Unexpected chef atlas reference')
                expected_files.add(relative)
                path = runtime / relative
                require(path.is_file(), f'Missing chef atlas: {relative}')
                raw = path.read_bytes()
                require(raw[:8] == b'\x89PNG\r\n\x1a\n' and len(raw) > 32, f'Invalid chef PNG: {relative}')
                require(list(struct.unpack('>II', raw[16:24])) == [2304, 1280] == entry['atlasSize'], f'Incorrect complete-frame atlas dimensions: {relative}')
                require(entry['columns'] == 6 and entry['rows'] == 2 and entry['rects'] == [[i % 6 * 384, i // 6 * 640, 384, 640] for i in range(12)], f'Stale or cropped chef frame regions: {relative}')
                require(sha(path) == entry['sha256'] == publication['atlases'][relative]['sha256'], f'Chef atlas bytes changed: {relative}')
                require(len(raw) == publication['atlases'][relative]['bytes'], f'Incomplete chef atlas: {relative}')
                frame_count += 12
    actual_files = {str(path.relative_to(runtime)) for path in (runtime / 'sprites').rglob('*.png')}
    require(actual_files == expected_files == set(publication['atlases']), 'Unexpected or missing chef atlas payload')
    captures = publication.get('captures', [])
    require(publication.get('frames') == frame_count == 96 and publication.get('atlasCount') == len(expected_files) == 8 and len(captures) == 96, 'Incomplete native chef capture evidence')
    keys = set()
    for capture in captures:
        key = (capture['assetId'], capture['clip'], capture['direction'], capture['index'])
        keys.add(key)
        require(capture['state'] == 'complete' and capture['sourceBlendSha256'] == publication['sourceBlendSha256'] and capture['fps'] == 12 and [capture['width'], capture['height']] == [768, 1280] and len(capture['sha256']) == 64 and len(capture['runtimePixelSha256']) == 64, 'Invalid native frame receipt')
        worker = read(author / 'export/capture-workers' / (capture['worker'] + '.status.json'))
        require(worker['state'] == 'complete' and worker['nativeSource']['blend'] == publication['sourceBlendSha256'] and worker['nativeSource']['samples'] == 32, 'Incomplete or stale native worker')
    require(keys == {(identity, clip, direction, index) for identity in IDS for clip in CLIPS for direction in DIRECTIONS for index in range(12)}, 'Duplicated or missing native chef frame receipts')
    return {'objects': len(IDS), 'atlases': len(expected_files), 'frames': frame_count, 'png_bytes': sum((runtime / path).stat().st_size for path in expected_files), 'blend_sha256': publication['sourceBlendSha256']}


def verify_chef_variants(project: Path, source_project: Path | None = None) -> dict:
    try:
        return _verify_chef_variants(project, source_project)
    except ValueError:
        raise
    except (OSError, KeyError, TypeError, AttributeError, IndexError, struct.error, zlib.error) as error:
        raise ValueError(f'Incomplete or invalid native chef variant contract: {error}') from error


if __name__ == '__main__':
    print(json.dumps(verify_chef_variants(Path(__file__).resolve().parents[1]), indent=2))
