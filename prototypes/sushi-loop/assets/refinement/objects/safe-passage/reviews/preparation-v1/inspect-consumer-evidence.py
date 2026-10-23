from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageChops,ImageStat
H=Path(__file__).resolve().parent
manifest=json.loads((H/'browser/manifest.json').read_text());comparisons=[];framecomparisons=[]
for mode in ['chromium','shell']:
 for kind,files in [('phone-backgrounds',[f'current-phone-{b}.png' for b in ['light','gray','dark']]),('logical-backgrounds',[f'current-logical-{b}.png' for b in ['light','gray','dark']])]:
  ims=[Image.open(H/'browser'/mode/f).convert('RGB') for f in files]
  if kind.startswith('phone'):ims=[im.resize((390,480),Image.Resampling.LANCZOS) for im in ims]
  sheet=Image.new('RGB',(sum(im.width for im in ims),max(im.height for im in ims)),'gray');x=0
  for im in ims:sheet.paste(im,(x,0));x+=im.width
  sheet.save(H/'sheets'/f'browser-{mode}-{kind}.png')
 for d in 'NESW':
  sheet=Image.new('RGB',(1158,738),'#777777');dr=ImageDraw.Draw(sheet)
  atlas=Image.open(H/'resources'/f'original-ambient-{d}.png').convert('RGBA')
  cat=json.loads((H/'resources/catalog-object.json').read_text())
  for i,rect in enumerate(cat['clips'][0]['directions'][d]['rects']):
   c=Image.open(H/'browser'/mode/'frames'/d/f'{i:03}.png').convert('RGBA');expected=Image.new('RGBA',(386,706));expected.alpha_composite(atlas.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3])),(1,1))
   diff=ImageChops.difference(c,expected);visible=[a for a in zip(c.getdata(),expected.getdata()) if a[0][3] or a[1][3]]
   framecomparisons.append({'mode':mode,'direction':d,'frame':i,'meanAbsoluteRGBA':ImageStat.Stat(diff).mean,'maxAbsoluteRGBA':[x[1] for x in diff.getextrema()],'alphaEqual':c.getchannel('A').tobytes()==expected.getchannel('A').tobytes(),'sameDecodedRGBA':c.tobytes()==expected.tobytes(),'visibleRGBAMismatchPixels':sum(a!=b for a,b in visible)})
   im=c.resize((193,353),Image.Resampling.LANCZOS);x=i%6*193;y=i//6*369;sheet.paste(im,(x,y+16),im);dr.text((x+3,y+2),f'{d} {i}',fill='white')
  sheet.save(H/'sheets'/f'browser-{mode}-allframes-{d}.png')
for size in ['logical','phone']:
 for bg in ['light','gray','dark']:
  a=Image.open(H/'browser/chromium'/f'current-{size}-{bg}.png').convert('RGBA');b=Image.open(H/'browser/shell'/f'current-{size}-{bg}.png').convert('RGBA');diff=ImageChops.difference(a,b);comparisons.append({'size':size,'background':bg,'sameDecodedRGBA':a.tobytes()==b.tobytes(),'meanAbsoluteRGBA':ImageStat.Stat(diff).mean,'maxAbsoluteRGBA':[x[1] for x in diff.getextrema()]})
canvas_equal=[]
for d in 'NESW':
 for i in range(12):
  a=Image.open(H/'browser/chromium/frames'/d/f'{i:03}.png');b=Image.open(H/'browser/shell/frames'/d/f'{i:03}.png');canvas_equal.append(a.tobytes()==b.tobytes())
(H/'browser-comparisons.json').write_text(json.dumps({'screenshotModes':comparisons,'canvasFramesEqualAcrossModes':sum(canvas_equal),'canvasFrameCount':len(canvas_equal),'originalCellToCanvas':framecomparisons,'interpretation':'Canvas has exact helper guard1px each side around authored384x704 frame. Browser PNG encode/decode may quantize low-alpha RGB; this is measured consumer output, no repair. Screenshot images preserve actual CSS scale and DPR; sheets uniformly resize phone DPR2 captures for inspection only.'},indent=2)+'\n')
print(json.dumps({'screenshotModes':comparisons,'canvasFramesEqualAcrossModes':sum(canvas_equal),'originalAlphaExactFrames':sum(r['alphaEqual'] for r in framecomparisons),'maxVisibleMismatchPixels':max(r['visibleRGBAMismatchPixels'] for r in framecomparisons)},indent=2))
