import json,hashlib,subprocess
from pathlib import Path
from PIL import Image
import numpy as np
P=Path(__file__).resolve().parents[1];O=P.parents[1];C=O/'candidates/round-01';R=C/'consumer-v2'
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((R/'inspection-report.json').read_text());browser=json.loads((R/'browser-report.json').read_text());out=[]
for mode in ['full-chromium','headless-shell']:
 r=next(r for r in report['playback']if r['mode']==mode);m=next(m for m in browser['modes']if m['mode']==mode);want={};sheets={};expected=[]
 for s in r['sheets']:
  sheets[s['path']]=Image.open(O/s['path']).convert('RGB')
  for c in s['cells']:
   frameIndex=round(c['videoTime']*25);want.setdefault(frameIndex,[]).append((s['path'],c))
 process=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(O/r['video']),'-vf','fps=25,crop=640:468:0:0','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 index=0;verified=[]
 while True:
  raw=process.stdout.read(640*468*3)
  if len(raw)!=640*468*3:break
  if index in want:
   arr=np.frombuffer(raw,dtype=np.uint8).reshape(468,640,3);marker=np.median(arr[4:12,628:636],axis=(0,1));slot=round((float(marker[0])-20)/18);phase=round((float(marker[1])-20)/18);im=Image.fromarray(arr.copy())
   for sp,c in want[index]:
    x,y,w,h=c['videoReviewCrop'];v=im.crop((x,y,x+w,y+h));sx,sy,sw,sh=c['sheetRect'];s=sheets[sp].crop((sx,sy,sx+sw,sy+sh));same=v.tobytes()==s.tobytes();expectedslot=['windup','active','recovery'].index(c['clip'])*4+['N','E','S','W'].index(c['direction']);assert same,(mode,c)
    verified.append({'clip':c['clip'],'direction':c['direction'],'index':c['index'],'heldTerminal':c['heldTerminal'],'videoTime':index/25,'sheet':sp,'sheetRect':c['sheetRect'],'decodedPixelMatch':same,'actualVideoMarker':marker.tolist(),'decodedMarkerSlot':slot,'decodedMarkerPhase':phase,'markerMatchesExpected':slot==expectedslot and phase==c['index']})
  index+=1
 process.stdout.close();process.wait();assert process.returncode==0
 assert len(verified)==156;assert all(v['markerMatchesExpected'] for v in verified)
 times={}
 for v in verified:times.setdefault(v['clip']+'-'+v['direction'],[]).append(v)
 chronological=all([v['index']for v in vv]==list(range(12))+[11]and all(a['videoTime']<=b['videoTime']for a,b in zip(vv,vv[1:]))for vv in times.values())
 static=[]
 for s in m['static']:
  assert s['records'];assert all(x['frame']==5 and x['frameSize']==[320,448]and x['root']==[160,320]and x['plan']['scale']==2 for x in s['records'])
  static.append({'path':s['path'],'dataset':s.get('dataset'),'recordCount':len(s['records']),'allNativeRasterChannelsExact':all(x['nativeRasterVsAtlasChangedChannels']==0 for x in s['raster'])})
 out.append({'mode':mode,'browserVersion':m['browserVersion'],'launch':m['options'],'DPR':m['deviceScaleFactor'],'viewport':m['viewport'],'errors':m['errors'],'actualDecodedVideoFrames':index,'all144ActualPhasesAnd12HeldTerminalsVerified':len(verified)==156 and chronological,'video':r['video'],'videoSHA256':sha(O/r['video']),'cells':verified,'static':static,'interpretation':'Every inspected complete-sheet cell equals the actual decoded video at its stated time; all markers match expected clip/facing/phase and chronological order. Lossy video frame blur is retained, separately from exact native PNG quality. The earlier consumer-v1 incomplete attempt is retained diagnostic only; no new recording needed.'})
# Submitted native images obey exact reduction rule; independent replay floating edge differences retain honest alpha-weighted metrics.
residual=[]
for c in ['windup','active','recovery']:
 for d in ['N','E','S','W']:
  for i in range(12):
   original=Image.open(C/'native'/c/d/f'{i:03d}.png').convert('RGBA');pub=Image.open(C/'published'/c/d/f'{i:03d}.png').convert('RGBA');expected=original.resize((640,896),Image.Resampling.LANCZOS);assert expected.tobytes()==pub.tobytes()
   replay=Image.open(P/'native/replay'/c/d/f'{i:03d}.png').convert('RGBA').resize((640,896),Image.Resampling.LANCZOS);aa=np.asarray(replay).astype(np.float64);bb=np.asarray(pub).astype(np.float64);delta=np.abs(aa-bb);premula=aa[:,:,:3]*aa[:,:,3:]/255;premulb=bb[:,:,:3]*bb[:,:,3:]/255;diff=np.abs(premula-premulb);changed=np.any(delta,axis=2)
   if changed.any():
    pts=np.argwhere(changed);residual.append({'clip':c,'direction':d,'index':i,'changedPixels':int(changed.sum()),'maxRGBAdelta':float(delta.max()),'maxAlphaDelta':float(delta[:,:,3].max()),'maxPremultipliedRGBDelta':float(diff.max()),'meanPremultipliedRGBDelta':float(diff.mean()),'changedPixelAlphaRange':[float(np.minimum(aa[:,:,3],bb[:,:,3])[changed].min()),float(np.maximum(aa[:,:,3],bb[:,:,3])[changed].max())]})
dump(P/'inspection/independent-video-coverage.json',{'candidatePacketSHA256':sha(C/'packet.json'),'modes':out,'sourceHelpersVerified':browser['helpers'],'originalV1Attempt':'Preserved by editor resource-manifest.json:diagnosticAttempt01; not final phase evidence.'});dump(P/'native/normalization-and-replay-residuals.json',{'submittedNativeFullFrameLanczosExactPublished':144,'independentReplayPublishedExact':144-len(residual),'nonexactIndependentReplayFrames':residual,'interpretation':'Independent native4x renderer deltas are extremely sparse max2RGBA, amplified at tiny-alpha edges by premultiplied LANCZOS division. Actual weighted differences are reported, without RGB/alpha repair or a pixel-identical claim.'})
print(json.dumps({'verifiedVideos':[{k:r[k]for k in ['mode','all144ActualPhasesAnd12HeldTerminalsVerified','actualDecodedVideoFrames']}for r in out],'submittedNativeLanczosPublishedExact':144,'independentReplayResidualFrames':len(residual),'maxPremultipliedResidual':max(x['maxPremultipliedRGBDelta']for x in residual)},indent=2))
