"""Lossless whole-desktop screenshot tiles for actual-resolution visual inspection only."""
import pathlib,json,hashlib
from PIL import Image,ImageChops
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-04';D=O/'diagnostics/desktop-strips';D.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for runtime in ['full-chromium','headless-shell']:
 for case in ['logical128-integer','logical128-fractional']:
  src=O/f'consumer/{runtime}-{case}.png';im=Image.open(src);restored=Image.new(im.mode,im.size);tiles=[]
  for i,y in enumerate(range(0,im.height,1280)):
   box=[0,y,im.width,min(y+1280,im.height)];tile=im.crop(box);dest=D/f'{runtime}-{case}-{i:02}.png';tile.save(dest);restored.paste(tile,(0,y));tiles.append({'path':str(dest.relative_to(P)),'sha256':sha(dest),'sourceBox':box,'size':list(tile.size)})
  eq=all(v==(0,0) for v in ImageChops.difference(im,restored).getextrema());assert eq
  records.append({'source':str(src.relative_to(P)),'sourceSHA256':sha(src),'sourceSize':list(im.size),'tiles':tiles,'decodedRGBExactlyRestored':eq,'discardedSourcePixels':0})
(O/'diagnostics/desktop-strips.json').write_text(json.dumps({'records':records,'scope':'Auxiliary actual-resolution inspection of every pixel of each declared desktop full-page screenshot. Same integer pixels, no scaling, fitting, color editing or altered art. Tiles are never art/consumer inputs or replacement screenshots.'},indent=2)+'\n')
print(json.dumps({'screenshots':len(records),'tiles':sum(len(q['tiles']) for q in records),'allSourcePixelsRestored':True}))
