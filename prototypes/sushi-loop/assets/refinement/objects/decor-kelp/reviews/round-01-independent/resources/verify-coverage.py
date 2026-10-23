from pathlib import Path
import json,hashlib
import PIL
PIL.__path__.append(str(Path(__file__).resolve().parent/'python-new/PIL'))
from PIL import Image,ImageChops
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];C=ROOT/'candidates/round-01';OUT=BASE.parent/'evidence'
def diff(a,b):
 d=ImageChops.difference(a.convert('RGBA'),b.convert('RGBA'));hist=d.histogram();return {'differentChannels':sum(n for i,n in enumerate(hist)if i%256),'maximumChannelDelta':max(i%256 for i,n in enumerate(hist)if n)}
rows=[]
for d in ['N','E','S','W']:
 sheet=Image.open(C/f'phases-{d}.png').convert('RGBA')
 for i in range(12):
  frame=Image.open(C/f'frames/idle/{d}/{i:03d}.png').convert('RGBA').resize((192,480),Image.Resampling.LANCZOS);expected=Image.new('RGBA',(192,480),(37,62,66,255));expected.alpha_composite(frame);x=i%6*192;y=i//6*500+20;rows.append({'sheet':f'phases-{d}.png','frame':f'frames/idle/{d}/{i:03d}.png','sheetRect':[x,y,192,480],**diff(sheet.crop((x,y,x+192,y+480)),expected)})
replays=[]
for mode in ['full-chromium','headless-shell']:
 for f in ['phone-detail','thumbnail-control','registered-context']:
  for suffix in ['', '-native-canvas']:
   name=f'{mode}-{f}{suffix}.png';replays.append({'replay':f'reviews/round-01-independent/evidence/consumer-replay/{name}','submitted':f'candidates/round-01/consumer-v02/{name}',**diff(Image.open(OUT/'consumer-replay'/name),Image.open(C/'consumer-v02'/name))})
(OUT/'visual-coverage-mappings.json').write_text(json.dumps({'phaseSheets':rows,'consumerReplayAliases':replays,'actualAPNGCoverage':'independent-pixel-proof.json verifies every decoded APNG phase equals the exact published frame. All four phase sheets were directly visually inspected; actual CSS playback phase-identification.json captures every phase in order and wrap over multiple loops.','invalidCanvasSampler':'playback/actual-browser-playback.json stores only a default frame per direction because drawImage animated image freezes its default frame; it is not counted as actual temporal evidence. True compositor screenshots under playback-actual-css supply temporal evidence.'},indent=2)+'\n')
print('all48 sheet mappings exact',all(x['differentChannels']==0 for x in rows),'consumer12 replay aliases exact',all(x['differentChannels']==0 for x in replays))
