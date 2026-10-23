from pathlib import Path
from PIL import Image
import json
BASE=Path(__file__).resolve().parent;repo=BASE.parents[8];prod=repo/'prototypes/sushi-loop/assets/production';lib=json.loads((prod/'library.json').read_text());objects=lib['objects'];objects=list(objects.values())if isinstance(objects,dict)else objects
own=json.loads((BASE/'object/inputs/catalog-object.json').read_text());records=[]
for p in own['interactions'][0]['placements'][1:]:
 o=next(x for x in objects if x['id']==p['object']);clip=next(c for c in o['clips']if c['id']==p['clip']);entry=clip['directions'][p['direction']];rect=entry['rects'][0];im=Image.open(prod/entry['image']).convert('RGBA');crop=im.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]));path=BASE/'consumer'/f"context-{o['id']}.png";crop.save(path);records.append({'object':o['id'],'placement':p,'frameSize':o['frameSize'],'root':o['root'],'sourceImage':entry['image'],'sourceRect':rect,'crop':path.name,'sourceScale':o['sourceScale']})
(BASE/'consumer/context-records.json').write_text(json.dumps(records,indent=2)+'\n')
