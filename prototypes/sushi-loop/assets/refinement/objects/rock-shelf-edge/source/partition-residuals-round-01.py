"""Separate retained outer-edge precision residuals from true internal join regions."""
from pathlib import Path
import sys,json
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent.parent;E=B/'candidates/round-01';sys.path.insert(0,str(B/'source/round-01-resources/python-library'))
from PIL import Image,ImageFilter,ImageChops
out={}
for d in 'NESW':
 a=Image.open(E/f'consumer-nativecanvas-independent-{d}.png').convert('RGBA');n=Image.open(E/f'consumer-nativecanvas-joined-{d}.png').convert('RGBA');local=Image.open(E/f'cutface-mask-{d}.png').convert('L')
 opaque=n.getchannel('A').point(lambda x:255 if x==255 else 0);interior=opaque.filter(ImageFilter.MinFilter(5));outer=ImageChops.subtract(opaque,interior)
 masks={'nativeOpaqueInteriorTwoSourcePixelErosion':interior,'outerPrecisionBandTwoSourcePixels':outer,'localJoinInterior':ImageChops.multiply(local,interior)}
 data={}
 for name,m in masks.items():
  coords=[];total=[0,0,0];maxd=[0,0,0];count=deficits=0
  for y in range(m.height):
   for x in range(m.width):
    if not m.getpixel((x,y)):continue
    count+=1;av=a.getpixel((x,y));nv=n.getpixel((x,y));deficits+=av[3]!=255
    delta=[abs(av[k]-nv[k]) for k in range(3)]
    for k in range(3):total[k]+=delta[k];maxd[k]=max(maxd[k],delta[k])
    if max(delta)>=8:coords.append([x,y,*delta])
  data[name]={'pixels':count,'alphaDeficitPixels':deficits,'maxRGB':maxd,'meanRGB':[t/count if count else None for t in total],'RGBResidualAtLeast8Count':len(coords),'first64CoordinatesRGBResidual':coords[:64]}
 out[d]=data
(E/'partitioned-residuals.json').write_text(json.dumps({'method':'Masks derived from actual connected-native opaque alpha. Two sourcepixel silhouette erosion separates outer extent/precision from visible interior. Actual projected finite cutface mask retained separately. No residual is waived; raw images and local traces remain for independent visual verdict.','measurements':out},indent=2)+'\n')
print(json.dumps({d:{k:{kk:vv for kk,vv in row.items() if kk!='first64CoordinatesRGBResidual'} for k,row in rows.items()} for d,rows in out.items()},indent=2))
