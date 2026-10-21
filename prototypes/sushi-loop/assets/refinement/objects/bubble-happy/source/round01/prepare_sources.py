"""Re-create each canonical raster from retained frozen raw source, one crop only."""
from pathlib import Path
import json,hashlib
from PIL import Image
S=Path(__file__).resolve().parent;O=S.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for kind,record in json.loads((S/'provenance.json').read_text())['crop'].items():
 raw=O/record['raw'];assert sha(raw)==record['rawSHA256']
 image=Image.open(raw).convert('RGBA');box=image.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox();assert list(box)==record['box']
 image.crop(box).save(O/record['canonical'],compress_level=9)
 assert sha(O/record['canonical'])==record['canonicalSHA256']
print('Recreated two canonical sources from sole lossless source rectangles.')
