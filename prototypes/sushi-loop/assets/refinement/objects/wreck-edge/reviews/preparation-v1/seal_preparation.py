from pathlib import Path
import hashlib,json,datetime
PREP=Path(__file__).resolve().parent;REV=PREP.parent;OBJECT=REV.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[REV/'initial.json',REV/'proposedcriteria.json',REV/'source-contract-proposal.json']+[p for p in PREP.rglob('*') if p.is_file() and p.name not in ['manifest.json','seal.json']]
paths=sorted(set(paths));assert not any(p.suffix=='.pyc' or '__pycache__' in p.parts for p in paths)
assert all(p.stat().st_size<100_000_000 for p in paths)
manifest={'schema':'wreck-edge-preparation-manifest-v1','asset':'wreck-edge','pathBase':'object-root','scope':'Preparation only; no candidate/family/production approval. Root reconciliation/freeze and fresh editor pending.','files':[{'path':str(p.relative_to(OBJECT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths]}
mf=PREP/'manifest.json';mf.write_text(json.dumps(manifest,indent=2)+'\n')
seal={'schema':'wreck-edge-preparation-seal-v1','asset':'wreck-edge','pathBase':'object-root','manifest':{'path':str(mf.relative_to(OBJECT)),'sha256':sha(mf)},'fileCount':len(paths),'totalBytes':sum(p.stat().st_size for p in paths),'candidateApproval':False,'sourceSHA256':sha(PREP/'resources/native/source-library.blend'),'canonicalSourceSHA256':sha(PREP/'resources/native/canonical-middle02.blend'),'canonicalPacketSHA256':sha(PREP/'resources/canonical/packet.json'),'canonicalReviewSHA256':sha(PREP/'resources/canonical/review.json'),'status':'STOP for root reconciliation/freeze; dispatch a fresh editor only after freeze.','createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(PREP/'seal.json').write_text(json.dumps(seal,indent=2)+'\n')
for e in manifest['files']:
 p=OBJECT/e['path'];assert sha(p)==e['sha256']
print(json.dumps(seal,indent=2))
