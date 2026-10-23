"""Exact native/independent/replay analysis and compact unmodified-image evidence."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageChops,ImageStat,ImageDraw,ImageOps
P=Path(__file__).resolve().parents[1];O=P/'candidates/round-03';report={};rows=[]
for d in 'NESW':
 native=Image.open(O/f'joins/native-{d}-published.png').convert('RGBA');ind=Image.open(O/f'consumer/full-chromium-logical128-integer-repeat-{d}.png').convert('RGBA')
 # Canonical consumer adds exactly one transparent native guard pixel per side.
 expected=ImageOps.expand(native,border=1,fill=(0,0,0,0));assert expected.size==ind.size
 a=list(expected.getdata());b=list(ind.getdata());diff=[tuple(abs(u-v) for u,v in zip(x,y)) for x,y in zip(a,b)]
 opaque=[i for i,(x,y) in enumerate(zip(a,b)) if x[3]==255 and y[3]==255]
 alpha=[i for i,(x,y) in enumerate(zip(a,b)) if x[3]!=y[3]]
 interior_alpha_loss=[i for i,(x,y) in enumerate(zip(a,b)) if x[3]==255 and y[3]<255]
 rgbbad=[i for i in opaque if max(diff[i][:3])>2]
 report[d]={'nativeSize':list(native.size),'consumerSize':list(ind.size),'commonCanvasGuard':1,'comparison':'Native published connected render plus one transparent guard on each side; exact integer registration, no fitting or discarded visible pixel.','allPixelDifferenceCount':sum(any(q) for q in diff),'alphaDifferenceCount':len(alpha),'opaqueRGBDifferenceOver2':len(rgbbad),'maxRGBDifferenceOnMutuallyOpaque':max((max(diff[i][:3]) for i in opaque),default=0),'nativeOpaqueButConsumerNotOpaque':len(interior_alpha_loss),'interiorAlphaLossBounds':Image.new('L',ind.size).getbbox() if not interior_alpha_loss else [min(i%ind.width for i in interior_alpha_loss),min(i//ind.width for i in interior_alpha_loss),max(i%ind.width for i in interior_alpha_loss)+1,max(i//ind.width for i in interior_alpha_loss)+1],'meanAbsoluteRGBA':ImageStat.Stat(ImageChops.difference(expected,ind)).mean}
 rows.append((d,native,ind))
# At logical1x show each entire common canvas; neutral backgrounds are evidence only.
sheet=Image.new('RGB',(4*456,2*664),(220,227,229));dr=ImageDraw.Draw(sheet)
for col,(d,native,ind) in enumerate(rows):
 for row,(label,im) in enumerate([('native connected',native),('independent consumer',ind)]):
  shown=im.resize((im.width//2,im.height//2),Image.Resampling.BOX);bg=Image.new('RGBA',shown.size,(122,137,148,255));bg.alpha_composite(shown);sheet.paste(bg.convert('RGB'),(col*456+4,row*664+20));dr.text((col*456+4,row*664+4),f'{d} / {label} / cell128',fill=(10,20,30))
sheet.save(O/'repeated.png')
# Native and independent parallel context at the same registered pixel density.
par=Image.open(O/'context/native-parallel-published.png').convert('RGBA');ind=Image.open(O/'consumer/full-chromium-logical128-integer-parallel-S.png').convert('RGBA')
ctx=Image.new('RGB',(916,664),(220,227,229));dr=ImageDraw.Draw(ctx)
for col,(label,im) in enumerate([('Native: two strips / .66 ground gap',par),('Independent: same placement/density',ind)]):
 shown=im.resize((im.width//2,im.height//2),Image.Resampling.BOX);bg=Image.new('RGBA',shown.size,(122,137,148,255));bg.alpha_composite(shown);ctx.paste(bg.convert('RGB'),(col*458+4,20));dr.text((col*458+4,4),label,fill=(10,20,30))
ctx.save(O/'parallel-context.png')
replays=[]
for d in 'NESW':
 a=Image.open(O/f'native/static/{d}/000.png').convert('RGBA');b=Image.open(O/f'replay/{d}.png').convert('RGBA');diff=ImageChops.difference(a,b)
 replays.append({'direction':d,'decodedRGBAEqual':diff.getbbox() is None,'differingPixels':sum(x!=y for x,y in zip(a.getdata(),b.getdata())),'maxDifference':max(x[1] for x in diff.getextrema()),'nativeSHA256':hashlib.sha256((O/f'native/static/{d}/000.png').read_bytes()).hexdigest(),'replaySHA256':hashlib.sha256((O/f'replay/{d}.png').read_bytes()).hexdigest()})
report['savedSourceReplay']=replays
report['interpretation']='Numerical differences are diagnostics; the native and independent renders and real CSS screenshots still require visual review. No local defect is waived.'
(O/'comparison-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
