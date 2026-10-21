"""Once-only authorized lossless source rectangle crop. All inputs are packaged.
No painting, alpha thresholding, background removal, resizing or 3D claims.
"""
from pathlib import Path
import hashlib,json
from PIL import Image
O=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;R=S/'resources'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
resources=json.loads((R/'inventory.json').read_text())
resources.append({'path':str((R/'inventory.json').relative_to(O)),'sha256':sha(R/'inventory.json'),'originalPath':'Packaged input dependency ledger.'})
for r in resources:assert sha(O/r['path'])==r['sha256'],r['path']
b=json.loads((R/'frozen-brief.json').read_text());raw=Image.open(R/'fixed-target-raw.png').convert('RGBA')
box=raw.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox();assert box==(109,877,869,1376)
art=raw.crop(box);art.save(S/'dish-eel.png');assert art.tobytes()==raw.crop(box).tobytes()
assert sha(R/'original-artwork.png')==sha(R/'original-backup.png')==b['source']['projectSHA256']
assert sha(R/'frozen-criteria.json')==b['qualityCriteria']['criteriaFileSHA256']
report={'asset':'dish-eel','round':'round01','representation':'existing-imagegen-2d','generation':{'provider':'Built-in ImageGen','newGenerationForCandidate':False,'adoptedFixedTarget':True,'fixedTargetSHA256':sha(R/'fixed-target-raw.png'),'exactPrompt':'source/round01/resources/exact-imagegen-target-prompt.txt','generationReferenceHashes':{v['role']:v['sha256']for v in b['target']['references']},'rawBytesRetained':True},'canonicalCrop':{'source':'source/round01/resources/fixed-target-raw.png','rawSize':list(raw.size),'rawSHA256':sha(R/'fixed-target-raw.png'),'criterion':'Bounding rectangle of raw alpha>8, ONCE ONLY. The threshold locates a rectangle and never changes interior alpha.','box':list(box),'project':'source/round01/dish-eel.png','canonicalSize':list(art.size),'canonicalSHA256':sha(S/'dish-eel.png'),'pixelRGBAUnchangedInsideCrop':True,'cropPixelSHA256':hashlib.sha256(art.tobytes()).hexdigest(),'alpha0Bounds':list(art.getchannel('A').getbbox()),'alpha8Bounds':list(art.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()),'publisherMustNotCropAgain':True},'resources':resources}
(S/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'canonicalSize':art.size,'crop':box,'canonicalSHA256':sha(S/'dish-eel.png'),'interiorRGBAIdentical':True}))
