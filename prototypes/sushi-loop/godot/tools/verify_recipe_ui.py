"""Release gate for the approved ImageGen headshots and separate dish layers."""
from pathlib import Path
import hashlib
import json
import struct


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_recipe_ui(project, source_project=None):
    project = Path(project).resolve()
    prototype = Path(source_project or project).resolve().parent
    manifest = json.loads((project / 'assets/ui/recipes/manifest.json').read_text())
    if manifest['version'] != 1 or manifest['dynamic_text_baked'] is not False:
        raise ValueError('Recipe UI requires separate native labels and the registered artwork family')
    expected = {f'assets/ui/chef-headshots/{name}.png' for name in ['lena','omar','ama','mateo','noor','dalia','ellis','rowan','instant-photo']}
    expected.update({'assets/ui/recipes/plates.png','assets/ui/recipes/food.png'})
    if set(manifest['artwork']) != expected:
        raise ValueError('Incomplete headshot, photo or independent plate/food family')
    for name, entry in manifest['artwork'].items():
        original = (prototype / entry['source']).resolve()
        if not original.is_relative_to(prototype) or sha(original) != entry['sha256'] or sha(project/name) != entry['sha256']:
            raise ValueError(f'Recipe UI original/runtime pixels changed: {name}')
        if list(struct.unpack_from('>II', (project/name).read_bytes(), 16)) != entry['size']:
            raise ValueError(f'Recipe UI dimensions changed: {name}')
    for source in manifest['sources']:
        record = json.loads((prototype/source).read_text())
        if not record:
            raise ValueError(f'Missing generation provenance: {source}')
    return {'images':len(expected), 'runtime_images':sorted(expected), 'independent_plate_food_layers':True}
