from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json, hashlib, math
BASE=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets')
OBJ=BASE/'refinement/objects/garbage-shelving'; OUT=OBJ/'reviews/source-audit';CAT=json.loads((OBJ/'inputs/catalog-object.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
frames={};report=[]
for c in CAT['clips']:
 for d,v in c['directions'].items():
  p=BASE/'production'/v['image'];im=Image.open(p).convert('RGBA')
  rr={'clip':c['id'],'direction':d,'path':str(p),'sha256':sha(p),'size':list(im.size),'columns':v['columns'],'rows':v['rows'],'frames':[]}
  for i,rect in enumerate(v['rects']):
   x,y,w,h=rect;fr=im.crop((x,y,x+w,y+h));frames[c['id'],d,i]=fr;a=fr.getchannel('A')
   rr['frames'].append({'frame0':i,'rgbaSHA256':hashlib.sha256(fr.tobytes()).hexdigest(),'alphaSHA256':hashlib.sha256(a.tobytes()).hexdigest(),'bboxAlphaGT0':a.getbbox(),'bboxAlphaGE128':a.point(lambda v:255 if v>=128 else 0).getbbox(),'alphaExtrema':a.getextrema(),'alphaMass':sum(n*i for i,n in enumerate(a.histogram()))/255,'opaquePixels':a.histogram()[255],'nonzeroPixels':sum(a.histogram()[1:])})
  rr['uniqueRGBA']=len(set(x['rgbaSHA256'] for x in rr['frames']));rr['uniqueAlpha']=len(set(x['alphaSHA256'] for x in rr['frames']));report.append(rr)
backgrounds={'light':(235,231,219,255),'gray':(118,118,118,255),'dark':(27,34,41,255)}
for d in ['N','E','S','W']:
 for c in ['highlighted','clearance']:
  imgs=[frames[c,d,i] for i in range(12)];bboxes=[x.getchannel('A').getbbox() for x in imgs];box=(min(b[0] for b in bboxes)-12,min(b[1] for b in bboxes)-12,max(b[2] for b in bboxes)+12,max(b[3] for b in bboxes)+12)
  sh=Image.new('RGB',(1200,660),(80,80,80));dr=ImageDraw.Draw(sh)
  for i,fr in enumerate(imgs):
   cr=fr.crop(box);cr.thumbnail((196,300));tile=Image.new('RGBA',(200,330),backgrounds['gray']);tile.alpha_composite(cr,((200-cr.width)//2,20+(300-cr.height)//2));sh.paste(tile.convert('RGB'),((i%6)*200,(i//6)*330));dr.text(((i%6)*200+5,(i//6)*330+3),f'{c} {d} {i:02}',fill='white')
  sh.save(OUT/f'published-{c}-{d}-all12.png')
sh=Image.new('RGB',(448*4,672*3),(80,80,80));dr=ImageDraw.Draw(sh)
for row,(bg,col) in enumerate(backgrounds.items()):
 for j,d in enumerate(['N','E','S','W']):
  im=frames['idle',d,0].resize((448,672),Image.Resampling.LANCZOS);base=Image.new('RGBA',im.size,col);base.alpha_composite(im);sh.paste(base.convert('RGB'),(j*448,row*672));dr.text((j*448+8,row*672+8),f'idle {d} logical 448x672 {bg}',fill='white')
sh.save(OUT/'published-idle-four-facing-backgrounds.png')
# Phone-size actual full-frame output 224x336, not fitted subject.
sh=Image.new('RGB',(224*4,336*3),(80,80,80));dr=ImageDraw.Draw(sh)
for row,(bg,col) in enumerate(backgrounds.items()):
 for j,d in enumerate(['N','E','S','W']):
  im=frames['idle',d,0].resize((224,336),Image.Resampling.LANCZOS);base=Image.new('RGBA',im.size,col);base.alpha_composite(im);sh.paste(base.convert('RGB'),(j*224,row*336));dr.text((j*224+8,row*336+8),f'{d} phone 224x336 {bg}',fill='white')
sh.save(OUT/'published-idle-phone-backgrounds.png')
refs=[]
for name in ['original.png','target.png']:
 p=OBJ/'inputs'/name;im=Image.open(p);refs.append({'path':str(p),'sha256':sha(p),'size':im.size,'mode':im.mode,'alphaExtrema':im.getchannel('A').getextrema() if 'A' in im.getbands() else None,'alphaBBox':im.getchannel('A').getbbox() if 'A' in im.getbands() else None})
refs.append({'path':str(BASE/'refinement/style/warm-soft-reference.png'),'sha256':sha(BASE/'refinement/style/warm-soft-reference.png')})
(OUT/'published-raster-audit.json').write_text(json.dumps({'atlasFrames':report,'referenceFiles':refs,'originalEqualsPublishedIdleS':sha(OBJ/'inputs/original.png')==sha(BASE/'production/sprites/garbage-shelving/idle-S.png'),'note':'Contact sheets use a constant direction/clip crop only for legibility. Published input files remain unchanged; final candidate required full registered frames.'},indent=2)+'\n')
print(json.dumps({'refs':refs,'uniqueFrames':[{'clip':r['clip'],'direction':r['direction'],'RGBA':r['uniqueRGBA'],'alpha':r['uniqueAlpha']} for r in report]},indent=2))
