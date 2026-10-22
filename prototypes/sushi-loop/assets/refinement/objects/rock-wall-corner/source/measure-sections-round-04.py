from pathlib import Path
import math,json
from PIL import Image,ImageDraw
import numpy as np
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-04';P=O/'previews'
DIR={'N':180,'E':90,'S':0,'W':-90};rows=[]
for d,deg in DIR.items():
 r=math.radians(deg);c=math.cos(r);s=math.sin(r);a=np.asarray(Image.open(O/f'published-native-joined-{d}.png').convert('RGBA'));b=np.asarray(Image.open(O/f'independent-published-joined-{d}.png').convert('RGBA'))
 for port in ['W','N']:
  normal=(c,-s) if port=='W' else (-s,-c)
  for kind,t,z in [('crown',0,1.15),('side-negative',-.5,.35),('side-positive',.5,.35),('ground-negative',-.5,0),('ground-positive',.5,0)]:
   x,y=(-.5,t) if port=='W' else (-t,.5);xx=c*x-s*y;yy=s*x+c*y;cx=round(448+256*xx);cy=round(768-256*yy-179.20008*z)
   section=[]
   for k in range(-8,9):
    px=round(cx+k*normal[0]);py=round(cy+k*normal[1]);section.append({'offsetPublishedPx':k,'pixel':[px,py],'nativeRGBA':a[py,px].tolist(),'independentRGBA':b[py,px].tolist(),'residualRGBA':(b[py,px].astype(int)-a[py,px].astype(int)).tolist()})
   rows.append({'direction':d,'port':port,'kind':kind,'profileTransverse':t,'height':z,'centerPublishedPx':[cx,cy],'crossSection':section})
(O/'side-alpha-cross-sections.json').write_text(json.dumps({'method':'Actual pixels at both exposed profile side limits, crown and ground silhouette; every four-way assembly rotation. Fully opaque samples preserve RGB residual; ground/occluded samples preserve actual alpha and are not relabeled as exposed. No pixel correction.','samples':rows},indent=2)+'\n')
# Four meaningful visible lower-side join crops, native and independent, plus actual alpha coverage.
choose={'S':('W','side-negative'),'N':('W','side-positive'),'E':('N','side-negative'),'W':('N','side-positive')};sheet=Image.new('RGB',(4*352,420),(144,149,156));dr=ImageDraw.Draw(sheet)
for i,d in enumerate(DIR):
 port,kind=choose[d];row=next(p for p in rows if p['direction']==d and p['port']==port and p['kind']==kind);x,y=row['centerPublishedPx'];box=(x-28,y-28,x+28,y+28)
 for j,(name,path) in enumerate([('native',O/f'published-native-joined-{d}.png'),('independent',O/f'independent-published-joined-{d}.png')]):
  im=Image.open(path).convert('RGBA');crop=im.crop(box).resize((168,168),Image.Resampling.NEAREST);back=Image.new('RGBA',crop.size,(144,149,156,255));back.alpha_composite(crop);sheet.paste(back.convert('RGB'),(i*352+j*176,30));dr.text((i*352+j*176+4,8),f'{d} {port} lower {name}',fill='black')
  ground=next(p for p in rows if p['direction']==d and p['port']==port and p['kind']==kind.replace('side','ground'));gx,gy=ground['centerPublishedPx'];gc=im.crop((gx-28,gy-28,gx+28,gy+28)).getchannel('A').resize((168,168),Image.Resampling.NEAREST);sheet.paste(gc.convert('RGB'),(i*352+j*176,240));dr.text((i*352+j*176+4,218),f'{d} {port} ground alpha {name}',fill='black')
sheet.save(P/'lower-side-and-ground-alpha.png')
