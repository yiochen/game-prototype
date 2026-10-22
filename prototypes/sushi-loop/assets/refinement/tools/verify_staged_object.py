"""Check approved evidence and promoted copies are present as exact Git index bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from acceptance_contract import acceptance

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

    def add_review(path, receipt):
        add(path, sha(path))
        technical_manifest = receipt.get('technicalEvidence', {}).get('supplementalEvidenceManifest')
        supplemental = receipt.get('supplementalEvidence', technical_manifest or {})
        assert isinstance(supplemental, (dict, list)), 'Unknown supplemental evidence format'
        manifest_descriptor = isinstance(supplemental, dict) and {'path', 'sha256'} <= supplemental.keys()
        if manifest_descriptor:
            supplemental = [supplemental]
        elif isinstance(supplemental, dict):
            supplemental = [{'path': name, 'sha256': digest} for name, digest in supplemental.items()]

        def add_supplement(record, relative_to):
            assert isinstance(record, dict) and {'path', 'sha256'} <= record.keys(), 'Incomplete supplemental evidence'
            # Historical reviews use either object- or review-relative paths.
            locations = {(base / record['path']).resolve() for base in (folder, relative_to)}
            existing = [resource for resource in locations if resource.is_file()]
            assert len(existing) == 1, f'Missing or ambiguous supplemental evidence: {record["path"]}'
            add(existing[0], record['sha256'])
            return existing[0]

        for record in supplemental:
            resource = add_supplement(record, path.parent)
            if manifest_descriptor:
                manifest = json.loads(resource.read_text())
                if technical_manifest and supplemental == [technical_manifest]:
                    assert manifest.get('candidatePacketSHA256') == receipt['candidatePacketSHA256'], 'Supplement manifest binds wrong packet'
                    assert isinstance(manifest.get('bindings'), dict), 'Technical supplement needs explicit input bindings'
                    assert isinstance(manifest.get('independentSupplementalEvidence'), list), 'Technical supplement needs explicit output records'
                    assert isinstance(manifest.get('originalIndependentAudit'), list), 'Technical supplement needs explicit source audit records'
                    entries = [*manifest['bindings'].values(), *manifest['independentSupplementalEvidence'],
                               *manifest['originalIndependentAudit']]
                else:
                    assert manifest.get('packetSHA256') == receipt['candidatePacketSHA256'], 'Supplement manifest binds wrong packet'
                    assert isinstance(manifest.get('files'), list), 'Supplement manifest needs explicit path/hash records'
                    entries = manifest['files']
                for entry in entries:
                    add_supplement(entry, resource.parent)

    add(base / 'packet.json', sha(base / 'packet.json'))
    accepted = acceptance(folder, args.round, packet)
    review = accepted['path']
    verdict = accepted['receipt']
    acceptance_hash_key = 'validationSHA256' if accepted['method'] == 'recipe-reuse' else 'reviewSHA256'
    add_review(review, verdict)
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
        old_recipe = old.get('qualityCriteria', {}).get('method') == 'established-native-family-recipe'
        old_review = folder / ('validations' if old_recipe else 'reviews') / f'{old_path.parent.name}.json'
        if old_review.exists():
            old_receipt = json.loads(old_review.read_text())
            assert old_receipt['candidatePacketSHA256'] == sha(old_path), 'Prior review binding changed'
            add_review(old_review, old_receipt)
    promotion = folder / 'final/promotion.json'
    if promotion.exists():
        promoted = json.loads(promotion.read_text())
        assert promoted['round'] == args.round, 'Promotion and selected round differ'
        assert promoted['candidatePacketSHA256'] == sha(base / 'packet.json'), 'Promotion packet changed'
        assert promoted[acceptance_hash_key] == sha(review), 'Promotion approval changed'
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
    runtime_variant = folder / 'final/runtime-variant-approval.json'
    if runtime_variant.exists():
        saved = json.loads(runtime_variant.read_text())
        assert saved['candidatePacketSHA256'] == sha(base / 'packet.json'), 'Runtime variant packet changed'
        assert saved['reviewSHA256'] == sha(review), 'Runtime variant approval changed'
        add(runtime_variant, sha(runtime_variant))
        file_base = saved.get('filesRelativeTo', 'receipt-directory')
        assert file_base in ['receipt-directory', 'object'], 'Unknown runtime variant file base'
        source_base = folder if file_base == 'object' else runtime_variant.parent
        for path, digest in saved['files'].items():
            add(source_base / path, digest)
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
