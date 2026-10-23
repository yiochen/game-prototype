#!/usr/bin/env python3
"""Pack complete 4x native captures to 2x runtime atlases, without silhouette edits."""
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image

HERE = Path(__file__).resolve().parent
PROTOTYPE = HERE.parents[4]
PROJECT = PROTOTYPE / 'godot'
DEST = PROJECT / 'assets/recipe-variants'
IDS = ['customer-rosa', 'customer-ellis', 'customer-samir', 'customer-june']
CLIPS = ['eat-salmon', 'seated-wait-empty']
DIRECTIONS = ['N', 'E', 'S', 'W']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, required=True)
    args = parser.parse_args()
    source = HERE / 'export/source'
    proof = json.loads((HERE / 'authorship.json').read_text())
    blend_sha = sha(HERE / 'starter-meals.blend')
    assert blend_sha == proof['derivativeBlend']['sha256']
    objects, atlases, captures = {}, {}, []
    for aid in IDS:
        obj = {'frameSize': [192, 320], 'root': [96, 248], 'sourceScale': 2, 'projection': 'character-orthographic', 'clips': {}}
        for clip in CLIPS:
            record = {'id': clip, 'frames': 12, 'fps': 12, 'loop': True, 'frameOrder': list(range(12)), 'directions': {}}
            for direction in DIRECTIONS:
                atlas = Image.new('RGBA', (2304, 1280))
                rects, unique = [], set()
                for index in range(12):
                    path = args.raw / aid / (clip + '-' + direction) / (str(index).zfill(3) + '.png')
                    receipt = json.loads(path.with_suffix('.capture.json').read_text())
                    assert receipt['state'] == 'complete' and receipt['assetId'] == aid and receipt['clip'] == clip and receipt['direction'] == direction and receipt['index'] == index and receipt['fps'] == 12
                    assert receipt['sha256'] == sha(path) and [receipt['width'], receipt['height']] == [768, 1280]
                    worker = json.loads((HERE / 'export/capture-workers' / (receipt['worker'] + '.status.json')).read_text())
                    assert worker['nativeSource']['blend'] == blend_sha and worker['state'] == 'complete'
                    with Image.open(path) as image:
                        assert image.size == (768, 1280)
                        image = image.convert('RGBA').resize((384, 640), Image.Resampling.LANCZOS)
                    pixel_sha = hashlib.sha256(image.tobytes()).hexdigest()
                    unique.add(pixel_sha)
                    x, y = index % 6 * 384, index // 6 * 640
                    atlas.paste(image, (x, y))
                    rects.append([x, y, 384, 640])
                    captures.append({**receipt, 'sourceBlendSha256': blend_sha, 'runtimePixelSha256': pixel_sha, 'runtimeRect': [x, y, 384, 640]})
                assert len(unique) >= 6, (aid, clip, direction)
                relative = 'sprites/' + aid + '/' + clip + '-' + direction + '.png'
                path = DEST / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                atlas.save(path, compress_level=9)
                atlases[relative] = {'sha256': sha(path), 'bytes': path.stat().st_size, 'width': 2304, 'height': 1280}
                record['directions'][direction] = {'image': relative, 'columns': 6, 'rows': 2, 'atlasSize': [2304, 1280], 'rects': rects, 'sha256': sha(path)}
            obj['clips'][clip] = record
        objects[aid] = obj
    evidence = {'version': 1, 'sourceBlendSha256': blend_sha, 'frames': len(captures), 'atlasCount': len(atlases), 'operation': 'Complete RGBA 768x1280 frame resampled uniformly to384x640 with Pillow LANCZOS; packed6columns; no alpha crop, mask, color edit, pose fit or per-frame scaling.', 'atlases': atlases, 'captures': captures}
    write(HERE / 'publication.json', evidence)
    source_files = [HERE / name for name in ['starter-meals.blend', 'authorship.json', 'author_meals.py', 'pack_meals.py', 'publication.json', 'native-audit.json', 'audit_native_meals.py', 'starter-meals-project.blend', 'finalize_meals.py', 'finalized-project.json']]
    source_files += sorted(source.rglob('*.json'))
    source_files += sorted((HERE / 'export/capture-workers/camera').rglob('*.json'))
    source_files += sorted((HERE / 'export/capture-workers').glob('*.status.json'))
    for name in ['capture_runtime.py', 'capture_worker.py', 'native_actions.py', 'catalog_style.py', 'catalog_faceted.py', 'concept_decoration_geometry.py']:
        source_files.append(PROTOTYPE / 'assets/production/source/blender' / name)
    source_files.append(PROTOTYPE / 'assets/production/source/2d/generated/dish-salmon.png')
    manifest = {'version': 1, 'baseLibrarySha256': sha(PROTOTYPE / 'assets/production/library.json'), 'provenance': 'Game-specific native meal variants; approved issue33 base catalog remains unchanged.', 'sourceFiles': {str(path.relative_to(PROTOTYPE)): sha(path) for path in source_files}, 'objects': objects}
    write(DEST / 'manifest.json', manifest)
    print(f'Packed {len(captures)} complete native frames into{len(atlases)} atlases; {sum(r["bytes"] for r in atlases.values()):,} bytes')


if __name__ == '__main__':
    main()
