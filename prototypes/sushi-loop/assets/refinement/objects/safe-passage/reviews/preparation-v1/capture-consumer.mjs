import { chromium } from '@playwright/test';
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));const out=path.join(here,'browser');fs.mkdirSync(out,{recursive:true});const records=[];
for(const mode of ['chromium','shell']){
 const options=mode==='chromium'?{headless:true,channel:'chromium'}:{headless:true};const browser=await chromium.launch(options);
 for(const size of ['logical','phone'])for(const bg of ['light','gray','dark']){
  const viewport=size==='logical'?{width:900,height:420}:{width:390,height:480};const recordVideo=(size==='phone'&&bg==='gray')?{dir:path.join(out,mode,'video'),size:viewport}:undefined;
  const context=await browser.newContext({viewport,deviceScaleFactor:size==='phone'?2:1,recordVideo});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(`http://127.0.0.1:5473/consumer.html?size=${size}&bg=${bg}&source=current`);await page.waitForFunction(()=>window.ready===true);
  const dir=path.join(out,mode);fs.mkdirSync(dir,{recursive:true});let name=`current-${size}-${bg}`;await page.screenshot({path:path.join(dir,name+'.png')});const evidence=await page.evaluate(()=>window.evidence);
  if(size==='phone'&&bg==='gray'){
   await page.evaluate(()=>window.startPlayback());await page.waitForFunction(()=>window.playbackDone===true,{timeout:10000});const playback=await page.evaluate(()=>window.evidence.playback);fs.writeFileSync(path.join(dir,'actual-playback.json'),JSON.stringify(playback,null,2)+'\n');
  }
  if(size==='logical'&&bg==='gray'){
   for(let index=0;index<12;index++){
    await page.evaluate(i=>window.setFrame(i),index);
    const canvases=await page.locator('canvas').evaluateAll(nodes=>nodes.map(c=>c.toDataURL('image/png')));
    for(let j=0;j<4;j++){let target=path.join(dir,'frames','NESW'[j]);fs.mkdirSync(target,{recursive:true});fs.writeFileSync(path.join(target,String(index).padStart(3,'0')+'.png'),Buffer.from(canvases[j].split(',')[1],'base64'));}
   }
   await page.goto(`http://127.0.0.1:5473/consumer.html?size=${size}&bg=${bg}&source=replay`);await page.waitForFunction(()=>window.ready===true);await page.screenshot({path:path.join(dir,'replay-logical-gray.png')});
  }
  records.push({mode,browserVersion:browser.version(),launchOptions:options,viewport,dpr:size==='phone'?2:1,size,bg,source:'actual catalog original atlases',screenshot:path.relative(here,path.join(dir,name+'.png')),evidence,errors});
  const video=page.video();await context.close();if(video)records[records.length-1].video=path.relative(here,await video.path());
 }
 await browser.close();
}
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({records},null,2)+'\n');
console.log(JSON.stringify({records:records.length,browserVersions:[...new Set(records.map(r=>r.browserVersion))],errors:records.flatMap(r=>r.errors)}));
