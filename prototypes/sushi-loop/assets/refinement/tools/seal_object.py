"""Seal one delivered object round, including raw frames, atlases and native recipes."""
import argparse
import json
from pathlib import Path
import subprocess

RUN = Path(__file__).resolve().parents[1]
HELPER = '/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset')
    parser.add_argument('--round', required=True)
    args = parser.parse_args()
    folder = RUN / 'objects' / args.asset
    delivery = json.loads((folder / 'delivery.json').read_text())
    candidate = folder / 'candidates' / args.round
    project = folder / delivery.get('project', delivery.get('source', {}).get('blend', ''))
    assert project.is_file() and project.suffix == '.blend', 'Native Blender project required'
    command = ['python3', HELPER, 'create', '--brief', str(folder / 'brief.json'),
               '--project', str(project), '--validation', str(folder / delivery['validation']),
               '--output', str(candidate / 'packet.json')]
    for facing, path in delivery.get('heroes', {d: f'candidates/{args.round}/{d}.png' for d in 'NESW'}).items():
        command += ['--render', f'{facing}={folder / path}']
    previews = delivery['previews']
    if isinstance(previews, list):
        previews = {Path(path).stem: path for path in previews}
    for name, path in previews.items():
        command += ['--preview', f'{name}={folder / path}']
    resources = {}
    # Include every delivered file in the round, not just its representative hero.
    for path in candidate.rglob('*'):
        if path.is_file() and path.name != 'packet.json':
            resources['round:' + path.relative_to(candidate).as_posix()] = path
    for path in (folder / 'source').glob('*'):
        if path.is_file() and path.suffix in ['.py', '.json', '.gd', '.blend']:
            resources['source:' + path.name] = path
    for name, path in resources.items():
        command += ['--resource', f'{name}={path}']
    subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
