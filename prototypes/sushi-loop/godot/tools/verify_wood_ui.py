"""Check the native HTML-export family against its editable source and PNGs."""
from pathlib import Path
import hashlib
import json
import struct


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_wood_ui(project, source_project=None):
    project = Path(project).resolve()
    prototype = Path(source_project or project).resolve().parent
    runtime = project / 'assets/ui/wood-editor'
    manifest = json.loads((runtime / 'manifest.json').read_text())
    source_root = prototype / 'assets/ui/editor/html-export-v1'
    if manifest['source_export'] != {'root': 'assets/ui/editor/html-export-v1', 'manifest_sha256': sha(source_root / 'manifest.json')}:
        raise ValueError('Native wood UI export identity changed')
    source = json.loads((source_root / 'manifest.json').read_text())
    if manifest.get('dynamic_text_baked') is not False or manifest['logical_canvas'] != [720,1280]:
        raise ValueError('Wood UI must retain native dynamic text and approved logical geometry')
    for name, expected in source['source']['files'].items():
        if not name.startswith('prototypes/sushi-loop/'):
            raise ValueError('Wood UI source escapes this prototype')
        current = prototype / name.removeprefix('prototypes/sushi-loop/')
        snapshot = manifest.get('source_snapshots', {}).get(name)
        if snapshot is not None:
            # A retained original is checked against the unchanged export's
            # recorded hash, never against a newly blessed current source hash.
            archived = (source_root / snapshot['path']).resolve()
            if not archived.is_relative_to(source_root.resolve()) or snapshot['sha256'] != expected or sha(archived) != expected:
                raise ValueError(f'Wood UI historical source snapshot changed: {name}')
        elif sha(current) != expected:
            raise ValueError(f'Wood UI needs a fresh HTML export: {name}')
    if set(manifest['assets']) != set(source['assets']) or len(manifest['assets']) != 26:
        raise ValueError('Wood UI component coverage changed')
    files = []
    for name, asset in manifest['assets'].items():
        original = source['assets'][name]
        if {k:v for k,v in asset.items() if k != 'variants'} != {k:v for k,v in original.items() if k != 'variants'}:
            raise ValueError(f'Wood UI native geometry differs from HTML: {name}')
        variant = asset['variants']['2x']
        path = runtime / variant['path']
        if variant['path'] != f'{name}.png' or sha(path) != original['variants']['2x']['sha256'] or sha(source_root / original['variants']['2x']['path']) != sha(path):
            raise ValueError(f'Wood UI runtime pixels differ from CSS export: {name}')
        data = path.read_bytes()
        if data[:8] != b'\x89PNG\r\n\x1a\n' or list(struct.unpack_from('>II',data,16)) != variant['size']:
            raise ValueError(f'Wood UI PNG dimensions changed: {name}')
        cuts = variant.get('nine_patch_margins_ltrb')
        if cuts and (min(cuts)<0 or cuts[0]+cuts[2]>=variant['size'][0] or cuts[1]+cuts[3]>=variant['size'][1]):
            raise ValueError(f'Wood UI slicing spans overlap: {name}')
        files.append(variant['path'])
    for name, texture in manifest['textures'].items():
        if sha(runtime / texture['path']) != source['textures'][name]['sha256']:
            raise ValueError(f'Wood UI background texture changed: {name}')
        files.append(texture['path'])
    if {p.name for p in runtime.glob('*.png')} != set(files):
        raise ValueError('Unexpected wood UI runtime PNG payload')
    if not manifest['assets']['shop-normal']['face_rect'][3] == manifest['assets']['tab-normal']['face_rect'][3] == 60:
        raise ValueError('Shop must match the unselected category height')
    return {'images':len(files),'runtime_images':files,'source_export_sha256':sha(source_root/'manifest.json')}


if __name__ == '__main__':
    print(json.dumps(verify_wood_ui(Path(__file__).resolve().parents[1]),indent=2))
