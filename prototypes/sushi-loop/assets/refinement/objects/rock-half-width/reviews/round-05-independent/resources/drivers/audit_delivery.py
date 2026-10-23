from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).resolve().parents[2];obj=B.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=obj/'delivery/round-05.json';alias=obj/'delivery-round-05.json';assert p.read_bytes()==alias.read_bytes();x=json.loads(p.read_text());rows=[]
for r in x['resources']:
 q=obj/r['path'];h=sha(q);assert h==r['sha256'];rows.append({'path':r['path'],'sha256':h,'bytes':q.stat().st_size})
dst=B/'resources/delivery-round-05.json'
if not dst.exists():shutil.copy2(p,dst)
else:assert dst.read_bytes()==p.read_bytes()
for name in ['round-comparison-record.json','geometry-field-derivative-proof.json']:
 q=obj/'candidates/round-05'/name
 if q.exists():
  d=B/'resources/candidate-records'/name
  if not d.exists():shutil.copy2(q,d)
  else:assert q.read_bytes()==d.read_bytes()
used_path=obj/'candidates/round-05/used-resources.json';used=json.loads(used_path.read_text());used_rows=[]
for r in used['files']:
 q=obj/r['path'];assert sha(q)==r['sha256'];used_rows.append({'path':r['path'],'sha256':sha(q),'bytes':q.stat().st_size})
d=B/'resources/candidate-records/used-resources.json'
if not d.exists():shutil.copy2(used_path,d)
else:assert d.read_bytes()==used_path.read_bytes()
logs=[r for r in rows if 'consumer' in r['path'] and ('log' in r['path'] or 'crash' in r['path'])]
(B/'evidence/delivery-verification.json').write_text(json.dumps({'deliverySHA256':sha(p),'aliasByteIdentical':True,'resourceHashesVerified':rows,'count':len(rows),'usedResourceHashesVerified':used_rows,'usedResourceCount':len(used_rows),'usedResourceManifestSHA256':sha(used_path),'retainedBrowserLogs':logs,'sourceSHA256':sha(obj/'source/round-05.blend')},indent=2)+'\n');print(len(rows),'explicit resources verified')
