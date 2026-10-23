import {createServer} from 'vite';
import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath}from'node:url';
const S=path.dirname(fileURLToPath(import.meta.url)),B=path.dirname(S),C=path.join(B,'candidates/round-01'),W=path.resolve(B,'../../../../../..');
const fixture='/'+path.relative(W,path.join(C,'consumer/fixture.html')).split(path.sep).join('/');
const server=await createServer({root:W,configFile:false,cacheDir:path.join(C,'consumer/vite-cache'),optimizeDeps:{noDiscovery:true,include:['react'],entries:[],force:true},server:{host:'127.0.0.1',port:0,strictPort:false},logLevel:'error'});await server.listen();
const report={fixture,helpers:[],modes:[],scope:'Private fixture using unchanged exact frozen current spriteFrame/groundRoot/orderPlacements/worldRasterPlan/paintWorldRaster. DPR1, actual CSS commoncanvas filter. Phase marker is evidence metadata outside sprite pixels.'};
for(const f of ['world-sprite-raster.js','sprite-layout.js']){const bytes=await fs.readFile(path.join(S,'round-01-inputs/consumer',f));report.helpers.push({path:'source/round-01-inputs/consumer/'+f,sha256:crypto.createHash('sha256').update(bytes).digest('hex')});}
try{
 for(const mode of ['full-chromium','headless-shell']){
  const options=mode==='full-chromium'?{headless:true,channel:'chromium'}:{headless:true};const browser=await chromium.launch(options);const out=path.join(C,'consumer',mode);await fs.mkdir(out,{recursive:true});
  const context=await browser.newContext({viewport:{width:1280,height:900},deviceScaleFactor:1,recordVideo:{dir:out,size:{width:1280,height:900}}});const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(new URL(fixture,server.resolvedUrls.local[0]).href);await page.waitForFunction(()=>window.ready===true);
  const m={mode,options,browserVersion:browser.version(),viewport:{width:1280,height:900},deviceScaleFactor:1,static:[],errors};
  for(const dataset of ['current','candidate'])for(const scale of [1,.5])for(const background of ['light','gray','dark']){
   const records=await page.evaluate(x=>window.renderEvidence(x),{datasets:[dataset],scale,background,seconds:5/12});const raster=await page.evaluate(()=>window.rasterEvidence());
   const name=`${dataset}-${scale===1?'logical':'phone'}-${background}.png`;await page.screenshot({path:path.join(out,name),fullPage:true});m.static.push({path:`candidates/round-01/consumer/${mode}/${name}`,records,raster});
  }
  m.frameSelections=[];for(let i=0;i<=12;i++){const records=await page.evaluate(seconds=>window.renderEvidence({datasets:['current','candidate'],scale:.5,background:'gray',seconds}),i/12);m.frameSelections.push({requestedSeconds:i/12,records});}
  await page.evaluate(()=>window.startPlayback());await page.waitForTimeout(15300);m.playbackLog=await page.evaluate(()=>{window.playing=false;return window.playbackLog;});
  await page.screenshot({path:path.join(out,'playback-last.png'),fullPage:true});const video=page.video();await context.close();const vp=await video.path();const dest=path.join(out,'actual-consumer-session.webm');await fs.rename(vp,dest);m.video=`candidates/round-01/consumer/${mode}/actual-consumer-session.webm`;
  await browser.close();report.modes.push(m);await fs.writeFile(path.join(C,'consumer/browser-report.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({mode,version:m.browserVersion,errors,playbackEvents:m.playbackLog.length}));
 }
}finally{await server.close();}
