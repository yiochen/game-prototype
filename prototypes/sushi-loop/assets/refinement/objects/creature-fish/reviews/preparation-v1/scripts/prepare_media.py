from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,shutil,hashlib
P=Path(__file__).resolve().parents[1];repo=P.parents[7]
C=json.loads((P/'resources/inputs/catalog-object.json').read_text())
# Actual supplied catalog images; source assets used by browser are copied exactly.
production=repo/'prototypes/sushi-loop/assets/production'
for clip in C['clips']:
 for d,entry in clip['directions'].items():
  dst=P/'resources/consumer'/entry['image'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(production/entry['image'],dst)
(P/'resources/consumer/catalog-object.json').write_text(json.dumps(C,indent=2)+'\n')
records=json.loads((P/'native-capture-records.json').read_text())['captureRecords'];summary=[]
for row in records:
 raw=Image.open(P/row['path']).convert('RGBA');published=raw.resize((896,1024),Image.Resampling.LANCZOS);dst=P/'native-published'/row['clip']/row['direction']/(f"{row['index']:03d}.png");dst.parent.mkdir(parents=True,exist_ok=True);published.save(dst)
 clip=next(c for c in C['clips'] if c['id']==row['clip']);entry=clip['directions'][row['direction']];atlas=Image.open(P/'resources/consumer'/entry['image']).convert('RGBA');x,y,w,h=entry['rects'][row['index']];original=atlas.crop((x,y,x+w,y+h));a=original.tobytes();b=published.tobytes();diff=ImageChops.difference(original,published)
 summary.append({'clip':row['clip'],'direction':row['direction'],'index':row['index'],'originalAtlas':entry['image'],'originalRect':[x,y,w,h],'rawNative':row['path'],'publishedReplay':str(dst.relative_to(P)),'wholeFrameReduction':'Pillow RGBA 1792x2048 -> 896x1024 LANCZOS, same publisher filter; no crop/fit/recolor/alpha/RGB repair','exactDecodedEquality':a==b,'differentChannelBytes':sum(x!=y for x,y in zip(a,b)),'meanAbsoluteRGBAByteError':sum(abs(x-y) for x,y in zip(a,b))/len(a),'maxByteError':max(abs(x-y) for x,y in zip(a,b)),'originalAlphaBBox':original.getbbox(),'replayAlphaBBox':published.getbbox()})
(P/'replay-residuals.json').write_text(json.dumps(summary,indent=2)+'\n')
# Compact all native sample sheet. Every cell is a whole registered frame.
colors=['#f3f1e8','#858c92','#152338'];cw,ch=224,278
sheet=Image.new('RGB',(cw*4,ch*11),'#d8d8d8');draw=ImageDraw.Draw(sheet)
for ci,clip in enumerate(C['clips']):
 for di,d in enumerate(['N','E','S','W']):
  row=next(r for r in records if r['clip']==clip['id'] and r['direction']==d);im=Image.open(P/row['path']).convert('RGBA').resize((224,256),Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,colors[ci%3]);bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),(di*cw,ci*ch+22));draw.text((di*cw+8,ci*ch+5),f"{clip['id']} {d} f{row['index']}",fill='black')
sheet.save(P/'native-allstates-fourviews.png')
# All catalog frame alpha/uniqueness audit, actual whole raw frames only.
audit=[]
for clip in C['clips']:
 for d,e in clip['directions'].items():
  atlas=Image.open(P/'resources/consumer'/e['image']).convert('RGBA');fs=[]
  for fi,(x,y,w,h) in enumerate(e['rects']):
   im=atlas.crop((x,y,x+w,y+h));alpha=im.getchannel('A');fs.append({'index':fi,'bbox':alpha.getbbox(),'decodedSHA256':hashlib.sha256(im.tobytes()).hexdigest(),'alphaBorderNonzero':bool(alpha.crop((0,0,w,1)).getbbox() or alpha.crop((0,h-1,w,h)).getbbox() or alpha.crop((0,0,1,h)).getbbox() or alpha.crop((w-1,0,w,h)).getbbox())})
  audit.append({'clip':clip['id'],'direction':d,'frames':fs,'uniqueFrameCount':len({f['decodedSHA256'] for f in fs})})
(P/'catalog-frame-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print('resources',len(list((P/'resources/consumer/sprites/creature-fish').glob('*.png'))),'residual exact',sum(r['exactDecodedEquality'] for r in summary),'of',len(summary),'max MAE',max(r['meanAbsoluteRGBAByteError'] for r in summary))
