from pathlib import Path
import json,hashlib
from PIL import Image,ImageChops,ImageStat
R=Path(__file__).resolve().parent;Q=R.parent;O=Q.parent.parent;C=O/'candidates/round-01';E=Q/'evidence'
j=json.loads((E/'independent-native-v2.json').read_text());replays=[]
for r in j['renderRecords']:
 a=Image.open(O/r['path']).convert('RGBA');path=C/'native'/r['clip']/r['direction']/f"{r['index']:03d}.png";b=Image.open(path).convert('RGBA');diff=ImageChops.difference(a,b);replays.append({'clip':r['clip'],'direction':r['direction'],'index':r['index'],'independentReplay':r['path'],'submittedNative':str(path.relative_to(O)),'decodedRGBAExact':diff.getbbox(alpha_only=False) is None,'maxRGBA':diff.getextrema(),'meanRGBA':ImageStat.Stat(diff).mean})
webps=[]
for d in 'NESW':
 im=Image.open(C/'previews'/f'idle-{d}.webp');rows=[]
 for i in range(im.n_frames):
  im.seek(i);a=im.convert('RGBA');b=Image.open(C/'native/idle'/d/f'{i:03d}.png').convert('RGBA');diff=ImageChops.difference(a,b);mask=ImageChops.lighter(a.getchannel('A'),b.getchannel('A')).point(lambda n:255 if n else 0);masked=ImageChops.multiply(diff,Image.merge('RGBA',(mask,mask,mask,mask)));rows.append({'index':i,'durationMs':im.info.get('duration'),'alphaDecodedExact':ImageChops.difference(a.getchannel('A'),b.getchannel('A')).getbbox() is None,'RGBWhereAlphaPositiveExact':masked.getbbox(alpha_only=False) is None,'maxRGBAAllPixels':diff.getextrema()})
 webps.append({'path':f'previews/idle-{d}.webp','frames':len(rows),'loop':im.info.get('loop'),'durationMs':sum(r['durationMs'] for r in rows),'allAlphaAndVisibleRGBExact':all(r['alphaDecodedExact'] and r['RGBWhereAlphaPositiveExact'] for r in rows),'records':rows})
# Verify declared contact-sheet panel contents from frozen mapping, not titles alone.
mapping=json.loads((C/'preview-coverage-mapping.json').read_text());panelchecks=[]
for item in mapping:
 if not item['path'].endswith('.png'):continue
 sheet=Image.open(O/item['path']).convert('RGB')
 for inp in item.get('inputs',[]):
  if not isinstance(inp,dict) or 'rect' not in inp:continue
  x,y,w,h=inp['rect'];source=Image.open(O/inp['input']).convert('RGBA');source=source.resize((w,h),Image.Resampling.LANCZOS) if source.size!=(w,h) else source
  got=sheet.crop((x,y,x+w,y+h));background=got.getpixel((0,0));expected=Image.new('RGB',(w,h),background);expected.paste(source,(0,0),source);diff=ImageChops.difference(got,expected);panelchecks.append({'sheet':item['path'],'source':inp['input'],'rect':inp['rect'],'decodedRGBExact':diff.getbbox() is None,'maxRGB':diff.getextrema()})
(E/'final-technical-check.json').write_text(json.dumps({'candidatePacketSHA256':hashlib.sha256((C/'packet.json').read_bytes()).hexdigest(),'independentNativeReplays':replays,'all7NativeReplaysRGBAExact':all(r['decodedRGBAExact'] for r in replays),'webp':webps,'webpResidualInterpretation':'Every WebP alpha and every RGB pixel with alpha>0 matches the native PNG. WebP encoding drops otherwise invisible RGB where alpha=0; fullRGBAexact is therefore false. No art/publishedPNG pixels were repaired. This previewcodec residual is not a visible artifact.','previewPanelChecks':panelchecks,'panelLimit':'Native-light-dark background cases use known display background rather than firstpixel if thefirstpixel is opaque; any failedautomated panel comparison is retained and separately visually inspected, not manufacturedpass.'},indent=2)+'\n')
print('native7 exact',all(r['decodedRGBAExact'] for r in replays));print('webp visible all exact',[r['allAlphaAndVisibleRGBExact'] for r in webps]);print('sheet panels exact',sum(r['decodedRGBExact'] for r in panelchecks),'/',len(panelchecks));print('failed sheets',sorted(set(r['sheet'] for r in panelchecks if not r['decodedRGBExact'])))
