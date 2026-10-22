from pathlib import Path
from PIL import Image,ImageDraw
import json,shutil,hashlib
B=Path(__file__).resolve().parent;E=B.parent;O=E/'candidates/round-01'
for d in 'NESW':
 n=O/f'native/static/{d}/000.png';im=Image.open(n).convert('RGBA');assert im.size==(768,1408);pub=im.resize((384,704),Image.Resampling.BOX)
 for p in [O/f'frames/static/{d}/000.png',O/f'atlases/static-{d}.png']:
  p.parent.mkdir(parents=True,exist_ok=True);pub.save(p)
 im=Image.open(O/f'canonical-middle/native/{d}.png').convert('RGBA');p=O/f'canonical-middle/published/{d}.png';p.parent.mkdir(parents=True,exist_ok=True);im.resize((384,704),Image.Resampling.BOX).save(p)
for p in (O/'family-native').glob('*.png'):
 im=Image.open(p);out=O/'family-published'/p.name;out.parent.mkdir(parents=True,exist_ok=True);im.resize((896,1216),Image.Resampling.BOX).save(out)
def sheet(paths,out,cols,size,crop=None):
 w,h=size;canvas=Image.new('RGB',(w*cols,h*((len(paths)+cols-1)//cols)),(238,232,220));draw=ImageDraw.Draw(canvas)
 for i,(label,p) in enumerate(paths):
  im=Image.open(p).convert('RGBA')
  if crop:im=im.crop(crop)
  im.thumbnail((w,h-24),Image.Resampling.LANCZOS);x=(i%cols)*w+(w-im.width)//2;y=(i//cols)*h+24;canvas.paste(im,(x,y),im);draw.text(((i%cols)*w+10,(i//cols)*h+6),label,fill='black')
 canvas.save(out)
sheet([(d,O/f'frames/static/{d}/000.png') for d in 'NESW'],O/'four-view-sheet.png',4,(240,280),crop=(48,290,340,640))
for kind in ['pair','closedRun']:
 sheet([(d,O/f'family-published/{kind}-{d}.png') for d in 'NESW'],O/f'native-{kind}-sheet.png',2,(600,510),crop=(30,270,870,1155))
cam=json.loads((O/'native-camera.json').read_text());pub=dict(cam);pub.pop('nativeFrame',None);pub.update(projection='top-down-oblique-square-grid',captureScale=2,publishedFrame=[384,704],nativeMeasurement=cam,publication='BOX wholeframe native4x->published2x; metadata normalized only');pub['calibration']={k:[v/2 for v in values] for k,values in cam['calibration'].items()};(O/'published-camera.json').write_text(json.dumps(pub,indent=2)+'\n')
asset=json.loads((E/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['groundRootObject']='rock-shelf-end__root';asset['artStyle']={'revision':'warm-soft-native-round01','lighting':'exact canonical middle03 five symmetric area lights','roughness':.47,'specularIORLevel':.24};(O/'assetRecord.json').write_text(json.dumps(asset,indent=2)+'\n')
rig=json.loads((E/'inputs/source-rig.json').read_text());rig.pop('sourceFiles',None);rig.update(groundRootObject='rock-shelf-end__root',source='source/round-01.blend',notes=['Native static shelf end; no actions or raster substitutes.']);(O/'rig.json').write_text(json.dumps(rig,indent=2)+'\n')
print('PUBLISHED all4 fullframe BOX')
