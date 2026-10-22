import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageChops
BASE=Path(__file__).resolve().parent;E=BASE/'evidence';D=json.loads((E/'consumer-report.json').read_text());BGS={'light':'#f2eee5','gray':'#808080','dark':'#182536'}
def comp(im,bg):
 out=Image.new('RGBA',im.size,bg);out.alpha_composite(im);return out.convert('RGB')
# Whole logical panels with a fixed crop that contains all source facings; phone is entire registered frame.
c=Image.new('RGB',(1180,910),'#ddd6cb');draw=ImageDraw.Draw(c)
for j,d in enumerate(['N','E','S','W']):
 im=Image.open(E/'packed'/('single-'+d)/'sheet.png').convert('RGBA')
 for k,(name,bg) in enumerate(BGS.items()):
  x=10+j*294;y=30+k*290;draw.text((x,y-16),d+' '+name+' logical128 / phone32',fill='black')
  c.paste(comp(im.resize((192,352),Image.Resampling.LANCZOS).crop((0,110,192,352)),bg),(x,y))
  c.paste(comp(im.resize((48,88),Image.Resampling.LANCZOS),bg),(x+202,y+100))
draw.text((10,900),'Logical fixed crop(0,110,192,352); phone whole48x88. All source content retained. Prior clipped contact retained as failed evidence.',fill='black');c.save(E/'single-all4-use-size-v2.png')
seams=[]
for d in ['N','E','S','W']:
 c=Image.new('RGB',(1420,740),'#ddd6cb');draw=ImageDraw.Draw(c)
 rect=(12,282,460,462) if d in 'NS' else (162,162,310,582)
 for bi,(bn,bg) in enumerate(BGS.items()):
  x=10+bi*470;draw.text((x,8),d+' '+bn+' phase0: native / independent',fill='black')
  r=next(r for r in D['records'] if r['direction']==d and r['zoom']==1 and r['phase']==0)
  for ki,kind in enumerate(['native','independent']):
   im=Image.open(E/r['images'][kind]).convert('RGBA').crop(rect)
   px=x+(ki*160 if d in 'EW' else 0);py=30+(0 if d in 'EW' else ki*200)
   draw.text((px,py-12),kind,fill='black');c.paste(comp(im,bg),(px,py))
  r=next(r for r in D['records'] if r['direction']==d and r['zoom']==.25 and r['phase']==0)
  for ki,kind in enumerate(['native','independent']):
   im=Image.open(E/r['images'][kind]).convert('RGBA');c.paste(comp(im,bg),(x+ki*150,500));draw.text((x+ki*150,480),'phone32 '+kind,fill='black')
 draw.text((10,715),'Logical128 panels use common fixed strips; phone32 entire common canvas. Native is actual3module geometry; independent uses actual consumer.',fill='black');c.save(E/('connection-'+d+'-use-size.png'))
 # Fractional local seams, both joins, all phases/backdrops/zooms. Rects deliberately fixed from native projected port bands.
 c=Image.new('RGB',(1560,1650),'#ddd6cb');draw=ImageDraw.Draw(c)
 for zi,z in enumerate([1,.25]):
  rects=([(166,310,178,440),(294,310,306,440)] if d in 'NS' else [(190,278,282,328),(190,406,282,456)]) if z==1 else ([(47,84,57,126),(79,84,89,126)] if d in 'NS' else [(58,77,82,94),(58,109,82,126)])
  for bi,(bn,bg) in enumerate(BGS.items()):
   y=20+(zi*3+bi)*265
   for pi,phase in enumerate([0,.25,.5,.75]):
    r=next(r for r in D['records'] if r['direction']==d and r['zoom']==z and r['phase']==phase);x=10+pi*390
    draw.text((x,y),f'{d} cell{int(128*z)} {bn} p{phase} native / independent',fill='black')
    for ki,kind in enumerate(['native','independent']):
     im=Image.open(E/r['images'][kind]).convert('RGBA');left=x+ki*192
     for ji,rect0 in enumerate(rects):
      crop=im.crop(rect0);mag=1 if z==1 and d in 'NS' else 1 if z==1 else 3
      crop=crop.resize((crop.width*mag,crop.height*mag),Image.Resampling.NEAREST);c.paste(comp(crop,bg),(left+(ji*94 if d in 'EW' else ji*40),y+22))
    # Technical residuals restricted to full-native opaque samples inside these fixed projected seam bands.
    a=Image.open(E/r['images']['independent']).convert('RGBA');b=Image.open(E/r['images']['native']).convert('RGBA');vals=[];rgb=[]
    for box in rects:
     for yy in range(box[1],min(box[3],a.height)):
      for xx in range(box[0],min(box[2],a.width)):
       aa=a.getpixel((xx,yy));bb=b.getpixel((xx,yy))
       if bb[3]==255:
        vals.append(aa[3]);rgb.append(max(abs(aa[k]-bb[k]) for k in range(3)))
    seams.append({'direction':d,'zoom':z,'phase':phase,'rectangles':rects,'nativeOpaqueSamples':len(vals),'minIndependentAlphaOnNativeOpaque':min(vals) if vals else None,'deficientAlphaSamples':sum(v<255 for v in vals),'maxRGBDelta':max(rgb) if rgb else None})
 draw.text((10,1630),'Each pair shows both fixed projected port bands. Phone crops ×3nearest for visibility; logical128 crops retain use-size.',fill='black');c.save(E/('fractional-seams-'+d+'.png'))
# Dedup because backgrounds repeat identical raw-alpha checks.
seams=[s for i,s in enumerate(seams) if s not in seams[:i]]
(E/'local-seam-residuals.json').write_text(json.dumps(seams,indent=2)+'\n');print('worst',min(s['minIndependentAlphaOnNativeOpaque'] for s in seams));print([(d,min(s['minIndependentAlphaOnNativeOpaque'] for s in seams if s['direction']==d),sum(s['deficientAlphaSamples'] for s in seams if s['direction']==d)) for d in 'NESW'])
