import json,subprocess,io,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
P=Path(__file__).resolve().parents[1]
def diff(a,b):
 aa=np.asarray(a).astype(np.int16);bb=np.asarray(b).astype(np.int16);d=np.abs(aa-bb);return {'equal':bool(np.array_equal(aa,bb)),'maxAbs':int(d.max()),'meanAbs':float(d.mean()),'changedPixels':int(np.any(d,axis=2).sum())}
def pixels(p,scale):
 im=Image.open(p).convert('RGBA');w,h=int(320*scale),int(448*scale);out=Image.new('RGBA',(w*4,h*3))
 for row in range(3):
  for col in range(4):out.paste(im.crop((col*w,row*(h+20)+20,(col+1)*w,row*(h+20)+20+h)),(col*w,row*h))
 return out
report={'staticComparisons':[],'playback':[],'decodeScope':'Contact sheets retain the actual video screen viewport containing both registered canvases, cropped to upper-left640x468 from1280x900 only to remove unused browser background; original full-session WebM remains bound. This is evidence layout only, not source sprite processing.'}
for mode in ['full-chromium','headless-shell']:
 out=P/'consumer'/mode
 for scale,name in [(1,'logical'),(.5,'phone')]:
  for bg in ['light','gray','dark']:
   a=pixels(out/f'current-{name}-{bg}.png',scale);b=pixels(out/f'replay-{name}-{bg}.png',scale);other=pixels(P/'consumer'/('headless-shell' if mode=='full-chromium' else 'full-chromium')/f'current-{name}-{bg}.png',scale)
   report['staticComparisons'].append({'mode':mode,'scale':scale,'background':bg,'currentVsReplayActualCanvasPixels':diff(a,b),'browserModeCanvasDifference':diff(a,other)})
 video=out/'actual-consumer-session.webm';probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','quiet','-show_format','-show_streams','-of','json',str(video)]));duration=float(probe['format']['duration'])
 # Locate actual playback onset from the first simultaneous matching colored
 # current/replay canvases; video finalization latency is not scene time.
 process=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(video),'-vf','fps=25,crop=640:468:0:0','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 found=[];frameIndex=0;bytesPerFrame=640*468*3
 while True:
  raw=process.stdout.read(bytesPerFrame)
  if len(raw)!=bytesPerFrame:break
  arr=np.frombuffer(raw,dtype=np.uint8).reshape(468,640,3)[20:];left=arr[:,:320].astype(np.int16);right=arr[:,320:].astype(np.int16);mask=np.maximum(left.max(2)-left.min(2),right.max(2)-right.min(2))>40
  score=float(np.abs(left-right)[mask].mean()) if mask.any() else 999
  if int(mask.sum())>500 and score<2.0:found.append({'videoTime':frameIndex/25,'coloredPixels':int(mask.sum()),'meanCanvasDifference':score})
  frameIndex+=1
 process.wait()
 if not found:raise RuntimeError('Could not identify actual paired-canvas playback onset')
 start=found[0]['videoTime']
 (out/'video-probe.json').write_text(json.dumps(probe,indent=2)+'\n')
 rec={'mode':mode,'videoDuration':duration,'detectedPlaybackStartVideoTime':start,'onsetDetection':found[:4],'startTimingLimit':'First decoded25fps video frame with paired identical colored canvases. Time quantization ±0.04s; visible native labels on decoded sheets establish actual clip/facing/frame.','sheets':[]}
 for ci,clip in enumerate(['windup','active','recovery']):
  sheet=Image.new('RGB',(1920,4*488),(112,118,128));dr=ImageDraw.Draw(sheet);members=[]
  for di,direction in enumerate(['N','E','S','W']):
   for fi,(label,offset)in enumerate([('early',.04),('middle',.46),('terminal',1.08)]):
    t=max(0,start+(ci*4+di)*1.25+offset);raw=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-f','image2pipe','-c:v','png','-']);im=Image.open(io.BytesIO(raw)).convert('RGB');crop=im.crop((0,0,640,468));sheet.paste(crop,(fi*640,di*488+20));dr.text((fi*640+4,di*488+3),f'{mode} {clip} {direction} {label} video t={t:.3f}',fill='white');members.append({'direction':direction,'sample':label,'videoTime':t})
  dest=out/f'actual-playback-{clip}.png';sheet.save(dest);rec['sheets'].append({'path':str(dest.relative_to(P)),'members':members})
 report['playback'].append(rec)
(P/'consumer/inspection-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'staticComparisons':report['staticComparisons'],'durations':[(m['mode'],m['videoDuration']) for m in report['playback']]},indent=2))
