"""Publish already inspected recipe applications serially to the existing PR preview.

This is a current-task runner, not a scheduler. It never creates acceptance or
changes artwork. Every next production promotion waits for the previous exact
commit's Netlify success. The coordinator retains ownership of the Git index.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[5]
RUN = ROOT / 'prototypes/sushi-loop/assets/refinement'
TOOLS = RUN / 'tools'
PYTHON = sys.executable
QUEUE = ['belt-corner-w-n', 'belt-corner-s-e', 'belt-corner-e-s',
         'belt-corner-s-w', 'belt-corner-w-s', 'belt-start-n', 'belt-start-e',
         'belt-start-s', 'belt-start-w', 'belt-end-n', 'belt-end-e',
         'belt-end-s', 'belt-end-w']


def command(args, log=None):
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    if log:
        log.write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(f'{args}: {result.stdout[-5000:]}')
    return result.stdout.strip()


def announce(value):
    print(json.dumps(value), flush=True)


def deploy_success(commit):
    while True:
        response = json.loads(command(['gh', 'api',
            f'repos/yiochen/game-prototype/commits/{commit}/status']))
        assert response['sha'] == commit
        latest = next((s for s in response['statuses']
                       if s['context'] == 'deploy/netlify'), None)
        if latest and latest['state'] == 'success':
            announce({'commit': commit, 'Netlify': 'success',
                      'url': latest['target_url']})
            return
        if latest and latest['state'] in ['failure', 'error']:
            raise RuntimeError(f'Netlify rejected {commit}: {latest}')
        time.sleep(15)


def mark_live(asset, commit):
    path = RUN / 'progress.json'
    progress = json.loads(path.read_text())
    entry = next(o for o in progress['objects'] if o['id'] == asset)
    entry.update(status='published', publishedCommit=commit)
    progress['published'] = sum(o['status'] == 'published'
                                for o in progress['objects'])
    progress['current'] = (f"{progress['published']} objects live. Remaining "
        'validated conveyor recipes publish individually; native character '
        'refinement and other fresh object pairs continue. Final Godot sync pending.')
    path.write_text(json.dumps(progress, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-commit', required=True)
    parser.add_argument('--previous-object', required=True)
    parser.add_argument('--start', choices=QUEUE, default=QUEUE[0])
    args = parser.parse_args()
    deploy_success(args.previous_commit)
    mark_live(args.previous_object, args.previous_commit)
    for asset in QUEUE[QUEUE.index(args.start):]:
        assert not command(['git', 'diff', '--cached', '--name-only']), 'Index must be empty'
        receipt = json.loads((RUN / 'objects' / asset / 'validations/round-01.json').read_text())
        assert receipt['verdict'] == 'validated' and receipt['independentReview'] is False
        announce({'asset': asset, 'stage': 'promoting-exact-validated-bytes'})
        command([PYTHON, str(TOOLS / 'promote_object.py'), asset,
                 '--round', 'round-01', '--apply'])
        logroot = Path('/tmp') / f'conveyor-publish-{asset}'
        logroot.mkdir(exist_ok=True)
        command(['node', '--test', *[str(p.relative_to(ROOT))
                 for p in (ROOT / 'prototypes/sushi-loop/tests').glob('*.test.js')]],
                logroot / 'engine-tests.log')
        command(['npm', 'run', 'build'], logroot / 'build.log')
        command(['node', str(TOOLS / 'smoke_object.mjs'), asset], logroot / 'browser.log')
        command(['git', 'add', str(RUN / 'objects' / asset),
                 str(RUN.parent / 'production'), str(RUN / 'progress.json')])
        if asset == QUEUE[0]:
            command(['git', 'add', str(Path(__file__)),
                     str(RUN / 'objects/belt-corner-e-n/source/batch')])
        closure = command([PYTHON, str(TOOLS / 'verify_staged_object.py'), asset,
                           '--round', 'round-01', '--stage-missing'])
        command(['git', 'diff', '--cached', '--check', '--', '.',
                 ':(exclude)**/*.log', ':(exclude)**/imagegen-prompt*.txt'])
        command(['git', 'commit', '-qm', f'Apply shared warm cartoon recipe to {asset}'])
        commit = command(['git', 'rev-parse', 'HEAD'])
        announce({'asset': asset, 'commit': commit, 'stage': 'pushing', 'closure': closure})
        command(['git', 'push', 'origin', 'codex/warm-soft-catalog'], logroot / 'push.log')
        deploy_success(commit)
        mark_live(asset, commit)
    announce({'status': 'all-queued-conveyors-live',
              'progressNote': 'Last confirmed live status is saved; next object commit records it.'})


if __name__ == '__main__':
    main()
