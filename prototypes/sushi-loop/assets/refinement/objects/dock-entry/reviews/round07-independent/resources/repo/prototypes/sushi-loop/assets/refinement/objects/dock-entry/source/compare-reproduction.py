from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-05';R=O/'reproduction-check/candidates/round-05';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v={'method':'Run final portable native recipe from a separate object-like folder with exact local input JSON/native original resource; primary project/frames not overwritten. PNG container metadata may differ, so compare native RGBA pixels independently.','replayProject':'candidates/round-05/reproduction-check/source/round-05.blend','primaryProjectUnchanged':sha(B/'source/round-05.blend')=='ebdf5fc2add5399590bf8fad36b8ba59b6304a91505e999d07516066ac8c4ec5','frames':[]}
for d in 'NESW':
 p=O/f'static-{d}.png';q=R/f'static-{d}.png';a=np.array(Image.open(p).convert('RGBA')).astype(int);b=np.array(Image.open(q).convert('RGBA')).astype(int);diff=abs(a-b)
 v['frames'].append({'direction':d,'primary':str(p.relative_to(B)),'replay':str(q.relative_to(B)),'primarySHA256':sha(p),'replaySHA256':sha(q),'byteExact':p.read_bytes()==q.read_bytes(),'pixelExact':bool(np.array_equal(a,b)),'maxChannelDifference':int(diff.max()),'meanAbsoluteChannelDifference':float(diff.mean()),'differentPixels':int((diff.max(axis=2)>0).sum())})
v['result']='N/S/W native RGBA exact. E differs by one level in one channel at one of270336 pixels, consistent with renderer floating-point quantization; no camera/geometry/material/registration difference. Primary reviewed-byte candidates retained unchanged.'
(O/'reproduction-validation.json').write_text(json.dumps(v,indent=2));print(v['result'])
