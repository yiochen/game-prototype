from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import json,hashlib
P=Path(__file__).resolve().parents[1]
report={'recipe':'Original native 4x exact copied source capture runtime, saved filter 1.5; whole-frame Pillow LANCZOS to sourceScale 2 following original publisher. Canonical future recipe .5 native filter + whole-frame BOX is distinct.','views':{}}
sheet=Image.new('RGB',(1632,376),'#404852');draw=ImageDraw.Draw(sheet)
for idx,d in enumerate('NESW'):
 n=Image.open(P/f'captures/original-native/{d}.png').convert('RGBA');pub=n.resize((384,704),Image.Resampling.LANCZOS);pub.save(P/f'captures/original-published/{d}.png')
 old=Image.open(P/f'resources/input/original-atlas-{d}.png').convert('RGBA')
 diff=ImageChops.difference(pub,old);hist=diff.histogram();neq=sum(a!=b for a,b in zip(pub.getdata(),old.getdata()));mx=max(max(c) for c in diff.getdata());alpha=ImageChops.difference(pub.getchannel('A'),old.getchannel('A'))
 box=n.resize((384,704),Image.Resampling.BOX)
 report['views'][d]={'dimensions':list(n.size),'publishedDimensions':list(pub.size),'originalSHA256':hashlib.sha256((P/f'resources/input/original-atlas-{d}.png').read_bytes()).hexdigest(),'replayPixelsDifferent':neq,'totalPixels':pub.width*pub.height,'maxRGBAChannelDifference':mx,'meanAbsRGBA':ImageStat.Stat(diff).mean,'alphaMaxDifference':alpha.getextrema()[1],'nativeAlphaBounds':n.getchannel('A').getbbox(),'originalAlphaBounds':old.getchannel('A').getbbox(),'replayAlphaBounds':pub.getchannel('A').getbbox()}
 for j,(im,label) in enumerate([(old,'known'),(pub,'replay')]):
  logical=im.resize((192,352),Image.Resampling.BOX);sheet.paste(logical,(idx*408+j*200+4,24),logical);draw.text((idx*408+j*200+5,10),f'{d} {label}',fill='white')
sheet.save(P/'captures/original-known-vs-replay.png')
(P/'measurements/original-replay-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
d=json.loads((P/'measurements/original-native.json').read_text())
print(json.dumps({'bounds':d['boundsLocalS'],'corePort':d['portXminusHalfVertices'],'objects':[{'name':o['name'],'location':o['location'],'bounds':[[min(v[i] for v in o['vertices']) for i in range(3)],[max(v[i] for v in o['vertices']) for i in range(3)]]} for o in d['objects'] if o['type']=='MESH'],'replay':report},indent=2))
