import json
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
H=Path(__file__).resolve().parent;O=H/'apng-screen-v3';j=json.loads((H/'actual-apng-screen-playback-v3.json').read_text());rows=[]
for r in j['results']:
 base=f"{r['clip']}-{r['direction']}";expected=[np.array(Image.open(O/f'{base}-expected-{n}.png').convert('RGB')).astype(np.int16) for n in range(12)];trace=[]
 for t in r['trace']:
  a=np.array(Image.open(O/t['file']).convert('RGB')).astype(np.int16);diff=[np.abs(a-b) for b in expected];mean=[v.mean() for v in diff];n=int(np.argmin(mean));dif=diff[n];trace.append({'seconds':t['seconds'],'file':t['file'],'nearestFrame':n,'maxChannelDifference':int(dif.max()),'differentPixels':int(np.any(dif,axis=2).sum()),'meanAbsoluteChannelDifference':float(dif.mean())})
 seen=sorted(set(t['nearestFrame'] for t in trace));rows.append({'clip':r['clip'],'direction':r['direction'],'trace':trace,'seen':seen,'finalObservedFrame':trace[-1]['nearestFrame']});print(base,'seen',seen,'max',max(t['maxChannelDifference'] for t in trace),'pixels',max(t['differentPixels'] for t in trace))
 # Sequence only unique native Chrome animation screen samples; whole screenshots retained.
 sheet=Image.new('RGB',(6*190,2*220),(160,168,176));draw=ImageDraw.Draw(sheet)
 for k,t in enumerate(trace[:12]):
  im=Image.open(O/t['file']).crop((65,165,255,360));sheet.paste(im,(k%6*190,k//6*220+20));draw.text((k%6*190+2,k//6*220+2),f"{t['seconds']:.2f}s frame{t['nearestFrame']}",fill='white')
 sheet.save(H/'visual'/f'{base}-actual-apng-sequence.png')
(H/'apng-screen-decoded-comparison.json').write_text(json.dumps({'method':'Compare actual screen PNG decoded RGB with each native static-screen PNG, retaining all unique actual screen images; encoded PNG SHA is not assumed to equal decoded pixels. Canvas animated-image API diagnostic is not a playback test.','results':rows},indent=2)+'\n')
