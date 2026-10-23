"""Registered logical-size/background and fixed-window diagnostic comparisons."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
HERE=Path(__file__).parent;OBJ=HERE.parents[1];OUT=HERE/'sheets';OUT.mkdir(exist_ok=True)
VALUES=[.45,.50,.525,.55,.575,.60];DIRS=['N','E','S','W'];BG={'light':(242,237,226),'gray':(119,123,128),'dark':(29,36,44)}
POSES=[('hold',1),('hold',4),('hold',10),('load',1),('load',6),('load',7),('load',12)]
def path(d,c,v,f):
 if d in [.45,.6]:return OBJ/f'candidates/round-{2 if d==.45 else 1:02}/frames/{c}-{v}-{f-1:02}.png'
 return HERE/f'renders/d{round(d*1000):03}-{c}-{v}-{f:02}.png'
def sheet(name,poses,values,bg,detail=False):
 crop=(80,320,304,475);size=(224,155) if detail else (192,320);cols=len(poses)*4;w=cols*size[0];h=len(values)*(size[1]+22)
 canvas=Image.new('RGB',(w,h),bg);draw=ImageDraw.Draw(canvas)
 for y,d in enumerate(values):
  for j,(c,f) in enumerate(poses):
   for x,v in enumerate(DIRS):
    im=Image.open(path(d,c,v,f)).convert('RGBA');im=im.crop(crop) if detail else im.resize(size,Image.Resampling.LANCZOS)
    px=(j*4+x)*size[0];py=y*(size[1]+22);canvas.paste(im,(px,py+22),im);draw.text((px+4,py+5),f'd={d:.3f} {c} {v} f{f:02}',fill='white' if sum(bg)<500 else '#22272d')
 canvas.save(OUT/name)
for name,bg in BG.items():
 sheet(f'all-facing-hold01-load06-{name}.png',[('hold',1),('load',6)],VALUES,bg)
 for c,f in POSES:sheet(f'logical-{name}-{c}{f:02}.png',[(c,f)],VALUES,bg)
 sheet(f'fixed-native-window-hold01-load06-{name}.png',[('hold',1),('load',6)],VALUES,bg,True)
# All sampled poses at each candidate depth, with complete logical frames.
for d in [.5,.525,.55,.575]:sheet(f'all-poses-d{round(d*1000):03}-gray.png',POSES,[d],BG['gray'])
print('Registered comparison sheets written',len(list(OUT.glob('*.png'))))
for name,bg in BG.items():
 for c,f in [('hold',1),('load',6)]:sheet(f'near-boundary-{c}{f:02}-{name}.png',[(c,f)],[.525,.55,.575],bg)
