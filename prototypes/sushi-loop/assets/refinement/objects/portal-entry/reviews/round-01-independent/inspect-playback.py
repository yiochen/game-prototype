from pathlib import Path
import json,subprocess,hashlib
from PIL import Image,ImageDraw
import numpy as np
H=Path(__file__).resolve().parent;O=H.parent.parent;C=O/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
results={};selected={}
for mode in ['chromium','shell']:
 video=C/f'consumer/{mode}-playback.webm';probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]));stream=next(x for x in probe['streams'] if x['codec_type']=='video');w,h=stream['width'],stream['height'];assert (w,h)==(390,844)
 screenshot=Image.open(C/f'consumer/{mode}-all48.png').convert('RGB');refs=np.stack([np.asarray(screenshot.crop((0,i*212+20,384,i*212+212)),dtype=np.float32) for i in range(12)])
 process=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(video),'-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 count=0;frames=[];best={}
 while True:
  data=process.stdout.read(w*h*3)
  if not data:break
  assert len(data)==w*h*3
  im=Image.frombytes('RGB',(w,h),data);ar=np.asarray(im.crop((0,20,384,212)),dtype=np.float32);errors=np.mean((refs-ar)**2,axis=(1,2,3));phase=int(errors.argmin());order=np.argsort(errors);frames.append({'decodedIndex':count,'closestPhase':phase,'meanSquaredError':float(errors[phase]),'nextBestPhase':int(order[1]),'nextBestMSE':float(errors[order[1]])})
  for i in range(12):
   if i not in best or errors[i]<best[i][0]:best[i]=(float(errors[i]),count,im.copy(),hashlib.sha256(data).hexdigest())
  count+=1
 stderr=process.stderr.read().decode();assert process.wait()==0,stderr
 results[mode]={'video':str(video.relative_to(O)),'sha256':sha(video),'ffprobe':probe,'decodedEveryFrame':True,'decodedFrameCount':count,'frameMatches':frames,'phaseSelections':[{'phase':i,'actualDecodedVideoFrame':best[i][1],'fullDecodedRGBSHA256':best[i][3],'MSEToActualSameModePhaseCSSScreenshot':best[i][0]} for i in range(12)],'interpretation':'Every saved video frame was decoded. Minimum squared-error matches against actual same-mode fullphase CSS evidence identify representative actual video frames; not claimed byte-identical or used as a replacement for independent actualrAF canvas progression. Contact sheets preserve all four complete96x192 authored sprite viewports and their label row; unused blank lower webpage is omitted only from the review sheet.'};selected[mode]=best
for start in [0,6]:
 sheet=Image.new('RGB',(780,6*232),(119,119,119));draw=ImageDraw.Draw(sheet)
 for col,mode in enumerate(['chromium','shell']):
  for row,i in enumerate(range(start,start+6)):
   score,index,im,digest=selected[mode][i];sheet.paste(im.crop((0,0,390,212)),(col*390,row*232+20));draw.text((col*390+2,row*232+3),f'{mode} phase{i} videoFrame{index} MSE{score:.3f}',fill='white')
 sheet.save(H/f'actual-video-phases-{start:02d}-{start+5:02d}.png')
(H/'playback-video-inspection.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'method':'Decode all actual webm frames at original390x844 with ffmpeg rgb24; inspect fullphase selected decoded video contact sheets; compare independently with saved native phase media and real currentconsumer rAF capture. No new video recorded.','modes':results},indent=2)+'\n')
print('ACTUAL_VIDEOS_DECODED',[(k,v['decodedFrameCount'],[(x['phase'],x['actualDecodedVideoFrame'],round(x['MSEToActualSameModePhaseCSSScreenshot'],3)) for x in v['phaseSelections']]) for k,v in results.items()])
