import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P.parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
seal=json.loads((P/'seal.json').read_text())
for name in ['review','manifest']:
 d=seal[name];p=O/d['path'];assert sha(p)==d['sha256'],p
review=json.loads((O/seal['review']['path']).read_text());manifest=json.loads((O/seal['manifest']['path']).read_text());packet=O/'candidates/round-01/packet.json';assert sha(packet)==review['candidatePacketSHA256']==manifest['candidatePacketSHA256']
for d in manifest['files']:
 p=Path(d['pathBase'])/d['path'];assert p.is_file(),p;assert p.stat().st_size==d['bytes']<100_000_000,p;assert sha(p)==d['sha256'],p
p=json.loads(packet.read_text());declared={r['path'] for k in ['candidateRenders','previews'] for r in p[k].values()};assert set(review['inspectedFiles'])==declared
assert review['verdict']=='needs_evidence' and review['allChecksPassed'] is False
assert not list(P.rglob('__pycache__'))
print(json.dumps({'status':'exact review/packet/coverage/closure verified; not approval','mediaPaths':len(declared),'manifestFiles':len(manifest['files']),'reviewSHA256':sha(O/seal['review']['path']),'manifestSHA256':sha(O/seal['manifest']['path'])},indent=2))
