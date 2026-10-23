import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
seal=json.loads((P/'preparation-seal.json').read_text());m=seal['manifest'];base=Path(m['pathBase']);mp=base/m['path'];assert sha(mp)==m['sha256'],'Manifest hash mismatch'
manifest=json.loads(mp.read_text());seen=set()
for item in manifest['files']:
 assert item['relativeTo']=='object'
 p=Path(item['pathBase'])/item['path'];assert p.is_file(),str(p);assert p.stat().st_size<100_000_000,str(p);assert p.stat().st_size==item['bytes'],str(p);assert sha(p)==item['sha256'],str(p);seen.add(str(p.resolve()))
for item in seal['proposals']:
 p=Path(item['pathBase'])/item['path'];assert sha(p)==item['sha256'],str(p)
assert all(str((Path(i['pathBase'])/i['path']).resolve()) in seen for i in manifest['resources'])
assert not list(P.rglob('__pycache__')),'Bytecode directory found'
print(json.dumps({'status':'exact-byte-closure-verified; no visual approval','files':len(manifest['files']),'resources':len(manifest['resources']),'manifestSHA256':sha(mp)},indent=2))
