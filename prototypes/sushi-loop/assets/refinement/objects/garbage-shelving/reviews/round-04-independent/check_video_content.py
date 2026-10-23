from pathlib import Path
from PIL import Image,ImageChops,ImageStat
import subprocess,json,hashlib
O=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-shelving');B=O/'candidates/round-04';P=B/'previews';OUT=O/'reviews/round-04-independent';rows=[]
for c,n in [('highlighted',48),('clearance',36)]:
 for d in ['S','E','N','W']:
  video=P/f'{c}-{d}-12fps.mp4';data=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(video),'-f','rawvideo','-pix_fmt','rgb24','pipe:1']);stride=1344*336*3;assert len(data)==n*stride,(c,d,len(data));fr=[]
  for i in range(n):
   im=Image.frombytes('RGB',(1344,336),data[i*stride:(i+1)*stride]);ep=P/'moving-frames'/f'{c}-{d}'/f'{i:03d}.png';expected=Image.open(ep).convert('RGB');diff=ImageChops.difference(im,expected);fr.append({'frame0':i,'expectedInput':str(ep),'expectedSHA256':hashlib.sha256(ep.read_bytes()).hexdigest(),'decodedRGBSHA256':hashlib.sha256(im.tobytes()).hexdigest(),'meanAbsoluteRGB':ImageStat.Stat(diff).mean})
   if i==4:im.save(OUT/f'decoded-{c}-{d}-frame04.png')
  rows.append({'path':str(video),'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'decodedFrames':n,'size':[1344,336],'fpsExpected':12,'maximumMeanChannelError':max(max(x['meanAbsoluteRGB']) for x in fr),'frames':fr})
(OUT/'video-content-audit.json').write_text(json.dumps({'purpose':'Independent full decoder verification of all8 encoded source/candidate3background comparison previews. All336decoded frames compared to exact bound frame-sequence inputs; loss from H264 accepted, universal bitidentity not asserted.','streams':rows},indent=2)+'\n');print('Decoded',sum(x['decodedFrames'] for x in rows),'max mean error',max(x['maximumMeanChannelError'] for x in rows))
