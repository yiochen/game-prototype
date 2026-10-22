from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;O=H.parent;C=O/'candidates/round-05';p=C/'previews/before-after-fourviews.png';p.parent.mkdir(exist_ok=True)
im=Image.new('RGBA',(1536,1280),'#70757a');records=[]
for row,round in enumerate(['round-04','round-05']):
 for col,d in enumerate(['N','E','S','W']):
  src=O/'candidates'/round/'frames'/('stand-'+d)/'000.png';im.alpha_composite(Image.open(src).convert('RGBA'),(384*col,640*row));ImageDraw.Draw(im).text((384*col+12,640*row+12),round+' '+d+' / exact full frame',fill='white');records.append({'round':round,'direction':d,'source':str(src.relative_to(O)),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'offset':[384*col,640*row],'fitting':False})
im.convert('RGB').save(p);(C/'before-after-provenance.json').write_text(json.dumps({'path':str(p.relative_to(O)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'placements':records},indent=2)+'\n')
