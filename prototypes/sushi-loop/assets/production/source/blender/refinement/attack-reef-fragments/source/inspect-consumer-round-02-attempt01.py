"""Decode actual timed browser frames and measure honest raster/mode residuals."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,subprocess,hashlib
S=Path(__file__).resolve().parent;B=S.parent;C=B/'candidates/round-02';R=C/'consumer'
def diff(a,b):
 aa=np.asarray(a).astype(np.int16);bb=np.asarray(b).astype(np.int16);d=np.abs(aa-bb)
 return {'equal':bool(np.array_equal(aa,bb)),'maxAbs':int(d.max()),'meanAbs':float(d.mean()),'changedPixels':int(np.any(d,axis=2).sum())}
browser=json.loads((R/'browser-report.json').read_text());report={'scope':'Actual complete12fps consumer playback, exact helper/atlas/currentconsumer selection. Native review resampling and actualCSS pixels are separate layers; no sprite repairs.','staticComparisons':[],'playback':[],'raster':[]}
for m in browser['modes']:
 assert not m['errors'];assert m['browserVersion'].startswith('153.');assert len(m['playbackLog'])>=144
 for s in m['static']:report['raster']+=s['raster']
 for phase in range(13):
  selection=m['frameSelections'][phase]['records'];assert all(x['frame']==min(11,phase) for x in selection)
for mode in ['full-chromium','headless-shell']:
 other='headless-shell' if mode=='full-chromium' else 'full-chromium';out=R/mode
 for scale,name in [(1,'logical'),(.5,'phone')]:
  w,h=int(320*scale),int(448*scale)
  for background,color in [('light',(246,242,232)),('gray',(112,118,128)),('dark',(18,26,42))]:
   actual=Image.open(out/f'candidate-{name}-{background}.png').convert('RGB');cross=Image.open(R/other/f'candidate-{name}-{background}.png').convert('RGB')
   expected=Image.new('RGB',(w*4,h*3),color);pixels=Image.new('RGB',(w*4,h*3));otherpixels=pixels.copy()
   for ci,clip in enumerate(['windup','active','recovery']):
    for di,direction in enumerate(['N','E','S','W']):
     source=Image.open(C/'published'/clip/direction/'005.png').convert('RGBA')
     # Exact integer native2x assembly with one native guard pixel; interpolation only over wholecanvas.
     common=Image.new('RGBA',(642,898));common.paste(source,(1,1));filtered=common.resize((round(321*scale),round(449*scale)),Image.Resampling.BILINEAR)
     native=Image.new('RGBA',(w,h),(*color,255));native.alpha_composite(filtered,(-round(.5*scale),-round(.5*scale)))
     expected.paste(native.convert('RGB'),(di*w,ci*h));box=(di*w,ci*(h+20)+20,(di+1)*w,ci*(h+20)+20+h)
     pixels.paste(actual.crop(box),(di*w,ci*h));otherpixels.paste(cross.crop(box),(di*w,ci*h))
   report['staticComparisons'].append({'mode':mode,'scale':scale,'background':background,'actualBrowserModeDifference':diff(pixels,otherpixels),'independentWholeNativeCanvasBilinearVsActualCSS':diff(expected,pixels),'residualInterpretation':'Source is first placed unfiltered on the common2x native canvas with1px guard. PIL wholecanvas BILINEAR and rounded review positioning approximate CSS filtering, whose fractional left/top and premultiplication are not pixel-identical. Differences are retained honestly; no postexport correction.'})
 video=out/'actual-consumer-session.webm';probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','quiet','-show_format','-show_streams','-of','json',str(video)]));(out/'video-probe.json').write_text(json.dumps(probe,indent=2)+'\n')
 p=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(video),'-vf','fps=25,crop=640:468:0:0','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 groups={};index=0;lastslot=-1;cycleDone=False;trace=[]
 while True:
  raw=p.stdout.read(640*468*3)
  if len(raw)!=640*468*3:break
  arr=np.frombuffer(raw,dtype=np.uint8).reshape(468,640,3);marker=np.median(arr[4:12,628:636],axis=(0,1));slot=int(round((float(marker[0])-20)/18));frame=int(round((float(marker[1])-20)/18))
  if marker[2]>210 and 0<=slot<12 and 0<=frame<12:
   if lastslot==11 and slot==0:cycleDone=True
   if not cycleDone:
    im=Image.fromarray(arr.copy());groups.setdefault((slot,frame),[]).append((index/25,im));trace.append({'videoTime':index/25,'slot':slot,'frame':frame,'markerRGB':marker.tolist()});lastslot=slot
  index+=1
 p.stdout.close();p.wait();assert p.returncode==0
 missing=[(s,f) for s in range(12) for f in range(12) if (s,f) not in groups]
 assert not missing,(mode,'actualvideo phases missing',missing)
 record={'mode':mode,'video':str(video.relative_to(B)),'duration':probe['format']['duration'],'all144PhasesDecoded':True,'decoded25fpsFrames':index,'phaseMarker':'Actual painted selection metadata outside sprite: R20+18slot/G20+18index/B245, median8x8; decoded labels and original video retained. No estimated timing or sparse-frame substitution.','decodedTrace':trace,'sheets':[]}
 for ci,clip in enumerate(['windup','active','recovery']):
  boxes=[]
  for direction in ['N','E','S','W']:
   for frame in range(12):
    im=Image.open(C/'published'/clip/direction/f'{frame:03d}.png').convert('RGBA');b=im.getbbox();boxes.append((b[0]//2,b[1]//2,(b[2]+1)//2,(b[3]+1)//2))
  box=(max(0,min(b[0] for b in boxes)-2),max(0,min(b[1] for b in boxes)-2),min(320,max(b[2] for b in boxes)+2),min(448,max(b[3] for b in boxes)+2));cw,ch=box[2]-box[0],box[3]-box[1]
  sheet=Image.new('RGB',((cw+4)*13,(ch+24)*4),(112,118,128));draw=ImageDraw.Draw(sheet);members=[]
  for di,direction in enumerate(['N','E','S','W']):
   slot=ci*4+di
   for column in range(13):
    frame=min(11,column);available=groups[(slot,frame)];timestamp,im=available[len(available)//2] if column<12 else available[-1]
    crop=im.crop((320+box[0],20+box[1],320+box[2],20+box[3]));x=column*(cw+4);y=di*(ch+24);sheet.paste(crop,(x,y+20));draw.text((x+2,y+2),f'{clip} {direction} {frame:02}'+(' hold' if column==12 else ''),fill='white')
    members.append({'clip':clip,'direction':direction,'index':frame,'heldTerminal':column==12,'videoTime':timestamp,'sheetRect':[x,y+20,cw,ch],'videoReviewCrop':[320+box[0],20+box[1],cw,ch],'decodedSamplesForPhase':len(available)})
  dest=out/f'actual-playback-allphase-{clip}.png';sheet.save(dest);record['sheets'].append({'path':str(dest.relative_to(B)),'cells':members})
 report['playback'].append(record)
assert all(r['nativeRasterVsAtlasChangedChannels']==0 for r in report['raster'])
(R/'inspection-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'modes':[(r['mode'],r['all144PhasesDecoded']) for r in report['playback']],'exactRasterRecords':len(report['raster']),'modeResiduals':[r['actualBrowserModeDifference'] for r in report['staticComparisons']],'nativeCSSResiduals':[r['independentWholeNativeCanvasBilinearVsActualCSS'] for r in report['staticComparisons']]},indent=2))
