#!/usr/bin/env python3
"""Stdlib verification for isolated issue11 ImageGen smiling-face feedback."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct

CLIPS = ['happy-smile-appear', 'happy-smile-idle', 'happy-smile-fade', 'happy-smile-transition']


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def _verify_feedback_variants(project: Path, source_project: Path | None = None) -> dict:
    project = Path(project).resolve()
    source_project = Path(source_project or project).resolve()
    prototype = source_project.parent
    source = prototype / 'assets/production/source/variants/customer-feedback'
    runtime = project / 'assets/feedback-variants'
    manifest = read(runtime / 'manifest.json')
    generation = read(source / 'imagegen.json')
    publication = read(source / 'publication.json')
    base = read(source_project / 'assets/catalog/manifest.json')['objects']['bubble-happy']
    require(manifest.get('version') == 1 and set(manifest.get('objects', {})) == {'bubble-happy'}, 'Invalid smiling-face feedback identity/version')
    require(manifest['baseLibrarySha256'] == sha(prototype / 'assets/production/library.json'), 'Smiling-face feedback refers to a stale approved library')
    require(generation.get('pipeline') == 'builtin-image_gen-edit' and generation.get('transparent_background') is True and isinstance(generation.get('prompt'), str) and generation['prompt'].strip(), 'ImageGen edit provenance is missing')
    original = prototype / 'assets/production/source/2d/generated/bubble-happy.png'
    require(sha(original) == generation['reference_sha256'], 'Approved heart-bubble reference changed')
    output = source / generation['output']
    require(output.resolve().is_relative_to(source) and sha(output) == generation['output_sha256'] == publication['source']['sha256'], 'Generated smiling-face image changed')
    raw = output.read_bytes()
    require(raw[:8] == b'\x89PNG\r\n\x1a\n' and list(struct.unpack('>II', raw[16:24])) == publication['source']['dimensions'] and raw[25] == 6, 'Smiling-face source lacks its recorded full RGBA dimensions')
    require(publication['source']['alphaRange'] == [0, 255] and len(publication['source']['fixedAlphaRectangle']) == 4, 'Smiling-face source transparency/registration proof is incomplete')
    require(publication['registration'] == {'frameSize': [192, 320], 'root': [96, 248], 'sourceScale': 2, 'cellSize': 128, 'frames': 12, 'fps': 12}, 'Smiling-face fixed frame/root/timing changed')
    expected_sources = {str(path.relative_to(prototype)) for path in [output, source / 'imagegen.json', source / 'pack_feedback.py', source / 'publication.json']}
    require(set(manifest.get('sourceFiles', {})) == expected_sources, 'Smiling-face source provenance set is incomplete')
    for relative, expected in manifest['sourceFiles'].items():
        path = (prototype / relative).resolve()
        require(path.is_relative_to(prototype) and sha(path) == expected, f'Smiling-face source/helper changed: {relative}')
    obj = manifest['objects']['bubble-happy']
    for key in ['frameSize', 'root', 'sourceScale', 'projection']:
        require(obj.get(key) == base[key], f'Smiling-face feedback changed approved {key}')
    require(set(obj.get('clips', {})) == set(CLIPS), 'Smiling-face animation coverage is incomplete')
    images = set()
    for clip in CLIPS:
        action = obj['clips'][clip]
        require(action['id'] == clip and action['frames'] == 12 and action['fps'] == 12 and action['loop'] is clip.endswith('-idle') and action['frameOrder'] == list(range(12)) and set(action['directions']) == {'S'}, f'Smiling-face cadence/facing changed: {clip}')
        entry = action['directions']['S']
        relative = f'sprites/bubble-happy/{clip}-S.png'
        images.add(relative)
        require(entry['image'] == relative and entry['columns'] == 6 and entry['rows'] == 2 and entry['atlasSize'] == [2304, 1280] and entry['rects'] == [[i % 6 * 384, i // 6 * 640, 384, 640] for i in range(12)], f'Smiling-face frame regions were cropped or shifted: {clip}')
        path = runtime / relative
        raw = path.read_bytes()
        record = publication['atlases'][relative]
        require(raw[:8] == b'\x89PNG\r\n\x1a\n' and list(struct.unpack('>II', raw[16:24])) == [2304, 1280], f'Smiling-face atlas dimensions are invalid: {clip}')
        require(sha(path) == entry['sha256'] == record['sha256'] and len(raw) == record['bytes'], f'Smiling-face atlas pixels changed: {clip}')
        require(len(record['framePixels']) == 12 and len(set(record['framePixels'])) >= 6 and all(len(value) == 64 for value in record['framePixels']), f'Smiling-face unique-frame evidence is incomplete: {clip}')
    require({str(path.relative_to(runtime)) for path in (runtime / 'sprites').rglob('*.png')} == images == set(publication['atlases']), 'Unexpected or missing smiling-face atlas payload')
    return {'objects': 1, 'atlases': 4, 'frames': 48, 'png_bytes': sum((runtime / path).stat().st_size for path in images), 'image_sha256': generation['output_sha256']}


def verify_feedback_variants(project: Path, source_project: Path | None = None) -> dict:
    try:
        return _verify_feedback_variants(project, source_project)
    except ValueError:
        raise
    except (OSError, KeyError, TypeError, AttributeError, IndexError, struct.error) as error:
        raise ValueError(f'Incomplete or invalid smiling-face feedback contract: {error}') from error


if __name__ == '__main__':
    print(json.dumps(verify_feedback_variants(Path(__file__).resolve().parents[1]), indent=2))
