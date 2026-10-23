"""Prove sameness of reused technical evidence against independently read round02."""
from pathlib import Path
import json,hashlib
OUT=Path(__file__).resolve().parent;OBJ=OUT.parent.parent
old=json.loads((OBJ/'reviews/round-01-independent-v1/native-inspection.json').read_text())
new=json.loads((OUT/'native-inspection.json').read_text())
digest=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
report={'candidatePacketSHA256':hashlib.sha256((OBJ/'candidates/round-02/packet.json').read_bytes()).hexdigest(),'comparisons':{}}
for k in ['materials','canonicalCollars','caps','support','lights','world','bounds','actions','armatures','images']:
    report['comparisons'][k]={'equal':old[k]==new[k],'round01ContentSHA256':digest(old[k]),'round02ContentSHA256':digest(new[k])}
report['captureSettingsEqual']=[]
for a,b in zip(old['captures'],new['captures']):
    fields=['direction','rootMatrix','frame','fps','startEnd','nativeFrame','percentage','aspect','filter','transparent','cameraWorld','ortho','cameraProjection','calibration']
    report['captureSettingsEqual'].append({'direction':b['direction'],'equal':all(a[f]==b[f] for f in fields)})
report['meaning']='Actual current native finite fields, support and rig/camera compared against own retained earlier native measurements. This technical sameness does not establish visual approval. Current wholeobject geometry/images were independently inspected anew.'
(OUT/'unchanged-technical-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
