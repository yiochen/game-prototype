import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from PIL import Image,ImageDraw
b=Path(__file__).resolve().parent/'evidence';report=json.loads((b/'direct2x-full-chrome-report.json').read_text());out=Image.new('RGB',(1200,600),'#ddd6cb');dr=ImageDraw.Draw(out)
for row,(d,box,title) in enumerate([('E',(252,270,290,338),'Opaque lit-blue / dark-side boundary RGB shift'),('N',(150,420,185,445),'Outer ground silhouette coverage / AA difference')]):
 r=next(r for r in report['records'] if r['direction']==d and r['zoom']==1 and r['rootPhaseLogical']==.25 and r['panPhaseOutput']==.75)
 for col,bg in enumerate(['#f2eee5','#808080','#182536']):
  x=10+col*400;y=30+row*300;dr.text((x,y-20),d+' direct2x .01 root.25 pan.75: native / independent',fill='black')
  for ki,kind in enumerate(['native','independent']):
   im=Image.open(b/r['images'][kind]).convert('RGBA').crop(box);im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);c=Image.new('RGBA',im.size,bg);c.alpha_composite(im);out.paste(c.convert('RGB'),(x+ki*150,y))
  dr.text((x,y+220),title,fill='black')
dr.text((10,585),'Diagnostic crops ×3nearest. Unresolved fullChrome staging/consumer behavior; no native construction or pixel repair performed.',fill='black');out.save(b/'full-chrome-residual-diagnostics.png')
p=b/'full-chrome-hard-boundary-residual-examples.json';data=json.loads(p.read_text());data['interpretation']='Opaque interior RGB residuals are not silhouette alpha and cannot all be dismissed as harmless outer AA or broad finite-light falloff. Example is at the original lit-blue/dark-side surface boundary in fullChrome fractional staging. Exact cause not isolated; retained consumer/capture concern before candidate acceptance.';p.write_text(json.dumps(data,indent=2)+'\n')
