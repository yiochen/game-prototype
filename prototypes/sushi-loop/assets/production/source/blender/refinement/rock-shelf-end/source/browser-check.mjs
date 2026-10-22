import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath} from 'node:url';
const B=path.dirname(fileURLToPath(import.meta.url));
for(const [mode,options] of [['fullChrome',{headless:true,channel:'chromium'}],['shell',{headless:true}]]){
const O=path.join(B,'../candidates/round-01/consumer',mode);await fs.mkdir(O,{recursive:true});
const browser=await chromium.launch(options);const cases=[];
for(const dpr of [1,2]){
 const context=await browser.newContext({viewport:{width:1840,height:1000},deviceScaleFactor:dpr});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('http://127.0.0.1:9138/source/consumer-review.html');await page.waitForFunction(()=>window.ready);
 for(const kind of ['single','pair','closedRun'])for(const size of [128,32]){
  if(dpr===2&&size!==32)continue;
  const manifest=await page.evaluate(o=>window.configure(o),{kind,size});const name=`${kind}-cell${size}-dpr${dpr}.png`;await page.screenshot({path:path.join(O,name),fullPage:true});cases.push({path:name,kind,size,dpr,manifest});
 }
 if(dpr===1)for(const kind of ['pair','closedRun'])for(const d of 'NESW'){const data=await page.evaluate(([k,d])=>window.commonRaster(k,d),[kind,d]);await fs.writeFile(path.join(O,`common-${kind}-${d}.png`),Buffer.from(data.split(',')[1],'base64'))}
 for(const [width,height] of [[360,780],[844,390]]){
  await page.setViewportSize({width,height});for(const d of 'NESW')for(const [pane,mult] of [['center',0],['endA',7],['endB',-7]]){
   const delta={S:[-128,0],N:[128,0],E:[0,128],W:[0,-128]}[d];const root=[width/2*4-delta[0]*mult,height/2*4-delta[1]*mult];
   const manifest=await page.evaluate(o=>window.configure(o),{long:true,size:32,viewport:[width,height],root,phase:pane==='center'?1:2,direction:d});const name=`long-${width}x${height}-${d}-${pane}-dpr${dpr}.png`;await page.screenshot({path:path.join(O,name)});cases.push({path:name,kind:'longRun',direction:d,pane,dpr,width,height,manifest});
  }
 }
 cases.push({dpr,pageErrors:errors});await context.close();
}
await fs.writeFile(path.join(O,'manifest.json'),JSON.stringify({browser:browser.version(),mode,launch:options,consumerHelpers:'byte-identical copies; no modifications',cases},null,2));await browser.close();console.log(mode+' consumer browser evidence complete');
}
