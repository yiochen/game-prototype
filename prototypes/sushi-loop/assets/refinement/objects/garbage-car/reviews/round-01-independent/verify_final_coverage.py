from pathlib import Path
import json,hashlib,subprocess
from PIL import Image
import numpy as np
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-car');C=P/'candidates/round-01';O=P/'reviews/round-01-independent'
checks=[]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def back(f,size,bg):
 im=Image.open(f).convert('RGBA')
 if size:im=im.resize(size,Image.Resampling.LANCZOS)
 out=Image.new('RGBA',im.size,'#'+bg);out.alpha_composite(im);return out.convert('RGB')
def check(path,actual,expected,label):checks.append({'path':str(path.relative_to(C)),'part':label,'exactRGB':actual.tobytes()==expected.convert('RGB').tobytes()})
for clip,n in [('idle',1),('highlighted',12),('clearance',12)]:
 for d in 'NESW':
  f=C/f'previews/all-{clip}-{d}.png';im=Image.open(f).convert('RGB')
  for i in range(n):
   x=i%6*248;y=24+i//6*358
   check(f,im.crop((x,y,x+248,y+358)),back(C/f'frames/{clip}-{d}/{i:03}.png',(248,358),'f5f2e9'),i)
for d in 'NESW':
 f=C/f'previews/idle-{d}-native-background.png';check(f,Image.open(f).convert('RGB'),back(C/f'frames/idle-{d}/000.png',None,'808080'),'native composite')
for label,size in [('logical128',(576,832)),('phone55',(248,358))]:
 for bg in ['f5f2e9','808080','202028']:
  f=C/f'previews/idle-four-view-{label}-{bg}.png';im=Image.open(f).convert('RGB')
  for j,d in enumerate('NESW'):
   check(f,im.crop((j*size[0],25,(j+1)*size[0],25+size[1])),back(C/f'frames/idle-{d}/000.png',size,bg),d)
for d in 'NESW':
 f=C/f'previews/floor-reveal-{d}-all.png';im=Image.open(f).convert('RGB');one=Image.open(C/f'previews/floor-reveal/{d}-00.png');w,h=one.size
 for i in range(13):
  part=C/f'previews/floor-reveal/{d}-{i:02}.png' if i<12 else C/f'previews/floor-reveal/{d}-postclip-removed.png'
  check(f,im.crop((i%4*w,i//4*h,i%4*w+w,i//4*h+h)),Image.open(part),str(i))
f=C/'previews/floor-reveal-S-12fps.mp4'
probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,avg_frame_rate,duration,nb_frames','-of','json',str(f)]))['streams'][0]
w,h=probe['width'],probe['height'];proc=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(f),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE);maes=[]
for i in range(36):
 data=proc.stdout.read(w*h*3)
 assert len(data)==w*h*3,(i,len(data))
 part=C/f'previews/floor-reveal/S-{i:02}.png' if i<12 else C/'previews/floor-reveal/S-11.png' if i<24 else C/'previews/floor-reveal/S-postclip-removed.png'
 actual=np.frombuffer(data,dtype=np.uint8).reshape(h,w,3).astype(np.float32);expected=np.asarray(Image.open(part).convert('RGB'),dtype=np.float32)
 maes.append(float(np.abs(actual-expected).mean()))
assert not proc.stdout.read(1);assert proc.wait()==0
out={'redundantPresentationPayloadChecks':checks,'failureCount':sum(not x['exactRGB'] for x in checks),'floorVideo':{'path':str(f.relative_to(C)),'sha256':sha(f),'ffprobe':probe,'decodedFrameCount':36,'order':'native 00..11, terminal 11 held12frames, separate consumer-removed floor12frames','frameRGBMAEvsVerifiedContext':maes,'lossyVideoPixelIdentityRequired':False},'scope':'Final coverage closure for redundant packet presentations and floor stream; no new native renders or source modifications.'}
(O/'final-coverage-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'payloadChecks':len(checks),'failures':out['failureCount'],'floorVideoFrames':len(maes),'floorMaxFrameRGBMAE':max(maes)}))
