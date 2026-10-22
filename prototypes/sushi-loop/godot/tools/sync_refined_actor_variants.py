#!/usr/bin/env python3
"""Copy approved chef/customer variant bytes to an explicitly chosen directory."""
import argparse
import json
from pathlib import Path
import shutil

from refined_actor_variants import CONTRACTS, approved_actor_variants
from verify_editor_ui import require, sha


def sync(prototype, kind, output):
    manifest, images, _ = approved_actor_variants(prototype, kind)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    for relative, source in images.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(sha(target) == sha(source), 'Runtime variant copy changed approved bytes')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', required=True, choices=list(CONTRACTS))
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = sync(Path(__file__).resolve().parents[2], args.kind, args.output)
    print(json.dumps({'output': str(args.output.resolve()), 'objects': len(result['objects'])}))
