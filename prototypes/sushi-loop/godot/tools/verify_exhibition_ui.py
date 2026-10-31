"""Bind the native unlock illustration to the user-approved ImageGen output."""
from pathlib import Path
import hashlib
import json


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_exhibition_ui(project, source_project=None):
    project = Path(project).resolve()
    prototype = Path(source_project or project).resolve().parent
    runtime = project / 'assets/ui/exhibition'
    record = json.loads((runtime / 'manifest.json').read_text())
    if record.get('version') != 1 or set(record.get('artwork', {})) != {'underwater.webp'}:
        raise ValueError('Incomplete exhibition unlock artwork')
    entry = record['artwork']['underwater.webp']
    source = (prototype / entry['source']).resolve()
    generation = (prototype / entry['generation']).resolve()
    if not source.is_relative_to(prototype) or not generation.is_relative_to(prototype):
        raise ValueError('Exhibition artwork reference escaped the prototype')
    provenance = json.loads(generation.read_text())
    approved = provenance['outputs']['underwater.webp']
    if entry['size'] != approved['size'] or entry['size'] != [1536, 1024]:
        raise ValueError('Exhibition illustration aspect/resolution changed')
    if not sha(runtime / 'underwater.webp') == sha(source) == entry['sha256'] == approved['sha256']:
        raise ValueError('Native exhibition artwork differs from the approved illustration')
    for name in ['underwater-original.png', 'underwater.webp']:
        if sha(generation.parent / name) != provenance['outputs'][name]['sha256']:
            raise ValueError('Exhibition generation provenance changed: ' + name)
    if sha(generation.parent / provenance['prompt']) != provenance['prompt_sha256']:
        raise ValueError('Exhibition ImageGen prompt changed')
    calibration = record['calibration']
    if calibration['aspect_ratio'] != [3, 2] or calibration['corner_radius'] != 16 or calibration['minimum_touch_pixels'] != 44:
        raise ValueError('Exhibition illustration calibration changed')
    if {p.name for p in runtime.iterdir() if p.suffix in {'.webp', '.png'}} != {'underwater.webp'}:
        raise ValueError('Unexpected exhibition runtime artwork')
    return {'runtime_images': ['assets/ui/exhibition/underwater.webp'], 'approved_artwork': 1,
            'artwork_sha256': entry['sha256'], 'dimensions': entry['size']}


if __name__ == '__main__':
    print(json.dumps(verify_exhibition_ui(Path(__file__).resolve().parents[1]), indent=2))
