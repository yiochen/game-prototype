"""Seal one delivered object round, including raw frames, atlases and native recipes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

RUN = Path(__file__).resolve().parents[1]
HELPER = '/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset')
    parser.add_argument('--round', required=True)
    parser.add_argument('--preview', action='append', default=[], help='Explicit additional name=object-relative preview alias')
    args = parser.parse_args()
    folder = RUN / 'objects' / args.asset
    delivery = json.loads((folder / 'delivery.json').read_text())
    candidate = folder / 'candidates' / args.round
    assert not (folder / 'reviews' / f'{args.round}.json').exists(), 'Do not reseal a reviewed round'
    snapshot = candidate / 'delivery.snapshot.json'
    snapshot.write_text(json.dumps(delivery, indent=2) + '\n')
    project = folder / delivery.get('project', delivery.get('source', {}).get('blend', ''))
    assert project.is_file() and project.suffix == '.blend', 'Native Blender project required'
    command = ['python3', HELPER, 'create', '--brief', str(folder / 'brief.json'),
               '--project', str(project), '--validation', str(folder / delivery['validation']),
               '--output', str(candidate / 'packet.json')]
    heroes = delivery.get('heroes', {d: f'candidates/{args.round}/{d}.png' for d in 'NESW'})
    if isinstance(heroes, list):
        heroes = {record['direction']: record['path'] for record in heroes}
    for facing, path in heroes.items():
        command += ['--render', f'{facing}={folder / path}']
    previews = delivery['previews']
    if isinstance(previews, list):
        previews = {record['id']: record['path'] for record in previews} if previews and isinstance(previews[0], dict) else {Path(path).stem: path for path in previews}
    for alias in args.preview:
        name, separator, path = alias.partition('=')
        assert separator and name and name not in previews and (folder / path).is_file(), 'Invalid extra preview alias'
        previews[name] = path
    for name, path in previews.items():
        command += ['--preview', f'{name}={folder / path}']
    resources = {}
    brief = json.loads((folder / 'brief.json').read_text())
    # Frozen native contracts and supplemental runtime sources are part of the
    # review, even when their pixels are not catalog animation frames.
    for path in (folder / 'inputs').rglob('*'):
        if path.is_file():
            resources['input:' + path.relative_to(folder / 'inputs').as_posix()] = path
    for name, record in brief.get('runtimeVariants', {}).get('resources', {}).items():
        path = folder / record['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], f'Changed runtime variant input: {name}'
    for name, path in brief.get('technicalResources', {}).items():
        assert (folder / path).is_file(), f'Missing frozen technical resource: {path}'
        resources['technical:' + name] = folder / path
    # Include every delivered file in the round, not just its representative hero.
    for path in candidate.rglob('*'):
        if path.is_file() and path.name != 'packet.json':
            resources['round:' + path.relative_to(candidate).as_posix()] = path
    for path in (folder / 'source').rglob('*'):
        if path.is_file() and path.suffix in ['.py', '.json', '.gd', '.gdshader', '.patch', '.blend', '.tscn', '.godot']:
            resources['source:' + path.relative_to(folder / 'source').as_posix()] = path
    for name, path in resources.items():
        command += ['--resource', f'{name}={path}']
    raise SystemExit(subprocess.run(command).returncode)


if __name__ == '__main__':
    main()
