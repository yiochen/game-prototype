"""Read-only numerical diagnostics of native/actual-canvas filter study outputs."""
from pathlib import Path
from PIL import Image
import numpy as np,json,math,hashlib
B=Path(__file__).resolve().parents[1];O=B/'candidates/alpha-filter-study';allrecords=[]
for folder in sorted(O.glob('eevee-*')):
 native_record=folder/'native-records.json'
 if not native_record.exists():continue
 settings=json.loads(native_record.read_text())['settings'];records=[]
 for n in sorted((folder/'browser').glob('*-native.png')):
  # Exact actual consumer exports. Native pair is sampled through that same canvas.
  d=n.name.split('-')[0];phase=float(n.name.split('-phase')[1].split('-')[0]);p=n.with_name(n.name.replace('-native.png','-independent.png'))
  if not p.exists():continue
  na=np.array(Image.open(n).convert('RGBA')).astype(int);pa=np.array(Image.open(p).convert('RGBA')).astype(int);a=math.pi/2 if d=='E' else -math.pi/2;x=576+math.sin(a)*384+phase*2;y=704-.22*179.2+phase*2;cx,cy=round(x),round(y);box=[math.floor(x)-3,round(y-96),math.floor(x)+4,round(y+96)];x0,y0,x1,y1=box;nn=na[y0:y1,x0:x1];pp=pa[y0:y1,x0:x1];diff=np.abs(nn-pp);loss=np.maximum(nn[:,:,3]-pp[:,:,3],0);along=(loss>=8).any(axis=1);longest=run=0
  for b in along:run=run+1 if b else 0;longest=max(longest,run)
  profile_n=na[cy,cx-5:cx+6,3].tolist();profile_p=pa[cy,cx-5:cx+6,3].tolist();r={'variant':folder.name,'settings':settings,'direction':d,'phase':phase,'nativeCanvas':str(n.relative_to(B)),'independentCanvas':str(p.relative_to(B)),'windowNative':box,'minNativeAlpha':int(nn[:,:,3].min()),'minIndependentAlpha':int(pp[:,:,3].min()),'maxAlphaLoss':int(loss.max()),'meanAlphaLoss':float(loss.mean()),'normalIntegratedMissingCoverageLogicalMax':float((loss.sum(axis=1)/255/2).max()),'tangentRunWithAlphaLossGE8Logical':longest/2,'centerNativeAlpha':profile_n,'centerIndependentAlpha':profile_p,'meanAbsoluteRGBDifference':float(diff[:,:,:3].mean()),'maxRGBDifference':int(diff[:,:,:3].max())};records.append(r);allrecords.append(r)
 if records:(folder/'metrics.json').write_text(json.dumps({'records':records},indent=2))
# Image-valued measurement that confirms whether a native engine honors a setting.
base=O/'eevee-filter-1p5';comparisons=[]
for folder in sorted(O.glob('eevee-*')):
 for d in ['E','W']:
  for kind in ['entry','floor','pair']:
   p=folder/f'{kind}-{d}.png';q=base/f'{kind}-{d}.png'
   if not p.exists() or not q.exists():continue
   aa=np.array(Image.open(p).convert('RGBA')).astype(int);bb=np.array(Image.open(q).convert('RGBA')).astype(int);diff=abs(aa-bb);comparisons.append({'variant':folder.name,'direction':d,'kind':kind,'pixelIdenticalToFilter1p5':bool(np.array_equal(aa,bb)),'alphaIdenticalToFilter1p5':bool(np.array_equal(aa[:,:,3],bb[:,:,3])),'maxRGBDifference':int(diff[:,:,:3].max()),'maxAlphaDifference':int(diff[:,:,3].max()),'differentAlphaPixels':int((diff[:,:,3]>0).sum())})
(O/'metrics-summary.json').write_text(json.dumps({'method':'Exact actual corrected-consumer RGBA exports; native reference passed through same consumer phase. No image modifications. Alpha-loss window is7nativepx normal by192nativepx tangent centered on immutable shared contact. Normal integrated missing coverage is analytical diagnostic; visual no-seam bar remains unchanged.','records':allrecords,'nativeSettingEffectVsFilter1p5':comparisons},indent=2));print(json.dumps([{k:r[k] for k in ['variant','direction','phase','minIndependentAlpha','maxAlphaLoss','normalIntegratedMissingCoverageLogicalMax','centerIndependentAlpha']} for r in allrecords],indent=2))
