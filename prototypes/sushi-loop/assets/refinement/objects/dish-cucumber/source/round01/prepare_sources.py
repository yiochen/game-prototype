"""Freeze existing raster inputs without artistic edits. Run before publishing."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image
O=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;R=S/'resources';P=O/'../../../production'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,dst):
 dst=S/dst;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);return {'path':str(dst.relative_to(O)),'sha256':sha(dst),'originalPath':str(src.relative_to(O)) if src.is_relative_to(O) else str(src)}
resources=[]
for src,dst in [(O/'inputs/target.png','resources/fixed-target-raw.png'),(O/'inputs/original.png','resources/original-registered.png'),(P/'source/2d/generated/dish-cucumber.png','resources/original-artwork.png'),(O/'../../backups/dd6d82508f72b2d9-dish-cucumber.png','resources/original-backup.png'),(O/'../../style/warm-soft-reference.png','resources/warm-soft-reference.png'),(O/'inputs/imagegen-prompt.txt','resources/exact-imagegen-target-prompt.txt'),(O/'brief.json','resources/frozen-brief.json'),(O/'inputs/catalog-object.json','resources/original-catalog-object.json')]:resources.append(copy(src,dst))
for name in ['README.md','publish_2d.py','prompts.json','overrides.json']:resources.append(copy(O/'inputs/original-2d-pipeline'/name,'resources/original-2d-pipeline/'+name))
library=json.loads((P/'library.json').read_text());ids=['dish-cucumber','belt-straight-e','stool-wood','customer-rosa','bubble-preference'];objects=[v for v in library['objects'] if v['id'] in ids]
(S/'resources/context-library.json').write_text(json.dumps({'originalLibrarySHA256':sha(P/'library.json'),'objects':objects},indent=2)+'\n')
resources.append({'path':str((R/'context-library.json').relative_to(O)),'sha256':sha(R/'context-library.json'),'originalPath':'../../../production/library.json','note':'Exact selected object records, subset preserves original record values.'})
need=[('belt-straight-e','running','S'),('stool-wood','static','S'),('customer-rosa','seated-wait','N')]+[('customer-rosa','eat',d)for d in ['N','E','S','W']]
for ident,clip,d in need:
 obj=next(o for o in objects if o['id']==ident);c=next(c for c in obj['clips'] if c['id']==clip);rel=c['directions'][d]['image'];resources.append(copy(P/rel,'resources/context/'+rel))
for src,dst in [(P/'source/2d/generated/bubble-preference.png','resources/context/bubble-preference-raw.png'),(P/'source/blender/character_composition.py','resources/context/character_composition.py'),(P/'source/variants/starter-meals/author_meals.py','resources/context/author_meals.py')]:resources.append(copy(src,dst))
raw=Image.open(R/'fixed-target-raw.png').convert('RGBA');box=raw.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox();canonical=raw.crop(box);canonical.save(S/'dish-cucumber.png')
assert canonical.tobytes()==raw.crop(box).tobytes()
assert sha(R/'original-artwork.png')==sha(R/'original-backup.png')=='dd6d82508f72b2d9019f1619e5f1fe878a5ad22935ab8c86d7a79b4434f64776'
report={'asset':'dish-cucumber','round':'round01','representation':'existing-imagegen-2d','generation':{'provider':'Built-in ImageGen','newGenerationForCandidate':False,'adoptedFixedTarget':True,'fixedTargetSHA256':sha(R/'fixed-target-raw.png'),'exactPrompt':'source/round01/resources/exact-imagegen-target-prompt.txt','generationReferenceHashes':{'nativeEditSource':'3e6e91ca068eb28041b9033eddf3dd2b06a5af50081ac221e95d4f89de4cb857','styleOnly':'02e6a13e71b6aba78b85b99f70ac37117b2b6939461ed1bdb2cc3ec334ab4d15'},'rawBytesRetained':True},'canonicalCrop':{'source':'source/round01/resources/fixed-target-raw.png','rawSize':list(raw.size),'rawSHA256':sha(R/'fixed-target-raw.png'),'criterion':'bounding rectangle of raw alpha>8, once only','box':list(box),'project':'source/round01/dish-cucumber.png','canonicalSize':list(canonical.size),'canonicalSHA256':sha(S/'dish-cucumber.png'),'pixelRGBAUnchangedInsideCrop':True,'cropPixelSHA256':hashlib.sha256(canonical.tobytes()).hexdigest(),'alpha0Bounds':list(canonical.getchannel('A').getbbox()),'alpha8Bounds':list(canonical.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()),'publisherMustNotCropAgain':True},'resources':resources}
(S/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
