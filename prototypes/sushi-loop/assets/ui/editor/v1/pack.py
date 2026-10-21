#!/usr/bin/env python3
"""Register ImageGen UI assets without repainting: alpha trim, downsample, mirror."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
PROTOTYPE = HERE.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    generation = json.loads((HERE / 'imagegen.json').read_text())
    runtime = PROTOTYPE / generation['runtime']
    runtime.mkdir(parents=True, exist_ok=True)
    manifest = {'version': 1, 'reference': generation['reference'],
                'reference_sha256': sha(PROTOTYPE / generation['reference']),
                'source_record': str((HERE / 'imagegen.json').relative_to(PROTOTYPE)),
                'source_record_sha256': sha(HERE / 'imagegen.json'),
                'packing_script_sha256': sha(Path(__file__)), 'assets': {}}
    for entry in generation['assets']:
        source = HERE / entry['raw']
        image = Image.open(source).convert('RGBA')
        bounds = image.getchannel('A').getbbox()
        if bounds is None:
            raise ValueError(f"Empty source: {entry['id']}")
        packed = image.crop(bounds)
        limit = 768 if entry['id'] == 'button-live' else 512 if entry['id'] == 'button-wood' else 384
        scale = min(1, limit / max(packed.size))
        packed = packed.resize(tuple(max(1, round(n * scale)) for n in packed.size), Image.Resampling.LANCZOS)
        # One-pixel transparent gutter prevents sampling the PNG outer edge.
        packed = ImageOps.expand(packed, border=2, fill=(0, 0, 0, 0))
        target = runtime / (entry['id'] + '.png')
        packed.save(target, optimize=True)
        manifest['assets'][entry['id']] = {
            'image': target.name, 'sha256': sha(target), 'bytes': target.stat().st_size,
            'dimensions': list(packed.size), 'source': str(source.relative_to(PROTOTYPE)),
            'source_sha256': sha(source), 'source_dimensions': list(image.size),
            'alpha_bounds': list(bounds), 'registration': 'fixed alpha trim; aspect-preserving Lanczos downsample; 2px gutter',
        }
    left = Image.open(runtime / 'caret-left.png')
    right_path = runtime / 'caret-right.png'
    ImageOps.mirror(left).save(right_path, optimize=True)
    manifest['assets']['caret-right'] = {'image': right_path.name, 'sha256': sha(right_path),
        'bytes': right_path.stat().st_size, 'dimensions': list(left.size), 'derived_from': 'caret-left', 'operation': 'horizontal mirror'}
    (runtime / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'images': len(manifest['assets']), 'bytes': sum(x['bytes'] for x in manifest['assets'].values())}))


if __name__ == '__main__':
    main()
