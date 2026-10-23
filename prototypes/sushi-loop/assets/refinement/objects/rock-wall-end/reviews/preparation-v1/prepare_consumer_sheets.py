from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
OUT=Path(__file__).resolve().parent
e=json.loads((OUT/'consumer-fixture-evidence.json').read_text());records=[]
for pitch in [128,32,47.3]:
 for background in ['808080']+(['f5f2e9','182231'] if pitch==128 else []):
  modes=['same-facing','reversed-middle'] if background=='808080' else ['same-facing']
  items=[]
  for mode in modes:
   for d in 'NESW':
    phase='0.25-0.5' if background=='808080' else '0-0'
    p=OUT/'consumer-baseline'/f'{d}-{mode}-{pitch}-{phase}-{background}.png';items.append((d,mode,p,Image.open(p).convert('RGB')))
  w=max(i[3].width for i in items);h=max(i[3].height for i in items)
  sheet=Image.new('RGB',(w*4,(h+24)*len(modes)),'#808080');draw=ImageDraw.Draw(sheet)
  for i,(d,mode,p,im) in enumerate(items):
   x=(i%4)*w;y=(i//4)*(h+24);sheet.paste(im,(x,y+24));draw.text((x+3,y+5),f'{d} '+('same' if mode=='same-facing' else 'rev')+f' {pitch}',fill='white');records.append({'file':str(p.relative_to(OUT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sheet':f'consumer-{pitch}-{background}.png'})
  sheet.save(OUT/f'consumer-{pitch}-{background}.png')
(OUT/'consumer-sheet-manifest.json').write_text(json.dumps({'method':'Whole retained browser screenshots placed without crop or pixel repair, at their original pixel size. Labels outside image bounds.','images':records},indent=2)+'\n')
