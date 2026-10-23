from PIL import Image,ImageDraw
from pathlib import Path
import math,json
P=Path(__file__).resolve().parent;E=P/'evidence';ledger=json.loads((E/'browser-ledger.json').read_text());maps=[]
# Preserve screenshot pixels exactly; crop unused body width to the complete authoredSVG presentation region.
items=[]
for rec in ledger['cases']:
 if rec['mode']!='views':continue
 src=E/'browser'/f"{rec['id']}.png";im=Image.open(src).convert('RGB');w=min(im.width,math.ceil(rec['bounds'][2]*rec['pitch']/128)+24);box=(0,0,w,im.height);part=im.crop(box);dest=E/'browser'/f"{rec['id']}-content.png";part.save(dest);maps.append({'source':str(src.relative_to(P.parent.parent)),'presented':str(dest.relative_to(P.parent.parent)),'cropBox':box,'method':'Discard unused right-hand body width outside complete SVG/canvas. No sprite crop/rescale/pixel edits.'});
 if rec['pitch']==32:items.append((rec['id'],part))
w=max(im.width for _,im in items)+20;h=sum(im.height+36 for _,im in items)+10;out=Image.new('RGB',(w,h),'#7d8792');dr=ImageDraw.Draw(out);y=10
for label,im in items:dr.text((10,y),label,fill='white');out.paste(im,(10,y+20));y+=im.height+36
out.save(E/'browser-phone-backgrounds.png')
rows=[(f'actual consumer frame{f}/12',Image.open(E/'browser'/f'temporal-{f:02d}.png').convert('RGB')) for f in range(13)];w=rows[0][1].width+20;h=rows[0][1].height+32;out=Image.new('RGB',(2*w,7*h),'#7d8792');dr=ImageDraw.Draw(out)
for i,(label,im) in enumerate(rows):x=i%2*w;y=i//2*h;dr.text((x+8,y+5),label,fill='white');out.paste(im,(x+8,y+24))
out.save(E/'browser-all4-temporal-coverage.png')
rows=[(f'{d} idle frame{f}',Image.open(E/'published-replay/idle'/d/f'{f:03d}.png').convert('RGBA').resize((192,384),Image.Resampling.LANCZOS)) for d in ['N','E','W'] for f in [1,7]];out=Image.new('RGB',(3*208,2*420),'#7d8792');dr=ImageDraw.Draw(out)
for i,(label,im) in enumerate(rows):x=i%3*208;y=i//3*420;dr.text((x+8,y+5),label,fill='white');out.paste(im,(x+8,y+24),im)
out.save(E/'native-other-view-temporal.png')
(E/'coverage-panel-mapping.json').write_text(json.dumps({'screenshotCropMappings':maps,'temporalCoverage':'Each13original browser temporal screenshot appears unscaled in browser-all4-temporal-coverage.png with phase label. All4cardinals at everyphase.','otherNativeCoverage':'N/E/W idleframes1and7 publishedreplay completeframe resized0.5 as declared for presentation only.'},indent=2)+'\n')
print('Coverage panels saved.')
