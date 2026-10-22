import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P.parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
seal=read(P/'seal.json')
for name in ['review','manifest','acceptanceOutput']:
 d=seal[name];p=Path(d['pathBase'])/d['path'];assert sha(p)==d['sha256'] and p.stat().st_size==d['bytes'],p
review=read(O/'reviews/round-02.json');manifest=read(P/'manifest.json');packet=O/'candidates/round-02/packet.json'
assert sha(packet)==review['candidatePacketSHA256']==manifest['candidatePacketSHA256']
assert review['supplementalEvidence']['sha256']==sha(P/'manifest.json')
for d in manifest['files']:
 p=Path(d['pathBase'])/d['path'];assert p.is_file() and p.stat().st_size==d['bytes']<100_000_000,p;assert sha(p)==d['sha256'],p
p=read(packet);declared={r['path'] for g in ['candidateRenders','previews'] for r in p[g].values()};assert len(declared)==39;assert set(review['inspectedFiles'])==declared
assert review['verdict']=='approve' and review['allChecksPassed'] is True and review['blockers']==[]
accept=read(P/'acceptance-tool-output.json');assert accept['sha256']==sha(O/'reviews/round-02.json');assert accept['method']=='independent-review' and accept['asset']=='floor-underwater'
assert not list(P.rglob('__pycache__'))
print(json.dumps({'status':'exact approved review/packet/39-path coverage/manifest/seal/final acceptance verified','manifestFiles':len(manifest['files']),'maximumFileBytes':max(d['bytes'] for d in manifest['files']),'reviewSHA256':sha(O/'reviews/round-02.json'),'manifestSHA256':sha(P/'manifest.json'),'sealSHA256':sha(P/'seal.json')},indent=2))
