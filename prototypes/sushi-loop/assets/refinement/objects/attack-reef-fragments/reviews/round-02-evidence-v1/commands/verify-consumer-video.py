import json,hashlib,subprocess
from pathlib import Path
from PIL import Image
import numpy as np
P=Path(__file__).resolve().parents[1];O=P.parents[1];C=O/'candidates/round-02';R=C/'consumer'
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((R/'inspection-report.json').read_text());browser=json.loads((R/'browser-report.json').read_text());out=[]
for mode in ['full-chromium','headless-shell']:
 r=next(r for r in report['playback']if r['mode']==mode);m=next(m for m in browser['modes']if m['mode']==mode);want={};sheets={};ordered=[]
 for s in r['sheets']:
  sheets[s['path']]=Image.open(O/s['path']).convert('RGB')
  for c in s['cells']:
   key=(c['video'],round(c['videoTime']*25));want.setdefault(key,[]).append((s['path'],c));ordered.append((s['path'],c))
 verified={};videos=[]
 for vp in dict.fromkeys(c['video']for _,c in ordered):
  process=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(O/vp),'-vf','fps=25,crop=640:468:0:0','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
  index=0;trace=[]
  while True:
   raw=process.stdout.read(640*468*3)
   if len(raw)!=640*468*3:break
   arr=np.frombuffer(raw,dtype=np.uint8).reshape(468,640,3);marker=np.median(arr[4:12,628:636],axis=(0,1));slot=round((float(marker[0])-20)/18);phase=round((float(marker[1])-20)/18)
   if abs(marker[0]-(20+18*slot))<12 and abs(marker[1]-(20+18*phase))<12 and abs(marker[2]-245)<15 and 0<=slot<12 and 0<=phase<12:trace.append({'frame':index,'time':index/25,'slot':slot,'phase':phase})
   if (vp,index) in want:
    im=Image.fromarray(arr.copy())
    for sp,c in want[(vp,index)]:
     x,y,w,h=c['videoReviewCrop'];v=im.crop((x,y,x+w,y+h));sx,sy,sw,sh=c['sheetRect'];s=sheets[sp].crop((sx,sy,sx+sw,sy+sh));same=v.tobytes()==s.tobytes();expectedslot=['windup','active','recovery'].index(c['clip'])*4+['N','E','S','W'].index(c['direction']);assert same,(mode,c)
     verified[(sp,tuple(c['sheetRect']))]={'clip':c['clip'],'direction':c['direction'],'index':c['index'],'heldTerminal':c['heldTerminal'],'video':vp,'videoTime':index/25,'sheet':sp,'sheetRect':c['sheetRect'],'decodedPixelMatch':same,'actualVideoMarker':marker.tolist(),'decodedMarkerSlot':slot,'decodedMarkerPhase':phase,'markerMatchesExpected':slot==expectedslot and phase==c['index']}
   index+=1
  process.stdout.close();process.wait();assert process.returncode==0
  seen={(x['slot'],x['phase']) for x in trace};missing=[(s,i)for s in range(12)for i in range(12)if(s,i)not in seen]
  videos.append({'path':vp,'sha256':sha(O/vp),'actualDecoded25fpsFrames':index,'seenUniquePhases':len(seen),'missingPhases':missing,'decodedMarkerTrace':trace})
 cells=[verified[(sp,tuple(c['sheetRect']))]for sp,c in ordered];assert len(cells)==156;assert all(v['markerMatchesExpected']for v in cells)
 times={}
 for v in cells:times.setdefault(v['clip']+'-'+v['direction'],[]).append(v)
 chronological=all([v['index']for v in vv]==list(range(12))+[11]and len({v['video']for v in vv})==1 and all(a['videoTime']<b['videoTime']for a,b in zip(vv,vv[1:]))for vv in times.values());assert chronological
 assert videos[0]['missingPhases']==([[5,0]]if False else ([(5,0)]if mode=='full-chromium'else []))
 if mode=='full-chromium':
  retry=videos[1];assert retry['seenUniquePhases']==12
  assert all(x['slot']==5 for x in retry['decodedMarkerTrace'])
  assert all(c['video']==retry['path']for c in cells if c['clip']=='active'and c['direction']=='E')
 static=[]
 for s in m['static']:
  assert s['records'];assert all(x['frame']==5 and x['frameSize']==[320,448]and x['root']==[160,320]and x['plan']['scale']==2 for x in s['records'])
  static.append({'path':s['path'],'dataset':s.get('dataset'),'recordCount':len(s['records']),'allNativeRasterChannelsExact':all(x['nativeRasterVsAtlasChangedChannels']==0 for x in s['raster'])})
 out.append({'mode':mode,'browserVersion':m['browserVersion'],'launch':m['options'],'DPR':m['deviceScaleFactor'],'viewport':m['viewport'],'errors':m['errors'],'all144ActualPhasesAnd12HeldTerminalsVerified':chronological,'actualVideos':videos,'cells':cells,'static':static,'interpretation':'Every sheet cell equals exact actual decoded video pixels/time; all painted markers match expected clip/facing/phase in chronological continuous rows. Full Chromium primary actually misses Active/E0; its entire Active/E12phase+hold row comes from the scoped timed retry. Prewarm marker is not a valid timed marker. Lossy codec blur retained and judged separately from PNG quality.'})
residual=[];raw=[]
for c in ['windup','active','recovery']:
 for d in ['N','E','S','W']:
  for i in range(12):
   original=Image.open(C/'native'/c/d/f'{i:03d}.png').convert('RGBA');pub=Image.open(C/'published'/c/d/f'{i:03d}.png').convert('RGBA');expected=original.resize((640,896),Image.Resampling.LANCZOS);assert expected.tobytes()==pub.tobytes()
   ownraw=Image.open(P/'native/replay'/c/d/f'{i:03d}.png').convert('RGBA');rd=np.abs(np.asarray(ownraw).astype(np.int16)-np.asarray(original).astype(np.int16));raw.append({'clip':c,'direction':d,'index':i,'equal':not rd.any(),'maxAbs':int(rd.max()),'meanAbs':float(rd.mean())})
   replay=ownraw.resize((640,896),Image.Resampling.LANCZOS);aa=np.asarray(replay).astype(np.float64);bb=np.asarray(pub).astype(np.float64);delta=np.abs(aa-bb);diff=np.abs(aa[:,:,:3]*aa[:,:,3:]/255-bb[:,:,:3]*bb[:,:,3:]/255);changed=np.any(delta,axis=2)
   if changed.any():residual.append({'clip':c,'direction':d,'index':i,'changedPixels':int(changed.sum()),'maxRGBAdelta':float(delta.max()),'maxAlphaDelta':float(delta[:,:,3].max()),'maxPremultipliedRGBDelta':float(diff.max()),'meanPremultipliedRGBDelta':float(diff.mean()),'changedPixelAlphaRange':[float(np.minimum(aa[:,:,3],bb[:,:,3])[changed].min()),float(np.maximum(aa[:,:,3],bb[:,:,3])[changed].max())]})
dump(P/'inspection/independent-video-coverage.json',{'candidatePacketSHA256':sha(C/'packet.json'),'modes':out,'sourceHelpersVerified':browser['helpers'],'recordingGap':'Primary full Chromium Active/E0 unavailable; all13 Active/E cells use exact continuous timed retry video, not prewarm. Primary diagnostic remains unchanged.'})
dump(P/'native/normalization-and-replay-residuals.json',{'submittedNativeFullFrameLanczosExactPublished':144,'rawReplayExact':sum(x['equal']for x in raw),'rawReplayResiduals':raw,'independentReplayPublishedExact':144-len(residual),'nonexactIndependentReplayFrames':residual,'interpretation':'Exact submitted wholecanvas normalization independently verified. Own recapture differences and premultiplied edge impact measured without RGB/alpha repair or pixel-identical recapture claim.'})
print(json.dumps({'verifiedVideos':[{k:r[k]for k in ['mode','all144ActualPhasesAnd12HeldTerminalsVerified']}for r in out],'rawReplayExact':sum(x['equal']for x in raw),'rawMaxAbs':max(x['maxAbs']for x in raw),'rawMaxMean':max(x['meanAbs']for x in raw),'submittedNativeLanczosPublishedExact':144,'independentReplayResidualFrames':len(residual),'maxPremultipliedResidual':max([x['maxPremultipliedRGBDelta']for x in residual]or[0])},indent=2))
