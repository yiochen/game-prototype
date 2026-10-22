import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
seal=json.loads((P/'seal.json').read_text());d=seal['manifest'];mp=Path(d['pathBase'])/d['path'];assert sha(mp)==d['sha256'];manifest=json.loads(mp.read_text())
for d in manifest['files']:
 p=Path(d['pathBase'])/d['path'];assert p.is_file(),p;assert p.stat().st_size==d['bytes']<100_000_000,p;assert sha(p)==d['sha256'],p
old=manifest['priorPreparation']['manifest'];p=Path(old['pathBase'])/old['path'];assert sha(p)==old['sha256'];prior=json.loads(p.read_text())
for d in prior['files']:
 p=Path(d['pathBase'])/d['path'];assert sha(p)==d['sha256'],p
assert not list(P.rglob('__pycache__'))
print(json.dumps({'status':'exact study closure and old preparation immutability verified; no candidate approval','files':len(manifest['files']),'manifestSHA256':sha(mp)},indent=2))
