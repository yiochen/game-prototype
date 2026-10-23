from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json,hashlib,math
BASE=Path(__file__).resolve().parent.parent
OUT=BASE/'reviews'
PROD=BASE.parents[2]/'production'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def info(im):
 a=im.getchannel('A');pts=[(i%im.width,i//im.width,v) for i,v in enumerate(a.getdata()) if v]
 total=sum(v for x,y,v in pts)
 return {'size':list(im.size),'alphaBounds':a.getbbox(),'alpha16Bounds':a.point(lambda v:255 if v>=16 else 0).getbbox(),'nonzeroPixels':len(pts),'alphaWeightedArea':total/255,'alphaCentroid':[sum(x*v for x,y,v in pts)/total,sum(y*v for x,y,v in pts)/total] if total else None}
audit={'sourceAtlases':{},'references':{},'frames':[],'diagnostics':[]}
font=ImageFont.load_default()
for d in 'NESW':
 p=PROD/f'sprites/coin-pop/pop-{d}.png';im=Image.open(p).convert('RGBA')
 audit['sourceAtlases'][d]={'path':str(p),'sha256':sha(p),'size':list(im.size),'decodedPixelSHA256':hashlib.sha256(im.tobytes()).hexdigest()}
 sheet=Image.new('RGB',(1152,752),(62,66,72));draw=ImageDraw.Draw(sheet)
 for i in range(12):
  x=(i%6)*384;y=(i//6)*704;fr=im.crop((x,y,x+384,y+704));s=info(fr)
  audit['frames'].append({'direction':d,'index':i,'phase':i/11,'rgbaSHA256':hashlib.sha256(fr.tobytes()).hexdigest(),**s})
  small=fr.resize((192,352),Image.Resampling.LANCZOS);xx=(i%6)*192;yy=(i//6)*376
  bg=Image.new('RGBA',(192,352),(235,231,221,255));bg.alpha_composite(small);sheet.paste(bg.convert('RGB'),(xx,yy+24))
  draw.text((xx+5,yy+5),f'{d} {i:02d} / {i/12:.3f}s',fill='white',font=font)
  draw.line((xx+91,yy+24+256,xx+101,yy+24+256),fill=(90,140,190));draw.line((xx+96,yy+24+251,xx+96,yy+24+261),fill=(90,140,190))
 out=OUT/f'original-whole-canvas-{d}.png';sheet.save(out);audit['diagnostics'].append({'path':str(out),'sha256':sha(out),'type':'all 12 original full canvases at logical size; blue root cross diagnostic'})
for name,p in [('original',BASE/'inputs/original.png'),('target',BASE/'inputs/target.png'),('styleReference',BASE/'../../style/warm-soft-reference.png')]:
 im=Image.open(p).convert('RGBA');audit['references'][name]={'path':str(p.resolve()),'sha256':sha(p),**info(im)}
# Side by side alpha crops are aesthetic diagnostics, with explicit independent zoom; never registration evidence.
sheet=Image.new('RGB',(1200,730),(62,66,72));draw=ImageDraw.Draw(sheet)
for idx,name in enumerate(('original','target')):
 p=BASE/'inputs'/f'{name}.png';im=Image.open(p).convert('RGBA');crop=im.crop(im.getchannel('A').getbbox());crop.thumbnail((540,500),Image.Resampling.LANCZOS)
 for j,bgcol in enumerate(((244,240,230),(111,115,124),(25,28,35))):
  small=im.resize((192,352),Image.Resampling.LANCZOS)
  bg=Image.new('RGBA',(192,352),bgcol+(255,));bg.alpha_composite(small);sheet.paste(bg.convert('RGB'),(idx*600+j*194,350))
 bg=Image.new('RGBA',(580,320),(111,115,124,255));c=crop.copy();c.thumbnail((540,290),Image.Resampling.LANCZOS);bg.alpha_composite(c,((580-c.width)//2,(320-c.height)//2));sheet.paste(bg.convert('RGB'),(idx*600,25))
 draw.text((idx*600+10,8),f'{name}: independent crop zoom above; full canvas logical-size diagnostic below',fill='white')
out=OUT/'original-target-backgrounds.png';sheet.save(out);audit['diagnostics'].append({'path':str(out),'sha256':sha(out),'type':'appearance only; top independently zoomed; bottom whole-canvas scaled'})
(OUT/'original-atlas-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({'atlasHashes':audit['sourceAtlases'],'references':audit['references'],'sourceFramesS':[f for f in audit['frames'] if f['direction']=='S']},indent=2))
