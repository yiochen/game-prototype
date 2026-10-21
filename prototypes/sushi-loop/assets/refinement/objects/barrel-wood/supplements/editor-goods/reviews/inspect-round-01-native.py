import bpy
import hashlib
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
B = R.parent
sys.path.insert(0, str(B / 'source'))
from native_state import state, camera_record

label = sys.argv[sys.argv.index('--') + 1]
result = {'sourcePath': bpy.data.filepath,
          'sourceSHA256': hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
          'nativeState': state(), 'camera': camera_record(), 'inspectionOnly': True}
(R / 'round-01-inspection' / ('source-' + label + '-native.json')).write_text(json.dumps(result, indent=2) + '\n')
print('JUDGE_NATIVE_STATE', label, result['sourceSHA256'], json.dumps(result['nativeState']['sectionHashes']))
