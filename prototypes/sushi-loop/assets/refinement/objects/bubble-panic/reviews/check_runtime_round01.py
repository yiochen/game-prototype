from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json
E=Path(__file__).resolve().parent.parent;C=E/'candidates/round01';R=C/'previews'
receipt=json.loads((C/'native-capture-evidence.json').read_text());record=next(r for r in receipt['files']if r['key']=='native-runtime-wander-playback')
an=Image.open(R/record['name']);assert an.n_frames==48 and an.info['loop']==0
samples=[0,6,11,12,24,47];sheet=Image.new('RGB',(1620,1200),'#f6f1e5');draw=ImageDraw.Draw(sheet)
for i in range(48):
 an.seek(i);im=an.convert('RGBA');assert abs(an.info['duration']-1000/12)<1e-8
 assert hashlib.sha256(im.tobytes()).hexdigest()==record['pixelSHA256ByFrame'][i]
 if i in samples:
  n=samples.index(i);x=n%3*540;y=n//3*600
  # Common world area; no pose/frame fitting. Preserve logical1:1 pixel size.
  sample=im.crop((0,145,1080,745)).resize((540,300),Image.Resampling.LANCZOS)
  sheet.paste(sample.convert('RGB'),(x,y+25));draw.text((x+8,y+8),f'Native frame{i} / t={i/12:.3f}s / common context crop',fill='#253b3b')
  # fixed first customer region enlarged; same registered window all samples.
  detail=im.crop((130,350,295,680));sheet.paste(detail.convert('RGB'),(x+10,y+300))
sheet.save(E/'reviews/round01-runtime-timing-contact.png')
p=E/'reviews/round01-runtime-verification.json';p.write_text(json.dumps({'frames':48,'fps':12,'durationSeconds':4,'allFramesRGBAEqualSealedCaptureReceipt':True,'allDurationsExactly1Over12Second':True,'sequenceLoopsForReview':True,'scope':'Isolated inherited current Godot renderer fixture with walking/leaving,wander,nonzero shared pose; no full-game simulation claim','sampledVisuallyInContactSheet':samples},indent=2)+'\n')
print(p)
