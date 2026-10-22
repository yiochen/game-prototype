"""Whole-canvas publication and evidence only; never edits rendered image pixels.
Uses BOX for uniform complete-frame native4x→published2x. Other outputs are
labeled preview composites/resizes. No crop, alpha repair, warp or pixel patch.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib,shutil,math
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-02';PRE=OUT/'previews';PRE.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def residual(a,b):
 assert a.size==b.size
 aa=a.convert('RGBA');bb=b.convert('RGBA');diff=ImageChops.difference(aa,bb);hist=diff.histogram();n=a.width*a.height
 maximum=[max(i for i,c in enumerate(hist[k*256:(k+1)*256]) if c) for k in range(4)]
 mean=[sum(i*c for i,c in enumerate(hist[k*256:(k+1)*256]))/n for k in range(4)]
 return {'size':list(a.size),'RGBAarrayEqual':aa.tobytes()==bb.tobytes(),'maxAbsoluteDeltaRGBA':maximum,'meanAbsoluteDeltaRGBA':mean,'changedPixelCount':sum(1 for p in diff.getdata() if any(p)),'alphaChangedPixels':sum(1 for p in diff.getdata() if p[3])}
raw=[];atlases=[];publication={};replay={}
for d in 'NESW':
 p=OUT/f'native-static-{d}.png';im=Image.open(p).convert('RGBA');pub=im.resize((384,704),Image.Resampling.BOX)
 for folder in ['published','atlases','raw/static-'+d]:(OUT/folder).mkdir(exist_ok=True,parents=True)
 pp=OUT/f'published/static-{d}.png';pub.save(pp);rr=OUT/f'raw/static-{d}/000.png';shutil.copy2(pp,rr);at=OUT/f'atlases/static-{d}.png';shutil.copy2(pp,at)
 raw.append({'clip':'static','direction':d,'index':0,'path':str(rr.relative_to(BASE)),'sha256':sha(rr)})
 atlases.append({'clip':'static','direction':d,'path':str(at.relative_to(BASE)),'sha256':sha(at),'columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]],'fps':12,'loop':False,'static':True,'frameOrder':[0]})
 publication[d]=residual(pub,Image.open(at))
 rp=OUT/f'replay/native-{d}.png'
 if rp.exists():replay[d]=residual(im,Image.open(rp))
# Whole complete frames on gray, ivory, dark at native/published/logical/phone cell pitch.
sheets=[]
for name,size,pitch in [('native',(768,1408),512),('published',(384,704),256),('logical',(192,352),128),('phone',(48,88),32),('landscape',(71,130),47.3)]:
 for bg in ['808080','f5f2e9','182231']:
  w,h=size;sheet=Image.new('RGB',(w*4,h+24),'#'+bg);dr=ImageDraw.Draw(sheet)
  for i,d in enumerate('NESW'):
   im=Image.open(OUT/f'native-static-{d}.png').convert('RGBA')
   if im.size!=size:im=im.resize(size,Image.Resampling.BOX if name in ['published','logical'] else Image.Resampling.LANCZOS)
   sheet.paste(im,(i*w,24),im);dr.text((i*w+3,5),f'{d} {name}',fill='white' if bg!='f5f2e9' else '#182231')
  p=PRE/f'standalone-{name}-{bg}.png';sheet.save(p);sheets.append({'path':str(p.relative_to(BASE)),'kind':'standalone-all4','frameSize':list(size),'directions':list('NESW'),'cellPitch':pitch,'method':'complete frames uniformly resized and alpha composited to background; labels outside bounds'})
shutil.copy2(PRE/'standalone-published-808080.png',PRE/'four-view-sheet.png')
# Native assembly sheets; original complete frames retained, sheets use whole BOX reduction.
for bg in ['808080','f5f2e9','182231']:
 sheet=Image.new('RGB',(640*4,960+24),'#'+bg);dr=ImageDraw.Draw(sheet)
 for i,d in enumerate('NESW'):
  im=Image.open(OUT/f'joined-native-{d}.png').convert('RGBA').resize((640,960),Image.Resampling.BOX);sheet.paste(im,(i*640,24),im);dr.text((i*640+4,5),f'{d} source pair, complete4x frame BOX2x',fill='white' if bg!='f5f2e9' else '#182231')
 p=PRE/f'joined-native-{bg}.png';sheet.save(p);sheets.append({'path':str(p.relative_to(BASE)),'kind':'native-source-join-all4','directions':list('NESW'),'method':'complete native assembly frames uniformly BOX4x→2x, alpha composite only'})
(OUT/'publication-and-replay-residuals.json').write_text(json.dumps({'publication':publication,'renderOnlyReopen':replay,'method':'Raw complete RGBA arrays; no image modifications other than documented wholeBOX publication'},indent=2)+'\n')
(OUT/'frame-records.json').write_text(json.dumps({'rawFrames':raw,'atlases':atlases,'nativeFrames':[{'clip':'static','direction':d,'index':0,'path':str((OUT/f'native-static-{d}.png').relative_to(BASE)),'sha256':sha(OUT/f'native-static-{d}.png'),'frameSize':[768,1408],'captureScale':4} for d in 'NESW']},indent=2)+'\n')
(OUT/'preview-manifest.json').write_text(json.dumps({'sheets':sheets,'aliasFourViewSheet':'previews/four-view-sheet.png'},indent=2)+'\n')
print(json.dumps({'published':len(atlases),'nativeReplaysCompared':len(replay),'previews':len(sheets)}))
