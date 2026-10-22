import pathlib,json,hashlib,sys,importlib.util,shutil
sys.dont_write_bytecode=True
sys.path.insert(0,str(pathlib.Path(__file__).parent/'resources/python-library'))
from PIL import Image,ImageChops,ImageStat,ImageDraw
BASE=pathlib.Path(__file__).parent;RES=BASE/'resources';E=BASE/'evidence'
sys.path.insert(0,str(RES/'packing'));from pack_captures import pack
stats={}
for d in 'NESW':
 raw=E/'raw'/d;raw.mkdir(parents=True,exist_ok=True);shutil.copyfile(E/f'source-{d}-4x.png',raw/'000.png')
 out=E/'packs'/d
 pack(raw,E/f'camera-{d}.json',out,kind='object',columns=1,gutter=0,sheet_scale=2)
 # Native strip uses identical complete-canvas declared 4x->2x Lanczos.
 n=Image.open(E/f'joined-{d}-4x.png').convert('RGBA');n.resize((896,1216),Image.Resampling.LANCZOS).save(E/f'joined-{d}-2x.png')
 a=Image.open(RES/f'historical/static-{d}.png').convert('RGBA');b=Image.open(out/'sheet.png').convert('RGBA')
 dif=ImageChops.difference(a,b);stats[d]={'historicalSHA256':hashlib.sha256((RES/f'historical/static-{d}.png').read_bytes()).hexdigest(),'replaySHA256':hashlib.sha256((out/'sheet.png').read_bytes()).hexdigest(),'maxRGBA':dif.getextrema(),'meanRGBA':ImageStat.Stat(dif).mean,'originalAlphaBBox':a.getchannel('A').getbbox(),'replayAlphaBBox':b.getchannel('A').getbbox(),'differentPixels':sum(1 for p in dif.getdata() if any(p))}
# Registered complete-frame comparisons; no alpha-fit, recolor or image repairs.
board=Image.new('RGB',(1536,1510),'#909090');draw=ImageDraw.Draw(board)
for i,d in enumerate('NESW'):
 for row,(name,img) in enumerate([('historical',Image.open(RES/f'historical/static-{d}.png').convert('RGBA')),('source replay',Image.open(E/'packs'/d/'sheet.png').convert('RGBA'))]):
  x=i*384;y=row*752;board.paste(img,(x,y+28),img);draw.text((x+8,y+6),f'{d} {name}, 2x frame384x704',fill='white')
board.save(E/'historical-replay-all4.png');(E/'historical-replay-differences.json').write_text(json.dumps(stats,indent=2))
# Log exact executed Pillow modules; frozen closure is retained read-only in resources/python-library.
modrecords=[]
for name,mod in sorted(sys.modules.items()):
 path=getattr(mod,'__file__',None)
 if name.startswith('PIL') and path and pathlib.Path(path).is_file():
  p=pathlib.Path(path);modrecords.append({'module':name,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(E/'python-loaded-modules.json').write_text(json.dumps({'python':sys.version,'Pillow':Image.__version__,'modules':modrecords},indent=2))
print(json.dumps(stats,indent=2))
