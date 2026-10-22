from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json,numpy as np,math
P=Path(__file__).resolve().parents[1];O=P/'candidates/round-01'
rots={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def masks(d,w,h):
 out={};r=rots[d]
 for name,axis in [('incoming',0),('outgoing',1)]:
  im=Image.new('L',(896,1216));dr=ImageDraw.Draw(im);pts=[]
  for a in [-.48,.48]:
   for delta in [-.014,.014]:
    for z in [.505,.695]:
     x,y=(.5+delta,a) if axis==0 else (a,.5+delta);xx=x*math.cos(r)-y*math.sin(r);yy=x*math.sin(r)+y*math.cos(r);pts.append((448+256*xx,752-256*yy-z*179.2))
  dr.rectangle((min(x for x,y in pts)-1,min(y for x,y in pts)-1,max(x for x,y in pts)+1,max(y for x,y in pts)+1),fill=255)
  if (w,h)!=(896,1216):im=im.resize((w,h),Image.Resampling.BOX).filter(ImageFilter.MaxFilter(5))
  out[name]=np.array(im)>0
 return out
def bounds(mask):
 ys,xs=np.where(mask);return [int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if len(xs) else None
def stats(a,b,mm):
 df=np.abs(a.astype(int)-b.astype(int));good=np.ones(df.shape[:2],bool);out={}
 for name,mask in [('full',good),*mm.items()]:
  dd=df[mask];bad=np.any(df[:,:,:3]>1,axis=2)&mask;alpha=(df[:,:,3]>0)&mask
  out[name]={'maxRGBA':dd.max(axis=0).tolist(),'alphaDifferentPixels':int(alpha.sum()),'RGBOver1Pixels':int(bad.sum()),'RGBOver1Bounds':bounds(bad),'alphaDifferenceBounds':bounds(alpha),'roiBounds':bounds(mask)}
 return out
native=[]
for d in rots:
 mm=masks(d,896,1216)
 for i in range(25):
  ims={k:np.array(Image.open(O/k/f'running-{d}-{i:02}.png').convert('RGBA')) for k in ['independent','connected','unbroken']}
  native.append({'direction':d,'index':i,**{f'{a}Vs{b.title()}':stats(ims[a],ims[b],mm) for a,b in [('independent','connected'),('connected','unbroken'),('independent','unbroken')]}})
(O/'native-localized-proof.json').write_text(json.dumps({'cases':native,'method':'Exact fullRGBA plus separately localized actual incoming/outgoing plane ROIs, every phase including closure. Bounds are destinationpixel inclusive.'},indent=2))
for kind,record,key in [('consumer','cases.json','evidence'),('godot-consumer','render-record.json','captures')]:
 C=O/kind
 if not (C/record).exists():continue
 cfg=json.loads((C/record).read_text());groups={}
 for e in cfg[key]:
  stem=e['case'] if kind=='consumer' else f"{e['direction']}-{e['pitch']}-f{e['index']}-{e['background']}-{e['origin']}"
  groups.setdefault(stem,{})[e['mode']]=e
 rows=[]
 for stem,group in groups.items():
  e=group['independent'];ims={}
  for mode in ['independent','connected','unbroken']:
   f=C/(f'{stem}-{mode}.png' if kind=='consumer' else group[mode]['path']);ims[mode]=np.array(Image.open(f).convert('RGBA'))
  h,w=ims['independent'].shape[:2];mm=masks(e['direction'],w,h)
  row={'case':stem,'direction':e['direction'],'pitch':e['pitch'],**{f'{a}Vs{b.title()}':stats(ims[a],ims[b],mm) for a,b in [('independent','connected'),('connected','unbroken'),('independent','unbroken')]}};rows.append(row)
  # Exact channel residual and an alpha-visible amplified QA map, separately retained.
  folder=C/'residuals';folder.mkdir(exist_ok=True)
  diff=np.abs(ims['independent'].astype(int)-ims['unbroken'].astype(int)).astype('uint8');Image.fromarray(diff).save(folder/f'{stem}-fullRGBA.png')
  vis=np.zeros_like(diff);vis[:,:,:3]=np.minimum(diff[:,:,:3].astype(int)*16,255);vis[:,:,3]=np.where(np.any(diff>0,axis=2),255,0);Image.fromarray(vis).save(folder/f'{stem}-visible16x.png')
 summary={}
 for pitch in [128,55,32,47.3]:
  rr=[r for r in rows if r['pitch']==pitch];summary[str(pitch)]={}
  for pair in ['independentVsConnected','connectedVsUnbroken','independentVsUnbroken']:
   summary[str(pitch)][pair]={'cases':len(rr),**{roi:{'maxRGBA':np.array([r[pair][roi]['maxRGBA'] for r in rr]).max(axis=0).tolist(),'alphaDifferentPixels':sum(r[pair][roi]['alphaDifferentPixels'] for r in rr),'RGBOver1Pixels':sum(r[pair][roi]['RGBOver1Pixels'] for r in rr)} for roi in ['full','incoming','outgoing']}}
 (O/f'{kind}-metrics.json').write_text(json.dumps({'summaryByPitch':summary,'cases':rows,'method':'Actual consumer PNG absolute fullRGBA residuals; exact source join planes uniformly mapped with2px conservative filtering margin. Transparent Godot readback is premultipliedRGB. All origins/backgrounds retained. No average or tolerance waiver.'},indent=2))
 print(kind,json.dumps(summary))
