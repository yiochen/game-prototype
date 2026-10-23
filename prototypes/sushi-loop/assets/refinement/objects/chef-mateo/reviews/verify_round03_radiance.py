"""Judge-only recomputation and ungraded views of the bound A/B/C controls."""
import json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

OBJ = Path(__file__).resolve().parent.parent
OUT = OBJ / 'candidates/round03'
REV = OBJ / 'reviews'
bound = json.loads((OUT/'calibrated-radiance-validation.json').read_text())
validation = json.loads((OUT/'validation.json').read_text())
source = json.loads((OUT/'controls/approved-source-old/index.json').read_text())
restored = json.loads((OUT/'controls/candidate-restored-old/index.json').read_text())
lookup = {(r['clip'],r['direction'],r['index']):r for r in validation['renders']}
old_lookup = {(r['clip'],r['direction'],r['index']):r for r in source['samples']}
assert source['renderSettingsHash'] == restored['renderSettingsHash'] == bound['identicalSettings']['hash']

def stats(x,y,mask):
    a = np.asarray(x.convert('RGB')).astype(np.int16)
    b = np.asarray(y.convert('RGB')).astype(np.int16)
    d = np.abs(a-b)[np.asarray(mask)>0]
    maximum = d.max(axis=1)
    return dict(pixels=len(d),meanAbsChannelDelta8bit=float(d.mean()),maxChannelDelta8bit=int(d.max()),pixelsAnyDelta=int((maximum>0).sum()),pixelsOver2=int((maximum>2).sum()),pixelsOver8=int((maximum>8).sum()))

rows=[]
for r in bound['rows']:
    key=(r['clip'],r['direction'],r['index'])
    paths=[r[k] for k in ['sourceOldPath','restoredCandidateOldPath','canonicalCandidatePath']]
    for p,k in zip(paths,['sourceOldSHA256','restoredOldSHA256','canonicalSHA256']):
        assert hashlib.sha256((OBJ/p).read_bytes()).hexdigest()==r[k]
    ims=[Image.open(OBJ/p).convert('RGBA') for p in paths]
    mask=Image.new('L',(384,640),255)
    for im in ims:
        mask=ImageChops.multiply(mask,im.getchannel('A').point(lambda x:255 if x>=128 else 0))
    v=lookup[key]
    if v['visible']:
        exclude=Image.new('L',(384,640));d=ImageDraw.Draw(exclude)
        for q in [old_lookup[key]['foodQuadProjected'],v['foodQuadProjected']]:
            d.polygon([tuple(p) for p in q],fill=255)
        mask=ImageChops.multiply(mask,ImageChops.invert(exclude.filter(ImageFilter.MaxFilter(9))))
    a,b=stats(ims[0],ims[1],mask),stats(ims[1],ims[2],mask)
    assert a==r['sameInputCalibration'] and b==r['canonicalActualRGBDelta']
    rows.append(dict(clip=key[0],direction=key[1],index=key[2],sameInputCalibration=a,canonicalActualRGBDelta=b))

for group in ['hidden','N','E','S','W']:
    subset=[r for r in bound['rows'] if ((r['clip'] in ['idle','work']) if group=='hidden' else (r['direction']==group and r['clip'] in ['hold','load']))]
    sheet=Image.new('RGB',(912,402*len(subset)),'#b6bbc0');d=ImageDraw.Draw(sheet)
    for y,r in enumerate(subset):
        for x,(label,k) in enumerate([('A old source','sourceOldPath'),('B old restored','restoredCandidateOldPath'),('C canonical','canonicalCandidatePath')]):
            im=Image.open(OBJ/r[k]).convert('RGBA').crop((40,150,344,520))
            bg=Image.new('RGBA',im.size,'#b6bbc0');bg.alpha_composite(im)
            sheet.paste(bg.convert('RGB'),(304*x,402*y+32))
            d.text((304*x+4,402*y+10),f"{r['clip']}-{r['direction']}-{r['index']:03} {label}",fill='#18212b')
    sheet.save(REV/f'round03-control-triplets-{group}.png')

def aggregate(k):
    a=[r[k] for r in rows];n=sum(r['pixels'] for r in a)
    return dict(measuredPixels=n,weightedMeanAbsChannelDelta8bit=sum(r['meanAbsChannelDelta8bit']*r['pixels'] for r in a)/n,maxChannelDelta8bit=max(r['maxChannelDelta8bit'] for r in a),pixelsAnyDelta=sum(r['pixelsAnyDelta'] for r in a),pixelsOver2=sum(r['pixelsOver2'] for r in a),pixelsOver8=sum(r['pixelsOver8'] for r in a))
result={'method':'Independent NumPy recomputation of bound conservative opaque nonfood screen masks, not semantic material segmentation. No grade; exact packet image hashes confirmed. A/B same-input floor; C/B observed changed-food response includes render noise.','all18BoundRowsReproducedExactly':True,'sameInputCalibration':aggregate('sameInputCalibration'),'canonicalActualRGBDelta':aggregate('canonicalActualRGBDelta'),'rows':rows}
(REV/'round03-independent-radiance-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
