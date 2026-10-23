from pathlib import Path
import json,hashlib
from PIL import Image
b=Path(__file__).resolve().parent.parent/'candidates/round-01';out={}
for file in ['consumer-metrics.json','floor-consumer-metrics.json']:
 pairs=json.loads((b/file).read_text())['pairs'];lookup={(p['pattern'],p['direction'],p['pitch'],p['background'],p['context'],p['index']):p for p in pairs};closures=[];unique=[]
 for key,p in lookup.items():
  if key[-1]!=24:continue
  first=lookup[key[:-1]+(0,)]
  for side in ['current','reference']:
   a=Image.open(p[side]).convert('RGBA');bb=Image.open(first[side]).convert('RGBA');closures.append(a.tobytes()==bb.tobytes())
 for key,p in lookup.items():
  if key[-1]!=0 or p['context'] not in [0,1] or p['background'] not in ['transparent','game-floor-cream']:continue
  frames=[hashlib.sha256(Image.open(lookup[key[:-1]+(i,)]['current']).convert('RGBA').tobytes()).hexdigest() for i in range(24)];unique.append(len(set(frames)))
 out[file]={'checkedClosureOutputPairs':len(closures),'allClosurePixelArraysEqual':all(closures),'uniqueFrameCaseCount':len(unique),'uniqueFrameCounts':sorted(set(unique))}
# native connected and independent25-frame captures
cl=[]
for pattern in ['SSS','SNS','NSN','SES','ESE']:
 for d in 'NESW':
  for directory,prefix in [('native-runs','native'),('independent-runs','independent')]:cl.append(Image.open(b/directory/f'{prefix}-{pattern}-{d}-00.png').convert('RGBA').tobytes()==Image.open(b/directory/f'{prefix}-{pattern}-{d}-24.png').convert('RGBA').tobytes())
out['nativeConnectedAndIndependent']={'checkedPairs':len(cl),'allPixelArraysEqual':all(cl)}
(Path(__file__).parent/'round-01-independent-closure-check.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
