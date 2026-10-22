from pathlib import Path
from PIL import Image,ImageChops,ImageOps,ImageFilter
import json,sys,shutil,hashlib
B=Path(__file__).resolve().parents[2];O=B/'evidence';r=json.loads((O/'consumer/record.json').read_text());run=next(x for x in r['runs'] if x['id']=='full-chromium' and x['case']['id']=='logical128-integer');records=[]
for d in 'NESW':
 c=next(x for x in run['records'] if x['direction']==d and x['kind']=='repeat' and x['background']=='gray');a=ImageOps.expand(Image.open(O/f'native-join-{d}-published.png').convert('RGBA'),border=1,fill=(0,0,0,0));b=Image.open(O/'consumer'/c['canvasFile']).convert('RGBA');aa=a.getchannel('A');delta=ImageChops.difference(aa,b.getchannel('A'));pts=[(i%a.width,i//a.width) for i,v in enumerate(delta.getdata()) if v];near=aa.point(lambda v:255 if v==0 else 0).filter(ImageFilter.MaxFilter(3));outside=sum(near.getpixel(p)>0 for p in pts);records.append({'direction':d,'alphaDifferencePixels':len(pts),'withinOnePixelOfNativeTransparentExterior':outside,'remainingInteriorAlphaDifferences':len(pts)-outside,'maxAlphaDifference':delta.getextrema()[1],'alphaDifferenceBounds':delta.getbbox()})
closure=[]
for m in list(sys.modules.values()):
 f=getattr(m,'__file__',None)
 if f and '/PIL/' in f:
  p=Path(f);q=B/'resources/python-loaded/PIL'/p.name;q.parent.mkdir(parents=True,exist_ok=True)
  if q.exists():assert q.read_bytes()==p.read_bytes()
  else:shutil.copy2(p,q)
  closure.append({'path':str(q.relative_to(B.parents[1])),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
(O/'residual-audit.json').write_text(json.dumps({'method':'Native whole-BOX join plus exact transparent1px guard versus independent current consumer native canvas; transparent-exterior neighborhood is a diagnostic, not image repair or defect waiver.','records':records,'PillowClosure':closure},indent=2)+'\n');print(json.dumps(records))
