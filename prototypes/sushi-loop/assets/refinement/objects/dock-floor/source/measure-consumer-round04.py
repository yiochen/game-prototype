"""Actual current browser-canvas RGBA coverage, all4 directions/allquarterphases."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,math
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-04';C=O/'browser-v3-native-sampling';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();out=[]
for d in ['N','E','S','W']:
 for phase in [0,.25,.5,.75]:
  p=C/f'independent-composite-{d}-phase{phase}.png';q=C/f'native-composite-{d}-phase{phase}.png';a=np.asarray(Image.open(p).convert('RGBA'));n=np.asarray(Image.open(q).convert('RGBA'));shift=phase*2;topY=704-179.2*.22
  # Actual native camera basis:256px/worldcell, height179.2px/worldZ.
  # Centered .75world interval lies inside guaranteed .78clear passage.
  if d in ['E','W']:
   x=(960 if d=='E' else 192)+shift;ys=(math.ceil(topY-96+shift),math.floor(topY+96+shift));xs=(math.floor(x)-2,math.ceil(x)+3)
  else:
   y=topY+(384 if d=='S' else -384)+shift;xs=(math.ceil(576-96+shift),math.floor(576+96+shift));ys=(math.floor(y)-2,math.ceil(y)+3)
  ac=a[ys[0]:ys[1],xs[0]:xs[1]];nc=n[ys[0]:ys[1],xs[0]:xs[1]];loss=nc[:,:,3].astype(int)-ac[:,:,3].astype(int);premult=lambda z:z[:,:,:3].astype(float)*(z[:,:,3:4]/255)
  rgb=abs(premult(ac)-premult(nc));opaqueReference=nc[:,:,3]==255;lost=(ac[:,:,3]<255)&opaqueReference
  along=lost.any(axis=1 if d in ['E','W'] else 0);longest=current=0
  for value in along:
   current=current+1 if value else 0;longest=max(longest,current)
  out.append({'direction':d,'phaseLogical':phase,'independent':{'path':str(p.relative_to(B)),'sha256':sha(p)},'native':{'path':str(q.relative_to(B)),'sha256':sha(q)},'exactViewport':[1152,1280],'contactStripNativeRect':[xs[0],ys[0],xs[1]-xs[0],ys[1]-ys[0]],'clearAnalyzedWorldWidth':.75,'independentMinAlpha':int(ac[:,:,3].min()),'nativeMinAlpha':int(nc[:,:,3].min()),'maxAlphaLoss':int(loss.max()),'pixelsLostAlphaAgainstOpaqueNative':int(lost.sum()),'longestContinuousLostCoverageNativePixels':longest,'longestContinuousLostCoverageLogicalPixels':longest/2,'maxPremultipliedRGBDifference':float(rgb.max()),'meanPremultipliedRGBDifference':float(rgb.mean())})
r={'method':'Exact actual current Chromium native-canvas PNG pixels, including RGBA and premultipliedRGB. Native and separately captured actual floor/entry assets use same analytical commonphase and native viewport; only1guardpixel viewport crop, no resampling/pixel edits/masks/nudges. Local ray geometry and frozen nativeframe calibration determine contact strip.','rendererSHA256':sha(B/'inputs/consumer-native-sampling/world-sprite-raster.js'),'floorSourceSHA256':sha(B/'source/round-04.blend'),'nativeFilterSize':.5,'directions':['N','E','S','W'],'quarterPhases':[0,.25,.5,.75],'actualContextStateRecords':'candidates/round-04/browser-v3-native-sampling/consumer-evidence.json','actualIntermediateSmoothingDisabled':all(c['actualIntermediateImageSmoothingEnabled'] is False for r in json.loads((C/'consumer-evidence.json').read_text())['records'] for c in r['cases']),'measurements':out,'all16NoCoverageLoss':all(r['pixelsLostAlphaAgainstOpaqueNative']==0 and r['independentMinAlpha']==255 for r in out),'editorScope':'Technical measurement only; original independent judge must assess final visible RGB/alpha presentations. Historical E/W1nativepixel alpha trough is retained in prior rounds and cannot count as passing evidence.'}
(O/'actual-consumer-contact-metrics.json').write_text(json.dumps(r,indent=2));print('ACTUAL_RGBA',r['all16NoCoverageLoss'],[(v['direction'],v['phaseLogical'],v['independentMinAlpha'],v['maxAlphaLoss']) for v in out])
