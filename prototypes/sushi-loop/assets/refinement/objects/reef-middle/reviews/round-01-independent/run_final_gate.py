"""Run the unchanged acceptance gate once against the sealed independent verdict."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
OBJ = HERE.parent.parent
REPO = OBJ.parents[5]
REVIEW = OBJ / 'reviews/round-01.json'
MANIFEST = HERE / 'manifest.json'
TOOL = REPO / 'prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py'
PYTHON = Path('/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3')
EXPECTED_REVIEW = 'c49d0c1260d34933b7633ed109f293fe0bbcba943ec5b84bdd158e6524505929'
EXPECTED_MANIFEST = '33ed13382b8852f85488901ffb4967fe3a78887e658e598a7786e73a21dbc68e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def descriptor(path):
    return {'path': os.path.relpath(path, OBJ), 'relativeTo': 'experiment',
            'sha256': sha(path), 'bytes': path.stat().st_size}


def save(path, value):
    assert not path.exists(), str(path)
    path.write_text(json.dumps(value, indent=2) + '\n')


assert sha(REVIEW) == EXPECTED_REVIEW
assert sha(MANIFEST) == EXPECTED_MANIFEST
manifest = json.loads(MANIFEST.read_text())
for record in manifest['files']:
    resource = (OBJ / record['path']).resolve()
    assert sha(resource) == record['sha256'], str(resource)
    assert resource.stat().st_size < 100_000_000, str(resource)
receipt = json.loads(REVIEW.read_text())
assert receipt['verdict'] == 'revise' and len(receipt['blockers']) == 1
assert sha(TOOL) == sha(HERE / 'resources/tools/acceptance_contract.py')
command = [str(PYTHON), str(TOOL.relative_to(REPO)), 'reef-middle', '--round', 'round-01']
environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
result = subprocess.run(command, cwd=REPO, env=environment,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
log = HERE / 'final-gate.log'
assert not log.exists()
log.write_bytes(result.stdout)
assert result.returncode == 1, result.returncode
assert b'Acceptance binds wrong or blocked candidate' in result.stdout
assert sha(REVIEW) == EXPECTED_REVIEW
assert sha(MANIFEST) == EXPECTED_MANIFEST
status = HERE / 'final-gate.json'
save(status, {
    'asset': 'reef-middle', 'round': 'round-01', 'cwd': str(REPO),
    'commandArgv': command, 'environmentOverrides': {'PYTHONDONTWRITEBYTECODE': '1'},
    'tool': descriptor(TOOL), 'reviewSHA256Before': EXPECTED_REVIEW,
    'reviewSHA256After': sha(REVIEW), 'supplementalManifestSHA256': sha(MANIFEST),
    'exitStatus': result.returncode, 'stdoutAndStderr': descriptor(log),
    'expectedResult': 'Rejected because the independent revise verdict has one visible blocker; no approval.',
})
seal = HERE / 'postreview-seal.json'
save(seal, {
    'asset': 'reef-middle', 'round': 'round-01', 'verdict': 'revise',
    'blockerCount': 1, 'candidatePacketSHA256': receipt['candidatePacketSHA256'],
    'sourceSHA256': receipt['sourceSHA256'], 'review': descriptor(REVIEW),
    'supplementalEvidence': descriptor(MANIFEST), 'finalGateLog': descriptor(log),
    'finalGateStatus': descriptor(status), 'unchangedAcceptanceTool': descriptor(TOOL),
    'gateRunner': descriptor(Path(__file__).resolve()),
    'supplementalManifestFilesVerified': len(manifest['files']),
    'scope': 'Exact reef-middle round-01 only; revise, no derivative-family or production approval.',
    'sealPolicy': 'Separate final seal avoids review/manifest self-hash cycles. Review and manifest unchanged after gate.',
})
assert sha(REVIEW) == EXPECTED_REVIEW
assert sha(MANIFEST) == EXPECTED_MANIFEST
print(json.dumps({'review': descriptor(REVIEW), 'manifest': descriptor(MANIFEST),
                  'seal': descriptor(seal), 'gateStatus': result.returncode}, indent=2))
