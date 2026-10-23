from pathlib import Path
from PIL import Image,ImageChops,ImageStat,ImageDraw
import json,hashlib,subprocess
H=Path(__file__).resolve().parent;C=H.parent.parent/'candidates/round-01';records=[];screens=[];playbacks=[]
def cmp(a,b):
 a=a.convert('RGBA');b=b.convert('RGBA');d=ImageChops.difference(a,b);return {'sameDecodedRGBA':a.tobytes()==b.tobytes(),'alphaExact':a.getchannel('A').tobytes()==b.getchannel('A').tobytes(),'maxAbsoluteRGBA':[x[1] for x in d.getextrema()],'meanAbsoluteRGBA':ImageStat.Stat(d).mean}
for m in ['chromium','shell']:
 for d in 'NESW':
  for i in range(12):records.append({'mode':m,'direction':d,'index':i,'comparison':cmp(Image.open(H/'browser'/m/'frames'/d/f'{i:03}.png'),Image.open(C/'browser'/m/'frames'/d/f'{i:03}.png'))})
 for size in ['logical','phone']:
  ims=[]
  for bg in ['light','gray','dark']:
   a=Image.open(H/'browser'/m/f'{size}-{bg}.png');b=Image.open(C/'browser'/m/f'{size}-{bg}.png');screens.append({'mode':m,'size':size,'background':bg,'comparison':cmp(a,b)})
   if size=='phone':a=a.resize((390,480),Image.Resampling.LANCZOS)
   ims.append(a.convert('RGB'))
  canvas=Image.new('RGB',(sum(x.width for x in ims),max(x.height for x in ims)));x=0
  for im in ims:canvas.paste(im,(x,0));x+=im.width
  canvas.save(H/'sheets'/f'independent-{m}-{size}-backgrounds.png')
 log=json.loads((H/'browser'/m/'actual-playback.json').read_text());samples=log['samples'];trans=[];errors=[]
 for x in samples:
  if len(set(x['phases']))!=1:errors.append(x)
  p=x['phases'][0]
  if not trans or p!=trans[-1]['phase']:trans.append({'phase':p,'timeMs':x['timeMs'],'absoluteIndex':x['absoluteIndex']})
 for a,b in zip(trans,trans[1:]):
  if b['phase']!=(a['phase']+1)%12:errors.append({'from':a,'to':b})
 playbacks.append({'mode':m,'elapsedMs':log['elapsedMs'],'sampleCount':len(samples),'transitions':trans,'cadenceIntervalsMs':[b['timeMs']-a['timeMs'] for a,b in zip(trans,trans[1:])],'wrapTimesMs':[b['timeMs'] for a,b in zip(trans,trans[1:]) if a['phase']==11 and b['phase']==0],'orderErrors':errors})
 # Inspect existing exact-packet compositor video: all fullframes via native retained12fps filmstrips, no duplicate video render.
 video=next((C/'browser'/m/'video').glob('*.webm'))
 probe=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=width,height,r_frame_rate','-of','json',str(video)],capture_output=True,text=True)
 (H/f'video-{m}-metadata.json').write_text(probe.stdout)
 for start,label in [(0,'first'),(1,'second')]:
  out=H/'sheets'/f'actual-compositor-{m}-{label}-second.png';args=['ffmpeg','-hide_banner','-loglevel','error','-ss',str(start),'-i',str(video),'-vf','fps=12,tile=4x3','-frames:v','1',str(out)];p=subprocess.run(args,capture_output=True,text=True);assert p.returncode==0,p.stderr
(H/'consumer-independent-comparison.json').write_text(json.dumps({'canvasFrameComparisons':records,'screenshotComparisons':screens,'actualIndependentPlayback':playbacks,'snapshotCases':12,'compositorVideoSource':'Exactpacket-bound existing browser videos; first and second12fps fullbrowser filmstrip seconds inspected, whole videos and source phase/rAF logs retained, no new redundant videos.','notFullGameOrDevice':True},indent=2)+'\n')
print(json.dumps({'exactCanvasFramesVsSubmitted':sum(r['comparison']['sameDecodedRGBA'] for r in records),'totalFrames':len(records),'exactScreenshotsVsSubmitted':sum(r['comparison']['sameDecodedRGBA'] for r in screens),'playback':[{'mode':r['mode'],'elapsedMs':r['elapsedMs'],'wrapTimesMs':r['wrapTimesMs'],'orderErrors':r['orderErrors']} for r in playbacks]},indent=2))
