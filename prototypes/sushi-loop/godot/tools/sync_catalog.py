#!/usr/bin/env python3
"""Copy the approved #33 restaurant subset without changing sprite pixels.

--check verifies selection, provenance and shipped bytes. Whole authored frames,
logical ground roots and the shared 128px pitch are preserved.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT.parent / 'assets/production'
DESTINATION = PROJECT / 'assets/catalog'
DIRECTIONS = ['N', 'E', 'S', 'W']
SELECTION = {
    'floor-cream': (['static'], ['S']),
    'floor-blue-wave': (['static'], ['S']),
    'entry-finished': (['static'], ['S']),
    'wall-middle': (['static'], ['S', 'E']),
    'wall-inner-corner': (['static'], ['S']),
    'wall-outer-corner': (['static'], ['S']),
    'wall-end': (['static'], ['S']),
    'plant-angular': (['idle'], ['S']),
    'barrel-wood': (['static'], ['S']),
    'crate-wood': (['static'], ['S']),
    'lantern-gold': (['idle'], ['S']),
    'stool-wood': (['static'], DIRECTIONS),
    'belt-start-e': (['running'], ['S']),
    'belt-straight-e': (['running'], ['S']),
    'belt-end-e': (['running'], ['S']),
    'chef-lena': (['idle', 'work', 'hold', 'load'], DIRECTIONS),
    'chef-blackboard': (['idle'], ['S']),
    'coin-pop': (['pop'], ['S']),
    **{identity: (['stand', 'walk', 'seated-wait', 'eat', 'sit-down', 'stand-up'], DIRECTIONS)
       for identity in ['customer-rosa', 'customer-ellis', 'customer-samir', 'customer-june']},
    **{identity: (['static'], ['S']) for identity in ['dish-salmon', 'dish-cucumber', 'dish-eel']},
    **{identity: (['idle'], ['S']) for identity in ['garbage-sofa', 'garbage-car', 'garbage-shelving']},
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_manifest() -> tuple[dict, set[str]]:
    library = json.loads((SOURCE / 'library.json').read_text())
    assert library['approval']['finalAssets'] == 'approved'
    objects = {entry['id']: entry for entry in library['objects']}
    result = {
        'version': 1, 'cellSize': library['cellSize'], 'approval': library['approval'],
        'source': {'library': '../assets/production/library.json', 'librarySha256': digest(SOURCE / 'library.json')},
        'policy': 'Exact approved atlas bytes; whole authored frames; fixed logical roots; no pose fitting or sprite distortion.',
        'objects': {},
    }
    files = set()
    for identity, (clip_names, directions) in SELECTION.items():
        original = objects[identity]
        entry = {key: original[key] for key in ['id', 'name', 'kind', 'footprint', 'frameSize', 'root', 'sourceScale', 'projection', 'sockets', 'ports', 'rootCell', 'directionRootCells', 'directionFootprints', 'facingPolicy'] if key in original}
        entry['source'] = {'captureFingerprint': original.get('captureFingerprint'), 'blend': original.get('source', {}).get('blend'), 'assetRecord': original.get('source', {}).get('assetRecord')}
        entry['clips'] = {}
        for clip in original['clips']:
            if clip['id'] not in clip_names:
                continue
            selected = {key: clip[key] for key in ['id', 'frames', 'fps', 'static', 'loop', 'frameOrder', 'frameSize', 'root', 'sourceScale'] if key in clip}
            selected['directions'] = {}
            for direction in directions:
                frame = dict(clip['directions'][direction])
                path = frame['image']
                frame['sha256'] = digest(SOURCE / path)
                selected['directions'][direction] = frame
                files.add(path)
            entry['clips'][clip['id']] = selected
        assert set(entry['clips']) == set(clip_names), identity
        result['objects'][identity] = entry
    return result, files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    manifest, files = make_manifest()
    encoded = json.dumps(manifest, indent=2, ensure_ascii=False) + '\n'
    if args.check:
        assert (DESTINATION / 'manifest.json').read_text() == encoded, 'Catalog registration/provenance is stale; run sync_catalog.py'
        actual = {str(path.relative_to(DESTINATION)) for path in (DESTINATION / 'sprites').rglob('*.png')}
        assert actual == files, 'Unexpected or missing runtime atlases'
        for path in sorted(files):
            assert digest(SOURCE / path) == digest(DESTINATION / path), path
    else:
        DESTINATION.mkdir(parents=True, exist_ok=True)
        for path in sorted(files):
            target = DESTINATION / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / path, target)
        (DESTINATION / 'manifest.json').write_text(encoded)
    print(f"{'Verified' if args.check else 'Copied'} {len(manifest['objects'])} approved objects / {len(files)} exact atlases / {sum((SOURCE / path).stat().st_size for path in files):,} bytes")


if __name__ == '__main__':
    main()
