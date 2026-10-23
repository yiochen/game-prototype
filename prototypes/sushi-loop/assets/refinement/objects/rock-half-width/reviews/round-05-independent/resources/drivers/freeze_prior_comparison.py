from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).resolve().parents[2];obj=B.parents[1];rows=[]
paths=[f'candidates/{r}/frames/static/{d}/000.png' for r in ['round-03','round-04'] for d in 'NESW']+['candidates/round-04/joins/native-S-published.png','candidates/round-03/packet.json','candidates/round-04/packet.json']
for n in paths:
 p=obj/n;d=B/'resources/comparison-inputs'/n;d.parent.mkdir(parents=True,exist_ok=True)
 if not d.exists():shutil.copy2(p,d)
 else:assert d.read_bytes()==p.read_bytes()
 rows.append({'originalPath':n,'frozenPath':str(d.relative_to(obj)),'sha256':hashlib.sha256(d.read_bytes()).hexdigest()})
(B/'evidence/frozen-prior-comparison.json').write_text(json.dumps({'files':rows,'scope':'Only prior-round pixels/packets actually used for current matched comparison and integer-restoration audit. Current candidate pixels remain bound by the current packet.'},indent=2)+'\n')
