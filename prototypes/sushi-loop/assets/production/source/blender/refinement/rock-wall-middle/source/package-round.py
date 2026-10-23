from PIL import Image,ImageDraw,ImageFont,ImageChops
from pathlib import Path
import json,hashlib,math
BASE=Path(__file__).resolve().parents[1];rnd='round-03';OUT=BASE/'candidates'/rnd
D=['N','E','S','W'];BGS={'light':'#f5f2e9','gray':'#808080','dark':'#182231'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def label(im,text):
 a=Image.new('RGB',(im.width,im.height+26),'#f5f2e9');a.paste(im,(0,26));ImageDraw.Draw(a).text((8,6),text,fill='#243c52');return a
for d in D:
 im=Image.open(OUT/f'native-static-{d}.png').convert('RGBA');im.resize((384,704),Image.Resampling.BOX).save(OUT/f'raw-static-{d}.png');im.resize((384,704),Image.Resampling.BOX).save(OUT/f'atlas-static-{d}.png')
 Image.open(OUT/f'connected-native-{d}.png').convert('RGBA').resize((896,1216),Image.Resampling.BOX).save(OUT/f'connected-published-{d}.png')
for key,bg in BGS.items():
 canv=Image.new('RGB',(4*230,430),bg)
 for i,d in enumerate(D):
  im=Image.open(OUT/f'raw-static-{d}.png').convert('RGBA');im=im.resize((192,352),Image.Resampling.BOX)
  canv.paste(im,(i*230+19,40),im);ImageDraw.Draw(canv).text((i*230+10,12),d+' logical 128px',fill='white' if key=='dark' else '#243c52')
  ph=im.resize((48,88),Image.Resampling.BOX);canv.paste(ph,(i*230+178,330),ph)
 canv.save(OUT/f'four-view-{key}.png')
 # Repeat independently from exact published PNG pixels at logical/native locked positions; not browser proof.
 sheet=Image.new('RGB',(2*448,2*608+34),bg);dr=ImageDraw.Draw(sheet)
 for n,d in enumerate(D):
  independent=Image.new('RGBA',(1792,2432));vertical=d in ['E','W'];sgn={'S':1,'N':-1,'E':-1,'W':1}[d]
  frame=Image.open(OUT/f'native-static-{d}.png').convert('RGBA')
  for i in sorted([-1,0,1],reverse=(sgn<0 and vertical)):
   dx=0 if vertical else i*512*sgn;dy=i*512*sgn if vertical else 0
   independent.alpha_composite(frame,(896+dx-384,1536+dy-1024))
  independent.save(OUT/f'independent-native-{d}.png')
  connected=Image.open(OUT/f'connected-native-{d}.png').convert('RGBA')
  ix=(n%2)*448;iy=(n//2)*608+34
  small=independent.resize((448,608),Image.Resampling.BOX);sheet.paste(small,(ix,iy),small);dr.text((ix+7,iy+4),d+' independent 128px',fill='white' if key=='dark' else '#243c52')
 sheet.save(OUT/f'repeated-{key}.png')
# Full 2x four-view hero and fixed-source/target comparison without altering candidate output.
hero=Image.new('RGB',(1536,740),'#eceae3');draw=ImageDraw.Draw(hero)
for i,d in enumerate(D):
 im=Image.open(OUT/f'raw-static-{d}.png').convert('RGBA');hero.paste(im,(i*384,28),im);draw.text((i*384+16,8),d+' published 2x',fill='#243c52')
hero.save(OUT/'four-view-enlarged.png')
print('packaged',OUT)
