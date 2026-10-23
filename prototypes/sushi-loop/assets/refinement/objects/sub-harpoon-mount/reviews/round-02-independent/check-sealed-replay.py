from pathlib import Path
from PIL import Image
import numpy as np,json
R=Path(__file__).parent;E=R.parents[1];C=E/'candidates/round-02';d=json.loads((C/'replay-audit.json').read_text());rows=[]
for r in d['renders']:
 a=np.asarray(Image.open(E/r['original']).convert('RGBA'),dtype=np.int16);b=np.asarray(Image.open(E/r['path']).convert('RGBA'),dtype=np.int16);q=np.abs(a-b);rows.append({'direction':r['direction'],'clip':r['clip'],'frame':r['sourceFrame'],'maxRGBA':q.max(axis=(0,1)).tolist(),'changedPixels':int(np.any(q,axis=2).sum()),'rmsRGBA':np.sqrt(np.mean(q.astype(float)**2,axis=(0,1))).tolist(),'alphaExact':bool(np.all(q[:,:,3]==0))})
summary={'frames':len(rows),'allAlphaExact':all(x['alphaExact'] for x in rows),'maxRGBDelta':max(max(x['maxRGBA'][:3]) for x in rows),'maxChangedPixels':max(x['changedPixels'] for x in rows),'maxRGBRms':max(max(x['rmsRGBA'][:3]) for x in rows),'exactRGBAFrames':sum(x['changedPixels']==0 for x in rows)}
(R/'sealed-replay-independent-check.json').write_text(json.dumps({'method':'Independent decoded arrays of all52 packet-bound raw source/replay pairs; no image edits.','summary':summary,'rows':rows},indent=2)+'\n');print(summary)
