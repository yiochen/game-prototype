from pathlib import Path
import json,numpy as np
from PIL import Image
p=Path(__file__).resolve().parent;r=[]
for f in (p/'consumer/chromium').glob('*.png'):
 other=p/'consumer/headless-shell'/f.name;a=np.asarray(Image.open(f).convert('RGBA')).astype(np.int16);b=np.asarray(Image.open(other).convert('RGBA')).astype(np.int16);diff=np.abs(a-b);mask=diff.max(2)>0;y,x=np.nonzero(mask);r.append({'fullChromium':str(f.relative_to(p)),'headlessShell':str(other.relative_to(p)),'sameDecodedPixels':bool((diff==0).all()),'changedPixels':int(mask.sum()),'maxRGBA':diff.max((0,1)).tolist(),'meanAbsRGBA':diff.mean((0,1)).tolist(),'differenceBounds':None if not len(x) else [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]})
(p/'consumer/mode-comparison.json').write_text(json.dumps(r,indent=2)+'\n');print('mode comparisons',len(r),'same',sum(x['sameDecodedPixels'] for x in r),'max changed',max(x['changedPixels'] for x in r))
