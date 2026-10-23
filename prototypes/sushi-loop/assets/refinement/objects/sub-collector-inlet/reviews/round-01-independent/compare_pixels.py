import pathlib,json,hashlib
from PIL import Image
import numpy as np
O=pathlib.Path(__file__).resolve().parent;E=O.parent.parent;C=E/'candidates/round-01'
def metric(a,b):
 a=np.array(a.convert('RGBA')).astype(np.int16);b=np.array(b.convert('RGBA')).astype(np.int16);d=np.abs(a-b);q=np.any(d,axis=2);ys,xs=np.where(q);return {'changedPixels':int(q.sum()),'changedAlphaPixels':int((d[:,:,3]>0).sum()),'maxRGBA':d.max(axis=(0,1)).tolist(),'sumRGBA':d.sum(axis=(0,1)).tolist(),'pixelLocations':[{'x':int(x),'y':int(y),'a':a[y,x].tolist(),'b':b[y,x].tolist()} for y,x in zip(ys,xs)]}
def compare(p,q):return metric(Image.open(p),Image.open(q))
publication=[];replay=[];closures=[];framesSeen=[]
for clip,count in [('idle',1),('active',12)]:
 for di in 'NESW':
  at=Image.open(C/f'atlases/{clip}-{di}.png').convert('RGBA')
  for idx in range(count):
   n=C/f'native/{clip}/{di}/{idx:03d}.png';p=C/f'frames/{clip}/{di}/{idx:03d}.png';im=Image.open(n).convert('RGBA').resize((384,704),Image.Resampling.BOX);pub=Image.open(p).convert('RGBA');atcell=at.crop(((idx%6)*384,(idx//6)*704,(idx%6+1)*384,(idx//6+1)*704));publication.append({'clip':clip,'direction':di,'index':idx,'wholeBOXExact':im.tobytes()==pub.tobytes(),'atlasCellExact':atcell.tobytes()==pub.tobytes()});rp=O/f'native/{clip}-{di}-{idx+1:02d}.png';replay.append({'clip':clip,'direction':di,'index':idx,'rawComparison':compare(n,rp)})
for di in 'NESW':
 pairs=[('submitted-closure',C/f'native/active/{di}/000.png',C/f'native/active/{di}/closure-013.png'),('fresh-closure',O/f'native/active-{di}-01.png',O/f'native/active-{di}-13.png'),('fresh-same1-repeat',O/f'native/control-{di}-1-a.png',O/f'native/control-{di}-1-b.png'),('fresh-same13-repeat',O/f'native/control-{di}-13-a.png',O/f'native/control-{di}-13-b.png'),('fresh1-vs13-control',O/f'native/control-{di}-1-a.png',O/f'native/control-{di}-13-a.png')]
 for label,p,q in pairs:
  a=Image.open(p).convert('RGBA');b=Image.open(q).convert('RGBA');closures.append({'direction':di,'comparison':label,'paths':[str(p.relative_to(E)),str(q.relative_to(E))],'raw':metric(a,b),'wholeBOXPublished':metric(a.resize((384,704),Image.Resampling.BOX),b.resize((384,704),Image.Resampling.BOX)),'wholeBOXLogical':metric(a.resize((192,352),Image.Resampling.BOX),b.resize((192,352),Image.Resampling.BOX))})
webps=[]
for p in sorted((C/'previews').glob('*.webp')):
 im=Image.open(p);meta=[]
 for idx in range(im.n_frames):im.seek(idx);meta.append({'index':idx,'duration':im.info.get('duration'),'sha256RGBA':hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()})
 webps.append({'path':str(p.relative_to(C)),'size':list(im.size),'frames':meta,'loop':im.info.get('loop')})
n=json.loads((O/'native-reopened.json').read_text());nativeClosure={d:next(x['stateSHA256'] for x in n['records'] if x['clip']=='active' and x['direction']==d and x['frame']==1)==next(x['stateSHA256'] for x in n['records'] if x['clip']=='active' and x['direction']==d and x['frame']==13) for d in 'NESW'}
r={'method':'Raw RGBA integer residuals, without masks/normalization/alpha repair; whole BOX reductions use complete RGBA cells exactly as frozen publication. All pixel locations retained. Same saved source/settings for closure and same-pose controls.','all52WholeBOXExact':all(x['wholeBOXExact'] for x in publication),'all52AtlasCellsExact':all(x['atlasCellExact'] for x in publication),'publication':publication,'independentReplayComparisons':replay,'closureAndRepeatability':closures,'nativeStateExactClosure':nativeClosure,'webpDecodedFrames':webps,'minimumGroundSweep':min(x['bounds'][0][2] for x in n['sweep']),'maximumSweep':[[min(x['bounds'][0][i] for x in n['sweep']) for i in range(3)],[max(x['bounds'][1][i] for x in n['sweep']) for i in range(3)]]}
(O/'pixels-publication-motion.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'publication52Exact':r['all52WholeBOXExact'],'atlas52Exact':r['all52AtlasCellsExact'],'nativeClosure':nativeClosure,'sweep':r['maximumSweep'],'closure':[{k:x[k] for k in ['direction','comparison']}|{v:{a:x[v][a] for a in ['changedPixels','changedAlphaPixels','maxRGBA']} for v in ['raw','wholeBOXPublished','wholeBOXLogical']} for x in closures],'webps':[(x['path'],len(x['frames']),[f['duration'] for f in x['frames']]) for x in webps]},indent=2))
