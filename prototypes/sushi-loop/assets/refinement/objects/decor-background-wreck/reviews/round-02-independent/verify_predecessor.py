from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;O=P.parent.parent;prev=O/'candidates/round-01/packet.json';pack=json.loads(prev.read_text());records=[]
for group in ['files','candidateRenders','previews']:
 for name,x in pack[group].items():
  f=prev.parent/x['path'];sha=hashlib.sha256(f.read_bytes()).hexdigest();records.append({'group':group,'name':name,'path':x['path'],'sha256':sha,'unchanged':sha==x['sha256']})
review=O/'reviews/round-01.json';report={'asset':'decor-background-wreck','currentRound':'round-02','priorPacketSHA256':hashlib.sha256(prev.read_bytes()).hexdigest(),'expectedPriorPacketSHA256':'f9524d3dffbb1bf59c29cfa9d634e2e438ed46f40731651e322a8081844a254c','priorReviewSHA256':hashlib.sha256(review.read_bytes()).hexdigest(),'expectedPriorReviewSHA256':'9382b2a20f8cafa9eaa4b0a8646a58bcd0616e97a636e7d184d20cfc523326fc','checkedRecords':len(records),'allPriorPacketRecordsUnchanged':all(x['unchanged'] for x in records),'records':records};(P/'predecessor-integrity.json').write_text(json.dumps(report,indent=2)+'\n');print(report['allPriorPacketRecordsUnchanged'])
