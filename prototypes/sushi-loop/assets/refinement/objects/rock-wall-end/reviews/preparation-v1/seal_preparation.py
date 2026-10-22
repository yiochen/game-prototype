"""Seal only this judge's preparation files; verify local snapshot closure.
The live catalog/library/consumer paths deliberately are not consulted.
"""
from pathlib import Path
import json,hashlib,shutil,datetime
OUT=Path(__file__).resolve().parent;REVIEWS=OUT.parent;EXP=REVIEWS.parent;RES=OUT/'resources'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Transient Python caches are not source dependencies.
for p in OUT.rglob('__pycache__'):
 if p.is_dir():shutil.rmtree(p)
for m in list(RES.glob('resource-manifest-*.json'))+[RES/'runtime/library-snapshot-manifest.json']:
 for r in json.loads(m.read_text())['resources']:
  p=EXP/r['snapshot'] if r['snapshot'].startswith('reviews/') else RES/r['snapshot']
  assert p.is_file(),str(p)
  assert sha(p)==r['sha256'],str(p)
# Verify every canonical reference byte against its immutable manifest.
family=RES/'approved-middle';reference=json.loads((family/'reference-manifest.json').read_text())
for name,r in reference['files'].items():assert sha(family/name)==r['sha256'],name
native=json.loads((OUT/'canonical-replay-comparison.json').read_text())
assert all(r['exactCanonicalNativeRGBAReplay'] and r['exactBOXPublishedRGBA'] for r in native.values())
consumer=json.loads((OUT/'consumer-fixture-evidence.json').read_text())
assert consumer['caseCount']==288
assert all(c['result']['smoothingAfterResize'] is False for c in consumer['cases'])
files=[]
exclude={'preparation-manifest.json','preparation-seal.json'}
for p in sorted(REVIEWS.rglob('*')):
 if p.is_file() and p.name not in exclude:
  assert p.stat().st_size<100_000_000,str(p)
  files.append({'path':str(p.relative_to(REVIEWS)),'bytes':p.stat().st_size,'sha256':sha(p)})
manifest={'asset':'rock-wall-end','stage':'independent preparation only','candidateApproval':False,'closure':'All used task inputs, exact consumer/Playwright code, source model/library and skills are local immutable snapshots. External installed Blender/Python/Node/Chromium runtimes are version/hash pinned. No later mutation of global catalog/library/code invalidates this closure.','files':files}
mp=OUT/'preparation-manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
seal={'asset':'rock-wall-end','stage':'preparation sealed; ready for coordinator freeze','candidateApproval':False,'manifest':'preparation-manifest.json','manifestSHA256':sha(mp),'fileCount':len(files),'totalBytes':sum(f['bytes'] for f in files),'largestFileBytes':max(f['bytes'] for f in files),'criteriaSHA256':sha(REVIEWS/'proposedcriteria.json'),'contractSHA256':sha(REVIEWS/'source-contract-proposal.json'),'initialSHA256':sha(REVIEWS/'initial.json'),'checks':{'localResourceManifests':True,'approvedMiddleReferenceManifest':True,'canonicalNativeRGBAAll4':True,'canonicalBOXPublicationAll4':True,'consumer288NearestAfterResize':True,'everyFileUnder100MB':True},'remaining':'Root freezes criteria and source contract; fresh editor and later exact-candidate independent review remain pending.'}
(OUT/'preparation-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps(seal,indent=2))
