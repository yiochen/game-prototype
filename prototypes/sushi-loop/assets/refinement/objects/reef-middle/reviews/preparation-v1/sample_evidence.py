import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,shutil
from PIL import Image,ImageDraw,ImageChops
BASE=Path(__file__).resolve().parent;E=BASE/'evidence';sys.path.insert(0,str(BASE/'resources/packing'))
from pack_captures import pack
meta=json.loads((E/'capture-measurements.json').read_text())
for d in ['N','E','S','W']:
 for prefix,key in [('single','singleCamera'),('three-joined','joinedCamera')]:
  raw=E/'packing-inputs'/(prefix+'-'+d);raw.mkdir(parents=True)
  shutil.copy2(E/'native'/(prefix+'-'+d+'.png'),raw/'000.png')
  cam=E/'packing-inputs'/(prefix+'-'+d+'-camera.json');cam.write_text(json.dumps(meta['facings'][d][key],indent=2)+'\n')
  pack(raw,cam,E/'packed'/(prefix+'-'+d),kind='object',columns=1,gutter=0,sheet_scale=2)
# Compact visible comparison sheet, explicitly registered full frames, no alpha-bound fitting.
bgs={'light':'#f2eee5','gray':'#808080','dark':'#182536'}
canvas=Image.new('RGB',(1180,790),'#ddd6cb');draw=ImageDraw.Draw(canvas)
for j,d in enumerate(['N','E','S','W']):
 im=Image.open(E/'packed'/('single-'+d)/'sheet.png').convert('RGBA')
 for k,(name,bg) in enumerate(bgs.items()):
  x=10+j*294;y=30+k*250
  draw.text((x,y-16),d+' '+name+' logical128 / phone32',fill='black')
  small=im.resize((192,352),Image.Resampling.LANCZOS)
  # all full-frame352 tall source would require1056; use native registration fixed crop(0,150,192,352), not alpha bounds.
  crop=small.crop((0,150,192,352));panel=Image.new('RGBA',crop.size,bg);panel.alpha_composite(crop);canvas.paste(panel.convert('RGB'),(x,y))
  phone=im.resize((48,88),Image.Resampling.LANCZOS);p=Image.new('RGBA',phone.size,bg);p.alpha_composite(phone);canvas.paste(p.convert('RGB'),(x+202,y+70))
draw.text((10,775),'Logical128 panels: fixed full-frame crop x0..192,y150..352. Phone32 panels retain whole48x88 frame. No fitting.',fill='black');canvas.save(E/'single-all4-use-size.png')
print('sample complete')
