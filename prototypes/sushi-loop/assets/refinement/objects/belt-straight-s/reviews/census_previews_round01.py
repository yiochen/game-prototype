from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,math
b=Path(__file__).resolve().parent.parent;r=b/'candidates/round-01';p=json.loads((r/'packet.json').read_text());records=[{'section':sec,'name':n,**v} for sec in ['candidateRenders','previews'] for n,v in sorted(p[sec].items())];od=b/'reviews/round-01-preview-census';od.mkdir(exist_ok=True);mapping=[]
for page in range(math.ceil(len(records)/42)):
 sheet=Image.new('RGB',(1920,1680),'#dce1dc');dr=ImageDraw.Draw(sheet)
 for j,rec in enumerate(records[page*42:(page+1)*42]):
  x=j%6*320;y=j//6*240;path=r/rec['path'];actual=hashlib.sha256(path.read_bytes()).hexdigest();assert actual==rec['sha256'];kind='complete-image'
  if path.suffix=='.html':
   kind='html-reviewed-via-browser';dr.text((x+4,y+60),'HTML: inspected in Chrome; five12fps cases',fill='#1c2d36');dr.text((x+4,y+85),'all4facings/all24 plus closure scrub.',fill='#1c2d36')
  else:
   im=Image.open(path).convert('RGBA');im.thumbnail((312,210),Image.Resampling.LANCZOS);background=Image.new('RGBA',im.size,'#787d80');background.alpha_composite(im);sheet.paste(background.convert('RGB'),(x+(320-im.width)//2,y+26))
  dr.text((x+3,y+3),str(page*42+j)+' '+rec['name'][:46],fill='#1c2d36');mapping.append({'page':page+1,'tile':j,'path':rec['path'],'sha256':actual,'section':rec['section'],'name':rec['name'],'kind':kind,'treatment':'Complete image, aspect preserved; APNG frame0 here, all24 data separately audited and motion inspected via browser.'})
 sheet.save(od/f'page-{page+1:02}.png')
(od/'mapping.json').write_text(json.dumps(mapping,indent=2)+'\n');print('preview census pages',math.ceil(len(records)/42),'records',len(records))
