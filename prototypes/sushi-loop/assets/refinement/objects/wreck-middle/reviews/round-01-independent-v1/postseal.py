"""Read-only postseal verification of a truthful revise receipt; no approval."""
from pathlib import Path
import hashlib,json
OUT=Path(__file__).resolve().parent; OBJ=OUT.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=OBJ/'reviews/round-01.json';manifest=OUT/'supplemental-manifest.json';gate=OUT/'acceptance-gate.log';seal=OUT/'seal.json'
d=json.loads(review.read_text());m=json.loads(manifest.read_text());s=json.loads(seal.read_text())
assert d['verdict']=='revise' and len(d['blockers'])==1
assert d['supplementalEvidence']['sha256']==sha(manifest)==s['manifestSHA256']
assert sha(review)==s['reviewSHA256'] and sha(gate)==s['gateSHA256']
assert 'Acceptance binds wrong or blocked candidate' in gate.read_text()
assert d['candidatePacketSHA256']==m['candidatePacketSHA256']==sha(OBJ/'candidates/round-01/packet.json')
for f in m['files']:
    p=(OBJ/f['path']).resolve();assert p.is_relative_to(OBJ) and p.is_file() and sha(p)==f['sha256']
    assert p not in [review,manifest,gate,seal]
packet=json.loads((OBJ/'candidates/round-01/packet.json').read_text())
assert {r['path'] for group in ['candidateRenders','previews'] for r in packet[group].values()}<=set(d['inspectedFiles'])
print(json.dumps({'status':'verified-acyclic-revise-handoff','candidatePacketSHA256':d['candidatePacketSHA256'],'reviewSHA256':sha(review),'manifestSHA256':sha(manifest),'gateExpectedRejected':True,'supplementalFiles':len(m['files']),'exactDeclaredVisualCoverage':len(d['inspectedFiles'])}))
