import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parents[1];C=B/'candidates/round-03';P=C/'previews'
previews=json.loads((C/'previews-map.json').read_text());delivery=json.loads((B/'delivery.json').read_text())
def save(im,name):
 p=P/(name+'.png');im.save(p);previews[name]=str(p.relative_to(B));delivery['previews'][name]=str(p.relative_to(B))
for scale in(1,2):
 sheet=Image.new('RGB',(192*4*scale,352*scale+28),(122,126,132));d=ImageDraw.Draw(sheet)
 for i,view in enumerate('NESW'):
  im=Image.open(C/'raw'/f'static-{view}-0000.png').getchannel('A').convert('RGB').resize((192*scale,352*scale),Image.Resampling.LANCZOS)
  sheet.paste(im,(i*192*scale,28));d.text((i*192*scale+8,8),view+' alpha '+('logical'if scale==1 else'enlarged'),fill='white')
 save(sheet,'four-view-alpha-'+('logical'if scale==1 else'enlarged'))
for view in 'NESW':
 sheet=Image.new('RGB',(896,640),(122,126,132));d=ImageDraw.Draw(sheet)
 for col,method in enumerate(('native-joins','sprite-joins')):
  im=Image.open(C/method/f'static-{view}-WS.png').getchannel('A').convert('RGB').resize((448,608),Image.Resampling.LANCZOS)
  sheet.paste(im,(col*448,28));d.text((col*448+8,8),view+' / '+method+' alpha at logical pitch128',fill='white')
 save(sheet,f'join-{view}-WS-alpha-logical')
(C/'previews-map.json').write_text(json.dumps(previews,indent=2))
v=json.loads((C/'validation.json').read_text());v['alphaReviewSurfaces']={k:p for k,p in previews.items()if'alpha' in k};(C/'validation.json').write_text(json.dumps(v,indent=2))
p='source/add-alpha-evidence.py';delivery['supportingRecipes'].append(p);delivery['resources'].append({'name':'recipe-add-alpha-evidence','path':p,'sha256':hashlib.sha256((B/p).read_bytes()).hexdigest()})
(B/'delivery.json').write_text(json.dumps(delivery,indent=2))
print('Added logical and enlarged alpha evidence; preview count',len(previews))

