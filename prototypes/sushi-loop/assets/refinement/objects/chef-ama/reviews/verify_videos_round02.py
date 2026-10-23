from pathlib import Path
from PIL import Image
import numpy as np,json,subprocess
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-ama');C=P/'candidates/round-02';records=[]
for clip in ['idle','work','hold','load']:
 for direction in ['N','E','S','W']:
  path=C/'playbacks'/f'{clip}-{direction}.mp4';data=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','rawvideo','-pix_fmt','rgb24','-'])
  actual=np.frombuffer(data,np.uint8).reshape(-1,640,384,3).astype(np.float32);assert len(actual)==12
  expected=[]
  for i in range(12):
   fr=Image.open(C/'frames'/f'{clip}-{direction}'/f'{i:03}.png').convert('RGBA');b=Image.new('RGBA',fr.size,'#d1d0c7');b.alpha_composite(fr);expected.append(np.array(b.convert('RGB'),dtype=np.float32))
  errors=[float(np.abs(actual[i]-expected[i]).mean()) for i in range(12)]
  records.append({'path':str(path.relative_to(C)),'decodedFrames':12,'inOrderMAEPerRGBChannel':errors,'maximumFrameMeanAbsoluteRGBError':max(errors),'note':'Native PNG alpha-composited on declared neutral video background; lossy H264/YUV conversion differences expected. All twelve decoded video frames compared to matching native PNG indices.'})
assert max(r['maximumFrameMeanAbsoluteRGBError'] for r in records)<2
(P/'reviews/round02-independent-video-check.json').write_text(json.dumps({'all16VideosDecoded':True,'all192VideoFramesComparedInOrder':True,'maximumFrameMeanAbsoluteRGBError':max(r['maximumFrameMeanAbsoluteRGBError'] for r in records),'records':records},indent=2)+'\n')
print('Decoded16 videos192 frames; maximum matching-frame RGB MAE',max(r['maximumFrameMeanAbsoluteRGBError'] for r in records))
