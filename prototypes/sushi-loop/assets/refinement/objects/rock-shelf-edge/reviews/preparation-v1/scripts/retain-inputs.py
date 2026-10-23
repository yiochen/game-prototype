from pathlib import Path
import json,hashlib,shutil,sys
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent
items=json.loads((BASE/'input-manifest.json').read_text())
for item in items:
 p=Path(item['source']);q=BASE/'resources'/item['path']
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 assert digest==item['sha256'],str(p)
 q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 assert hashlib.sha256(q.read_bytes()).hexdigest()==digest
print(json.dumps({'retainedInputs':len(items),'bytes':sum(i['bytes'] for i in items),'exactHashVerified':True},indent=2))
