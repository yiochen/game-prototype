"""Portable single alpha-bounds rectangle crop. Raw fixed target stays byte exact.
Threshold selects the rectangle only; all RGBA inside it remains untouched.
"""
from pathlib import Path
import hashlib,json
from PIL import Image
S=Path(__file__).resolve().parent;R=S/'resources'
raw=Image.open(R/'target.png').convert('RGBA');alpha=raw.getchannel('A');bounds=alpha.point(lambda a:255 if a>8 else 0).getbbox()
assert bounds==(174,633,798,1194),bounds
art=raw.crop(bounds);art.save(S/'bubble-puzzled.png',compress_level=9)
inside=alpha.crop(bounds);allhist=alpha.histogram();inhist=inside.histogram();outside=[a-b for a,b in zip(allhist,inhist)]
# Every omitted nonzero pixel is measured. This is original pipeline bounds
# policy, not a claim that every alpha>0 raw target pixel remains in cutout.
record={'raw':'source/round01/resources/target.png','rawSHA256':hashlib.sha256((R/'target.png').read_bytes()).hexdigest(),'rawSize':list(raw.size),'thresholdForBoundsOnly':8,'box':list(bounds),'canonical':'source/round01/bubble-puzzled.png','canonicalSize':list(art.size),'canonicalSHA256':hashlib.sha256((S/'bubble-puzzled.png').read_bytes()).hexdigest(),'cropRGBAEqualRawRectangle':True,'alphaInsideRectangleUnchanged':True,'rawAlpha0Bounds':alpha.getbbox(),'rawAlpha1Bounds':alpha.point(lambda a:255 if a>1 else 0).getbbox(),'omittedOutsideRectangle':{'nonzeroPixels':sum(outside[1:]),'maxAlpha':max(i for i,n in enumerate(outside)if n),'alphaHistogram':{str(i):n for i,n in enumerate(outside)if i and n},'totalAlphaWeight':sum(i*n for i,n in enumerate(outside))},'interpretation':'Exact raw target retained. Original publisher uses alpha>8 only to choose a once-only crop rectangle. Faint alpha1 outliers outside rectangle are omitted by this authorized original pipeline crop. A requirement to preserve all nonzero raw alpha in the packed cutout conflicts with this crop/82logical visible-width contract and requires coordinator resolution, never a waiver by editor.'}
(S/'crop.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
