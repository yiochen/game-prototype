#!/usr/bin/env python3
"""Pack exact approved native goods canvases to an explicitly chosen directory."""
import argparse
import json
from pathlib import Path

from refined_goods_contract import IDS, approved_goods
from verify_editor_ui import sha


def pack(prototype, output):
    from PIL import Image
    metadata, renders = approved_goods(prototype)
    atlas = Image.new('RGBA', tuple(metadata['atlas_size']))
    for asset in IDS:
        with Image.open(renders[asset]) as image:
            assert image.mode == 'RGBA' and image.size == (384, 384)
            # Paste the full canvas directly. An alpha-mask paste would multiply
            # edge alpha and alter the approved render, so no mask is supplied.
            atlas.paste(image, tuple(metadata['sprites'][asset]['region'][:2]))
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    atlas_path = output / 'atlas.png'
    atlas.save(atlas_path, compress_level=9)
    metadata.update(atlas_sha256=sha(atlas_path), atlas_bytes=atlas_path.stat().st_size)
    (output / 'manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = pack(Path(__file__).resolve().parents[2], args.output)
    print(json.dumps({'output': str(args.output.resolve()), 'sprites': len(result['sprites'])}))
