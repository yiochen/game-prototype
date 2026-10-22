from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
O=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-shelving');B=O/'candidates/round-04';OUT=O/'reviews/round-04-independent';bgs=[('light',(235,231,219,255)),('gray',(118,118,118,255)),('dark',(27,34,41,255))];inputs=[]
def load(p):
 inputs.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});return Image.open(p).convert('RGBA')
for c in ['highlighted','clearance']:
 for d in ['S','E','N','W']:
  # Whole native frames uniformly displayed200x300, without per-frame fit.
  sheet=Image.new('RGB',(1200,1944),(85,85,85));draw=ImageDraw.Draw(sheet)
  for i in range(12):
   im=load(B/'frames'/f'{c}-{d}'/f'{i:03d}.png').resize((200,300),Image.Resampling.LANCZOS)
   for j,(name,bg) in enumerate(bgs):
    cell=Image.new('RGBA',(200,324),bg);cell.alpha_composite(im,(0,24));x=(i%2)*600+j*200;y=(i//2)*324;sheet.paste(cell.convert('RGB'),(x,y));draw.text((x+3,y+3),f'{c}{d} {i:02} {name}',fill=(30,30,30) if name=='light' else 'white')
  sheet.save(OUT/f'allphase-{c}-{d}-three-backgrounds.png')
for d in ['S','E','N','W']:
 for kind in ['floor-reveal','repeated-clearance']:
  paths=[B/'previews'/kind/d/(f'clearance-{i:03d}.png' if kind=='floor-reveal' else f'{i:03d}.png') for i in range(12)]
  ims=[load(p) for p in paths];ratio=55/256;size=(round(ims[0].width*ratio),round(ims[0].height*ratio));w,h=size;sh=Image.new('RGB',(w*4,(h+24)*3),(27,34,41));dr=ImageDraw.Draw(sh)
  for i,im in enumerate(ims):
   x=i%4*w;y=i//4*(h+24);sh.paste(im.resize(size,Image.Resampling.LANCZOS).convert('RGB'),(x,y+24));dr.text((x+4,y+4),f'{d} {kind} {i:02}',fill='white')
  sh.save(OUT/f'context-{kind}-{d}-all12.png')
for kind in ['human-context','repeated']:
 paths=[B/'previews'/f'{kind}-{d}-mask-root.png' for d in ['S','E','N','W']];ims=[load(p) for p in paths];ratio=55/256;size=(round(ims[0].width*ratio),round(ims[0].height*ratio));w,h=size;sh=Image.new('RGB',(w*2,(h+20)*2),(27,34,41));dr=ImageDraw.Draw(sh)
 for i,(d,im) in enumerate(zip(['S','E','N','W'],ims)):
  x=(i%2)*w;y=(i//2)*(h+20);sh.paste(im.resize(size,Image.Resampling.LANCZOS).convert('RGB'),(x,y+20));dr.text((x+3,y+3),f'{kind} {d} roots/mask',fill='white')
 sh.save(OUT/f'context-{kind}-all4-mask-root-consumer55.png')
(OUT/'review-sheet-inputs.json').write_text(json.dumps({'purpose':'Judge-only legibility sheets from exact sealed full frames/contexts. No candidate pixels/files modified; all native whole-frame checks independent. Three-background frame200x300 is documented review display, not a changed export.','inputs':inputs},indent=2)+'\n')
