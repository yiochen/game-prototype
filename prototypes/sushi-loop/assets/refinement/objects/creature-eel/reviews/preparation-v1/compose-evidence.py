from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageChops,ImageStat
P=Path(__file__).resolve().parent
cat=json.loads((P/'resources/inputs/catalog-object.json').read_text())
reports=[];dmap={}
for branch in ['', 'diagnostic-euler']:
 B=P/branch
 records=json.loads((B/'capture-records.json').read_text())['records']
 for r in records:
  im=Image.open(B/r['nativePath']).convert('RGBA');small=im.resize((896,1024),Image.Resampling.LANCZOS);out=B/'published-replay'/r['clip']/r['direction']/f"{r['frame']:03}.png";out.parent.mkdir(parents=True,exist_ok=True);small.save(out)
  r['reducedPath']=str(out.relative_to(P));r['nativeAlphaBounds']=im.getchannel('A').getbbox();r['publishedAlphaBounds']=small.getchannel('A').getbbox()
  if r['publishedIndex'] is not None:
   clip=next(c for c in cat['clips'] if c['id']==r['clip']);e=clip['directions'][r['direction']];x,y,w,h=e['rects'][r['publishedIndex']];atlas=Image.open(P/'resources/published'/e['image']);original=atlas.crop((x,y,x+w,y+h)).convert('RGBA');diff=ImageChops.difference(small,original);stat=ImageStat.Stat(diff);reports.append({'branch':branch or 'untouched','clip':r['clip'],'direction':r['direction'],'frame':r['frame'],'nativePath':str((B/r['nativePath']).relative_to(P)),'reducedPath':str(out.relative_to(P)),'publishedAtlas':e['image'],'publishedRect':e['rects'][r['publishedIndex']],'pixelExact':diff.getbbox(alpha_only=False) is None,'channelMAE':stat.mean,'channelMax':[x[1] for x in diff.getextrema()],'originalAlphaBounds':original.getchannel('A').getbbox(),'replayAlphaBounds':small.getchannel('A').getbbox()})
 (B/'visual-map.json').write_text(json.dumps(records,indent=2)+'\n');dmap[branch]=records
(P/'replay-published-residuals.json').write_text(json.dumps({'process':'Native1792x2048 → 896x1024 uniform whole-frame Pillow LANCZOS only; exact untouched original 896x1024 atlas extraction; no fitting, RGB/alpha repairs, position offsets or recolor.','records':reports},indent=2)+'\n')
# Native body evidence at uniform logical scale. No subject fitting or per-view offsets.
for first in range(0,11,3):
 clips=cat['clips'][first:first+3];sheet=Image.new('RGB',(1792,536*len(clips)), '#8e9196');draw=ImageDraw.Draw(sheet)
 for j,c in enumerate(clips):
  for k,f in enumerate(['N','E','S','W']):
   fr=10 if c['id']=='normal' else 7;im=Image.open(P/'captures'/c['id']/f/f'{fr:03}.png').convert('RGBA').resize((448,512),Image.Resampling.LANCZOS);sheet.paste(im,(448*k,536*j+24),im);draw.text((448*k+8,536*j+6),f"UNTOUCHED {c['id']} {f} native frame {fr}",fill='#ffffff')
 sheet.save(P/f'native-states-{first+1:02}-{first+len(clips):02}.png')
# Native full motion strips, baseline then diagnostic. Panels always full frame, uniform quarter native size.
for clip,facing in [('normal','S'),('caught','E')]:
 sheet=Image.new('RGB',(6*224,4*280),'#8e9196');draw=ImageDraw.Draw(sheet)
 for row,branch in enumerate(['','diagnostic-euler']):
  for fr in range(1,13):
   im=Image.open(P/branch/'captures'/clip/facing/f'{fr:03}.png').convert('RGBA').resize((224,256),Image.Resampling.LANCZOS);x=(fr-1)%6*224;y=row*560+(fr-1)//6*280;sheet.paste(im,(x,y+24),im);draw.text((x+4,y+5),f"{branch or 'untouched'} {clip} {facing} {fr}",fill='#ffffff')
 sheet.save(P/f'motion-{clip}-{facing}-baseline-diagnostic.png')
# Honest target layout comparison; every complete input canvas retained.
sheet=Image.new('RGB',(3*448,640),'#8e9196');draw=ImageDraw.Draw(sheet)
for i,(label,path) in enumerate([('Original snapshot','resources/inputs/original.png'),('Frozen target (aesthetic only)','resources/inputs/target.png'),('GLOBAL warm-soft style','resources/inputs/warm-soft-reference.png')]):
 im=Image.open(P/path).convert('RGBA');im.thumbnail((448,600),Image.Resampling.LANCZOS);sheet.paste(im,(i*448+(448-im.width)//2,30),im);draw.text((i*448+10,8),label,fill='#ffffff')
sheet.save(P/'reference-comparison.png')
# Geometry observations are distinct from any proposed design budget.
summary={}
for branch in ['', 'diagnostic-euler']:
 d=json.loads((P/branch/'native-measurements.json').read_text());summary[branch or 'untouched']={'envelopeByFacing':{f:{'rawAuthored':[[min(r['rawAuthoredBounds'][j][i] for r in rows) if j==0 else max(r['rawAuthoredBounds'][j][i] for r in rows) for i in range(3)] for j in range(2)],'evaluated':[[min(r['evaluatedBounds'][j][i] for r in rows) if j==0 else max(r['evaluatedBounds'][j][i] for r in rows) for i in range(3)] for j in range(2)]} for f,rows in d['views'].items()},'closures':d['closures']}
(P/'source-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('native replay diff sample',reports[0]);print('untouched max channel MAE', [max(r['channelMAE'][i] for r in reports if r['branch']=='untouched') for i in range(4)])
