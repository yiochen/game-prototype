"""Seal one delivered object round, including raw frames, atlases and native recipes."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

RUN = Path(__file__).resolve().parents[1]
HELPER = '/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset')
    parser.add_argument('--round', required=True)
    parser.add_argument('--brief', default='brief.json', help='Versioned brief filename in the object folder; never overwrite a sealed brief')
    parser.add_argument('--delivery', default='delivery.json', help='Versioned delivery filename in the object folder')
    parser.add_argument('--preview', action='append', default=[], help='Explicit additional name=object-relative preview alias')
    args = parser.parse_args()
    folder = RUN / 'objects' / args.asset
    brief_path = (folder / args.brief).resolve()
    assert brief_path.parent == folder.resolve() and brief_path.suffix == '.json', 'Brief must stay in the same object folder'
    delivery_path = (folder / args.delivery).resolve()
    assert delivery_path.parent == folder.resolve() and delivery_path.suffix == '.json', 'Delivery must stay in the same object folder'
    delivery = json.loads(delivery_path.read_text())
    candidate = folder / 'candidates' / args.round
    assert not (folder / 'reviews' / f'{args.round}.json').exists(), 'Do not reseal a reviewed round'
    assert not (candidate / 'packet.json').exists(), 'Do not overwrite any sealed round'
    candidate.mkdir(parents=True, exist_ok=True)
    snapshot = candidate / 'delivery.snapshot.json'
    snapshot.write_text(json.dumps(delivery, indent=2) + '\n')
    source_record = delivery.get('source', {})
    source_project = source_record.get('blend', '') if isinstance(source_record, dict) else source_record
    project = folder / (delivery.get('project') or source_project)
    brief = json.loads(brief_path.read_text())
    pipeline = brief.get('constraints', {}).get('pipeline')
    allowed_sources = ['.png', '.gd'] if pipeline == 'existing-2d' else ['.blend']
    assert project.is_file() and project.suffix in allowed_sources, 'Actual editable source required for declared pipeline'
    command = ['python3', HELPER, 'create', '--brief', str(brief_path),
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
    criteria = brief['qualityCriteria']
    criteria_sha = criteria.get('criteriaFileSHA256', criteria.get('criteriaSHA256'))
    if criteria.get('criteriaFile') and criteria_sha:
        criteria_path = folder / criteria['criteriaFile']
        assert hashlib.sha256(criteria_path.read_bytes()).hexdigest() == criteria_sha, 'Frozen criteria file changed'
        resources['frozenQualityCriteria'] = criteria_path
    # Frozen native contracts and supplemental runtime sources are part of the
    # review, even when their pixels are not catalog animation frames.
    for path in (folder / 'inputs').rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            resources['input:' + path.relative_to(folder / 'inputs').as_posix()] = path
    for name, record in brief.get('runtimeVariants', {}).get('resources', {}).items():
        path = folder / record['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], f'Changed runtime variant input: {name}'
    for name, path in brief.get('technicalResources', {}).items():
        assert (folder / path).is_file(), f'Missing frozen technical resource: {path}'
        resources['technical:' + name] = folder / path
    # A revision may reuse exact frames/evidence from an earlier immutable
    # round. Those referenced bytes must be bound too, not just the new folder.
    for kind in ['resources', 'rawFrames', 'atlases']:
        records = delivery.get(kind, [])
        entries = records.items() if isinstance(records, dict) else enumerate(records)
        for index, record in entries:
            path = folder / (record['path'] if isinstance(record, dict) else record)
            assert path.is_file(), f'Missing delivered {kind}: {path}'
            resources[f'delivery:{kind}:{index}'] = path
    # Include every delivered file in the round, not just its representative hero.
    for path in candidate.rglob('*'):
        if path.is_file() and path.name != 'packet.json' and '__pycache__' not in path.parts:
            resources['round:' + path.relative_to(candidate).as_posix()] = path
    for path in (folder / 'source').rglob('*'):
        if path.is_file() and path.suffix in ['.py', '.json', '.gd', '.gdshader', '.patch', '.blend', '.tscn', '.godot']:
            resources['source:' + path.relative_to(folder / 'source').as_posix()] = path
    for name, path in resources.items():
        command += ['--resource', f'{name}={path}']
    # Large animation/consumer packets exceed macOS ARG_MAX. Invoke the same
    # helper in process; retain every resource and all its validation rules.
    values = {flag: [] for flag in ['--render', '--preview', '--resource']}
    scalar = {}
    for flag, value in zip(command[3::2], command[4::2]):
        if flag in values:
            values[flag].append(value)
        else:
            scalar[flag.removeprefix('--')] = value
    packet_args = argparse.Namespace(**scalar,
        render=values['--render'], preview=values['--preview'], resource=values['--resource'])
    runpy.run_path(HELPER)['create'](packet_args)


if __name__ == '__main__':
    main()
