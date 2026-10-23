import {chromium} from '@playwright/test';
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));const out=path.join(here,'browser');fs.mkdirSync(out,{recursive:true});const records=[];
for(const mode of ['chromium','shell']){
 const launchOptions=mode==='chromium'?{headless:true,channel:'chromium'}:{headless:true},browser=await chromium.launch(launchOptions);
 for(const size of ['logical','phone'])for(const bg of ['light','gray','dark']){
  const viewport=size==='logical'?{width:900,height:420}:{width:390,height:480},dpr=size==='phone'?2:1;
  const ctx=await browser.newContext({viewport,deviceScaleFactor:dpr});const page=await ctx.newPage(),errors=[],failed=[];page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failed.push({url:r.url(),failure:r.failure()}));
  await page.goto(`http://127.0.0.1:5521/source/browser/consumer.html?size=${size}&bg=${bg}`);await page.waitForFunction(()=>window.ready===true);
  const dir=path.join(out,mode);fs.mkdirSync(dir,{recursive:true});await page.screenshot({path:path.join(dir,`${size}-${bg}.png`)});
  const evidence=await page.evaluate(()=>window.evidence);
  if(size==='logical'&&bg==='gray'){
   for(let i=0;i<12;i++){
    await page.evaluate(i=>window.setFrame(i),i);let frames=await page.locator('canvas').evaluateAll(cs=>cs.map(c=>c.toDataURL('image/png')));
    for(let j=0;j<4;j++){const d=path.join(dir,'frames','NESW'[j]);fs.mkdirSync(d,{recursive:true});fs.writeFileSync(path.join(d,`${String(i).padStart(3,'0')}.png`),Buffer.from(frames[j].split(',')[1],'base64'));}
   }
  }
  if(size==='phone'&&bg==='gray'){
   await page.evaluate(()=>window.startPlayback());await page.waitForFunction(()=>window.playbackDone===true,null,{timeout:10000});const playback=await page.evaluate(()=>({startedPerformanceMs:window.evidence.playbackStartedPerformanceMs,elapsedMs:window.evidence.playbackElapsedMs,samples:window.evidence.playback}));fs.writeFileSync(path.join(dir,'actual-playback.json'),JSON.stringify(playback,null,2)+'\n');
  }
  records.push({mode,launchOptions,version:browser.version(),viewport,dpr,size,bg,evidence,errors,failed,screenshot:path.relative(here,path.join(dir,`${size}-${bg}.png`))});await ctx.close();
 }
 await browser.close();
}
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({records,source:'Exact immutable submitted consumer.html, actual099/570 helper modules, candidate4original6x2atlases; all media outputs under own reviews. No APNG drawImage or helper changes. Existing packet-bound real compositor videos inspected separately; no redundant video created.'},null,2)+'\n');console.log(JSON.stringify({cases:records.length,versions:[...new Set(records.map(r=>r.version))],errors:records.flatMap(r=>r.errors),failed:records.flatMap(r=>r.failed)}));
