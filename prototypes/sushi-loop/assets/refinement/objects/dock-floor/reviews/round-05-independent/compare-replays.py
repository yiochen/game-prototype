from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;B=R.parents[1];expected=B/'candidates/round-05/browser-v4-human-reference'
def compare(a,b):
 x=np.array(Image.open(a).convert('RGBA'));y=np.array(Image.open(b).convert('RGBA'));d=np.abs(x.astype(int)-y.astype(int));return {'shape':list(x.shape),'pixelIdentical':bool(np.array_equal(x,y)),'changedPixels':int(np.any(d,axis=2).sum()),'maxDeltaRGBA':d.max(axis=(0,1)).tolist(),'meanAbsDeltaRGBA':d.mean(axis=(0,1)).tolist()}
browser=[]
for p in sorted((R/'browser').rglob('*.png')):
 q=expected/p.relative_to(R/'browser');browser.append({'own':str(p.relative_to(R)),'packet':str(q.relative_to(B)),**compare(p,q)})
native=[];nr=json.loads((R/'own-native-replay.json').read_text())
for r in nr['renders']:native.append({'own':r['path'],'packet':r['packetCorresponding'],**compare(R/r['path'],B/r['packetCorresponding'])})
(R/'own-replay-pixel-comparison.json').write_text(json.dumps({'browser':browser,'native':native,'browserAllRGBAIdentical':all(r['pixelIdentical']for r in browser),'browserCount':len(browser),'nativeAllRGBAIdentical':all(r['pixelIdentical']for r in native),'nativeCount':len(native)},indent=2)+'\n')
# Actual consumer mobile frames: retain recognizable all4facings/4phases at viewport size.
for bg in ['light','gray','dark']:
 for orient in ['portrait','landscape']:
  wh='390x844'if orient=='portrait'else'844x390';w,h=map(int,wh.split('x'));scale=.5 if orient=='landscape'else .6;cw,ch=round(w*scale),round(h*scale);sheet=Image.new('RGB',(cw*4,ch*4),'#bbb')
  for j,d in enumerate(['N','E','S','W']):
   for k in range(4):p=R/'browser'/f'viewport-{wh}-{d}-{bg}-phase{k}.png';sheet.paste(Image.open(p).convert('RGB').resize((cw,ch)),(k*cw,j*ch))
  sheet.save(R/f'own-mobile-coverage-{bg}-{orient}.png')
print(json.dumps({'browser':len(browser),'browserAllIdentical':all(r['pixelIdentical']for r in browser),'native':len(native),'nativeMaxDelta':[max(r['maxDeltaRGBA'][i]for r in native)for i in range(4)],'nativeChangedPixels':[r['changedPixels']for r in native]},indent=2))
