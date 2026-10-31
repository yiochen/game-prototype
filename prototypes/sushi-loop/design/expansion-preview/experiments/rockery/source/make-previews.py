"""Preview-only contact sheets. Native frames remain untouched."""
import json,sys,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
folder=Path(sys.argv[1]).resolve()
sheet=Image.new('RGBA',(768,384),(0,0,0,0));draw=ImageDraw.Draw(sheet)
for i,direction in enumerate(['N','E','S','W']):
 im=Image.open(folder/f'static-{direction}.png').convert('RGBA')
 sheet.alpha_composite(im.resize((192,352),Image.Resampling.LANCZOS),(i*192,32))
 draw.text((i*192+92,10),direction,fill='#c9d3df')
sheet.save(folder/'four-view-sheet.png')
phone=Image.new('RGBA',(800,880),(0,0,0,0));draw=ImageDraw.Draw(phone)
if (folder/'phone-edge.png').exists() and (folder/'phone-corner.png').exists():
 for x,name,label in [(0,'phone-edge.png','Native edge · default phone camera x1.25'),(410,'phone-corner.png','Native corner · default x1.25, pan y-5')]:
  draw.text((x+8,10),label,fill='#c9d3df')
  phone.alpha_composite(Image.open(folder/name).convert('RGBA'),(x,36))
 phone.save(folder/'phone-consumer.png')
if (folder/'phone-edge-pan.png').exists() and (folder/'phone-corner-pan.png').exists():
 phone=Image.new('RGBA',(800,880),(0,0,0,0));draw=ImageDraw.Draw(phone)
 for x,name,label in [(0,'phone-edge-pan.png','Supplement · pan +0.4 cell, x1.65'),(410,'phone-corner-pan.png','Supplement · pan +0.4 cell, x1.65,y-5')]:
  draw.text((x+8,10),label,fill='#c9d3df')
  phone.alpha_composite(Image.open(folder/name).convert('RGBA'),(x,36))
 phone.save(folder/'phone-consumer-pan.png')
metrics={}
for d in ['N','E','S','W']:
 im=Image.open(folder/f'static-{d}.png').convert('RGBA');alpha=im.getchannel('A');b=alpha.getbbox()
 metrics[d]={'frame':list(im.size),'alphaBounds':b,'noAlphaClipping':bool(b and b[0]>0 and b[1]>0 and b[2]<384 and b[3]<704),'rgba':im.mode,'transparentPixels':sum(1 for x in alpha.getdata() if x==0)}
(folder/'alpha-validation.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps({'folder':str(folder),'alpha':metrics}))
