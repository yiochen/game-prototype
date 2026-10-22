from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np
R=Path(__file__).resolve().parents[1];profile=[[-.45,0],[.45,0],[.45,.28],[.39,.43],[-.39,.43],[-.45,.28]];results=[]
for kind in ['pair','closedRun']:
 for d in 'EW':
  na=np.array(Image.open(R/f'captures/native/{kind}-{d}-2x.png').convert('RGBA')).astype(int);ca=np.array(Image.open(R/f'captures/consumer/fullChrome-raw-{kind}-{d}.png').convert('RGBA')).astype(int)
  centers=[440 if d=='E' else 312] if kind=='pair' else [312,440]
  for j,yroot in enumerate(centers):
   coords=[((224+(-1 if d=='E' else 1)*128*y)*2,(yroot-89.6*z)*2) for y,z in profile]
   mask=Image.new('L',(896,1216));ImageDraw.Draw(mask).polygon(coords,fill=255);m=np.array(mask)>0;opaque=m&(na[:,:,3]==255);diff=abs(na[:,:,:3]-ca[:,:,:3]);deficit=na[:,:,3]-ca[:,:,3]
   results.append({'kind':kind,'direction':d,'join':j,'projectedFiniteCutPolygon2x':coords,'nativeOpaqueSamples':int(opaque.sum()),'alphaDeficitCount':int(((deficit>0)&opaque).sum()),'alphaDeficitMax':int(deficit[opaque].max()),'rgbMean':float(diff[opaque].mean()),'rgbMax':int(diff[opaque].max())})
(R/'measurements/projected-finite-join-checks.json').write_text(json.dumps({'metrics':results,'meaning':'Independent finite projected cut region checks supplement the narrow crown strips. Visible native/consumer comparisons remain decisive; no numerical-only seam waiver.'},indent=2)+'\n');print(json.dumps(results,indent=2))
