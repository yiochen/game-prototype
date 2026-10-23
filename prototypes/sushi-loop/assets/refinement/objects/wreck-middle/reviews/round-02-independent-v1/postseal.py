"""Verify the acyclic exact-packet approval handoff without changing it."""
from pathlib import Path
import json,hashlib
OUT=Path(__file__).resolve().parent;OBJ=OUT.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=OBJ/'reviews/round-02.json';manifest=OUT/'supplemental-manifest.json';gate=OUT/'acceptance-gate.log';seal=OUT/'seal.json'
d=json.loads(review.read_text());m=json.loads(manifest.read_text());g=json.loads(gate.read_text());s=json.loads(seal.read_text())
assert d['verdict']=='approve' and d['blockers']==[]
assert d['supplementalEvidence']['sha256']==sha(manifest)==s['manifestSHA256']
assert sha(review)==s['reviewSHA256']==g['sha256']
assert sha(gate)==s['gateSHA256'] and g['method']=='independent-review'
assert d['candidatePacketSHA256']==m['candidatePacketSHA256']==sha(OBJ/'candidates/round-02/packet.json')
for r in m['files']:
    p=(OBJ/r['path']).resolve();assert p.is_relative_to(OBJ) and p.is_file() and sha(p)==r['sha256']
    assert p not in [review,manifest,gate,seal]
packet=json.loads((OBJ/'candidates/round-02/packet.json').read_text())
expected={r['path'] for group in ['candidateRenders','previews'] for r in packet[group].values()}
assert expected<=set(d['inspectedFiles']) and len(expected)==18
print(json.dumps({'status':'verified-acyclic-approve-handoff','candidatePacketSHA256':d['candidatePacketSHA256'],'reviewSHA256':sha(review),'manifestSHA256':sha(manifest),'sealSHA256':sha(seal),'unchangedAcceptanceGatePassed':True,'exactVisualCoverage':len(expected),'scope':'Exact wreck-middle round02 only; no family/production approval'}))
