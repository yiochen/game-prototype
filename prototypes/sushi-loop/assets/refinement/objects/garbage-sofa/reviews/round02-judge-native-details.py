from pathlib import Path
from PIL import Image, ImageDraw
import json,hashlib
O=Path(__file__).resolve().parents[1];R=O/'reviews';P=O/'candidates/round-02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pages=[]
for clip in ['idle','highlighted','clearance']:
 for d in ['N','E','S','W']:
  frames=sorted((P/'frames'/f'{clip}-{d}').glob('*.png'))
  for first in range(0,len(frames),4):
   pieces=[]
   for p in frames[first:first+4]:
    im=Image.open(p).convert('RGBA');b=im.getchannel('A').getbbox()
    b=(max(0,b[0]-8),max(0,b[1]-8),min(im.width,b[2]+8),min(im.height,b[3]+8))
    pieces.append((p,im.crop(b),b))
   w=max(i.width for _,i,_ in pieces);h=max(i.height for _,i,_ in pieces)+22
   out=Image.new('RGBA',(w*2,h*2),(110,113,120,255));draw=ImageDraw.Draw(out);records=[]
   for n,(p,im,b) in enumerate(pieces):
    xy=((n%2)*w,(n//2)*h+22);out.alpha_composite(im,xy);draw.text((xy[0]+2,xy[1]-19),f'{clip}-{d}/{p.stem} native pixels',fill='white')
    records.append({'path':str(p.relative_to(O)),'sha256':sha(p),'sourceRect':b,'pasteXY':xy,'noResampling':True,'sourceAlphaBBox':Image.open(p).getchannel('A').getbbox()})
   dest=R/f'round02-native-detail-{clip}-{d}-{first:03d}.png';out.save(dest)
   pages.append({'path':str(dest.relative_to(O)),'sha256':sha(dest),'size':out.size,'frames':records})
(R/'round02-judge-native-detail-manifest.json').write_text(json.dumps({'packetSHA256':sha(P/'packet.json'),'scope':'Diagnostic alpha-bounds crops only, no resampling. Registration is checked on complete source frames and context sheets, never inferred from these crops.','pages':pages},indent=2)+'\n')
print(len(pages),'detail pages',sum(len(p['frames'])for p in pages),'native frames')
