import {chromium} from '@playwright/test';
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),base=path.resolve(here,'../..'),out=path.join(base,'candidates/round-01/browser');fs.mkdirSync(out,{recursive:true});
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const records=[],helperHashes=Object.fromEntries(['world-sprite-raster.js','sprite-layout.js'].map(n=>[n,hash(path.join(here,'resources',n))]));
for(const mode of ['chromium','shell']){
 const launchOptions=mode==='chromium'?{headless:true,channel:'chromium'}:{headless:true};const browser=await chromium.launch(launchOptions);
 for(const size of ['logical','phone'])for(const bg of ['light','gray','dark']){
  const viewport=size==='logical'?{width:900,height:420}:{width:390,height:480},dir=path.join(out,mode);fs.mkdirSync(dir,{recursive:true});
  const playbackCase=size==='phone'&&bg==='gray';const context=await browser.newContext({viewport,deviceScaleFactor:size==='phone'?2:1,recordVideo:playbackCase?{dir:path.join(dir,'video'),size:viewport}:undefined});
  const page=await context.newPage(),errors=[],requestFailures=[];page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>requestFailures.push({url:r.url(),failure:r.failure()}));
  await page.goto(`http://127.0.0.1:5517/source/browser/consumer.html?size=${size}&bg=${bg}`);await page.waitForFunction(()=>window.ready===true);
  const evidence=await page.evaluate(()=>window.evidence),screenshot=path.join(dir,`${size}-${bg}.png`);await page.screenshot({path:screenshot});
  if(size==='logical'&&bg==='gray'){
   for(let index=0;index<12;index++){
    await page.evaluate(i=>window.setFrame(i),index);const images=await page.locator('canvas').evaluateAll(nodes=>nodes.map(c=>c.toDataURL('image/png')));
    for(let j=0;j<4;j++){const d=path.join(dir,'frames','NESW'[j]);fs.mkdirSync(d,{recursive:true});fs.writeFileSync(path.join(d,String(index).padStart(3,'0')+'.png'),Buffer.from(images[j].split(',')[1],'base64'));}
   }
  }
  let playback;
  if(playbackCase){await page.evaluate(()=>window.startPlayback());await page.waitForFunction(()=>window.playbackDone===true,null,{timeout:10000});playback=await page.evaluate(()=>({startedPerformanceMs:window.evidence.playbackStartedPerformanceMs,elapsedMs:window.evidence.playbackElapsedMs,samples:window.evidence.playback}));fs.writeFileSync(path.join(dir,'actual-playback.json'),JSON.stringify(playback,null,2)+'\n');}
  const video=page.video();await context.close();
  records.push({mode,launchOptions,browserVersion:browser.version(),viewport,dpr:size==='phone'?2:1,size,bg,helperHashes,screenshot:path.relative(base,screenshot),evidence,errors,requestFailures,playbackElapsedMs:playback?.elapsedMs,video:video?path.relative(base,await video.path()):undefined});
 }
 await browser.close();
}
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({asset:'safe-passage',round:'round-01',pathBase:'object experiment',records,helperHashes,notes:'Native nearest after common canvas resize; whole-canvas CSS filtering. Full sequence playback is from atlas cells, not APNG drawImage.'},null,2)+'\n');
console.log(JSON.stringify({cases:records.length,versions:[...new Set(records.map(r=>r.browserVersion))],errors:records.flatMap(r=>r.errors),requestFailures:records.flatMap(r=>r.requestFailures),playbackDurations:records.filter(r=>r.playbackElapsedMs).map(r=>({mode:r.mode,elapsedMs:r.playbackElapsedMs}))}));
