import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';import path from 'node:path';
const R=path.dirname(new URL(import.meta.url).pathname),url='http://127.0.0.1:4196',errors=[],results=[],videoResults=[];await fs.mkdir(path.join(R,'browser'),{recursive:true});await fs.mkdir(path.join(R,'video-complete'),{recursive:true});
const browser=await chromium.launch({headless:true});
for(const name of ['active-N-12fps','active-E-12fps','active-S-12fps','active-W-12fps','all4-12fps']){
 const page=await browser.newPage({viewport:{width:1100,height:900},deviceScaleFactor:1});page.on('pageerror',e=>errors.push(String(e)));await page.goto(`${url}/reviews/round-02-independent/video.html?src=${encodeURIComponent('/candidates/round-02/previews/'+name+'.mp4')}`);await page.waitForFunction(()=>v.readyState>=2);
 const playback=await page.evaluate(async()=>{
  const frames=[];v.playbackRate=1;const cv=document.createElement('canvas');cv.width=v.videoWidth;cv.height=v.videoHeight;const cx=cv.getContext('2d');let done=false;let first;cx.drawImage(v,0,0);frames.push({initialDecodedFrame:true,mediaTime:v.currentTime,data:cv.toDataURL('image/png').split(',')[1]});
  const grab=(now,meta)=>{first??=now;cx.drawImage(v,0,0);frames.push({callbackNow:now,wallSinceFirst:now-first,mediaTime:meta.mediaTime,presentedFrames:meta.presentedFrames,expectedDisplayTime:meta.expectedDisplayTime,data:cv.toDataURL('image/png').split(',')[1]});if(!done)v.requestVideoFrameCallback(grab);};v.requestVideoFrameCallback(grab);
  const start=performance.now();await v.play();await new Promise(resolve=>v.addEventListener('ended',resolve,{once:true}));done=true;await new Promise(r=>requestAnimationFrame(r));return{duration:v.duration,videoWidth:v.videoWidth,videoHeight:v.videoHeight,playbackRate:v.playbackRate,elapsed:performance.now()-start,frames,quality:v.getVideoPlaybackQuality?{total:v.getVideoPlaybackQuality().totalVideoFrames,dropped:v.getVideoPlaybackQuality().droppedVideoFrames}:null};
 });
 for(let i=0;i<playback.frames.length;i++){const fr=playback.frames[i],n=`video-complete/${name}-${String(i).padStart(2,'0')}.png`;await fs.writeFile(path.join(R,n),Buffer.from(fr.data,'base64'));delete fr.data;fr.path=n;}
 playback.declaredPath=`previews/${name}.mp4`;videoResults.push(playback);await page.close();
}
await fs.writeFile(path.join(R,'video-review-complete.json'),JSON.stringify({method:'Independent ordinary Chromium actual snapshotted consumer cases and actual declared MP4 playback at rate1 using requestVideoFrameCallback; no synthetic animation or source change.',browser:browser.version(),errors,cases:results,videos:videoResults},null,2)+'\n');await browser.close();console.log('BROWSER_COMPLETE',results.length,videoResults.map(v=>[v.declaredPath,v.frames.length,v.elapsed,v.quality]));
