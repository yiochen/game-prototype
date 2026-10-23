import json,hashlib,time
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'candidates/round-01/packet.json'
OUT=Path(__file__).resolve().parent
p=json.loads(PACKET.read_text());cache={};failed=[];counts={};start=time.time()
for section in ('files','candidateRenders','previews'):
    entries=p[section];counts[section]=len(entries)
    for key,record in entries.items():
        path=(PACKET.parent/record['path']).resolve()
        if path not in cache:
            cache[path]=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if cache[path]!=record['sha256']: failed.append({'section':section,'key':key,'path':str(path),'expected':record['sha256'],'actual':cache[path]})
report={'packetSHA256':hashlib.sha256(PACKET.read_bytes()).hexdigest(),'counts':counts,'uniqueFilesHashed':len(cache),'elapsedSeconds':time.time()-start,'failures':failed,'criteriaSHA256':hashlib.sha256((ROOT/'reviews/criteria.json').read_bytes()).hexdigest()}
(OUT/'packet-hash-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
