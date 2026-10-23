// One actual timed Active/E retry for the recorder's missing phase0; no source/atlas/helper edits.
import {createServer} from 'vite';import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath} from 'node:url';
const S=path.dirname(fileURLToPath(import.meta.url)),B=path.dirname(S),C=path.join(B,'candidates/round-02'),W=path.resolve(B,'../../../../../..'),out=path.join(C,'consumer/full-chromium/scoped-retry-active-E');await fs.mkdir(out,{recursive:true});
const fixture='/'+path.relative(W,path.join(C,'consumer/fixture.html')).split(path.sep).join('/');
const server=await createServer({root:W,configFile:false,cacheDir:path.join(out,'vite-cache'),optimizeDeps:{noDiscovery:true,include:['react'],entries:[],force:true},server:{host:'127.0.0.1',port:0,strictPort:false},logLevel:'error'});await server.listen();
const options={headless:true,channel:'chromium'},browser=await chromium.launch(options);
try{
 const context=await browser.newContext({viewport:{width:1280,height:900},deviceScaleFactor:1,recordVideo:{dir:out,size:{width:1280,height:900}}});const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(new URL(fixture,server.resolvedUrls.local[0]).href);await page.waitForFunction(()=>window.ready===true);
 await page.evaluate(()=>window.renderPlayback('active','E',0));await page.waitForTimeout(250);
 await page.evaluate(()=>{
  window.retryLog=[];window.retryPlaying=true;let start=null,previous=-1;
  function tick(now){
   if(!window.retryPlaying)return;if(start===null)start=now;const t=(now-start)/1000,frame=Math.min(11,Math.floor(t*12));
   if(frame!==previous){document.getElementById('phase-marker').style.background=`rgb(110,${20+18*frame},245)`;window.renderPlayback('active','E',t);window.retryLog.push({elapsed:t,clip:'active',direction:'E',frame});previous=frame;}
   requestAnimationFrame(tick);
  }requestAnimationFrame(tick);
 });
 await page.waitForTimeout(1300);const log=await page.evaluate(()=>{window.retryPlaying=false;return window.retryLog;});await page.screenshot({path:path.join(out,'terminal.png'),fullPage:true});const video=page.video();await context.close();await fs.rename(await video.path(),path.join(out,'actual-active-E-session.webm'));
 const report={scope:'Single scoped recorder retry of all12 Active/E phases plus heldterminal at original12fps;250ms frame0 prewarm occurs BEFORE timed playback and is not phase evidence. Same exact original fixture and current helpers/atlases. No source change or extra native render.',mode:'full-chromium',browserVersion:browser.version(),launchOptions:options,DPR:1,viewport:{width:1280,height:900},errors,playbackLog:log,video:'candidates/round-02/consumer/full-chromium/scoped-retry-active-E/actual-active-E-session.webm'};
 await fs.writeFile(path.join(out,'retry-report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{await browser.close();await server.close();}
