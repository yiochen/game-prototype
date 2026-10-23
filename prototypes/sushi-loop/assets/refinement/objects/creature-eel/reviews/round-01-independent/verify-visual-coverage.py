from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib
J=Path(__file__).resolve().parent;O=J.parent.parent;C=O/'candidates/round-01';m=json.loads((C/'visual-coverage-map.json').read_text());publication=json.loads((C/'publication.json').read_text());coverage=[];tiles=[];fail=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for sheet in m['all528NativeUsefulPixelCoverage']:
 sp=O/sheet['sheet'];im=Image.open(sp).convert('RGBA');assert sha(sp)==sheet['sha256'];assert list(im.size)==sheet['dimensions']
 for cell in sheet['cells']:
  p=O/cell['path'];src=Image.open(p).convert('RGBA');assert sha(p)==cell['sha256'];box=cell['sourceBox'];bb=src.getchannel('A').getbbox();assert bb and all([box[0]<=bb[0],box[1]<=bb[1],box[2]>=bb[2],box[3]>=bb[3]])
  assert src.crop(box).tobytes()==im.crop(cell['sheetBox']).tobytes(),cell['path'];coverage.append({'native':cell['path'],'sheet':sheet['sheet'],'sourceBox':box,'sheetBox':cell['sheetBox'],'nativeSHA256':sha(p),'fullUsefulPixelsExact':True})
 # Exact non-overlapping tiles small enough to inspect without resampling. No export is changed.
 for y in range(0,im.height,1500):
  for x in range(0,im.width,1500):
   box=[x,y,min(x+1500,im.width),min(y+1500,im.height)];dest=J/'tiles'/f"{sp.stem}-x{x}-y{y}.png";dest.parent.mkdir(exist_ok=True);im.crop(box).save(dest);tiles.append({'path':str(dest.relative_to(O)),'sha256':sha(dest),'sheet':sheet['sheet'],'box':box,'scale':1})
# Verify full-canvas publication and original atlas rectangles for all528 images.
for record in publication['rawFrames']:
 p=O/record['path'];src=O/record['path'].replace('/published/frames/','/native/');im=Image.open(src).convert('RGBA');out=Image.open(p).convert('RGBA');assert im.size==(1792,2048) and out.size==(896,1024);assert im.resize((896,1024),Image.Resampling.LANCZOS).tobytes()==out.tobytes(),record['path']
for record in publication['atlases']:
 im=Image.open(O/record['path']).convert('RGBA');assert im.size==(5376,2048)
 for i,(x,y,w,h) in enumerate(record['rects']):
  p=C/'published/frames'/record['clip']/record['direction']/f'{i:03}.png';assert im.crop((x,y,x+w,y+h)).tobytes()==Image.open(p).convert('RGBA').tobytes()
for kind in ['publishedHeroCoverage']:
 sm=m[kind];im=Image.open(O/sm['sheet']).convert('RGBA');assert sha(O/sm['sheet'])==sm['sha256']
 for cell in sm['cells']:assert Image.open(O/cell['path']).convert('RGBA').crop(cell['sourceBox']).tobytes()==im.crop(cell['sheetBox']).tobytes()
(J/'coverage-proof.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'nativeFrames':len(coverage),'nativeSheetCount':len(m['all528NativeUsefulPixelCoverage']),'publishedWholeCanvasLANCZOSExact':len(publication['rawFrames']),'atlasCellsExact':528,'heroesExact':4,'coverage':coverage,'tiles':tiles,'failures':fail},indent=2)+'\n');print('VISUAL_PIXEL_PROOF',len(coverage),'native',len(tiles),'lossless inspection tiles',len(publication['rawFrames']),'wholecanvas reductions')
