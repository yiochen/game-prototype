from pathlib import Path
from PIL import Image
import json,hashlib
here=Path(__file__).resolve().parent
source=here/'raw/hiring-stamp-cutout.png'
image=Image.open(source)
bounds=image.getchannel('A').point(lambda value:255 if value>=32 else 0).getbbox()
image.crop(bounds).save(here/'assets/hiring-stamp.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=here.parents[1]
refs=['design/art-directions/restaurant-item-catalog.png','review/16/application-motion/phone-01-applicants.png']
record={'tool':'built-in image_gen.imagegen','generation_origins':['/Users/yiouchen/.codex/generated_images/01a17712-262b-7de3-8a16-0aa83c438c0b/exec-d0f30f88-2e38-4bc7-8999-b3e772f32e95.png','/Users/yiouchen/.codex/generated_images/01a17712-262b-7de3-8a16-0aa83c438c0b/exec-11845d31-633d-44c2-85ad-aa4ef3aff6bb.png'],'prompts':['hiring-stamp-prompt.txt','hiring-stamp-cutout-prompt.txt'],'full_originals':{name:sha(here/'raw'/name) for name in ['hiring-stamp-v1.png','hiring-stamp-cutout.png']},'references':{name:sha(root/name) for name in refs},'derivative':{'path':'assets/hiring-stamp.png','sha256':sha(here/'assets/hiring-stamp.png'),'source_crop_ltrb':bounds,'resize':'No resampling; render with uniform contain fitting','anchor':'Visible bottom-center rubber contact edge'},'imprint':'Existing independent assigned-stamp frame with live Hired text; no labels baked into prop'}
(here/'hiring-stamp-provenance.json').write_text(json.dumps(record,indent=2)+'\n')
print(bounds,image.size)
