from pathlib import Path
import numpy as np,json,hashlib,math
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;O=R.parents[1];C=O/'candidates/round-04';rec=json.loads((R/'own-seam-consumer-replay.json').read_text());report={'standalone':[],'contacts':[],'rawReplayMatches':[]}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for d in 'NESW':
 p=C/f'frames/static-{d}/000.png';a=np.array(Image.open(p).convert('RGBA'));partial=(a[:,:,3]>0)&(a[:,:,3]<128);red=(a[:,:,0]>100)&(a[:,:,1]<12)&(a[:,:,2]<12);yellow=(a[:,:,0]>100)&(a[:,:,1]>100)&(a[:,:,2]<12)
 report['standalone'].append({'facing':d,'path':str(p),'sha256':sha(p),'bboxAlpha':Image.open(p).getbbox(),'nativeFrame':list(Image.open(p).size),'frameAtlasBytesIdentical':sha(p)==sha(C/f'atlases/static-{d}.png'),'RGBAtAlphaZeroNonzeroPixels':int(np.count_nonzero((a[:,:,3]==0)&np.any(a[:,:,:3]>0,axis=2))),'lowAlphaRedIndicator':int(np.count_nonzero(partial&red)),'lowAlphaYellowIndicator':int(np.count_nonzero(partial&yellow)),'opaqueRGBBelow12Pixels':int(np.count_nonzero((a[:,:,3]>=250)&np.all(a[:,:,:3]<12,axis=2)))})
 for i,phase in enumerate([0,.25,.5,.75]):
  npth=R/f'seam-browser/raw-pair-{d}-gray-1-{i*2}.png';ipth=R/f'seam-browser/raw-pair-{d}-gray-1-{i*2+1}.png';n=np.array(Image.open(npth).convert('RGBA')).astype(int);a=np.array(Image.open(ipth).convert('RGBA')).astype(int)
  if d in 'NS':
   cx=576+phase*2;cy=(280.576 if d=='N' else 1048.576)+phase*2;box=[math.ceil(cx-.35*256),math.floor(cy-2),math.floor(cx+.35*256),math.ceil(cy+2)]
  else:
   cx=(960 if d=='E' else 192)+phase*2;cy=664.576+phase*2;box=[math.floor(cx-2),math.ceil(cy-.35*256),math.ceil(cx+2),math.floor(cy+.35*256)]
  x0,y0,x1,y1=box;nn=n[y0:y1,x0:x1];aa=a[y0:y1,x0:x1];da=nn[:,:,3]-aa[:,:,3];rgb=abs(nn[:,:,:3]-aa[:,:,:3]);report['contacts'].append({'facing':d,'phase':phase,'rawNative':npth.name,'rawIndependent':ipth.name,'physicalSeamROI':box,'minNativeAlpha':int(nn[:,:,3].min()),'minIndependentAlpha':int(aa[:,:,3].min()),'maximumAlphaLoss':int(da.max()),'pixelsWithAlphaLoss':int(np.count_nonzero(da>0)),'maxRGBChannelDelta':rgb.max(axis=(0,1)).tolist(),'meanAbsRGBChannelDelta':rgb.mean(axis=(0,1)).tolist()})
  # Candidate's original raw export uses exactly the same common-grid protocol.
  for native,pp,own in [(True,C/f'browser-v3-native-sampling/native-composite-{d}-phase{phase:g}.png',n),(False,C/f'browser-v3-native-sampling/independent-composite-{d}-phase{phase:g}.png',a)]:
   old=np.array(Image.open(pp).convert('RGBA')).astype(int);delta=abs(own-old);report['rawReplayMatches'].append({'facing':d,'phase':phase,'native':native,'candidateExport':str(pp),'pixelIdentical':bool((delta==0).all()),'maxDelta':int(delta.max())})
report['method']='Full rawRGBA from independent fresh actual-consumer browser replay. Physical contact ROIs follow measured registered0.22surface across centered0.70worldwidth, excluding decorative side bevels/posts. ROI spans both sides of seam, not a fitted alpha bbox.'
report['packetSHA256']='411bb31bdb772f94f7db68e7ae9d704dd6f376f090396a0af2c8cc97c8a0e65c';(R/'own-raster-measurements.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'contacts':report['contacts'],'standalone':report['standalone'],'all32RawReplaysPixelIdentical':all(r['pixelIdentical'] for r in report['rawReplayMatches'])},indent=2))
