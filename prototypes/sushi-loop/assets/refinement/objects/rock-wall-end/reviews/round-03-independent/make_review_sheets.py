from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib
OUT=Path(__file__).resolve().parent;C=OUT/'resources/experiment/candidates/round-03'
records=[];sheet=Image.new('RGB',(1688,940),'#808080');draw=ImageDraw.Draw(sheet)
for row,pitch in enumerate([32,47.3]):
 for col,d in enumerate('NESW'):
  p=OUT/'consumer-reproduction'/f'viewport-{d}-same-facing-{pitch}-0.25-0.5-808080.png';im=Image.open(p).convert('RGB');small=im.resize((round(im.width/2),round(im.height/2)),Image.Resampling.BOX)
  x=col*422;y=row*470;sheet.paste(small,(x,y+24));draw.text((x+5,y+5),f'{d}, full viewport, pitch{pitch}, uniform50%',fill='white');records.append({'path':str(p.relative_to(OUT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'originalSize':list(im.size),'displayScale':.5})
sheet.save(OUT/'full-viewport-contact-sheet.png')
published=Image.open(C/'previews/four-view-sheet.png').convert('RGB');checks={}
for i,d in enumerate('NESW'):
 frame=Image.open(C/f'published/static-{d}.png').convert('RGBA');bg=Image.new('RGBA',frame.size,'#808080');bg.alpha_composite(frame);actual=published.crop((i*384,24,i*384+384,728))
 checks[d]={'expectedSize':list(frame.size),'sheetBodyRGBAExact':bg.convert('RGB').tobytes()==actual.tobytes()}
(OUT/'review-sheet-verification.json').write_text(json.dumps({'publishedFourViewBodyChecks':checks,'viewportSheet':records,'method':'Full screenshots uniformly scaled50% and placed without crops/warps; whole source-frame body cells compared to exact published bytes alpha-composited on declared gray.'},indent=2)+'\n')
