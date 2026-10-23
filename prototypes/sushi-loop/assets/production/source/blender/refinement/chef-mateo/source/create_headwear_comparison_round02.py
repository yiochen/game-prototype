"""Registered review-only crops; native source frames remain untouched."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round02';PRE=OUT/'previews'
sheet=Image.new('RGB',(1960,768),'#b6bbc0');draw=ImageDraw.Draw(sheet)
for j,round_name in enumerate(['round01','round02']):
 for i,d in enumerate(['N','E','S','W']):
  raw=Image.open(OBJ/'candidates'/round_name/'raw-frames'/('idle-'+d)/'000.png').convert('RGBA').crop((70,180,315,360))
  image=Image.new('RGBA',raw.size,'#b6bbc0');image.alpha_composite(raw);image=image.convert('RGB').resize((490,360),Image.Resampling.NEAREST)
  sheet.paste(image,(i*490,j*384+24));draw.text((i*490+12,j*384+7),round_name+' '+d+' native registered headwear crop, 2x',fill='#18212b')
path=PRE/'headband-before-after.png';sheet.save(path)
deliveryPath=OBJ/'delivery.json';d=json.loads(deliveryPath.read_text());d['previews']['headband-before-after']=str(path.relative_to(OBJ));deliveryPath.write_text(json.dumps(d,indent=2)+'\n')
print(path)
