"""Check approved evidence and promoted copies are present as exact Git index bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[3]
PRODUCTION = RUN.parent / 'production'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset')
    parser.add_argument('--round', required=True)
    parser.add_argument('--stage-missing', action='store_true', help='Preserve exact ignored/missing evidence in the index')
    args = parser.parse_args()
    folder = (RUN / 'objects' / args.asset).resolve()
    assert folder.is_relative_to(RUN / 'objects'), 'Object must stay inside this experiment'
    base = folder / 'candidates' / args.round
    packet = json.loads((base / 'packet.json').read_text())
    records = [*packet['files'].values(), *packet['candidateRenders'].values(), *packet['previews'].values()]
    expected = {}

    def add(path, digest):
        path = path.resolve()
        assert path.is_relative_to(ROOT), f'External dependency needs a retained repo copy: {path}'
        name = path.relative_to(ROOT).as_posix()
        assert expected.setdefault(name, digest) == digest, f'Conflicting dependency hash: {name}'
        assert path.is_file() and sha(path) == digest, f'Changed or missing evidence: {name}'

    add(base / 'packet.json', sha(base / 'packet.json'))
    review = folder / 'reviews' / f'{args.round}.json'
    verdict = json.loads(review.read_text())
    assert verdict['verdict'] == 'approve' and verdict['blockers'] == [], 'Independent approval required'
    assert verdict['candidatePacketSHA256'] == sha(base / 'packet.json'), 'Review binds a different candidate'
    add(review, sha(review))
    for record in records:
        add(base / record['path'], record['sha256'])
    # Prior sealed rounds remain reproducible even when the current handoff
    # no longer references an ignored cache/resource from an older packet.
    for old_path in sorted((folder / 'candidates').glob('*/packet.json')):
        if old_path == base / 'packet.json':
            continue
        old = json.loads(old_path.read_text())
        add(old_path, sha(old_path))
        for record in [*old['files'].values(), *old['candidateRenders'].values(), *old['previews'].values()]:
            add(old_path.parent / record['path'], record['sha256'])
        old_review = folder / 'reviews' / f'{old_path.parent.name}.json'
        if old_review.exists():
            assert json.loads(old_review.read_text())['candidatePacketSHA256'] == sha(old_path), 'Prior review binding changed'
            add(old_review, sha(old_review))
    promotion = folder / 'final/promotion.json'
    if promotion.exists():
        promoted = json.loads(promotion.read_text())
        assert promoted['round'] == args.round, 'Promotion and selected round differ'
        assert promoted['candidatePacketSHA256'] == sha(base / 'packet.json'), 'Promotion packet changed'
        assert promoted['reviewSHA256'] == sha(review), 'Promotion approval changed'
        for path, digest in promoted['files'].items():
            add(PRODUCTION / path, digest)
        add(promotion, sha(promotion))
    supplement = folder / 'final/approval.json'
    if supplement.exists():
        saved = json.loads(supplement.read_text())
        assert saved['packetSHA256'] == sha(base / 'packet.json'), 'Supplement packet changed'
        assert saved['reviewSHA256'] == sha(review), 'Supplement approval changed'
        add(supplement, sha(supplement))
        add(supplement.parent / saved['image'], saved['imageSHA256'])
        add(supplement.parent / saved['editableSource'], saved['editableSourceSHA256'])
    index = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT).decode()
    indexed = {entry.split('\t', 1)[1]: entry.split('\t', 1)[0].split()[1]
               for entry in index.split('\0') if entry}
    missing = sorted(set(expected) - set(indexed))
    if missing and args.stage_missing:
        for start in range(0, len(missing), 100):
            subprocess.run(['git', 'add', '-f', '--', *missing[start:start+100]], cwd=ROOT, check=True)
        index = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT).decode()
        indexed = {entry.split('\t', 1)[1]: entry.split('\t', 1)[0].split()[1]
                   for entry in index.split('\0') if entry}
    assert set(expected) <= set(indexed), f'Evidence omitted from Git index: {missing}'
    names = sorted(expected)
    actual = subprocess.check_output(['git', 'hash-object', '--stdin-paths'],
        input='\n'.join(names)+'\n', text=True, cwd=ROOT).splitlines()
    assert len(actual) == len(names), 'Incomplete Git object hashing'
    changed = [name for name, digest in zip(names, actual) if indexed[name] != digest]
    assert not changed, f'Current evidence bytes not staged: {changed}'
    print(json.dumps({'asset': args.asset, 'round': args.round, 'artifacts': len(names),
                      'preservedIgnoredFiles': len(missing) if args.stage_missing else 0,
                      'status': 'exact-evidence-and-promoted-copies-ready-for-commit'}))


if __name__ == '__main__':
    main()
