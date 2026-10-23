from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,shutil
out=Path(__file__).resolve().parent; root=out.parents[4]; prod=root/'production';resources=out/'resources';atlases=resources/'published-atlases';atlases.mkdir(exist_ok=True)
cat=json.loads((resources/'catalog-object.json').read_text());manifest=[];metrics=[]
for clip in cat['clips']:
 sheet=Image.new('RGB',(960,8*208+30),(125,125,125));draw=ImageDraw.Draw(sheet);draw.text((5,5),clip['id']+' / all 48 published source frames / quarter logical display',fill='white')
 for di,d in enumerate(['N','E','S','W']):
  entry=clip['directions'][d];p=prod/entry['image'];q=atlases/p.name
  if not q.exists():shutil.copyfile(p,q)
  im=Image.open(q).convert('RGBA');manifest.append({'original':str(p),'snapshot':str(q),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'bytes':q.stat().st_size})
  for i,rect in enumerate(entry['rects']):
   x,y,w,h=rect;cell=im.crop((x,y,x+w,y+h));metrics.append({'clip':clip['id'],'direction':d,'frame':i,'bbox':cell.getbbox(),'rgbaSHA256':hashlib.sha256(cell.tobytes()).hexdigest()});cell=cell.resize((160,192),Image.Resampling.LANCZOS);x=(i%6)*160;y=30+(di*2+i//6)*208;sheet.paste(cell,(x,y),cell);draw.text((x+3,y+193),f'{d} {i:02}',fill='white')
 sheet.save(out/'evidence'/('published-'+clip['id']+'-48.png'))
(out/'published-atlas-manifest.json').write_text(json.dumps(manifest,indent=2));(out/'published-frame-metrics.json').write_text(json.dumps(metrics,indent=2))
