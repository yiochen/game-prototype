import json,hashlib,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent/"round-03-resources/python-library"))
from PIL import Image,ImageDraw
BASE=Path(__file__).resolve().parent;E=BASE.parent/'candidates/round-03'
proof={}
for d in 'NESW':
 raw=Image.open(E/f'native-{d}-4x.png').convert('RGBA');pub=raw.resize((384,704),Image.Resampling.BOX)
 pack=E/'atlases'/d;pack.mkdir(parents=True,exist_ok=True);pub.save(pack/'sheet.png');pub.save(E/f'static-{d}.png')
 joined=Image.open(E/f'native-strip-{d}-4x.png').convert('RGBA').resize((896,1216),Image.Resampling.BOX);joined.save(E/f'strip-{d}-2x.png')
 source=Image.open(pack/'sheet.png').convert('RGBA');assert source.tobytes()==pub.tobytes()
 proof[d]={'nativeFrame':list(raw.size),'publishedFrame':list(source.size),'operation':'Pillow BOX on complete RGBA native canvas, no other pixel operations','wholeRGBAPixelIdentity':True,'nativeSHA256':hashlib.sha256((E/f'native-{d}-4x.png').read_bytes()).hexdigest(),'publishedSHA256':hashlib.sha256((E/f'static-{d}.png').read_bytes()).hexdigest(),'atlasSHA256':hashlib.sha256((pack/'sheet.png').read_bytes()).hexdigest(),'layout':{'columns':1,'rows':1,'frameOrder':[0],'frame':[192,352],'root':[96,248],'sourceScale':2,'sourceRect':[0,0,384,704]}}
 (pack/'guide.json').write_text(json.dumps(proof[d]['layout'],indent=2)+'\n')
(E/'publication-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
# Full-canvas native four-view contact sheet is technical evidence; no per-view fit or crop.
full=Image.new('RGBA',(3072,1408));
for i,d in enumerate('NESW'):full.alpha_composite(Image.open(E/f'native-{d}-4x.png').convert('RGBA'),(768*i,0))
full.save(E/'native-all4-4x.png')
# Declared review sheet. Exact source2x all4, logical128cell all3 backgrounds, phone32cell all3.
W=1560;H=704+24+3*(352+24)+3*(88+24);sheet=Image.new('RGB',(W,H),'#243044');dr=ImageDraw.Draw(sheet)
def comp(im,bg):
 back=Image.new('RGBA',im.size,bg);back.alpha_composite(im);return back.convert('RGB')
y=0
for i,d in enumerate('NESW'):
 dr.text((i*390+4,y+4),d+' source384x704 · wholeBOX',fill='white');sheet.paste(comp(Image.open(E/f'static-{d}.png').convert('RGBA'),'#eef2ed'),(i*390,y+24))
y=728
for name,bg in [('light','#eef2ed'),('gray','#909090'),('dark','#172539')]:
 dr.text((4,y+4),'All4 logical192x352 /128cell · '+name,fill='white')
 for i,d in enumerate('NESW'):sheet.paste(comp(Image.open(E/f'static-{d}.png').convert('RGBA').resize((192,352),Image.Resampling.BOX),bg),(i*390,y+24))
 y+=376
for name,bg in [('light','#eef2ed'),('gray','#909090'),('dark','#172539')]:
 dr.text((4,y+4),'All4 phone48x88 /32cell · '+name,fill='white')
 for i,d in enumerate('NESW'):sheet.paste(comp(Image.open(E/f'static-{d}.png').convert('RGBA').resize((48,88),Image.Resampling.BOX),bg),(i*390,y+24))
 y+=112
sheet.save(E/'four-view-sheet.png')
