import json,hashlib,concurrent.futures,time
from pathlib import Path
b=Path(__file__).resolve().parent.parent/'candidates/round-01'; p=json.loads((b/'packet.json').read_text())
unique={};conflicts=[]
for cat in ['files','candidateRenders','previews']:
 for name,v in p[cat].items():
  path=(b/v['path']).resolve()
  if path in unique and unique[path]!=v['sha256']:conflicts.append(str(path))
  unique[path]=v['sha256']
def one(kv):
 path,expected=kv
 try:
  h=hashlib.sha256()
  with path.open('rb') as f:
   for block in iter(lambda:f.read(1048576),b''):h.update(block)
  return None if h.hexdigest()==expected else {'path':str(path),'actual':h.hexdigest(),'expected':expected}
 except Exception as e:return {'path':str(path),'error':str(e)}
t=time.time()
with concurrent.futures.ThreadPoolExecutor(8) as pool:errors=[r for r in pool.map(one,unique.items()) if r]
out={'packetSHA256':hashlib.sha256((b/'packet.json').read_bytes()).hexdigest(),'uniqueFilesChecked':len(unique),'conflicts':conflicts,'errors':errors,'allBoundFilesMatch':not conflicts and not errors,'seconds':time.time()-t}
(Path(__file__).parent/'round-01-packet-check.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
