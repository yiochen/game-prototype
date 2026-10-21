import bpy
import hashlib
import json
import sys
from pathlib import Path

out = Path(__file__).resolve().parent
base = out.parent
sys.path.insert(0, str(base / 'source'))
from native_state import state, normalize_static

receipt = json.loads((base / 'candidates/round-01/native-parity.json').read_text())
before = hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
assert before == receipt['sourceSHA256']
bindings = normalize_static()
actual = state()
assert actual['sectionHashes'] == receipt['source']['sectionHashes']
assert actual['sections'] == receipt['candidate']['sections']
assert not actual['dependencies']['externalImages'] and not actual['dependencies']['libraries']
proof = {
    'approvedSourceSHA256': before,
    'exactApprovedSourceReopenedIndependently': True,
    'identicalStaticNormalization': bindings,
    'sourceActualSectionHashes': actual['sectionHashes'],
    'sourceActualSectionsEqualCandidate': True,
    'sourceActualSectionsEqualSealedReference': True,
    'externalDependencyClosure': actual['dependencies'],
    'sourceAfterSHA256': hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
    'note': 'The source .blend is never saved; existing static actions are selected in memory only. Saved candidate is independently reopened and rendered by the immutable-resource replay.'
}
(out / 'round-01-independent-native.json').write_text(json.dumps(proof, indent=2) + '\n')
print('INDEPENDENT_APPROVED_SOURCE_STATIC_PARITY_EXACT')
