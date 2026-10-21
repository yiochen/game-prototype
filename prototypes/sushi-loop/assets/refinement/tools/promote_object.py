"""Promote exact independently approved native captures without changing registration."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from PIL import Image

RUN = Path(__file__).resolve().parents[1]
PRODUCTION = RUN.parent / 'production'
PACKET_HELPER = Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py')


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def relative(path):
    return str(Path(path).relative_to(PRODUCTION))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset')
    parser.add_argument('--round', default='round-02')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    folder = RUN / 'objects' / args.asset
    round_folder = folder / 'candidates' / args.round
    packet_path = round_folder / 'packet.json'
    review_path = folder / 'reviews' / f'{args.round}.json'
    subprocess.run(['python3', str(PACKET_HELPER), 'verify', '--packet', str(packet_path),
                    '--review', str(review_path)], check=True)
    packet, delivery = read(packet_path), read(folder / 'delivery.json')
    library = read(PRODUCTION / 'library.json')
    original = next(o for o in library['objects'] if o['id'] == args.asset)
    obj = copy.deepcopy(original)
    require(not obj.get('refinement'), 'Object already promoted; do not overwrite an approved version')
    require(delivery.get('asset', delivery.get('assetId')) == args.asset, 'Wrong delivery object')
    # Every byte-bearing project, recipe, raw PNG and atlas must belong to the approved packet.
    bound = {(packet_path.parent / f['path']).resolve(): f['sha256']
             for f in [*packet['files'].values(), *packet['candidateRenders'].values(), *packet['previews'].values()]}
    copies, generated, tracked = [], {}, {}

    def copy_file(source, dest, sealed=True):
        source, dest = Path(source).resolve(), Path(dest)
        sha = digest(source)
        if sealed:
            require(bound.get(source) == sha, f'Unreviewed or changed artifact: {source}')
        copies.append((source, dest, sha))
        tracked[relative(dest)] = sha

    def generate(dest, value):
        generated[Path(dest)] = value

    project = folder / delivery.get('project', delivery.get('source', {}).get('blend', ''))
    recipe = folder / delivery.get('recipe', delivery.get('source', {}).get('reproductionScript', ''))
    native_base = PRODUCTION / 'source/blender/refinement' / args.asset
    project_dest = native_base / 'source' / project.name
    recipe_dest = native_base / 'source' / recipe.name
    copy_file(project, project_dest)
    copy_file(recipe, recipe_dest)
    # Keep the native recipe's original relative inputs alongside its saved project.
    # These are reproduction dependencies; approved render bytes remain packet-bound.
    for dependency in (folder / 'inputs').iterdir():
        if dependency.suffix in ['.blend', '.json']:
            copy_file(dependency, native_base / 'inputs' / dependency.name, sealed=False)
    if (recipe.parent / 'original-library.blend').exists():
        copy_file(recipe.parent / 'original-library.blend', native_base / 'source/original-library.blend', sealed=False)
    copy_file(folder / 'brief.json', native_base / 'brief.json')
    record_paths = delivery.get('nativeRecords')
    if not record_paths:
        metadata = read(folder / 'metadata-delivery.json')
        require(metadata['approvedPacket']['sha256'] == digest(packet_path), 'Metadata belongs to a different candidate')
        record_paths = {('assetRecord' if k == 'asset' else k): v['path'] for k, v in metadata['records'].items()}
        for record in metadata['records'].values():
            require(digest(folder / record['path']) == record['sha256'], 'Supplementary record changed')
    records = {k: read(folder / v) for k, v in record_paths.items()}
    camera = records['camera']
    require(camera.get('captureScale') == obj['sourceScale'], 'Native record has stale capture scale')
    require(camera.get('frame') == obj['frameSize'] and camera.get('anchor') == obj['root'], 'Native registration differs')
    for key, name in [('camera', 'camera'), ('assetRecord', 'asset'), ('rig', 'rig')]:
        dest = PRODUCTION / 'source/records' / args.asset / f'{name}.json'
        copy_file(folder / record_paths[key], dest, sealed=bool(delivery.get('nativeRecords')))
        obj['source'][key] = relative(dest)

    atlases = delivery.get('atlases')
    if not atlases:
        atlases = [{'clip': 'static', 'direction': direction, **record,
                    'size': record['atlasSize']} for direction, record in delivery['sprites'].items()]
    atlas_map = {(a['clip'], a['direction']): a for a in atlases}
    expected = {(c['id'], d) for c in obj['clips'] for d in c['directions']}
    require(set(atlas_map) == expected, 'Delivery does not cover every original clip/facing')
    guides, raw_frames = [], []
    for clip in obj['clips']:
        for direction, current in clip['directions'].items():
            a = atlas_map[(clip['id'], direction)]
            source_atlas = folder / a['path']
            require(digest(source_atlas) == a['sha256'], 'Atlas differs from delivery')
            require(a['size'] == current['atlasSize'] and a['columns'] == current['columns']
                    and a['rows'] == current['rows'] and a['rects'] == current['rects'], 'Atlas layout drift')
            image = Image.open(source_atlas)
            require(image.mode == 'RGBA' and list(image.size) == current['atlasSize'], 'Atlas size/alpha drift')
            copy_file(source_atlas, PRODUCTION / current['image'])
            captures = []
            for index, rect in enumerate(current['rects']):
                clip_dir = f'{clip["id"]}-{direction}'
                raw = round_folder / 'raw' / clip_dir / f'{index:03}.png'
                if not raw.exists():
                    require(clip['frames'] == 1, 'Animated raw capture missing')
                    raw = folder / delivery.get('heroes', {}).get(direction, f'candidates/{args.round}/{direction}.png')
                raw_image = Image.open(raw)
                x, y, w, h = rect
                require(raw_image.mode == 'RGBA' and list(raw_image.size) == [w, h], 'Raw frame registration drift')
                require(image.crop((x, y, x+w, y+h)).tobytes() == raw_image.tobytes(), 'Atlas is not exact native frames')
                dest = PRODUCTION / 'source/registered' / args.asset / clip_dir / 'source-captures' / f'{index:03}.png'
                copy_file(raw, dest)
                captures.append({'path': f'source-captures/{index:03}.png', 'sha256': digest(raw)})
                raw_frames.append({'image': relative(dest), 'sha256': digest(raw), 'clip': clip['id'], 'direction': direction, 'index': index})
            guide_path = PRODUCTION / 'source/registered' / args.asset / f'{clip["id"]}-{direction}' / 'guide.json'
            guide = {'version': 1, 'kind': 'rendered-3d-sheet', 'assetKind': 'object',
                     'size': current['atlasSize'], 'frame': clip.get('frameSize', obj['frameSize']),
                     'anchor': clip.get('root', obj['root']), 'cellSize': library['cellSize'],
                     'captureScale': obj['sourceScale'], 'sourceCaptureScale': obj['sourceScale'],
                     'gutter': 0, 'columns': current['columns'], 'rows': current['rows'],
                     'cells': [{'index': i, 'rect': rect} for i, rect in enumerate(current['rects'])],
                     'groundAnchorAlignment': 'center', 'projection': obj['projection'],
                     'camera': camera['camera'], 'occupiedCells': obj.get('occupiedCells', []),
                     'elevationPx': clip.get('elevationPx', obj.get('elevationPx', 0)),
                     'sourceCaptures': captures, 'processing': 'Exact native scale2 RGBA frames; lossless atlas placement only'}
            generate(guide_path, guide)
            guides.append(relative(guide_path))

    validation_dest = PRODUCTION / 'source/records' / args.asset / 'warm-refinement-validation.json'
    copy_file(folder / delivery['validation'], validation_dest)
    source = obj['source']
    source.update({'blend': relative(project_dest), 'refinedBlend': relative(project_dest),
                   'modelScript': relative(recipe_dest), 'captureScale': obj['sourceScale'],
                   'rawFrames': raw_frames, 'guides': guides, 'guide': guides[0],
                   'nativeScripts': {recipe.name: relative(recipe_dest)},
                   'refinement': {'packet': f'../refinement/objects/{args.asset}/candidates/{args.round}/packet.json',
                                  'review': f'../refinement/objects/{args.asset}/reviews/{args.round}.json',
                                  'validation': relative(validation_dest)}})
    obj['captureFingerprint'] = digest(packet_path)
    obj['registration']['sourceCaptureScale'] = obj['sourceScale']
    obj['artStyle'] = {'revision': f'warm-soft-{args.asset}-{args.round}',
                       'style': 'Warm softly lit cartoon', 'nativeEditable': True,
                       'lighting': read(folder / delivery['validation']).get('lighting', camera.get('artStyle', {}).get('lighting'))}
    obj['productionStage'] = 'Native Blender · warm soft cartoon · independent judge approved'
    obj['refinement'] = {'status': 'approved', 'round': args.round, 'packetSHA256': digest(packet_path),
                         'reviewSHA256': digest(review_path), 'editor': f'catalog_{args.asset.replace("-", "_")}_editor',
                         'judge': f'catalog_{args.asset.replace("-", "_")}_judge'}
    # Existing capture layout, gameplay metadata and model attachment fields are deliberately inherited.
    require(obj['clips'] == original['clips'], 'Clip contract changed during promotion')
    if not args.apply:
        print(json.dumps({'asset': args.asset, 'copyCount': len(copies), 'guides': len(generated), 'frames': len(raw_frames), 'status': 'verified-dry-run'}))
        return
    write(folder / 'final/original-catalog-object.json', original)
    for source_path, dest, sha in copies:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest)
        require(digest(dest) == sha, 'Copy changed bytes')
    for path, value in generated.items():
        write(path, value)
        tracked[relative(path)] = digest(path)
    obj['source']['hashes'] = tracked
    library['objects'] = [obj if o['id'] == args.asset else o for o in library['objects']]
    write(PRODUCTION / 'library.json', library)
    write(folder / 'final/promotion.json', {'asset': args.asset, 'round': args.round,
          'candidatePacketSHA256': digest(packet_path), 'reviewSHA256': digest(review_path),
          'files': tracked, 'status': 'exact-approved-bytes-promoted'})
    progress = read(RUN / 'progress.json')
    item = next(o for o in progress['objects'] if o['id'] == args.asset)
    item.update({'status': 'approved', 'round': args.round, 'packetSHA256': digest(packet_path)})
    obj['refinement'].update({'editor': item.get('editor'), 'judge': item.get('judge')})
    write(PRODUCTION / 'library.json', library)
    progress['completed'] = sum(o['status'] in ['approved', 'published'] for o in progress['objects'])
    write(RUN / 'progress.json', progress)
    print(json.dumps({'asset': args.asset, 'frames': len(raw_frames), 'status': 'promoted', 'completed': progress['completed']}))


if __name__ == '__main__':
    main()
