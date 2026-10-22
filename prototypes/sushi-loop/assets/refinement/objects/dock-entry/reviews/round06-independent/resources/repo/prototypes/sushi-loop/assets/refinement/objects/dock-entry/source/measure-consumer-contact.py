"""Quantify exact native and browser-exported source-over RGBA at shared seam.
No source/exported pixels changed. All phase browser screenshots remain separate.
"""
from pathlib import Path
from PIL import Image
import numpy as np,json,math,hashlib
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-05';C=B/'source/resources/paired-consumer/floor-packet/candidates/round-03';records=[]
for d,a in zip('NESW',[math.pi,math.pi/2,0,-math.pi/2]):
 native=C/f'native-pair-{d}.png';independent=C/f'browser-v2-supported/independent-composite-{d}-phase0.png';n=np.array(Image.open(native).convert('RGBA')).astype(int);p=np.array(Image.open(independent).convert('RGBA')).astype(int)
 x=576+math.sin(a)*384;y=704+math.cos(a)*384-.22*179.2
 if d in 'NS':box=[round(x-96),math.floor(y)-1,round(x+96),math.floor(y)+3]
 else:box=[math.floor(x)-1,round(y-96),math.floor(x)+3,round(y+96)]
 x0,y0,x1,y1=box;nn=n[y0:y1,x0:x1];pp=p[y0:y1,x0:x1];diff=np.abs(nn-pp);alpha=pp[:,:,3];opaque=nn[:,:,3]>=250;flatlow=(alpha<250)&opaque
 # Tangent support extent retains every non-opaque sample as a diagnostic,
 # while visible appearance is judged from genuine logical/phone screenshots.
 if d in 'NS':lowalong=flatlow.any(axis=0)
 else:lowalong=flatlow.any(axis=1)
 longest=run=0
 for b in lowalong:
  run=run+1 if b else 0;longest=max(longest,run)
 records.append({'direction':d,'phase':0,'nativePath':str(native.relative_to(B)),'nativeSHA256':hashlib.sha256(native.read_bytes()).hexdigest(),'independentPath':str(independent.relative_to(B)),'independentSHA256':hashlib.sha256(independent.read_bytes()).hexdigest(),'nativeSize':list(n.shape[1::-1]),'seamCenterNative':[x,y],'contactBoxNative':box,'minNativeAlpha':int(nn[:,:,3].min()),'minIndependentAlpha':int(alpha.min()),'maxAlphaDifference':int(diff[:,:,3].max()),'meanAbsoluteRGBDifference':float(diff[:,:,:3].mean()),'maxRGBDifference':int(diff[:,:,:3].max()),'opaqueNativePixels':int(opaque.sum()),'independentBelow250AgainstOpaqueNative':int(flatlow.sum()),'longestTangentRunAnyBelow250NativePixels':int(longest),'longestTangentRunLogicalPixels':longest/2,'interpretation':'RGBA diagnostic of exact phase0 consumer canvas versus one native depth-tested image. RGB need not be identical because finite shared lights illuminate translated entry and local contact shadows differently. Complete actual browser phase0/.25/.5/.75 sheets and contact/viewport screenshots establish intended-size appearance; this metric never replaces native physical no-gap proof.'})
(O/'consumer-contact-metrics.json').write_text(json.dumps({'method':'Exact saved RGBA native pair and actual Chromium canvas export, no resampling. Fixed interior centered.75world contact window,4nativepx normal band, phase0. All other common phases preserved in genuine browser records.','records':records},indent=2));print(json.dumps([{k:r[k] for k in ['direction','minNativeAlpha','minIndependentAlpha','maxAlphaDifference','meanAbsoluteRGBDifference','longestTangentRunLogicalPixels']} for r in records],indent=2))
