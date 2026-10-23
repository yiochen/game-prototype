"""Exact approved warm-cartoon smile overlay; no repaint or animation changes."""
import copy
from pathlib import Path

from refinement_contract import contained, read, verified_packet
from verify_editor_ui import _crop, _decode_png, require, sha

ROOT = 'assets/refinement/objects/bubble-happy'
RECEIPT = ROOT + '/final/runtime-variant-approval.json'
PRODUCTION_ROOT = 'assets/production/source/2d/refinement/bubble-happy'
CLIPS = ['happy-smile-appear', 'happy-smile-idle', 'happy-smile-fade', 'happy-smile-transition']


def approved_feedback(prototype):
    prototype = Path(prototype).resolve()
    receipt_path = prototype / RECEIPT
    receipt = read(receipt_path)
    require(receipt.get('asset') == 'bubble-happy'
            and receipt.get('kind') == 'existing-smile-runtime-variant'
            and receipt.get('status') == 'exact-approved-variant-bytes-saved-final-Godot-cutover-pending',
            'Invalid approved smile receipt')
    experiment = prototype / ROOT
    candidate = contained(experiment, experiment / 'candidates' / receipt['round'])
    packet = candidate / 'packet.json'
    review = contained(experiment, experiment / 'reviews' / (receipt['round'] + '.json'))
    _, bound = verified_packet(prototype, packet, receipt['candidatePacketSHA256'],
                               review, receipt['reviewSHA256'], 'bubble-happy')
    library = read(prototype / 'assets/production/library.json')
    base = next(obj for obj in library['objects'] if obj['id'] == 'bubble-happy')
    require(base['refinement']['packetSHA256'] == receipt['candidatePacketSHA256']
            and base['refinement']['reviewSHA256'] == receipt['reviewSHA256'],
            'Smile variant does not match the approved main object')
    require(len(receipt.get('files', {})) == 53, 'Approved smile source bundle is incomplete')
    for relative, expected in receipt['files'].items():
        path = contained(candidate, candidate / relative)
        require(bound.get(path) == expected and sha(path) == expected,
                f'Approved smile artifact changed: {relative}')
    approved = read(candidate / 'runtime-variants/smile/manifest.json')
    canonical = contained(experiment, experiment / receipt['canonicalSource'])
    production = contained(prototype, prototype / 'assets/production' / receipt['sourceCopyInProduction'])
    require(bound.get(canonical) == receipt['canonicalSourceSHA256'] == sha(canonical) == sha(production),
            'Approved canonical smile source changed')
    manifest = copy.deepcopy(approved)
    manifest['baseLibrarySha256'] = sha(prototype / 'assets/production/library.json')
    manifest['sourceFiles'] = {}
    for relative, expected in approved['sourceFiles'].items():
        source = contained(experiment, experiment / relative)
        target_relative = PRODUCTION_ROOT + '/' + relative
        target = contained(prototype, prototype / target_relative)
        require(bound.get(source) == expected == sha(source) == sha(target),
                f'Approved smile production source changed: {relative}')
        manifest['sourceFiles'][target_relative] = expected
    manifest['refinement'] = {'receipt': RECEIPT, 'receiptSHA256': sha(receipt_path),
                              'packetSHA256': receipt['candidatePacketSHA256'],
                              'reviewSHA256': receipt['reviewSHA256']}
    return manifest, receipt, candidate


def verify_refined_feedback(project, source_project):
    project, source_project = Path(project).resolve(), Path(source_project).resolve()
    prototype = source_project.parent
    expected, receipt, candidate = approved_feedback(prototype)
    runtime = project / 'assets/feedback-variants'
    require(read(runtime / 'manifest.json') == expected,
            'Refined smile metadata differs from approved registration or relocated provenance')
    base = read(source_project / 'assets/catalog/manifest.json')['objects']['bubble-happy']
    obj = expected['objects']['bubble-happy']
    require(expected['version'] == 1 and set(expected['objects']) == {'bubble-happy'},
            'Refined smile identity/version changed')
    for key in ('frameSize', 'root', 'sourceScale', 'projection'):
        require(obj[key] == base[key], f'Refined smile changed approved {key}')
    require(set(obj['clips']) == set(CLIPS), 'Refined smile clip coverage changed')
    images, total_bytes = set(), 0
    for clip in CLIPS:
        action = obj['clips'][clip]
        require(action['id'] == clip and action['frames'] == 12 and action['fps'] == 12
                and action['loop'] is clip.endswith('-idle')
                and action['frameOrder'] == list(range(12)) and set(action['directions']) == {'S'},
                f'Refined smile cadence/facing changed: {clip}')
        entry = action['directions']['S']
        image = f'sprites/bubble-happy/{clip}-S.png'
        rects = [[i % 6 * 384, i // 6 * 640, 384, 640] for i in range(12)]
        require(entry['image'] == image and entry['columns'] == 6 and entry['rows'] == 2
                and entry['atlasSize'] == [2304, 1280] and entry['rects'] == rects,
                f'Refined smile frame regions changed: {clip}')
        path = runtime / image
        bundle_path = f'runtime-variants/smile/atlases/{clip}-S.png'
        require(sha(path) == entry['sha256'] == receipt['files'][bundle_path],
                f'Refined smile atlas changed: {clip}')
        dimensions, pixels = _decode_png(path.read_bytes())
        require(dimensions == [2304, 1280], f'Refined smile atlas dimensions changed: {clip}')
        for index, rect in enumerate(rects):
            raw = candidate / f'runtime-variants/smile/raw/{clip}-S-{index:04}.png'
            raw_dimensions, raw_pixels = _decode_png(raw.read_bytes())
            require(raw_dimensions == [384, 640] and _crop(pixels, dimensions, rect) == raw_pixels,
                    f'Refined smile atlas is not the approved whole frame: {clip}/{index}')
        images.add(image)
        total_bytes += path.stat().st_size
    require({path.relative_to(runtime).as_posix() for path in runtime.rglob('*.png')} == images,
            'Unexpected refined smile image payload')
    return {'objects': 1, 'atlases': 4, 'frames': 48, 'png_bytes': total_bytes,
            'image_sha256': receipt['canonicalSourceSHA256'],
            'approval_packet_sha256': receipt['candidatePacketSHA256']}
