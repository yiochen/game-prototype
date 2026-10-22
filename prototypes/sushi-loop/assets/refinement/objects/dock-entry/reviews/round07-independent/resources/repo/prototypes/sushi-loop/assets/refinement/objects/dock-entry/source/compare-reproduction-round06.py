from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-06';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();r={'method':'Read-only exactsource06 replay, identical persisted camera/filter.5/EEVEE64; compare RGBA independently from PNG metadata. No approved frame/project overwritten.','sourceSHA256':sha(B/'source/round-06.blend'),'sourceUnchanged':json.loads((O/'reproduction-check/native-replay.json').read_text())['sourceUnchanged'],'frames':[]}
for d in 'NESW':
 p=O/f'static-{d}.png';q=O/f'reproduction-check/static-{d}.png';a=np.array(Image.open(p).convert('RGBA')).astype(int);b=np.array(Image.open(q).convert('RGBA')).astype(int);diff=abs(a-b);r['frames'].append({'direction':d,'primary':str(p.relative_to(B)),'replay':str(q.relative_to(B)),'primarySHA256':sha(p),'replaySHA256':sha(q),'byteExact':p.read_bytes()==q.read_bytes(),'pixelExact':bool(np.array_equal(a,b)),'differentPixels':int((diff.max(axis=2)>0).sum()),'maxChannelDifference':int(diff.max())})
(O/'reproduction-validation.json').write_text(json.dumps(r,indent=2));print([(v['direction'],v['pixelExact'],v['differentPixels'],v['maxChannelDifference']) for v in r['frames']])
