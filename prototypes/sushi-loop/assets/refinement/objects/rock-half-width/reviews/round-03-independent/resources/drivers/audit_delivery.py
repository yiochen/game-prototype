from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).resolve().parents[2];obj=B.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=obj/'delivery/round-03.json';alias=obj/'delivery-round-03.json';assert p.read_bytes()==alias.read_bytes();x=json.loads(p.read_text());rows=[]
for r in x['resources']:
 q=obj/r['path'];h=sha(q);assert h==r['sha256'];rows.append({'path':r['path'],'sha256':h,'bytes':q.stat().st_size})
dst=B/'resources/delivery-round-03.json'
if not dst.exists():shutil.copy2(p,dst)
else:assert dst.read_bytes()==p.read_bytes()
for n in ['attempts.json','first-browser-attempt.log']:
 q=obj/'candidates/round-03/diagnostics'/n;d=B/'resources/candidate-records'/n
 if not d.exists():shutil.copy2(q,d)
 else:assert q.read_bytes()==d.read_bytes()
for name in ['round-comparison-record.json','geometry-field-derivative-proof.json']:
 q=obj/'candidates/round-03'/name
 if q.exists():
  d=B/'resources/candidate-records'/name
  if not d.exists():shutil.copy2(q,d)
  else:assert q.read_bytes()==d.read_bytes()
logs=[r for r in rows if 'consumer' in r['path'] and ('log' in r['path'] or 'crash' in r['path'])]
(B/'evidence/delivery-verification.json').write_text(json.dumps({'deliverySHA256':sha(p),'aliasByteIdentical':True,'resourceHashesVerified':rows,'count':len(rows),'retainedBrowserLogs':logs,'sourceSHA256':sha(obj/'source/round-03.blend')},indent=2)+'\n');print(len(rows),'explicit resources verified')
