"""Copy unchanged first production frames and record their grid-root calibration."""
import json,hashlib
from pathlib import Path
from PIL import Image
here=Path(__file__).resolve().parent
root=here.parents[1]
lib=json.loads((root/'assets/production/library.json').read_text())
records={}
for name in ['stool-wood','plant-angular','crate-wood','barrel-wood','belt-straight-e']:
 obj=next(o for o in lib['objects'] if o['id']==name)
 clip=obj['clips'][0]['directions']['S'];x,y,w,h=clip['rects'][0]
 src=root/'assets/production'/clip['image'];dest=here/f'assets/world-{name}.png'
 Image.open(src).crop((x,y,x+w,y+h)).save(dest)
 records[name]={'source':str(src.relative_to(root)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'crop_xywh':[x,y,w,h],'frame_size':obj['frameSize'],'root':obj['root'],'source_scale':obj['sourceScale'],'destination':str(dest.relative_to(here)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
(here/'world-registration.json').write_text(json.dumps(records,indent=2)+'\n')
