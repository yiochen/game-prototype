from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,hashlib,math,sys,shutil
P=Path('prototypes/sushi-loop/assets/refinement/objects')/sys.argv[1];O=P/'candidates/round-01';S=O/'supplemental-browser-02';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();cfg=json.loads((S/'cases.json').read_text());v=json.loads((O/'validation.json').read_text());rots={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def masks(d,w,h):
 r=rots[d];out={}
 for name,p in v['ports']['S'].items():
  if name=='deck':continue
  nx,ny=round(p['world'][0]*2),round(p['world'][1]*2);tx,ty=-ny,nx;pts=[];im=Image.new('L',(896,1216));dr=ImageDraw.Draw(im)
  for a in [-.48,.48]:
   for delta in [-.014,.014]:
    for z in [.505,.695]:
     x,y=nx*(.5+delta)+tx*a,ny*(.5+delta)+ty*a;xx=x*math.cos(r)-y*math.sin(r);yy=x*math.sin(r)+y*math.cos(r);pts.append((448+256*xx,752-256*yy-z*179.2))
  dr.rectangle((min(x for x,y in pts)-1,min(y for x,y in pts)-1,max(x for x,y in pts)+1,max(y for x,y in pts)+1),fill=255);out[name]=np.array(im.resize((w,h),Image.Resampling.BOX).filter(ImageFilter.MaxFilter(5)))>0
 return out
groups={}
for e in cfg['evidence']:groups.setdefault(e['case'],{})[e['mode']]=e
rows=[]
for key,g in groups.items():
 e=g['independent'];ims={m:np.array(Image.open(S/f'{key}-{m}.png').convert('RGBA')) for m in g};h,w=ims['independent'].shape[:2];mm=masks(e['direction'],w,h);diff=np.abs(ims['independent'].astype(int)-ims['unbroken'].astype(int));local={}
 for name,mask in mm.items():local[name]={'maximumRGBA':diff[mask].max(axis=0).tolist(),'alphaDifferentPixels':int((diff[:,:,3][mask]>0).sum()),'RGBOver1Pixels':int(np.any(diff[:,:,:3][mask]>1,axis=1).sum())}
 rows.append({'case':key,'direction':e['direction'],'pitch':e['pitch'],'fullMaximumRGBA':diff.max(axis=(0,1)).tolist(),'ports':local})
report={'asset':P.name,'originalPacketSHA256':sha(O/'packet.json'),'cases':len(groups),'modeCases':len(cfg['evidence']),'allStableNonblankNoReloadPainted':all(x['stable'] and x['nonblank'] and x['noReload'] and x['painted'] for x in cfg['evidence']),'pageErrors':cfg['errors'],'navigationCount':sum(e['event']=='main-navigation' for e in cfg['events']),'expectedExplicitNavigations':len(cfg['evidence'])+1,'maximumJoinRGBA':np.array([s['maximumRGBA'] for r in rows for s in r['ports'].values()]).max(axis=0).tolist(),'joinAlphaDifferentPixels':sum(s['alphaDifferentPixels'] for r in rows for s in r['ports'].values()),'joinRGBOver1Pixels':sum(s['RGBOver1Pixels'] for r in rows for s in r['ports'].values()),'actualRows':rows,'interpretation':'The initial blank was not reproduced in this properlyisolated stablepage run. No cause is inferred for the old missingSVG readback. Each mode retained its first screenshot before any actualcanvasreadback and two repeats; screenshot/nativecanvas hashes/paintcall signatures/currentURLs were stable. No renderer,source,asset or pixel changes.'};assert report['allStableNonblankNoReloadPainted'] and not report['pageErrors'];assert report['joinAlphaDifferentPixels']==0 and report['joinRGBOver1Pixels']==0
(S/'metrics.json').write_text(json.dumps(report,indent=2));shutil.copyfile(Path(__file__).with_name('isolated_consumer.mjs'),S/'capture-harness.mjs');files={f.relative_to(S).as_posix():{'path':f.relative_to(S).as_posix(),'sha256':sha(f)} for f in sorted(S.rglob('*')) if f.is_file() and f.name!='supplemental-packet.json'};packet={'schemaVersion':1,'asset':P.name,'method':'immutable-supplemental-evidence','originalPacketSHA256':sha(O/'packet.json'),'files':files,'metrics':'metrics.json'};assert not(S/'supplemental-packet.json').exists();(S/'supplemental-packet.json').write_text(json.dumps(packet,indent=2));print(json.dumps({'asset':P.name,'supplementalPacketSHA256':sha(S/'supplemental-packet.json'),'metricsSHA256':sha(S/'metrics.json'),'summary':{k:report[k] for k in ['cases','modeCases','allStableNonblankNoReloadPainted','navigationCount','maximumJoinRGBA','joinAlphaDifferentPixels','joinRGBOver1Pixels']}}))
