from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import json,hashlib,sys,shutil
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent
mode=sys.argv[1] if len(sys.argv)>1 else 'historical'
folder=BASE/'captures'/mode
results={}
sheet=Image.new('RGB',(4*300,430),(144,144,144));draw=ImageDraw.Draw(sheet)
for ix,d in enumerate('NESW'):
 raw=Image.open(folder/f'native-{d}-4x.png').convert('RGBA')
 resample=Image.Resampling.LANCZOS if mode=='historical' else Image.Resampling.BOX
 pub=raw.resize((384,704),resample);pub.save(folder/f'published-{d}-2x.png')
 if mode=='historical':
  known=Image.open(BASE/f'resources/historical/static-{d}.png').convert('RGBA')
  diff=ImageChops.difference(pub,known);counts=sum(p!=(0,0,0,0) for p in diff.getdata())
  results[d]={'pixelsDifferent':counts,'maximumRGBA':[v[1] for v in diff.getextrema()],'replaySHA256':hashlib.sha256((folder/f'published-{d}-2x.png').read_bytes()).hexdigest(),'historicalSHA256':hashlib.sha256((BASE/f'resources/historical/static-{d}.png').read_bytes()).hexdigest(),'exactPngByteMatch':(folder/f'published-{d}-2x.png').read_bytes()==(BASE/f'resources/historical/static-{d}.png').read_bytes()}
 # Display at actual cell128: full logical source frame; crop only the evidence display after registered rendering.
 logical=pub.resize((192,352),Image.Resampling.BOX)
 crop=logical.crop((12,145,180,306))
 enlarged=crop.resize((252,242),Image.Resampling.NEAREST)
 sheet.paste(enlarged,(ix*300+24,48),enlarged)
 draw.text((ix*300+20,15),f'{d}: cell128 shown x1.5',fill='white')
 phone=logical.resize((48,88),Image.Resampling.BOX);sheet.paste(phone,(ix*300+120,310),phone);draw.text((ix*300+95,407),'cell32',fill='white')
sheet.save(folder/'all4-source-sheet.png')
(folder/'comparison.json').write_text(json.dumps({'recipe':mode,'resample':resample.name,'results':results},indent=2)+'\n')
loaded=[]
for name,m in sorted(sys.modules.items()):
 p=getattr(m,'__file__',None)
 if p and ('/PIL/' in p):
  p=Path(p);dest=BASE/'resources/python-library/PIL'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
  loaded.append({'module':name,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(BASE/'resources/python-loaded-modules.json').write_text(json.dumps(loaded,indent=2)+'\n')
print(json.dumps(results,indent=2))
