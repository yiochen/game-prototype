"""Report actual video phase coverage; no missing-frame waiver or pixel repair."""
from pathlib import Path
import subprocess,json,numpy as np
S=Path(__file__).resolve().parent;C=S.parent/'candidates/round-02';R=C/'consumer';report=[]
for mode in ['full-chromium','headless-shell']:
 video=R/mode/'actual-consumer-session.webm';p=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(video),'-vf','fps=25,crop=16:16:624:0','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 seen=set();lastslot=-1;done=False
 while True:
  raw=p.stdout.read(16*16*3)
  if len(raw)!=16*16*3:break
  a=np.frombuffer(raw,dtype=np.uint8).reshape(16,16,3);m=np.median(a[4:12,4:12],axis=(0,1));slot=int(round((float(m[0])-20)/18));frame=int(round((float(m[1])-20)/18))
  if m[2]>210 and 0<=slot<12 and 0<=frame<12:
   if lastslot==11 and slot==0:done=True
   if not done:seen.add((slot,frame));lastslot=slot
 p.stdout.close();p.wait();missing=[{'slot':slot,'clip':['windup','active','recovery'][slot//4],'direction':['N','E','S','W'][slot%4],'index':frame} for slot in range(12) for frame in range(12) if (slot,frame) not in seen]
 report.append({'mode':mode,'video':str(video.relative_to(S.parent)),'seenPhases':len(seen),'missing':missing})
(R/'first-video-coverage-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
