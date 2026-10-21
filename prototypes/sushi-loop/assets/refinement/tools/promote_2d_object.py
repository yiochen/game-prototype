"""Promote approved existing2D artwork without fabricating Blender provenance."""
import copy
import json
import shutil
import subprocess
from pathlib import Path
from PIL import Image
from promote_object import RUN, PRODUCTION, PACKET_HELPER, read, write, digest, require, relative


def promote(args):
    folder = RUN / 'objects' / args.asset
    brief = read(folder / 'brief.json')
    require(brief['constraints']['pipeline'] == 'existing-2d', 'Explicit existing2D brief required')
    root = folder / 'candidates' / args.round
    packet_path = root / 'packet.json'
    review_path = folder / 'reviews' / f'{args.round}.json'
    subprocess.run(['python3', str(PACKET_HELPER), 'verify', '--packet', str(packet_path),
                    '--review', str(review_path)], check=True)
    packet = read(packet_path)
    require(packet['asset'] == args.asset, 'Wrong approved object')
    snapshot = packet['files'].get('candidateResource:round:delivery.snapshot.json')
    require(snapshot is not None, 'Approved immutable delivery snapshot required')
    delivery = read(root / snapshot['path'])
    require(delivery.get('asset', packet['asset']) == args.asset, 'Wrong delivery object')
    bound = {(root / record['path']).resolve(): record['sha256']
             for record in [*packet['files'].values(), *packet['candidateRenders'].values(), *packet['previews'].values()]}
    library = read(PRODUCTION / 'library.json')
    original = next(o for o in library['objects'] if o['id'] == args.asset)
    obj = copy.deepcopy(original)
    previous = obj.get('refinement')
    require(not previous or args.replace_approved, 'Object already promoted; explicit --replace-approved required')
    require(not previous or previous['round'] != args.round, 'Selected round already promoted')
    require(obj['source']['pipeline'] in ['imagegen-2d', 'procedural-2d'], 'Not an existing2D source')
    copies, generated, hashes = {}, {}, {}

    def copy_file(source, destination):
        source, destination = Path(source).resolve(), Path(destination)
        sha = digest(source)
        require(bound.get(source) == sha, f'Unreviewed or changed artifact: {source}')
        if destination in copies:
            require(copies[destination][1] == sha, 'Conflicting shared output path')
        copies[destination] = (source, sha)
        hashes[relative(destination)] = sha

    source_root = PRODUCTION / 'source/2d/refinement' / args.asset
    project = (folder / delivery['project']).resolve()
    recipe = (folder / delivery['recipe']).resolve()
    require(project.is_relative_to(folder / 'source') and recipe.is_relative_to(folder / 'source'),
            'Editable artwork and recipe must stay inside owned source directory')
    require(project.suffix in ['.png', '.gd'], 'Actual raster/Godot2D source required')
    require(recipe.is_file(), 'Editable deterministic packing recipe required')
    project_dest = source_root / project.relative_to(folder)
    recipe_dest = source_root / recipe.relative_to(folder)
    copy_file(project, project_dest)
    copy_file(recipe, recipe_dest)
    for directory in ['source', 'inputs']:
        for path in (folder / directory).rglob('*'):
            if path.is_file() and path.resolve() in bound:
                copy_file(path, source_root / directory / path.relative_to(folder / directory))
    copy_file(folder / 'brief.json', source_root / 'brief.json')
    validation_dest = PRODUCTION / 'source/records' / args.asset / 'warm-refinement-validation.json'
    copy_file(folder / delivery['validation'], validation_dest)
    expected = {(clip['id'], direction) for clip in obj['clips'] for direction in clip['directions']}
    atlases = {(a['clip'], a['direction']): a for a in delivery['atlases']}
    require(len(atlases) == len(delivery['atlases']) and set(atlases) == expected,
            'Every original clip/facing required exactly once')
    raw = {(r['clip'], r['direction'], r['index']): r for r in delivery['rawFrames']}
    expected_raw = {(c['id'], d, i) for c in obj['clips'] for d in c['directions'] for i in range(c['frames'])}
    require(len(raw) == len(delivery['rawFrames']) and set(raw) == expected_raw,
            'Every original indexed2D frame required exactly once')
    raw_frames, guides, facing_pixels = [], [], {}
    for clip in obj['clips']:
        for direction, current in clip['directions'].items():
            a = atlases[clip['id'], direction]
            rects = [[r[k] for k in ['x','y','width','height']] if isinstance(r, dict) else r for r in a['rects']]
            require(a.get('size', a.get('atlasSize')) == current['atlasSize']
                    and a['columns'] == current['columns'] and a['rows'] == current['rows']
                    and rects == current['rects'], 'Original atlas layout changed')
            atlas_path = folder / a['path']
            atlas = Image.open(atlas_path)
            require(atlas.mode == 'RGBA' and list(atlas.size) == current['atlasSize'], 'Atlas size/alpha drift')
            copy_file(atlas_path, PRODUCTION / current['image'])
            captures = []
            for i, (x,y,width,height) in enumerate(rects):
                frame_path = folder / raw[clip['id'], direction, i]['path']
                frame = Image.open(frame_path)
                require(frame.mode == 'RGBA' and list(frame.size) == [width,height], 'Frame size/alpha drift')
                require(atlas.crop((x,y,x+width,y+height)).tobytes() == frame.tobytes(), 'Atlas pixels differ from approved frame')
                if obj.get('facingPolicy') == 'camera-facing':
                    key = (clip['id'], i)
                    pixels = frame.tobytes()
                    require(facing_pixels.setdefault(key, pixels) == pixels, 'Camera-facing art changes with facing')
                destination = PRODUCTION / 'source/registered' / args.asset / f'{clip["id"]}-{direction}' / 'source-captures' / f'{i:03}.png'
                copy_file(frame_path, destination)
                captures.append({'path': f'source-captures/{i:03}.png', 'sha256': digest(frame_path)})
                raw_frames.append({'image': relative(destination), 'sha256': digest(frame_path),
                                   'clip': clip['id'], 'direction': direction, 'index': i})
            guide_path = PRODUCTION / 'source/registered' / args.asset / f'{clip["id"]}-{direction}' / 'guide.json'
            generated[guide_path] = {'version':1, 'kind':'registered-2d-sheet', 'representation':obj['source']['pipeline'],
                'frame':obj['frameSize'], 'anchor':obj['root'], 'captureScale':obj['sourceScale'],
                'size':current['atlasSize'], 'columns':current['columns'], 'rows':current['rows'],
                'cells':[{'index':i,'rect':rect} for i,rect in enumerate(rects)], 'sourceCaptures':captures,
                'processing':'Exact approved fixed-frame2D pixels; lossless atlas placement only. No Blender camera or geometry.'}
            guides.append(relative(guide_path))
    source = obj['source']
    source.update({'modelScript':relative(recipe_dest), 'recipe':relative(recipe_dest),
                   'refinedSource':relative(project_dest), 'rawFrames':raw_frames, 'guides':guides,
                   'refinement':{'packet':f'../refinement/objects/{args.asset}/candidates/{args.round}/packet.json',
                                 'review':f'../refinement/objects/{args.asset}/reviews/{args.round}.json',
                                 'validation':relative(validation_dest)}})
    if project.suffix == '.png':
        source.update(artwork=relative(project_dest), sha256=digest(project))
    else:
        source['godot'] = relative(project_dest)
    # Existing2D registration retains sourceScale, without native3D capture fields.
    require('captureFingerprint' not in obj and 'sourceCaptureScale' not in obj['registration'],
            'Existing2D object contains superseded native3D registration')
    obj['artStyle'].update(revision=f'warm-soft-{args.asset}-{args.round}', style='Warm softly lit cartoon',
                           representation='existing2D artwork with editable packing recipe')
    obj['productionStage'] = 'Existing2D · warm soft cartoon · independent judge approved'
    progress = read(RUN / 'progress.json')
    item = next(o for o in progress['objects'] if o['id'] == args.asset)
    obj['refinement'] = {'status':'approved', 'round':args.round, 'packetSHA256':digest(packet_path),
                         'reviewSHA256':digest(review_path), 'editor':item['editor'], 'judge':item['judge']}
    require(obj['clips'] == original['clips'], 'Clip contract changed')
    if not args.apply:
        print(json.dumps({'asset':args.asset,'status':'verified-dry-run','frames':len(raw_frames),'copies':len(copies)}))
        return
    if previous:
        write(folder / 'final/history' / previous['round'] / 'catalog-object.json', original)
        write(folder / 'final/history' / previous['round'] / 'promotion.json', read(folder / 'final/promotion.json'))
    else:
        write(folder / 'final/original-catalog-object.json', original)
    for destination,(path,sha) in copies.items():
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,destination)
        require(digest(destination) == sha, 'Copy changed bytes')
    for destination,value in generated.items():
        write(destination,value)
        hashes[relative(destination)] = digest(destination)
    source['hashes'] = hashes
    library['objects'] = [obj if o['id'] == args.asset else o for o in library['objects']]
    write(PRODUCTION / 'library.json',library)
    write(folder / 'final/promotion.json',{'asset':args.asset,'round':args.round,
        'candidatePacketSHA256':digest(packet_path),'reviewSHA256':digest(review_path),
        'files':hashes,'status':'exact-approved-bytes-promoted','representation':'existing-2d'})
    item.update(status='approved',round=args.round,packetSHA256=digest(packet_path))
    progress['completed'] = sum(o['status'] in ['approved','published'] for o in progress['objects'])
    write(RUN / 'progress.json',progress)
    print(json.dumps({'asset':args.asset,'status':'promoted','frames':len(raw_frames),'completed':progress['completed']}))
