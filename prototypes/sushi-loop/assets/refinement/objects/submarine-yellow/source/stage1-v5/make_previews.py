from pathlib import Path
from PIL import Image,ImageDraw
import json
H=Path(__file__).resolve().parent;B=H.parents[1];O=B/'candidates/stage1-v5'
sheet=Image.new('RGB',(1280,824),(41,46,51));d=ImageDraw.Draw(sheet)
for row,clip in enumerate(['dock-ready','upgraded-dock-ready']):
 for col,di in enumerate(['N','E','S','W']):
  im=Image.open(O/(clip+'-'+di+'.png')).convert('RGBA').resize((320,384),Image.Resampling.NEAREST);sheet.paste(im,(col*320,row*412+24),im);d.text((col*320+8,row*412+5),di+' | '+('BODY PRELIMINARY' if row==0 else 'PROVISIONAL EQUIPMENT'),fill=(240,240,240))
sheet.save(O/'stage1-four-view-logical.png')
j=json.loads((O/'component-projection-feasibility.json').read_text());im=Image.new('RGB',(1024,1280),(245,246,248));d=ImageDraw.Draw(im)
d.text((14,10),'TECHNICAL PROJECTION | fixed standalone logical192x352 / root96,248 / 55deg',fill='black');d.text((14,28),'Gray: original native mesh bbox | Blue: provisional mesh bbox | Orange: proposed reservation',fill='black')
for row,c in enumerate(j['components']):
 for col,di in enumerate(['N','E','S','W']):
  ox=col*256+32;oy=row*406+66;d.rectangle((ox,oy,ox+192,oy+352),outline=(50,50,50),width=1);d.text((ox,oy-17),c['asset']+' '+di,fill='black')
  for kind,color in [('originalSourceMesh',(120,120,120)),('proposedReservationBox',(222,130,30)),('provisionalMesh',(0,135,205))]:
   r=next(x for x in c['projection'] if x['kind']==kind and x['direction']==di);(x0,y0),(x1,y1)=r['logicalBounds'];d.rectangle((ox+x0,oy+y0,ox+x1,oy+y1),outline=color,width=2)
  d.line((ox+91,oy+248,ox+101,oy+248),fill=(20,20,20),width=1);d.line((ox+96,oy+243,ox+96,oy+253),fill=(20,20,20),width=1)
im.save(O/'component-projection-feasibility.png')
family=Image.new('RGB',(1280,1536),(41,46,51));d=ImageDraw.Draw(family)
for i,di in enumerate(['N','E','S','W']):
 im=Image.open(O/('family-PROVISIONAL-'+di+'.png')).convert('RGBA').resize((640,768),Image.Resampling.NEAREST);family.paste(im,((i%2)*640,(i//2)*768),im);d.text(((i%2)*640+8,(i//2)*768+8),di+' | NATIVE FAMILY / PROVISIONAL EQUIPMENT',fill='white')
family.save(O/'stage1-family-four-view.png')
