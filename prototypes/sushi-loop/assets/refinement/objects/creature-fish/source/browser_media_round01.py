from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import json,subprocess,hashlib,math,io
P=Path(__file__).resolve().parent;E=P.parent;O=E/'candidates/round-01';B=json.loads((O/'browser-evidence.json').read_text());OUT=O/'playback-decoded';OUT.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def residual(a,b):
 d=ImageChops.difference(a.convert('RGB'),b.convert('RGB'));h=d.histogram();return {'meanAbsoluteRGBByteError':sum(ImageStat.Stat(d).mean)/3,'maxByteError':max(i%256 for i,n in enumerate(h) if n),'differentChannelBytes':sum(n for i,n in enumerate(h) if i%256),'pixels':a.width*a.height}
manifest=[]
for mode in B['modes']:
 for play in mode['playback']:
  p=Path(play['video']['path']);probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_streams','-show_frames','-show_entries','stream=width,height,avg_frame_rate,duration:frame=best_effort_timestamp_time','-of','json',str(p)]));st=probe['streams'][0];w,h=st['width'],st['height'];size=w*h*3
  crop=(0,60,360,430) if play['viewport']=='phone' else (0,140,1792,470);scale=1 if play['viewport']=='phone' else .5;cw=round((crop[2]-crop[0])*scale);ch=round((crop[3]-crop[1])*scale);cols=7 if play['viewport']=='phone' else 4
  proc=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(p),'-vsync','0','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  thumbs=[];frames=[];i=0
  while True:
   data=proc.stdout.read(size)
   if not data:break
   assert len(data)==size
   im=Image.frombytes('RGB',(w,h),data);cut=im.crop(crop)
   if scale!=1:cut=cut.resize((cw,ch),Image.Resampling.LANCZOS)
   thumbs.append(cut);frames.append({'decodedIndex':i,'timestamp':probe['frames'][i].get('best_effort_timestamp_time'),'fullDecodedRGB_SHA256':hashlib.sha256(data).hexdigest()});i+=1
  stderr=proc.stderr.read().decode();assert proc.wait()==0,stderr
  rows=math.ceil(len(thumbs)/cols);sheet=Image.new('RGB',(cw*cols,(ch+18)*rows),'#858c92');dr=ImageDraw.Draw(sheet)
  for i,im in enumerate(thumbs):
   x=i%cols*cw;y=i//cols*(ch+18);sheet.paste(im,(x,y+18));dr.text((x+3,y+3),f"decoded {i} · {frames[i]['timestamp']} s",fill='white');frames[i]['sheetCell']=[x,y+18,cw,ch]
  q=OUT/f"{mode['mode']}-{play['viewport']}-{play['clip']}.png";sheet.save(q)
  manifest.append({'mode':mode['mode'],'viewport':play['viewport'],'clip':play['clip'],'originalVideo':str(p.relative_to(E)),'originalVideoSHA256':sha(p),'actualViewport':[w,h],'decodedFrames':len(frames),'completeDecode':True,'avgFrameRate':st['avg_frame_rate'],'diagnosticCrop':list(crop),'diagnosticScale':scale,'sheet':str(q.relative_to(E)),'sheetSHA256':sha(q),'frames':frames,'stderr':stderr,'scope':'Every recorded compositor video frame decoded, hash-bound and represented. Review crop contains the four fish actors; full original viewport video retained. No claim of arbitrary twelve distinct decoded hashes; page RAF trace supplies cadence/order/wrap/terminal state, while these pixels supply actual playback appearance.'})
  print('FISH_VIDEO_DECODE',mode['mode'],play['viewport'],play['clip'],len(frames),flush=True)
(O/'playback-decoded-manifest.json').write_text(json.dumps({'ffmpegVersion':subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-version'],text=True).splitlines()[0],'ffprobeVersion':subprocess.check_output(['/opt/homebrew/bin/ffprobe','-version'],text=True).splitlines()[0],'records':manifest},indent=2)+'\n')
# Honest browser launch-mode raster residuals and native-Pillow versus ordinary CSS filtering.
pairs=[];css=[]
a,b=B['modes']
byname={Path(r['path']).name:r for r in b['checks']}
for r in a['checks']:
 name=Path(r['path']).name
 if name in byname:
  q=byname[name];im=Image.open(r['path']);jm=Image.open(q['path']);assert im.size==jm.size;pairs.append({'name':name,'fullChromiumSHA256':sha(Path(r['path'])),'headlessShellSHA256':sha(Path(q['path'])),**residual(im,jm)})
for mode in B['modes']:
 for bg in ['light','dark']:
  r=next(r for r in mode['checks'] if Path(r['path']).name==f'logical-normal-{bg}.png');actual=Image.open(r['path']).convert('RGB');expected=Image.new('RGB',(448*4,512),{'light':'#f3f1e8','dark':'#152338'}[bg])
  for di,d in enumerate(['N','E','S','W']):
   im=Image.open(O/'published/normal'/d/'000.png').convert('RGBA').resize((448,512),Image.Resampling.LANCZOS);tile=Image.new('RGBA',im.size,{'light':'#f3f1e8','dark':'#152338'}[bg]);tile.alpha_composite(im);expected.paste(tile.convert('RGB'),(di*448,0))
  assert actual.size==expected.size,(actual.size,expected.size)
  css.append({'mode':mode['mode'],'bg':bg,'actualBrowserPath':r['path'],'comparison':'Pillow whole published frame2x→logical LANCZOS/reference alpha composite vs exact helper native-nearest common canvas then ordinary whole CSS filtering; exclude top32px labels. Expected residuals measured, no image repair.',**residual(actual.crop((0,32,1792,512)),expected.crop((0,32,1792,512)))})
(O/'browser-mode-and-CSS-residuals.json').write_text(json.dumps({'modePairs':pairs,'nativePublicationVsCSS':css,'pixelRepairs':'None; residuals disclosed as measurements, not corrected.'},indent=2)+'\n')
print('FISH_BROWSER_MEDIA_COMPLETE',len(manifest),flush=True)
