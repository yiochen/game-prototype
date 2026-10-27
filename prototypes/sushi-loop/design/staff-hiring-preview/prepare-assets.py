"""Deterministic source crops; no repainting or resizing of original artwork."""
from PIL import Image
from pathlib import Path
import json,hashlib,shutil
here=Path(__file__).resolve().parent
root=here.parents[1]
origin=Path('/Users/yiouchen/.codex/generated_images/01a17712-262b-7de3-8a16-0aa83c438c0b/exec-0cd447e7-c940-4d85-9089-44535c4fa2e1.png')
raw=here/'raw'; assets=here/'assets';assets.mkdir(exist_ok=True)
if not (raw/'resume-paper.png').exists():shutil.copyfile(origin,raw/'resume-paper.png')
# Plain middle spans, symmetric 170px corners; retain tiny organic edge texture.
Image.open(raw/'resume-paper.png').crop((24,120,1058,1344)).save(assets/'resume-paper.png')
for name,rect in [('photo-outer',(132,103,1094,1203)),('photo-inner',(123,145,1131,1111)),('assigned-stamp',(64,120,2112,608))]:
 src={'photo-outer':'outer-paper','photo-inner':'inner-picture','assigned-stamp':'assigned-stamp'}[name]
 Image.open(root/f'assets/ui/people-photos/v2/raw/{src}.png').crop(rect).save(assets/f'{name}.png')
library=json.loads((root/'assets/production/library.json').read_text())
for chef in ['lena','omar','ama','mateo','noor','dalia','ellis','rowan']:
 obj=next(x for x in library['objects'] if x['id']=='chef-'+chef)
 clip=next(x for x in obj['clips'] if x['id']=='idle')['directions']['S']
 x,y,w,h=clip['rects'][0]
 Image.open(root/'assets/production'/clip['image']).crop((x,y,x+w,y+h)).save(assets/f'world-{chef}.png')
for object_id in ['floor-cream','belt-straight-e','belt-start-e','belt-end-e']:
 obj=next(x for x in library['objects'] if x['id']==object_id)
 clip=obj['clips'][0]['directions']['S']
 x,y,w,h=clip['rects'][0]
 Image.open(root/'assets/production'/clip['image']).crop((x,y,x+w,y+h)).save(assets/f'world-{object_id}.png')
refs=['design/art-directions/restaurant-item-catalog.png','assets/ui/editor/v4/raw/b-indigo-ceramic.png','assets/ui/chef-headshots/v1/raw/ama.png']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'tool':'built-in image_gen.imagegen','origin':str(origin),'prompt':'paper-prompt.txt','references':{p:sha(root/p) for p in refs},'original':{'path':'raw/resume-paper.png','sha256':sha(raw/'resume-paper.png')},'calibration':{'source_crop_xywh':[24,120,1034,1224],'nine_slice_px':[170,170,170,170],'destination_border_px':36,'safe_content_insets_px':[20,20,20,20],'plain_center':'Only central paper and plain edge spans resize; corners retain uniform 36/170 scale.'},'derived':{p.name:sha(p) for p in assets.glob('*.png')}}
(here/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
