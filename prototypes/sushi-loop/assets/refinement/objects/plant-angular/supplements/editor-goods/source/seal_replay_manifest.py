"""Freeze explicit replay inputs, excluding caches, root delivery and volatile logs."""
from pathlib import Path
import json,hashlib
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'candidates/round-01'
DEST=OUT/'replay-manifest-v1.json';assert not DEST.exists()
paths=[BASE/'source'/n for n in ['round-01.blend','native_state.py','build_goods.py','reopen_goods.py',
 'prepare_consumer.py','consumer-bench.gd','portable_verify.py','package_goods.py','seal_replay_manifest.py']]
paths += [BASE/'inputs'/n for n in ['approved-world-model.blend','original.png','target.png','camera-contract.json']]
paths += [BASE/'brief.json',BASE/'reviews/criteria.json',OUT/'goods.png',OUT/'native-parity.json']
paths += [p for p in (BASE/'source/resources/current-consumer').rglob('*') if p.is_file()]
paths += [p for p in (OUT/'consumer').iterdir() if p.is_file()]
records=[{'path':str(p.relative_to(BASE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]
assert not any(Path(r['path']).suffix in ['.log','.pyc','.import'] for r in records)
DEST.write_text(json.dumps({'schemaVersion':1,'asset':'plant-angular','round':'round-01','resources':records,
 'rules':'Immutable round-specific input manifest. No root delivery or volatile logs are recipe dependencies.'},indent=2)+'\n')
print(json.dumps({'manifest':str(DEST),'resources':len(records)}))
