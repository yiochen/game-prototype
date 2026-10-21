import json,time,collections
from pathlib import Path
import numpy as np
from PIL import Image
b=Path(__file__).resolve().parent.parent/'candidates/round-01';out={'packetSHA256':'612d71d45c15be7141e7e75e9e342c5eeff3a7190432799fc4c16cab011d3a14'};start=time.time()
def check_set(file):
 d=json.loads((b/file).read_text());pairs=d['pairs'] if isinstance(d,dict) else d;errors=[];summary={};coverage=collections.Counter();bboxes=collections.defaultdict(set)
 for i,p in enumerate(pairs):
  if 'current' in p:a=np.asarray(Image.open(p['current']).convert('RGBA')).astype(np.int16);bb=np.asarray(Image.open(p['reference']).convert('RGBA')).astype(np.int16)
  else:
   a=np.asarray(Image.open(p['path']).convert('RGBA')).astype(np.int16);bb=np.asarray(Image.open(b/'native-runs'/('native-'+p['pattern']+'-'+p['direction']+'-'+str(p['index']).zfill(2)+'.png')).convert('RGBA')).astype(np.int16)
  diff=np.abs(a-bb);mx=diff.max(axis=(0,1)).tolist();mask=(diff[:,:,:3]>1).any(axis=2);yy,xx=np.where(mask);bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)] if len(xx) else None
  if mx!=p['fullMaxRGBA']:errors.append({'case':i,'field':'fullMaxRGBA','actual':mx,'recorded':p['fullMaxRGBA']})
  if bbox!=p.get('fullResidualBoundsOver1'):errors.append({'case':i,'field':'bounds','actual':bbox,'recorded':p.get('fullResidualBoundsOver1')})
  if 'fullResidualPixelsOver1' in p and int(mask.sum())!=p['fullResidualPixelsOver1']:errors.append({'case':i,'field':'pixelCount'})
  pitch=str(p.get('pitch','native'));s=summary.setdefault(pitch,{'pairs':0,'maxRGBA':[0]*4,'joinMaxRGBA':[0]*4,'alphaDifferentPixels':0,'rgbOver1Pixels':0,'maxFullResidualPixelCount':0})
  s['pairs']+=1;s['maxRGBA']=[max(x,y) for x,y in zip(s['maxRGBA'],mx)];s['maxFullResidualPixelCount']=max(s['maxFullResidualPixelCount'],int(mask.sum()));s['alphaDifferentPixels']+=int((diff[:,:,3]>0).sum());s['rgbOver1Pixels']+=int(mask.sum())
  for j,jr in enumerate(p['joins']):
   x,y,w,h=jr['rect'];reg=diff[y:y+h,x:x+w];jmx=reg.max(axis=(0,1)).tolist();jalpha=int((reg[:,:,3]>0).sum());jrgb=int((reg[:,:,:3]>1).any(axis=2).sum());s['joinMaxRGBA']=[max(x,y) for x,y in zip(s['joinMaxRGBA'],jmx)]
   if jmx!=jr['maxRGBA'] or jalpha!=jr.get('differentAlphaPixels',jr.get('alphaPixels')) or jrgb!=jr.get('differentRGBOver1Pixels',jr.get('rgbOver1Pixels')):errors.append({'case':i,'join':j,'field':'joinNumeric','actual':[jmx,jalpha,jrgb]})
  coverage[(p['pattern'],p['direction'],pitch,p.get('context'),p.get('background'))]+=1
  if bbox:bboxes[pitch].add(tuple(bbox))
 return {'pairCount':len(pairs),'allPixelMetricsMatch':not errors,'errors':errors[:20],'summary':summary,'coverage':{'/'.join(map(str,k)):v for k,v in coverage.items()},'fullResidualBounds':{k:[list(x) for x in sorted(v)] for k,v in bboxes.items()}}
for file in ['native-vs-independent-metrics.json','consumer-metrics.json','floor-consumer-metrics.json']:
 out[file]=check_set(file);print(file,out[file]['pairCount'],'pairs match',out[file]['allPixelMetricsMatch'],flush=True)
# Source atlas/frame closure and native alpha geometry are independently read.
source={}
for dr in 'NESW':
 frames=[np.asarray(Image.open(b/'frames'/f'running-{dr}-{i:02}.png').convert('RGBA')) for i in range(25)]
 atlas=np.asarray(Image.open(b/'atlases'/f'running-{dr}.png').convert('RGBA'))
 source[dr]={'uniqueFrames':len({f.tobytes() for f in frames[:24]}),'closurePixelsEqual':np.array_equal(frames[0],frames[24]),'alphaStableAllFrames':all(np.array_equal(frames[0][:,:,3],f[:,:,3]) for f in frames),'atlasSize':[atlas.shape[1],atlas.shape[0]],'all24AtlasRegionsPixelExact':all(np.array_equal(atlas[(i//6)*704:(i//6+1)*704,(i%6)*384:(i%6+1)*384],frames[i]) for i in range(24))}
out['sourceFramesAndAtlases']=source;out['seconds']=time.time()-start
(Path(__file__).parent/'round-01-independent-pixel-check.json').write_text(json.dumps(out,indent=2)+'\n');print('DONE',out['seconds'])
