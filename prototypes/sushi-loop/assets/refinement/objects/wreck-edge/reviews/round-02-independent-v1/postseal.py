from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
receipt=OBJ/'reviews/round-02.json';review=read(receipt);assert review['verdict']=='approve' and review['blockers']==[]
packet=OBJ/'candidates/round-02/packet.json';assert sha(packet)==review['candidatePacketSHA256']=='7fe4e36723fe87bea1a94d12f9b85e62b4cafffcc0e34b814b3298e8866aaae1'
supp=OBJ/review['supplementalEvidence']['path'];assert sha(supp)==review['supplementalEvidence']['sha256']
for f in read(supp)['files']:assert sha(OBJ/f['path'])==f['sha256']
assert read(HERE/'direction-audit.log')['status']=='passed'
assert read(HERE/'acceptance-gate.log')['sha256']==sha(receipt)
assert 'Artifact integrity verified; exact independent approval binding verified.' in (HERE/'integrity-gate.log').read_text()
skill=Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py');assert sha(skill)==sha(HERE/'resources/candidate_packet.py')
files=sorted([receipt]+[p for p in HERE.rglob('*') if p.is_file() and p.name!='postseal.json']);assert not any(p.suffix=='.pyc' or '__pycache__' in p.parts for p in files);assert all(p.stat().st_size<100_000_000 for p in files)
post={'candidatePacketSHA256':sha(packet),'pathBase':'object-root','review':{'path':str(receipt.relative_to(OBJ)),'sha256':sha(receipt),'verdict':'approve'},'status':'Exact evidence-only round02 approved after unchanged integrity, direction and acceptance gates passed. No production/family/publish approval.','files':[{'path':str(p.relative_to(OBJ)),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'hashGraph':'Acyclic: same-art prior native/visual manifests and measured ledger -> new audit; supplemental manifest -> frozen evidence; review -> supplement; gate logs -> exact review/packet; this postseal -> prior bytes and never itself.'}
(HERE/'postseal.json').write_text(json.dumps(post,indent=2)+'\n')
for p in files+[HERE/'postseal.json']:p.chmod(p.stat().st_mode&~0o222)
print(json.dumps({'reviewSHA256':sha(receipt),'supplementSHA256':sha(supp),'postsealSHA256':sha(HERE/'postseal.json'),'files':len(files),'verdict':'approve'},indent=2))
