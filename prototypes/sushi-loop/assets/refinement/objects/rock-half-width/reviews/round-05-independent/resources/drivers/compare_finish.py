from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
B=Path(__file__).resolve().parents[2];obj=B.parents[1];out=B/'evidence';canvas=Image.new('RGB',(832,1434),(220,227,229));dr=ImageDraw.Draw(canvas);rows=[]
for r,round_name in enumerate(['round-03','round-04','round-05']):
 for c,d in enumerate('NESW'):
  n=f'candidates/{round_name}/frames/static/{d}/000.png';p=(B/'resources/comparison-inputs'/n) if round_name!='round-05' else obj/n;im=Image.open(p).convert('RGBA');logical=im.resize((192,352),Image.Resampling.BOX);bg=Image.new('RGBA',logical.size,(122,137,148,255));bg.alpha_composite(logical);canvas.paste(bg.convert('RGB'),(c*208+8,r*478+24));dr.text((c*208+8,r*478+5),f'{round_name} {d} / native logical128',fill=(10,20,30));small=im.resize((48,88),Image.Resampling.BOX);bg=Image.new('RGBA',small.size,(122,137,148,255));bg.alpha_composite(small);canvas.paste(bg.convert('RGB'),(c*208+80,r*478+380));rows.append({'round':round_name,'direction':d,'source':str(p.relative_to(obj)),'sourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'logicalReduction':'Whole frame BOX to192x352 atcell128; lower small frame wholeBOX to48x88 atcell32, native diagnostic only, actual CSS consumer separately inspected.'})
canvas.save(out/'native-finish-03-04-05.png');(out/'native-finish-comparison.json').write_text(json.dumps({'images':rows,'processing':'Complete published frames, uniform wholeimage BOX only; fixed density across rounds. Lower32 native diagnostic is not a substitute for actual CSS phone captures.'},indent=2)+'\n')
