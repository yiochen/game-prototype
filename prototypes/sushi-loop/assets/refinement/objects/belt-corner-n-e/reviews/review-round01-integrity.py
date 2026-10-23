from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
B=Path(__file__).resolve().parent.parent; C=B/'candidates/round-01'; R=B/'reviews';p=json.loads((C/'packet.json').read_text());sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
unique={}
for name,v in p['files'].items():
 if isinstance(v,dict) and 'path' in v and 'sha256' in v:unique[(C/v['path']).resolve()]=v['sha256']
bad=[]
for f,h in unique.items():
 if not f.exists() or sha(f)!=h:bad.append(str(f))
report={'packetSHA256':sha(C/'packet.json'),'referencedFileEntries':len(p['files']),'uniqueReferencedFiles':len(unique),'fileHashFailures':bad,'allAtlasRectsExact':True,'frameCoverage':{},'closure':{},'gifCadence':{}}
for d in 'NESW':
 atlas=Image.open(C/f'atlases/frames-{d}.png').convert('RGBA'); hashes=[]
 for i in range(24):
  f=Image.open(C/f'frames/running-{d}-{i:02}.png').convert('RGBA');a=np.array(f);hashes.append(hashlib.sha256(a.tobytes()).hexdigest())
  report['allAtlasRectsExact'] &= f.size==(384,704) and np.array_equal(a,np.array(atlas.crop(((i%6)*384,(i//6)*704,(i%6+1)*384,(i//6+1)*704))))
 report['frameCoverage'][d]={'count':len(hashes),'uniquePixelFrames':len(set(hashes))}
 x=np.array(Image.open(C/f'frames/running-{d}-00.png').convert('RGBA')).astype(int);y=np.array(Image.open(C/f'closure/running-{d}-24.png').convert('RGBA')).astype(int);delta=abs(x-y);where=np.any(delta,axis=2);ys,xs=np.where(where)
 report['closure'][d]={'maxRGBA':delta.max(axis=(0,1)).tolist(),'differentPixels':int(where.sum()),'bounds':None if not len(xs) else [int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]}
 g=Image.open(C/f'previews/running-{d}.gif');dur=[]
 for i in range(g.n_frames):g.seek(i);dur.append(g.info.get('duration'))
 report['gifCadence'][d]={'frames':g.n_frames,'durationMs':dur,'sumMs':sum(dur),'loop':g.info.get('loop')}
# Independently recompute100 native raw residual cases with supplied spatial mask, not editor summary.
summary={}
for key in ['independentVsConnected','connectedVsUnbroken']:
 rows=[]
 for d in 'NESW':
  mask=np.array(Image.open(C/f'residuals/join-mask-{d}.png').convert('L'))>0
  for i in range(25):
   left='independent' if key.startswith('independent') else 'connected';right='connected' if key.startswith('independent') else 'unbroken'
   x=np.array(Image.open(C/f'{left}/running-{d}-{i:02}.png').convert('RGBA')).astype(int);y=np.array(Image.open(C/f'{right}/running-{d}-{i:02}.png').convert('RGBA')).astype(int);dif=abs(x-y)
   rows.append({'direction':d,'frame':i,'fullMaxRGBA':dif.max(axis=(0,1)).tolist(),'joinMaxRGBA':dif[mask].max(axis=0).tolist(),'joinAlphaPixels':int(np.count_nonzero(dif[:,:,3][mask])),'joinRGBOver1Pixels':int(np.any(dif[:,:,:3]>1,axis=2)[mask].sum())})
 summary[key]={'cases':len(rows),'fullMaxRGBA':np.max([x['fullMaxRGBA'] for x in rows],axis=0).tolist(),'joinMaxRGBA':np.max([x['joinMaxRGBA'] for x in rows],axis=0).tolist(),'joinAlphaPixels':sum(x['joinAlphaPixels'] for x in rows),'joinRGBOver1Pixels':sum(x['joinRGBOver1Pixels'] for x in rows)}
report['independentlyRecomputedNativeResiduals']=summary
(R/'round01-independent-integrity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
