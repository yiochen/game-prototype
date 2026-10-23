from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=OBJ/'reviews/round-01.json';r=json.loads(review.read_text());assert r['verdict']=='needs_evidence' and len(r['blockers'])==1
supp=OBJ/r['supplementalEvidence']['path'];assert sha(supp)==r['supplementalEvidence']['sha256']
for name in ['supplemental-manifest.json','supplemental-manifest-v2.json']:
 m=json.loads((HERE/name).read_text());assert m['candidatePacketSHA256']==r['candidatePacketSHA256']
 for f in m['files']:assert sha(OBJ/f['path'])==f['sha256'],f['path']
assert 'missing measured root rotation evidence' in (HERE/'direction-audit-preliminary.log').read_text()
assert 'Acceptance binds wrong or blocked candidate' in (HERE/'acceptance-gate.log').read_text()
packet=OBJ/'candidates/round-01/packet.json';assert sha(packet)==r['candidatePacketSHA256']
paths=sorted([review]+[p for p in HERE.rglob('*') if p.is_file() and p.name!='postseal.json']);assert not any(p.suffix=='.pyc' for p in paths);assert all(p.stat().st_size<100_000_000 for p in paths)
out={'candidatePacketSHA256':sha(packet),'pathBase':'object-root','finalReview':{'path':str(review.relative_to(OBJ)),'sha256':sha(review),'verdict':'needs_evidence'},'status':'Stopped: unchanged direction gate rejected compatible capture-ledger discovery. Visual/native inspection passed; no final approval.','files':[{'path':str(p.relative_to(OBJ)),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths],'hashGraph':'Acyclic: original supplement -> source/evidence; preliminary receipt -> original supplement; v2 supplement -> immutable preliminary history; final needs_evidence receipt -> v2 supplement; gate logs -> receipt hash/blocked result; this postseal -> all preceding bytes, never itself.'}
(HERE/'postseal.json').write_text(json.dumps(out,indent=2)+'\n')
for p in paths+[HERE/'postseal.json']:p.chmod(p.stat().st_mode&~0o222)
print(json.dumps({'verdict':r['verdict'],'reviewSHA256':sha(review),'postsealSHA256':sha(HERE/'postseal.json'),'fileCount':len(paths)},indent=2))
