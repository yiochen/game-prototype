from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib,math
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-01';C=O/'consumer'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def arr(p):return np.asarray(Image.open(p).convert('RGBA'))
def comp(a,bg=(128,128,128)):
 f=a[...,3:4]/255;return a[...,:3]*f+np.array(bg)*(1-f)
def stats(d,m=None):
 v=d if m is None else d[m]
 if not v.size:return {'pixels':0,'max':0,'mean':0,'p99':0,'pixelsOver5':0}
 v=v.reshape(-1,v.shape[-1]);return {'pixels':int(len(v)),'max':float(v.max()),'mean':float(v.mean()),'p99':float(np.percentile(v,99)),'pixelsOver5':int(np.count_nonzero(v.max(axis=1)>5))}
profile=[[-.5,0],[.5,0],[.5,.67],[.45,1.04],[.31,1.15],[-.31,1.15],[-.45,1.04],[-.5,.67]]
def maskFor(d,pitch,phase,shape):
 m=Image.new('1',(shape[1],shape[0]),0);dr=ImageDraw.Draw(m);sc=pitch/128;px,py=phase
 for cut in [-.5,.5]:
  ps=[]
  for y,z in profile:
   wx,wy={'S':(cut,y),'N':(-cut,-y),'E':(-y,cut),'W':(y,-cut)}[d];ps.append(((224+128*wx)*sc+px,(384-128*wy-89.6*z)*sc+py))
  if d in 'NS':
   x=ps[0][0];ys=[p[1] for p in ps];dr.rectangle((math.floor(x)-1,math.ceil(min(ys))+2,math.floor(x)+1,math.floor(max(ys))-2),fill=1)
  else:dr.polygon(ps,fill=1)
 return np.asarray(m).astype(bool)
# Exact native independently captured mixed assembly, roots at -1/0/+1 cells.
native={}
for d in 'NESW':
 output=Image.new('RGBA',(1792,2432));vertical=d in 'EW';sign={'S':1,'N':-1,'E':-1,'W':1}[d]
 for i in sorted([-1,0,1],reverse=(sign<0 and vertical)):
  f=O/f'native-static-{d}.png' if i==0 else O/'middle-replay'/f'native-static-{d}.png'
  im=Image.open(f).convert('RGBA');dx=0 if vertical else i*512*sign;dy=i*512*sign if vertical else 0;output.alpha_composite(im,(896+dx-384,1536+dy-1024))
 output.save(O/f'independent-native-{d}.png');a=np.asarray(output);b=arr(O/f'connected-native-{d}.png');m=maskFor(d,512,[0,0],a.shape);native[d]={'whole':stats(abs(comp(a)-comp(b))),'projectedBothJoinRegion':stats(abs(comp(a)-comp(b)),m),'alphaMax':int(abs(a[...,3].astype(int)-b[...,3].astype(int)).max())}
# Reopen exact final source twice. Canonical bytes come from first relocated replay.
replay={}
for d in 'NESW':
 a=arr(O/f'native-static-{d}.png');b=arr(O/'replay-verify'/f'native-static-{d}.png');dif=abs(a.astype(int)-b.astype(int));replay[d]={'exactRGBA':bool(np.array_equal(a,b)),'maxChannelDelta':int(dif.max()),'canonicalSHA256':sha(O/f'native-static-{d}.png'),'replaySHA256':sha(O/'replay-verify'/f'native-static-{d}.png')}
# Validate exact approved middle publication bytes against render-only replay from input dependency.
family={}
for d in 'NESW':
 im=Image.open(O/'middle-replay'/f'native-static-{d}.png').convert('RGBA').resize((384,704),Image.Resampling.BOX);a=np.asarray(im);b=arr(B/'inputs/approved-middle'/f'published-{d}.png');family[d]={'exactRGBA':bool(np.array_equal(a,b)),'maxChannelDelta':int(abs(a.astype(int)-b.astype(int)).max())}
frameAudit={}
for d in 'NESW':
 frameAudit[d]={}
 for scale,name in [(4,'native-static'),(2,'raw-static')]:
  im=Image.open(O/f'{name}-{d}.png').convert('RGBA');aa=np.asarray(im)[...,3];border=np.concatenate([aa[0,:],aa[-1,:],aa[:,0],aa[:,-1]]);frameAudit[d][str(scale)]={'dimensions':list(im.size),'alphaBBox':list(im.getchannel('A').getbbox()),'borderAlphaMax':int(border.max()),'maxAlpha':int(aa.max()),'transparentPixelCount':int(np.count_nonzero(aa==0))}
data=json.loads((C/'cases.json').read_text());records=[]
for e in data['evidence']:
 if e['mode']!='independent':continue
 stem=e['case'];a=arr(C/(stem+'-independent.png'));b=arr(C/(stem+'-connected.png'));m=maskFor(e['direction'],e['pitch'],[e['phaseX'],e['phaseY']],a.shape);opaque=m&(b[...,3]>=250)&(a[...,3]>=250);expected=m&(b[...,3]>=250);delta=abs(comp(a)-comp(b));ad=abs(a[...,3].astype(int)-b[...,3].astype(int));fg=b[...,3]>0
 records.append({'case':stem,'direction':e['direction'],'pitch':e['pitch'],'phase':[e['phaseX'],e['phaseY']],'background':e['background'],'size':[a.shape[1],a.shape[0]],'whole':stats(delta),'projectedBothJoinRegion':stats(delta,m),'opaqueBothJoinRegion':stats(delta,opaque),'alphaMax':int(ad.max()),'opaqueReferenceJoinAlphaMax':int(ad[expected].max()) if expected.any() else 0,'independentAlphaMinAtOpaqueReferenceJoin':int(a[...,3][expected].min()) if expected.any() else None,'worldRasterReady':e['worldRaster']['ready'],'worldRasterError':e['worldRaster']['error'],'independentSHA256':sha(C/(stem+'-independent.png')),'connectedSHA256':sha(C/(stem+'-connected.png'))})
gray=[r for r in records if r['background']=='#808080'];keep=set()
for d in 'NESW':
 for pitch in [128,32]:keep.add(max([r for r in gray if r['direction']==d and r['pitch']==pitch],key=lambda r:(r['opaqueBothJoinRegion']['max'],r['whole']['mean']))['case'])
keep.add(max([r for r in gray if r['pitch']==47.3],key=lambda r:r['whole']['max'])['case'])
for bg in ['#f5f2e9','#182231','transparent']:keep.add(max([r for r in records if r['background']==bg],key=lambda r:r['whole']['max'])['case'])
worst=max(gray,key=lambda r:(r['whole']['max'],r['whole']['mean']));keep.add(worst['case'])
# Compact representative/worst context, and all four actual phone cases at their actual cell pitch.
stem=worst['case'];a=Image.open(C/(stem+'-independent.png')).convert('RGB');b=Image.open(C/(stem+'-connected.png')).convert('RGB');sheet=Image.new('RGB',(a.width*2,a.height+52),'#f5f2e9');sheet.paste(a,(0,52));sheet.paste(b,(a.width,52));ImageDraw.Draw(sheet).text((8,8),stem+' actual SpriteScene',fill='#243c52');ImageDraw.Draw(sheet).text((8,26),'Mixed independent | native reference',fill='#243c52');sheet.save(O/'consumer-worst-comparison.png')
sheet=Image.new('RGB',(640,4*180),'#f5f2e9');dr=ImageDraw.Draw(sheet)
for row,d in enumerate('NESW'):
 r=max([r for r in gray if r['direction']==d and r['pitch']==32],key=lambda r:r['opaqueBothJoinRegion']['max']);stem=r['case'];a=Image.open(C/(stem+'-independent.png')).convert('RGB');b=Image.open(C/(stem+'-connected.png')).convert('RGB');yy=row*180;dr.text((8,yy+8),stem+' actual32px: independent / native',fill='#243c52');sheet.paste(a,(8,yy+24));sheet.paste(b,(130,yy+24));sheet.paste(a.crop((0,45,112,115)).resize((224,140),Image.Resampling.NEAREST),(260,yy+24))
sheet.save(O/'consumer-phone-four-view.png')
for r in records:r['screenshotsRetained']=r['case'] in keep
retained=[e for e in data['evidence'] if e['case'] in keep];(C/'retained-dom-evidence.json').write_text(json.dumps(retained,indent=2))
for p in C.glob('*.png'):
 if p.name.rsplit('-',1)[0] not in keep:p.unlink()
for e in data['evidence']:
 for k in ['placements','bounds']:e.pop(k,None)
(C/'cases.json').write_text(json.dumps(data,indent=2))
summary={'cases':len(records),'allWorldRasterReady':all(r['worldRasterReady']=='true' and not r['worldRasterError'] for r in records),'errors':data['errors'],'dependenciesUnchanged':data['dependenciesUnchanged'],'maxWholeRGBDelta':max(r['whole']['max'] for r in records),'maxOpaqueJoinRGBDelta':max(r['opaqueBothJoinRegion']['max'] for r in records),'maxOpaqueReferenceJoinAlphaDelta':max(r['opaqueReferenceJoinAlphaMax'] for r in records if r['background']=='transparent'),'retainedPairs':len(keep),'worstWhole':worst,'interpretation':'Separate finite Cycles sample grids and alpha antialiasing produce sparse residuals. Full-image and projected/opaque connector metrics remain explicit; inspect representative worst captures. No automatic score or approval threshold.'}
metrics={'asset':'rock-wall-edge','round':1,'replay':replay,'approvedFamilyReplay':family,'frameAudit':frameAudit,'nativeMixedAssembly':native,'consumer':summary,'dependencies':data['dependencies'],'caseMetrics':records};(O/'metrics.json').write_text(json.dumps(metrics,indent=2));print(json.dumps({k:v for k,v in metrics.items() if k!='caseMetrics'},indent=2))
