from pathlib import Path
import json,hashlib
from PIL import Image,ImageChops
R=Path(__file__).resolve().parent;Q=R.parent;O=Q.parent.parent;C=O/'candidates/round-01';E=Q/'evidence';maps=[]
for name in ['all-motion-phases','context-motion','native-four-view','native-light-dark']:
 p=C/'previews'/f'{name}.png';im=Image.open(p).convert('RGB');W,H=im.size;boxes=[]
 if name=='all-motion-phases':
  for row in range(4):
   for half in range(2):boxes.append((half*(W//2),row*(H//4),(half+1)*(W//2),(row+1)*(H//4)))
 elif name=='context-motion':
  for col in range(5):boxes.append((col*(W//5),0,(col+1)*(W//5),H))
 elif name=='native-four-view':
  for col in range(4):boxes.append((col*(W//4),0,(col+1)*(W//4),H))
 else:
  for row in range(2):
   for col in range(4):boxes.append((col*(W//4),row*(H//2),(col+1)*(W//4),(row+1)*(H//2)))
 for i,b in enumerate(boxes):
  out=E/f'{name}-part-{i:02d}.png';im.crop(b).save(out);maps.append({'original':str(p.relative_to(O)),'reviewPanel':str(out.relative_to(O)),'crop':b,'discardedVisiblePixels':False,'operation':'Partition full original preview into adjacent unscaled rectangles; together preserve all original pixels.'})
# Verify every published frame is precisely whole-frame reduction, atlasrect is exact; decode everyWebP source phase/timing.
raw=json.loads((C/'raw-records.json').read_text());print('raw type',type(raw).__name__,'keys',list(raw)[:10] if isinstance(raw,dict) else len(raw));pub=[]
for clip,count in [('static',1),('idle',12)]:
 for d in 'NESW':
  atlas=Image.open(C/'atlases'/f'{clip}-{d}.png').convert('RGBA')
  for i in range(count):
   native=Image.open(C/'native'/clip/d/f'{i:03d}.png').convert('RGBA');frame=Image.open(C/'frames'/clip/d/f'{i:03d}.png').convert('RGBA');reduced=native.resize((384,768),Image.Resampling.LANCZOS);x=(i%6)*384 if clip=='idle' else 0;y=(i//6)*768 if clip=='idle' else 0;panel=atlas.crop((x,y,x+384,y+768));pub.append({'clip':clip,'direction':d,'index':i,'nativeReductionExact':ImageChops.difference(reduced,frame).getbbox(alpha_only=False) is None,'atlasRectExact':ImageChops.difference(panel,frame).getbbox(alpha_only=False) is None,'nativeBorderAlpha':max(max(native.getchannel('A').crop(b).getextrema()) for b in [(0,0,768,1),(0,1535,768,1536),(0,0,1,1536),(767,0,768,1536)])})
webps=[]
for d in 'NESW':
 im=Image.open(C/'previews'/f'idle-{d}.webp');rows=[]
 for i in range(im.n_frames):
  im.seek(i);frame=im.convert('RGBA');native=Image.open(C/'native/idle'/d/f'{i:03d}.png').convert('RGBA');rows.append({'frame':i,'duration':im.info.get('duration'),'timestamp':im.info.get('timestamp'),'nativeRGBAExact':ImageChops.difference(frame,native).getbbox(alpha_only=False) is None})
 webps.append({'path':f'previews/idle-{d}.webp','frames':im.n_frames,'loop':im.info.get('loop'),'timingSum':sum(r['duration'] or 0 for r in rows),'records':rows})
(E/'review-panel-mapping.json').write_text(json.dumps({'candidatePacketSHA256':hashlib.sha256((C/'packet.json').read_bytes()).hexdigest(),'partitions':maps},indent=2)+'\n')
(E/'publication-and-playback-verification.json').write_text(json.dumps({'candidatePacketSHA256':hashlib.sha256((C/'packet.json').read_bytes()).hexdigest(),'frames':pub,'webp':webps,'limits':'Decodedframe/timing verification supplements actual liveChrome playback inspection; it is not alone a motion/aesthetic verdict.'},indent=2)+'\n')
print('published exact',all(r['nativeReductionExact'] and r['atlasRectExact'] for r in pub),'52frames',len(pub),'native border max',max(r['nativeBorderAlpha'] for r in pub));print('webp',[(r['path'],r['timingSum'],all(a['nativeRGBAExact'] for a in r['records'])) for r in webps])
