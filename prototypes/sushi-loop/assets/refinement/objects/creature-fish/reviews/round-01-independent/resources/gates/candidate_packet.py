#!/usr/bin/env python3
"""Seal and verify refinement handoffs; integrity checks do not judge art quality."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import sys


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def resolve(base, value):
    path = Path(value).expanduser()
    return (path if path.is_absolute() else base/path).resolve()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def png_frame(path):
    with Path(path).open('rb') as stream:
        head = stream.read(33)
    require(len(head) == 33 and head[:8] == b'\x89PNG\r\n\x1a\n' and head[12:16] == b'IHDR',
            f'Expected native PNG capture: {path}')
    return list(struct.unpack('>II', head[16:24]))


def named_paths(values):
    result = {}
    for value in values:
        name, sep, path = value.partition('=')
        require(sep and name and path and name not in result, f'Expected unique name=path: {value}')
        result[name] = Path(path).expanduser().resolve()
    return result


def create(args):
    brief_path = Path(args.brief).expanduser().resolve()
    brief, base = read(brief_path), brief_path.parent
    require(isinstance(brief.get('asset'), str) and brief['asset'].strip(), 'Missing asset')
    require(isinstance(brief.get('style'), str) and brief['style'].strip(), 'Missing chosen style')
    require(isinstance(brief.get('qualityCriteria'), dict) and brief['qualityCriteria'],
            'Freeze shared qualityCriteria before submission')
    frame, views = brief['capture']['frame'], brief['capture']['views']
    require(isinstance(frame, list) and len(frame) == 2 and all(type(v) is int and v > 0 for v in frame),
            'capture.frame must be [positive width, positive height]')
    require(isinstance(views, list) and views and all(isinstance(v, str) and v for v in views)
            and len(set(views)) == len(views), 'capture.views must name unique required captures')
    renders, previews = named_paths(args.render), named_paths(args.preview)
    require(set(renders) == set(views), 'Named native renders must exactly cover capture.views')
    require(set(brief['capture'].get('previews', [])) <= set(previews), 'Missing required preview')
    original = resolve(base, brief['source']['project'])
    backup = resolve(base, brief['source']['backup'])
    project = Path(args.project).expanduser().resolve()
    require(original != backup, 'Backup must be a separate file')
    require(project not in (original, backup), 'Candidate must be separate from original and backup')
    require(digest(original) == digest(backup), 'Original project differs from its untouched backup')
    validation = Path(args.validation).expanduser().resolve()
    require(isinstance(read(validation), dict) and read(validation), 'Missing native validation evidence')
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    require(not output.exists(), 'Packet already exists; create a new round instead of overwriting')

    def record(path):
        path = Path(path).resolve()
        return {'path': os.path.relpath(path, output.parent), 'sha256': digest(path)}

    files = {
        'brief': record(brief_path), 'originalProject': record(original), 'backup': record(backup),
        'originalSnapshot': record(resolve(base, brief['source']['snapshot'])),
        'target': record(resolve(base, brief['target']['image'])),
        'candidateProject': record(project), 'nativeValidation': record(validation)
    }
    target = brief['target']
    require(target.get('provenance'), 'Record target provenance')
    require(target.get('provenance') != 'imagegen' or target.get('prompt'), 'Save the actual imagegen prompt')
    if target.get('prompt'):
        files['targetPrompt'] = record(resolve(base, target['prompt']))
    for role, path in brief.get('agentPrompts', {}).items():
        files[f'agentPrompt:{role}'] = record(resolve(base, path))
    for name, path in named_paths(args.resource).items():
        files[f'candidateResource:{name}'] = record(path)
    captures = {}
    for name, path in renders.items():
        require(png_frame(path) == frame, f'{name} does not match declared frame {frame}')
        captures[name] = {**record(path), 'frame': frame}
    packet = {
        'schemaVersion': 1, 'asset': brief['asset'], 'style': brief['style'],
        'qualityCriteria': brief['qualityCriteria'], 'capture': brief['capture'],
        'files': files, 'candidateRenders': captures,
        'previews': {name: record(path) for name, path in previews.items()}
    }
    with output.open('x', encoding='utf-8') as stream:
        json.dump(packet, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'packet': str(output), 'sha256': digest(output), 'views': list(captures)}))


def verify(args):
    packet_path = Path(args.packet).expanduser().resolve()
    packet, base = read(packet_path), packet_path.parent
    require(packet['schemaVersion'] == 1, 'Unsupported packet version')
    records = [*packet['files'].values(), *packet['candidateRenders'].values(), *packet['previews'].values()]
    for item in records:
        path = resolve(base, item['path'])
        require(digest(path) == item['sha256'], f'Changed artifact: {item["path"]}')
    require(set(packet['candidateRenders']) == set(packet['capture']['views']), 'Incomplete capture set')
    for item in packet['candidateRenders'].values():
        require(png_frame(resolve(base, item['path'])) == item['frame'] == packet['capture']['frame'],
                f'Capture frame changed: {item["path"]}')
    if args.review:
        review = read(Path(args.review).expanduser().resolve())
        require(review.get('candidatePacketSHA256') == digest(packet_path), 'Review binds a different packet')
        require(review.get('verdict') == 'approve', 'Independent review has not approved this candidate')
        require(review.get('blockers') == [], 'Approved review must explicitly have no blockers')
        expected = {item['path'] for item in [*packet['candidateRenders'].values(), *packet['previews'].values()]}
        inspected = review.get('inspectedFiles', [])
        require(isinstance(inspected, list) and all(isinstance(item, str) for item in inspected),
                'Review must list inspected render/preview paths')
        require(expected <= set(inspected), 'Review lacks required render/preview inspection coverage')
    print('Artifact integrity verified' + ('; exact independent approval binding verified.' if args.review else '.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    seal = commands.add_parser('create')
    for name in ('brief', 'project', 'validation', 'output'):
        seal.add_argument(f'--{name}', required=True)
    seal.add_argument('--render', action='append', required=True)
    seal.add_argument('--preview', action='append', default=[])
    seal.add_argument('--resource', action='append', default=[])
    check = commands.add_parser('verify')
    check.add_argument('--packet', required=True)
    check.add_argument('--review')
    args = parser.parse_args()
    try:
        (create if args.command == 'create' else verify)(args)
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(f'Packet check failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
