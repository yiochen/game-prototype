from pathlib import Path
import hashlib, json

B = Path(__file__).resolve().parents[1]
D = B / 'delivery/round-05'
D.mkdir(parents=True, exist_ok=True)

def record(p):
    return {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}

prior = B / 'delivery/round-04/handoff-manifest.json'
old = json.loads(prior.read_text())
changed = [name for name, expected in old['files'].items()
           if not (B/name).is_file() or record(B/name) != expected]
assert not changed, changed
(B/'source/round-05-resources/round-04-preservation-check.json').write_text(json.dumps({
    'priorHandoffManifest': 'delivery/round-04/handoff-manifest.json',
    'sha256': record(prior)['sha256'], 'fileCount': len(old['files']),
    'changedOrMissing': changed
}, indent=2)+'\n')

inputs = {}
for directory in ['source/resources', 'source/round-04-resources', 'source/round-05-resources']:
    for p in sorted((B/directory).rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            inputs[p.relative_to(B).as_posix()] = record(p)

(D/'resource-closure.json').write_text(json.dumps({
    'sourceProject': 'source/round-05.blend',
    'nativeSavedExternalImages': [], 'nativeSavedLinkedLibraries': [],
    'reproductionInputs': inputs,
    'runtime': 'See source/resources/runtime-versions.json. Immutable consumer, skill, native middle, original, target, contract and signed review snapshots are retained. All executable round05 scripts and retained prior projects are separately bound by the handoff manifest. Native geometry uses no target image material.'
}, indent=2)+'\n')
