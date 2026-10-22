"""Strict per-character approved native food/empty runtime variant imports."""
from pathlib import Path

from refinement_contract import contained, read, verified_packet
from verify_editor_ui import _crop, _decode_png, require, sha

CONTRACTS = {
    'chef': (['chef-omar'], ['hold-cucumber', 'load-cucumber'], 'dish-cucumber'),
    'recipe': (['customer-rosa', 'customer-ellis', 'customer-samir', 'customer-june'],
               ['eat-salmon', 'seated-wait-empty'], 'dish-salmon'),
}
DIRECTIONS = ['N', 'E', 'S', 'W']
RECTS = [[i % 6 * 384, i // 6 * 640, 384, 640] for i in range(12)]


def approved_actor_variants(prototype, kind):
    prototype = Path(prototype).resolve()
    identities, clips, food = CONTRACTS[kind]
    library_path = prototype / 'assets/production/library.json'
    library = {obj['id']: obj for obj in read(library_path)['objects']}
    canonical = contained(prototype, prototype / 'assets/production' / library[food]['source']['artwork'])
    manifest = {'version': 1, 'baseLibrarySha256': sha(library_path),
                'provenance': {'method': 'Independently approved per-character native captures'},
                'sourceFiles': {}, 'objects': {}, 'refinement': {}}
    images, raw_frames = {}, {}
    for identity in identities:
        experiment = prototype / 'assets/refinement/objects' / identity
        receipt_path = experiment / 'final/runtime-variant-approval.json'
        receipt = read(receipt_path)
        require(receipt.get('asset') == identity
                and receipt.get('status') == 'exact-approved-variant-bytes-saved-final-Godot-cutover-pending'
                and receipt.get('filesRelativeTo') == 'object'
                and receipt.get('bundleKey') == 'runtimeVariants'
                and receipt.get('requiredClips') == clips
                and receipt.get('frames') == 96 and receipt.get('atlases') == 8
                and receipt.get('canonicalFood') == food
                and receipt.get('canonicalSourceSHA256') == sha(canonical),
                f'Invalid approved runtime variant receipt: {identity}')
        packet_path = contained(experiment, experiment / receipt['packet'])
        review_path = contained(experiment, experiment / receipt['review'])
        packet, bound = verified_packet(prototype, packet_path, receipt['candidatePacketSHA256'],
                                         review_path, receipt['reviewSHA256'], identity)
        base = library[identity]
        require(base['refinement']['packetSHA256'] == receipt['candidatePacketSHA256']
                and base['refinement']['reviewSHA256'] == receipt['reviewSHA256'],
                f'Runtime variant and main body approvals differ: {identity}')
        require(sha(canonical) in bound.values(), f'Runtime canonical food is not packet-bound: {identity}')
        delivery_path = contained(experiment, experiment / receipt['delivery'])
        require(sha(delivery_path) == receipt['deliverySHA256']
                == packet['files']['candidateResource:round:delivery.snapshot.json']['sha256'],
                f'Runtime delivery is not the approved snapshot: {identity}')
        bundle = read(delivery_path)['runtimeVariants']
        for relative, expected in receipt['files'].items():
            path = contained(experiment, experiment / relative)
            require(bound.get(path) == expected == sha(path),
                    f'Approved runtime artifact changed: {identity}/{relative}')
            manifest['sourceFiles'][path.relative_to(prototype).as_posix()] = expected
        native = contained(experiment, experiment / bundle['project'])
        require(receipt['editableSource'] == bundle['project']
                and bound.get(native) == receipt['editableSourceSHA256'] == sha(native),
                f'Runtime editable source changed: {identity}')
        for path in (packet_path, review_path, receipt_path, delivery_path, canonical):
            manifest['sourceFiles'][path.relative_to(prototype).as_posix()] = sha(path)
        obj = {key: base[key] for key in ('frameSize', 'root', 'sourceScale', 'projection')}
        require(obj['frameSize'] == [192, 320] and obj['root'] == [96, 248]
                and obj['sourceScale'] == bundle['publishedSourceScale'] == 2,
                f'Runtime variant registration changed: {identity}')
        obj['clips'] = {}
        atlases = {(entry['clip'], entry['direction']): entry for entry in bundle['atlases']}
        require(len(atlases) == len(bundle['atlases']) == 8
                and set(atlases) == {(clip, facing) for clip in clips for facing in DIRECTIONS},
                f'Runtime atlas coverage changed: {identity}')
        frames = {(entry['clip'], entry['direction'], entry['index']): entry for entry in bundle['rawFrames']}
        require(len(frames) == len(bundle['rawFrames']) == 96
                and set(frames) == {(clip, facing, i) for clip in clips for facing in DIRECTIONS for i in range(12)},
                f'Runtime whole-frame coverage changed: {identity}')
        for clip in clips:
            loop = clip != 'load-cucumber'
            action = {'id': clip, 'frames': 12, 'fps': 12, 'loop': loop,
                      'frameOrder': list(range(12)), 'directions': {}}
            for facing in DIRECTIONS:
                atlas = atlases[clip, facing]
                require(atlas['columns'] == 6 and atlas['rows'] == 2
                        and atlas['size'] == [2304, 1280] and atlas['rects'] == RECTS
                        and atlas['fps'] == 12 and atlas['loop'] is loop
                        and atlas['frameOrder'] == list(range(12)),
                        f'Runtime timing or complete-canvas regions changed: {identity}/{clip}/{facing}')
                path = contained(experiment, experiment / atlas['path'])
                require(receipt['files'].get(atlas['path']) == atlas['sha256'] == bound.get(path),
                        f'Runtime atlas is outside its approved bundle: {identity}')
                relative = f'sprites/{identity}/{clip}-{facing}.png'
                action['directions'][facing] = {'image': relative, 'columns': 6, 'rows': 2,
                                               'atlasSize': [2304, 1280], 'rects': RECTS,
                                               'sha256': atlas['sha256']}
                images[relative] = path
                raw_frames[relative] = []
                for index in range(12):
                    frame = frames[clip, facing, index]
                    raw = contained(experiment, experiment / frame['path'])
                    require(receipt['files'].get(frame['path']) == frame['sha256'] == bound.get(raw),
                            f'Runtime frame is outside its approved bundle: {identity}')
                    raw_frames[relative].append(raw)
            obj['clips'][clip] = action
        manifest['objects'][identity] = obj
        manifest['refinement'][identity] = {'receipt': receipt_path.relative_to(prototype).as_posix(),
                                           'receiptSHA256': sha(receipt_path),
                                           'packetSHA256': receipt['candidatePacketSHA256'],
                                           'reviewSHA256': receipt['reviewSHA256'],
                                           'nativeCaptureScale': bundle['nativeCaptureScale']}
    return manifest, images, raw_frames


def verify_refined_actor_variants(project, source_project, kind):
    project, source_project = Path(project).resolve(), Path(source_project).resolve()
    manifest, images, frames = approved_actor_variants(source_project.parent, kind)
    runtime = project / f'assets/{kind}-variants'
    require(read(runtime / 'manifest.json') == manifest,
            f'Refined {kind} metadata, cadence or approval changed')
    base = read(source_project / 'assets/catalog/manifest.json')['objects']
    for identity, obj in manifest['objects'].items():
        for key in ('frameSize', 'root', 'sourceScale', 'projection'):
            require(obj[key] == base[identity][key], f'Refined {kind} changed base {key}: {identity}')
    for relative, approved in images.items():
        path = runtime / relative
        require(sha(path) == sha(approved), f'Refined {kind} atlas differs from approved bytes: {relative}')
        dimensions, pixels = _decode_png(path.read_bytes())
        require(dimensions == [2304, 1280], f'Refined {kind} atlas dimensions changed')
        for rect, frame in zip(RECTS, frames[relative]):
            frame_dimensions, frame_pixels = _decode_png(frame.read_bytes())
            require(frame_dimensions == [384, 640] and _crop(pixels, dimensions, rect) == frame_pixels,
                    f'Refined {kind} atlas is not the approved whole frame: {frame.name}')
    require({path.relative_to(runtime).as_posix() for path in runtime.rglob('*.png')} == set(images),
            f'Unexpected refined {kind} image payload')
    return {'objects': len(manifest['objects']), 'atlases': len(images), 'frames': len(images) * 12,
            'png_bytes': sum((runtime / name).stat().st_size for name in images),
            'approval_packets': {key: value['packetSHA256'] for key, value in manifest['refinement'].items()}}
