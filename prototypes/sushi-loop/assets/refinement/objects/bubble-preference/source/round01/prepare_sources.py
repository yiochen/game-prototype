"""Reproduce the sole authorized lossless rectangular crop; food is never cropped."""
from pathlib import Path
import hashlib,json
from PIL import Image
S=Path(__file__).resolve().parent;O=S.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((S/'provenance.json').read_text());r=p['crop'];raw=O/r['raw'];assert sha(raw)==r['rawSHA256']
im=Image.open(raw).convert('RGBA');box=im.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox();assert list(box)==r['box']
im.crop(box).save(O/r['canonical'],compress_level=9);assert sha(O/r['canonical'])==r['canonicalSHA256']
for r in p['foods'].values():assert sha(O/r['path'])==r['sha256']
print('Recreated blank balloon with one lossless alpha>8 rectangle; exact approved food sources retained full bounds.')
