"""Save an already promoted actor's exact independently approved runtime bundle."""
import argparse
import json
from pathlib import Path
import sys

from PIL import Image
from acceptance_contract import acceptance, read, require, sha

RUN = Path(__file__).resolve().parents[1]
PROTOTYPE = RUN.parents[1]
sys.path.insert(0, str(PROTOTYPE / 'godot/tools'))
from refined_actor_variants import CONTRACTS, DIRECTIONS, RECTS


def make_receipt(asset, round_name):
    kind = next((kind for kind, (ids, _, _) in CONTRACTS.items() if asset in ids), None)
    require(kind is not None, 'No existing actor runtime bundle for this object')
    _, clips, food = CONTRACTS[kind]
    folder = RUN / 'objects' / asset
    base = folder / 'candidates' / round_name
    packet_path = base / 'packet.json'
    packet = read(packet_path)
    approved = acceptance(folder, round_name, packet)
    require(approved['method'] == 'independent-review', 'Actor variants need their independent judge')
    bound = {(base / item['path']).resolve(): item['sha256']
             for group in ['files', 'candidateRenders', 'previews']
             for item in packet[group].values()}
    for path, expected in bound.items():
        require(path.is_relative_to(PROTOTYPE) and sha(path) == expected,
                f'Changed or external packet resource: {path}')
    objects = {obj['id']: obj for obj in read(RUN.parent / 'production/library.json')['objects']}
    main = objects[asset].get('refinement', {})
    require(main.get('packetSHA256') == sha(packet_path)
            and main.get('reviewSHA256') == approved['sha256'],
            'Promote the exact independently approved main actor before saving its runtime receipt')
    delivery_path = base / packet['files']['candidateResource:round:delivery.snapshot.json']['path']
    bundle = read(delivery_path)['runtimeVariants']
    canonical = (RUN.parent / 'production' / objects[food]['source']['artwork']).resolve()
    require(bound.get(canonical) == sha(canonical), 'Canonical food must be exact and packet-bound')
    files = {}

    def add(relative):
        path = (folder / relative).resolve()
        require(path.is_relative_to(folder) and bound.get(path) == sha(path),
                f'Runtime resource is outside this approved object bundle: {relative}')
        files[path.relative_to(folder).as_posix()] = sha(path)

    for key in ['project', 'recipe', 'recipeScript', 'validation']:
        if bundle.get(key):
            add(bundle[key])
    for path in bundle.get('nativeRecords', {}).values():
        add(path)
    resources = bundle.get('resources', [])
    for record in resources.values() if isinstance(resources, dict) else resources:
        add(record['path'] if isinstance(record, dict) else record)
    frames = {(row['clip'], row['direction'], row['index']): row for row in bundle['rawFrames']}
    atlases = {(row['clip'], row['direction']): row for row in bundle['atlases']}
    require(len(frames) == len(bundle['rawFrames']) == 96
            and set(frames) == {(clip, facing, i) for clip in clips for facing in DIRECTIONS for i in range(12)},
            'Incomplete runtime frame coverage')
    require(len(atlases) == len(bundle['atlases']) == 8
            and set(atlases) == {(clip, facing) for clip in clips for facing in DIRECTIONS},
            'Incomplete runtime atlas coverage')
    require(bundle['publishedSourceScale'] == 2, 'Runtime publication scale changed')
    for (clip, facing), atlas in atlases.items():
        require(atlas['columns'] == 6 and atlas['rows'] == 2 and atlas['size'] == [2304, 1280]
                and atlas['rects'] == RECTS and atlas['fps'] == 12
                and atlas['loop'] is (clip != 'load-cucumber') and atlas['frameOrder'] == list(range(12)),
                'Runtime layout or cadence changed')
        add(atlas['path'])
        require(files[atlas['path']] == atlas['sha256'], 'Atlas declared hash differs')
        with Image.open(folder / atlas['path']) as image:
            require(image.size == (2304, 1280), 'Runtime atlas dimensions changed')
            for i, (x, y, w, h) in enumerate(RECTS):
                frame = frames[clip, facing, i]
                add(frame['path'])
                require(files[frame['path']] == frame['sha256'], 'Frame declared hash differs')
                with Image.open(folder / frame['path']) as raw:
                    require(raw.size == (384, 640)
                            and image.crop((x, y, x+w, y+h)).convert('RGBA').tobytes() == raw.convert('RGBA').tobytes(),
                            'Runtime atlas is not the exact whole approved frame')
    return {'asset': asset, 'kind': f'existing-{kind}-runtime-variants', 'round': round_name,
            'status': 'exact-approved-variant-bytes-saved-final-Godot-cutover-pending',
            'packet': str(packet_path.relative_to(folder)), 'candidatePacketSHA256': sha(packet_path),
            'review': str(approved['path'].relative_to(folder)), 'reviewSHA256': approved['sha256'],
            'delivery': str(delivery_path.relative_to(folder)), 'deliverySHA256': sha(delivery_path),
            'bundleKey': 'runtimeVariants', 'frames': 96, 'atlases': 8, 'requiredClips': clips,
            'canonicalFood': food, 'canonicalSourceSHA256': sha(canonical),
            'editableSource': bundle['project'], 'editableSourceSHA256': files[bundle['project']],
            'filesRelativeTo': 'object', 'files': dict(sorted(files.items())),
            'integrationNotes': 'Exact same-packet actor and runtime approvals; native publication scale2. Final combined Godot cutover remains pending.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset')
    parser.add_argument('--round', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    receipt = make_receipt(args.asset, args.round)
    path = RUN / 'objects' / args.asset / 'final/runtime-variant-approval.json'
    if args.apply:
        require(not path.exists(), 'Preserve an existing runtime approval; never overwrite it')
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'asset': args.asset, 'frames': 96, 'atlases': 8,
                      'files': len(receipt['files']), 'saved': args.apply}))
