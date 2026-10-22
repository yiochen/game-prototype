from PIL import Image,ImageDraw
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parents[2];W=next(p for p in B.parents if (p/'prototypes.json').exists());P=W/'prototypes/sushi-loop/assets/production/sprites/belt-corner-e-n';O=B/'reviews/initial-evidence';rec={};frames={};box=None
for d in 'NESW':
 im=Image.open(P/f'running-{d}.png').convert('RGBA');fs=[im.crop((i%6*384,i//6*704,(i%6+1)*384,(i//6+1)*704))for i in range(24)];frames[d]=fs
 for f in fs:
  b=f.getbbox();box=(min(box[0],b[0]),min(box[1],b[1]),max(box[2],b[2]),max(box[3],b[3]))if box else b
 rec[d]={'atlas':str(P/f'running-{d}.png'),'sha256':hashlib.sha256((P/f'running-{d}.png').read_bytes()).hexdigest(),'size':im.size,'uniqueRGBAFrames':len(set(f.tobytes()for f in fs))}
box=(box[0]-5,box[1]-5,box[2]+5,box[3]+5)
for d,fs in frames.items():
 w,h=(box[2]-box[0])//2,(box[3]-box[1])//2;sheet=Image.new('RGB',(6*(w+10),4*(h+26)),(128,128,128));draw=ImageDraw.Draw(sheet)
 for i,f in enumerate(fs):
  crop=f.crop(box).resize((w,h),Image.Resampling.BOX);x=i%6*(w+10)+5;y=i//6*(h+26)+21;sheet.paste(crop,(x,y),crop);draw.text((x,y-17),f'{d} {i:02d}',fill='white')
 sheet.save(O/f'original-all24-{d}.png')
 small=[f.crop(box).resize((w,h),Image.Resampling.BOX)for f in fs];small[0].save(O/f'original-playback-{d}.webp',save_all=True,append_images=small[1:],duration=[83,84,83]*8,loop=0,lossless=True)
rec['commonRegisteredCrop']=box;rec['sheetMethod']='Common crop across all96 source frames, uniform half-scale BOX, gray background. Atlas source not changed.';(O/'original-frames.json').write_text(json.dumps(rec,indent=2))
