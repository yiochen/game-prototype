"""Rebuild copied current consumer from the bound portable snapshot. No production access or writes."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image,ImageChops
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
SNAP=HERE/'resources/current-consumer';CON=HERE/'consumer';OUT=BASE/'candidates/round-01';CON.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
files=json.loads((SNAP/'snapshot-manifest.json').read_text())
for rel,record in files.items():
 src=SNAP/rel;dest=CON/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 assert sha(src)==record['sha256'];shutil.copyfile(src,dest)
 assert sha(dest)==record['sha256']
shutil.copyfile(HERE/'bench.gd',CON/'bench.gd')
shutil.copyfile(HERE/'consumer-project.godot',CON/'project.godot')
shutil.copyfile(BASE/'inputs/original.png',CON/'original.png');shutil.copyfile(OUT/'goods.png',CON/'candidate.png')
manifest=json.loads((CON/'assets/ui/editor-goods/manifest.json').read_text());assert list(manifest['sprites'])==['belt-straight-e','stool-wood','plant-angular','crate-wood','barrel-wood','floor-cream']
original=Image.open(CON/'baseline-atlas.png').convert('RGBA');current=original.copy();candidate=Image.open(CON/'candidate.png').convert('RGBA')
x,y,w,h=manifest['sprites']['barrel-wood']['region'];assert candidate.size==(w,h)==(384,384);current.paste(candidate,(x,y));current.save(CON/'assets/ui/editor-goods/atlas.png')
rect=lambda r:(r[0],r[1],r[0]+r[2],r[1]+r[3])
checks={}
for identity,v in manifest['sprites'].items():
 a=original.crop(rect(v['region']));b=current.crop(rect(v['region']));checks[identity]={'unchangedPixels':a.tobytes()==b.tobytes(),'baselinePixelSHA256':hashlib.sha256(a.tobytes()).hexdigest(),'candidatePixelSHA256':hashlib.sha256(b.tobytes()).hexdigest()}
assert all(v['unchangedPixels'] for k,v in checks.items() if k!='barrel-wood')
floor=current.crop(rect(manifest['sprites']['floor-cream']['region']))
assert sha(CON/'floor-cream.png')=='6ded9330f3106d1d4941ac84e94c3e54436f098d261f5f36436d7115af239177'
assert hashlib.sha256(floor.tobytes()).hexdigest()=='1cee44c04199f35fd17b2774d667dfa7ed95656ad2b8f88f16df628d2d8a1ce1'
masked=current.copy();masked.paste(original.crop((x,y,x+w,y+h)),(x,y));assert masked.tobytes()==original.tobytes()
report={'copiedCurrentFiles':files,'sixGoods':list(manifest['sprites']),'candidateOnlyRect':[x,y,w,h],'onlyCandidateRectChanged':True,'cellSize384Preserved':True,'floorSourceSHA256':sha(CON/'floor-cream.png'),'floorAtlasPixelSHA256':hashlib.sha256(floor.tobytes()).hexdigest(),'atlasChecks':checks,'baselineAtlasSHA256':sha(CON/'baseline-atlas.png'),'copiedCandidateAtlasSHA256':sha(CON/'assets/ui/editor-goods/atlas.png'),'consumerCodeUnchanged':all(v['sha256']==v['copiedSHA256'] for v in files.values()),'qualification':'Isolated actual current card consumer. Solid room placeholder; no room/world rendering claim. Only barrel region differs in copied atlas.'}
(OUT/'consumer-parity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'consumer':str(CON),'allOtherGoodsAndFloorPixelsUnchanged':True,'filesCopied':len(files)}))
