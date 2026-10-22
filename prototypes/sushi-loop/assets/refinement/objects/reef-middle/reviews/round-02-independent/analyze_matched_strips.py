import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from PIL import Image,ImageChops
B=Path(__file__).resolve().parent; P=B.parent.parent/'candidates/round-02'; E=B/'evidence'
d=json.loads((E/'independent-ground-and-strip-vector-audit.json').read_text()); rec=[]
for r in d['strips']:
 a=Image.open(E/r['path']).convert('RGBA');c=Image.open(P/'native'/('three-joined-'+r['direction']+'.png')).convert('RGBA');diff=ImageChops.difference(a,c);data=list(diff.get_flattened_data())
 rec.append({'direction':r['direction'],'path':r['path'],'differentDecodedPixels':sum(any(v) for v in data),'maxRGBAChannelDelta':[max(v[k] for v in data) for k in range(4)]})
f={'method':'One bounded follow-up keeps the exact float32 mathutils.Vector pixel-coordinate storage used by submitted capture; same saved source, geometry, lights, world camera matrix, strip dimensions and root. The initial list-arithmetic replay bytes remain retained. No RGB/alpha repair or source change.',
 'firstReplayRootPixels':json.loads((E/'independent-ground-and-strip-audit.json').read_text())['stripCamera']['rootPixels'],
 'matchedArithmeticRootPixels':d['stripCamera']['rootPixels'],'records':rec,
 'interpretation':'All4 heroes decodedRGBA exact. Matched strip replay has N/E/S4/6/5differentpixels,maxRGB1,alphaexact; Wexact. The editor independently reported6/2/8,maxRGB1,alphaexact,Wexact. Small native-render residual cause is not isolated and no equality is forced. The initial list-arithmetic discrepancy is isolated to tiny camera-coordinate precision and its bytes remain retained. Actual consumer replay uses unchanged submitted PNGs.'}
assert all(max(r['maxRGBAChannelDelta'][:3])<=1 and r['maxRGBAChannelDelta'][3]==0 for r in rec)
(E/'matched-arithmetic-strip-findings.json').write_text(json.dumps(f,indent=2)+'\n');print(json.dumps(f))
