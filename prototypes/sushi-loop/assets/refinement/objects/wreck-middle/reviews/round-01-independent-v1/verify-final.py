"""Verify final unchanged-gate run after the exact receipt bytes were sealed."""
from pathlib import Path
import hashlib,json
OUT=Path(__file__).resolve().parent;OBJ=OUT.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((OUT/'post-gate-seal-v2.json').read_text())
for name,r in s['files'].items():assert sha(OBJ/r['path'])==r['sha256'],name
review=json.loads((OBJ/'reviews/round-01.json').read_text());manifest=json.loads((OUT/'supplemental-manifest.json').read_text())
assert review['verdict']=='revise' and len(review['blockers'])==1
assert review['supplementalEvidence']['sha256']==sha(OUT/'supplemental-manifest.json')
assert 'Acceptance binds wrong or blocked candidate' in (OUT/'acceptance-gate-final.log').read_text()
for f in manifest['files']:assert sha(OBJ/f['path'])==f['sha256']
print(json.dumps({'status':'verified-final-acyclic-revise','candidatePacketSHA256':review['candidatePacketSHA256'],'reviewSHA256':sha(OBJ/'reviews/round-01.json'),'finalPostGateSealSHA256':sha(OUT/'post-gate-seal-v2.json'),'gateExpectedRejected':True}))
