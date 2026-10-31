"""Verify #19 static artwork and the original native cover reveal animation."""
from pathlib import Path
import json
import struct
from verify_editor_ui import require, sha, _decode_png, _crop

TRASH = ['garbage-sofa', 'garbage-car', 'garbage-shelving', 'garbage-armchair', 'garbage-cabinet']
LANDMARKS = ['dock-cover', 'dock-floor', 'submarine-yellow', 'workshop-hut']

def verify_expansion(project: Path, source_project: Path | None = None) -> dict:
    project = Path(project).resolve()
    prototype = Path(source_project or project).resolve().parent
    preview = prototype / 'design/expansion-preview'
    runtime = project / 'assets/expansion'
    manifest = json.loads((runtime / 'manifest.json').read_text())
    registry = json.loads((preview / 'world-registration.json').read_text())
    require(manifest['version'] == 1 and manifest['cellSize'] == 128, 'Invalid expansion manifest')
    require(manifest['previewRegistrySha256'] == sha(preview / 'world-registration.json'), 'Stale expansion registration')
    require(set(manifest['objects']) == set(TRASH + LANDMARKS), 'Incomplete expansion object set')
    expected = set()
    for identity in TRASH + LANDMARKS:
        clip = 'clearance-static' if identity in TRASH else 'static'
        action = manifest['objects'][identity]['clips'][clip]
        faces = ['N', 'E', 'S', 'W'] if identity in TRASH else ['S']
        require(set(action['directions']) == set(faces) and action['frames'] == 1 and action['loop'] is False, 'Expansion static/facing contract changed')
        for face in faces:
            key = f'{identity}-{face}' if identity in TRASH else identity
            record = registry[key]
            entry = action['directions'][face]
            image = f'sprites/{key}.png'
            expected.add(image)
            native = runtime / image
            approved = preview / record['destination']
            require(entry['image'] == image and sha(native) == sha(approved) == record['sha256'], f'Expansion approved bytes changed: {key}')
            require(entry['frameSize'] == record['frame_size'] and entry['root'] == record['root'] and entry['sourceScale'] == 2, f'Expansion root/frame changed: {key}')
            require(entry['visibleBounds'] == record['visible_bounds'], f'Expansion preview crop changed: {key}')
            width, height = record['crop_xywh'][2:]
            require(entry['rects'] == [[0, 0, width, height]], f'Expansion frame region changed: {key}')
            require(list(struct.unpack('>II', native.read_bytes()[16:24])) == [width, height], f'Expansion frame size changed: {key}')
            require(manifest['sources'][image] == {'path': approved.relative_to(prototype).as_posix(), 'sha256': record['sha256'], 'registration': key}, 'Expansion lineage changed')
            if identity in ['garbage-armchair', 'garbage-cabinet']:
                asset = 'armchair' if identity.endswith('armchair') else 'cabinet'
                final = preview / 'experiments' / asset / 'final'
                final_image = final / (f'{face}.png' if asset == 'armchair' else f'static-{face}.png')
                require(sha(native) == sha(final_image), 'New model differs from independently approved native frame')
                approval = json.loads((final / 'manifest.json').read_text())
                if asset == 'armchair':
                    experiment = final.parent
                    require(sha(experiment / approval['packet']) == approval['packetSHA256'] and sha(experiment / approval['review']) == approval['reviewSHA256'], 'Armchair approval binding changed')
                    require(sha(final / 'armchair.blend') == approval['files']['model']['sha256'], 'Armchair source changed after approval')
                else:
                    experiment = final.parent
                    require(approval['verdict'] == 'approve' and sha(experiment / 'candidates/evidence-02/packet.json') == approval['candidatePacketSHA256'] and sha(experiment / 'reviews/evidence-02.json') == approval['independentReviewSHA256'], 'Cabinet approval binding changed')
                    require(sha(final / 'cabinet.blend') == approval['files']['cabinet.blend']['sha256'], 'Cabinet source changed after approval')
            else:
                source = prototype / record['source']
                require(sha(source) == record['source_sha256'], f'Original production source changed: {key}')
                dimensions, pixels = _decode_png(source.read_bytes())
                cropped = _crop(pixels, dimensions, record['crop_xywh'])
                native_dimensions, native_pixels = _decode_png(native.read_bytes())
                require(native_dimensions == [width, height] and cropped == native_pixels, f'Expansion crop pixels differ from production: {key}')
    library = json.loads((prototype / 'assets/production/library.json').read_text())
    source_object = next(o for o in library['objects'] if o['id'] == 'dock-cover')
    source_clip = next(c for c in source_object['clips'] if c['id'] == 'uncover')
    original = source_clip['directions']['S']
    cover = manifest['objects']['dock-cover']['clips']
    action = cover['uncover']; entry = action['directions']['S']
    require(action['frames'] == source_clip['frames'] == 12 and action['fps'] == source_clip['fps'] == 12 and action['loop'] is False, 'Cover reveal must retain its native one-shot timing')
    require(set(action['directions']) == {'S'} and entry['rects'] == original['rects'], 'Cover reveal frames/order changed')
    source = prototype / 'assets/production' / original['image']
    image = 'sprites/dock-cover-uncover-S.png'; expected.add(image)
    require(entry['image'] == image and entry['sha256'] == sha(runtime / image) == sha(source), 'Cover animation must be the exact approved native atlas')
    require(manifest['sources'][image] == {'path': source.relative_to(prototype).as_posix(), 'sha256': sha(source), 'registration': 'dock-cover/uncover/S'}, 'Cover animation lineage changed')
    for direction in [entry,cover['uncovered']['directions']['S']]:
        require(direction['frameSize'] == source_object['frameSize'] and direction['root'] == source_object['root'] and direction['sourceScale'] == source_object['sourceScale'], 'Cover reveal registration changed')
    image = 'sprites/dock-cover-uncovered-S.png'; expected.add(image)
    opened = cover['uncovered']; entry = opened['directions']['S']; region = original['rects'][-1]
    require(opened['frames'] == 1 and opened['loop'] is False and set(opened['directions']) == {'S'} and entry['image'] == image and entry['rects'] == [[0,0,region[2],region[3]]], 'Completed cover pose must hold the native final frame')
    dimensions,pixels = _decode_png(source.read_bytes()); final_dimensions,final_pixels = _decode_png((runtime / image).read_bytes())
    require(final_dimensions == region[2:] and final_pixels == _crop(pixels,dimensions,region), 'Completed cover pose differs from the native final frame')
    require(entry['sha256'] == sha(runtime / image) and manifest['sources'][image] == {'path':source.relative_to(prototype).as_posix(),'source_sha256':sha(source),'sha256':sha(runtime / image),'crop_xywh':region,'registration':'dock-cover/uncovered/S'}, 'Completed cover pose lineage changed')
    require({p.relative_to(runtime).as_posix() for p in runtime.rglob('*.png')} == expected == set(manifest['sources']), 'Unexpected expansion runtime image')
    return {'objects': len(manifest['objects']), 'frames': 37, 'images': len(expected), 'bytes': sum((runtime / p).stat().st_size for p in expected), 'manifest_sha256': sha(runtime / 'manifest.json')}

if __name__ == '__main__':
    print(json.dumps(verify_expansion(Path(__file__).resolve().parents[1]), indent=2))
