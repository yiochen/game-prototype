#!/usr/bin/env python3
"""Verify ImageGen editor UI provenance and exact production PNG payload."""
from pathlib import Path
import hashlib
import json
import struct

ASSETS = {'button-wood', 'button-live', 'people', 'layout', 'floor', 'rotate', 'remove', 'caret-left', 'caret-right'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def png(path):
    data = path.read_bytes()
    require(data[:8] == b'\x89PNG\r\n\x1a\n' and data[25] == 6, f'Expected RGBA PNG: {path.name}')
    return list(struct.unpack('>II', data[16:24]))


def verify_editor_ui(project: Path, source_project: Path | None = None) -> dict:
    project = Path(project).resolve()
    prototype = Path(source_project or project).resolve().parent
    runtime = project / 'assets/ui/editor'
    try:
        manifest = json.loads((runtime / 'manifest.json').read_text())
        require(manifest.get('version') == 1 and set(manifest.get('assets', {})) == ASSETS, 'Editor UI asset coverage is incomplete')
        require(manifest['reference'] == 'design/art-directions/restaurant-item-catalog.png', 'Editor UI uses the wrong catalog reference')
        require(sha(prototype / manifest['reference']) == manifest['reference_sha256'], 'Editor UI catalog reference changed')
        source_record = (prototype / manifest['source_record']).resolve()
        require(source_record.is_relative_to(prototype) and sha(source_record) == manifest['source_record_sha256'], 'Editor ImageGen prompt record changed')
        generation = json.loads(source_record.read_text())
        require(sha(source_record.parent / 'pack.py') == manifest['packing_script_sha256'], 'Editor UI packing procedure changed')
        generated = {entry['id']: entry for entry in generation['assets']}
        require(set(generated) == ASSETS - {'caret-right'}, 'Editor ImageGen prompt set is incomplete')
        total_bytes = 0
        for identity, entry in manifest['assets'].items():
            path = (runtime / entry['image']).resolve()
            require(path.parent == runtime and path.name == identity + '.png', f'Invalid editor UI path: {identity}')
            require(sha(path) == entry['sha256'] and path.stat().st_size == entry['bytes'], f'Editor UI pixels changed: {identity}')
            require(png(path) == entry['dimensions'] and max(entry['dimensions']) >= 250, f'Editor UI resolution changed: {identity}')
            total_bytes += entry['bytes']
            if identity == 'caret-right':
                require(entry.get('derived_from') == 'caret-left' and entry.get('operation') == 'horizontal mirror', 'Right caret lacks mirror provenance')
                continue
            record = generated[identity]
            require(record.get('mode') == 'builtin-image_gen' and record.get('transparent_background') is True and len(record.get('prompt', '')) > 100, f'Missing ImageGen source prompt: {identity}')
            source = (prototype / entry['source']).resolve()
            require(source.is_relative_to(source_record.parent) and source == source_record.parent / record['raw'] and sha(source) == entry['source_sha256'], f'Editor UI source changed: {identity}')
            require(png(source) == entry['source_dimensions'] and min(entry['source_dimensions']) >= 768, f'Editor source resolution changed: {identity}')
            require(len(entry['alpha_bounds']) == 4 and all(isinstance(v, int) for v in entry['alpha_bounds']), f'Missing fixed alpha registration: {identity}')
        require({p.name for p in runtime.glob('*.png')} == {name + '.png' for name in ASSETS}, 'Unexpected editor UI image payload')
        return {'images': len(ASSETS), 'imagegen_sources': len(generated), 'png_bytes': total_bytes, 'reference_sha256': manifest['reference_sha256']}
    except (OSError, KeyError, TypeError, IndexError, struct.error) as error:
        raise ValueError(f'Invalid editor UI provenance: {error}') from error


if __name__ == '__main__':
    print(json.dumps(verify_editor_ui(Path(__file__).resolve().parents[1]), indent=2))
