#!/usr/bin/env python3
"""Copy the exact approved smile variant to an explicitly chosen directory."""
import argparse
import json
from pathlib import Path
import shutil

from refined_feedback_contract import approved_feedback
from verify_editor_ui import require, sha


def sync(prototype, output):
    manifest, receipt, candidate = approved_feedback(prototype)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    for clip, action in manifest['objects']['bubble-happy']['clips'].items():
        relative = f'runtime-variants/smile/atlases/{clip}-S.png'
        source = candidate / relative
        target = output / action['directions']['S']['image']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(sha(target) == receipt['files'][relative], 'Smile copy changed approved bytes')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = sync(Path(__file__).resolve().parents[2], args.output)
    print(json.dumps({'output': str(args.output.resolve()), 'objects': len(result['objects'])}))
