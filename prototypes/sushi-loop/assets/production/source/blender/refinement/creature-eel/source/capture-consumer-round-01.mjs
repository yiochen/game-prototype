import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const P=path.dirname(fileURLToPath(import.meta.url)),E=path.dirname(P),C=path.join(E,'candidates/round-01');
const url='http://127.0.0.1:5167/prototypes/sushi-loop/assets/refinement/objects/creature-eel/candidates/round-01/consumer.html';
const hash=async p=>crypto.createHash('sha256').update(await fs.readFile(p)).digest('hex');
const records=[];
for(const[id,launch]of[['chromium',{headless:true,channel:'chromium'}],['shell',{headless:true}]]){
 const out=path.join(C,'browser',id);await fs.mkdir(out,{recursive:true});
 const browser=await chromium.launch(launch),context=await browser.newContext({viewport:{width:1800,height:960},deviceScaleFactor:1}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push({text:m.text(),location:m.location()})});page.on('response',r=>{if(r.status()>=400)errors.push({status:r.status(),url:r.url()})});
 await page.goto(url);await page.waitForFunction(()=>window.studyReady===true);
 const cdp=await context.newCDPSession(page);const versionDetails=await cdp.send('Browser.getVersion');
 const r={id,launch,version:browser.version(),versionDetails,DPR:await page.evaluate(()=>devicePixelRatio),viewport:{width:1800,height:960},helperHashes:{spriteLayout:await hash(path.join(C,'resources/consumer/sprite-layout.js')),worldRaster:await hash(path.join(C,'resources/consumer/world-sprite-raster.js'))},errors,modes:[],playback:[]};
 for(const mode of['all','logical','attachments','repeated']){const viewport={width:mode==='logical'?1800:920,height:960};await page.setViewportSize(viewport);const plan=await page.evaluate(m=>window.showStudy(m),mode),p=path.join(out,mode+'.png');await page.screenshot({path:p,fullPage:true});r.modes.push({mode,viewport,plan,path:path.relative(E,p),sha256:await hash(p)})}
 await page.setViewportSize({width:390,height:844});r.phoneViewport={width:390,height:844};const phonePlan=await page.evaluate(()=>window.showStudy('phone'));await page.screenshot({path:path.join(out,'phone.png'),fullPage:true});r.modes.push({mode:'phone',plan:phonePlan,path:path.relative(E,path.join(out,'phone.png')),sha256:await hash(path.join(out,'phone.png'))});
 await context.close();
 for(const panel of['wave','turn','reaction']){
  const context=await browser.newContext({viewport:{width:480,height:640},deviceScaleFactor:1,recordVideo:{dir:path.join(out,'video',panel),size:{width:480,height:640}}}),p=await context.newPage();p.on('pageerror',e=>errors.push(String(e)));await p.goto(url);await p.waitForFunction(()=>window.studyReady===true);const plan=await p.evaluate(panel=>window.showStudy('playback',panel),panel),play=await p.evaluate(()=>window.startPlayback(2.2)),boundaryWitness=await p.evaluate(()=>window.boundaryWitness());await p.evaluate(()=>window.setSeconds(.5));const shot=path.join(out,'playback-'+panel+'.png');await p.screenshot({path:shot,fullPage:true});const video=await p.video().path();await context.close();r.playback.push({panel,plan,viewport:{width:480,height:640},DPR:1,...play,boundaryWitness,representative:{path:path.relative(E,shot),sha256:await hash(shot)},video:{path:path.relative(E,video),sha256:await hash(video)}});
 }
 await browser.close();records.push(r);await fs.writeFile(path.join(C,'browser-records.json'),JSON.stringify(records,null,2)+'\n');console.log('MODE_COMPLETE',id,r.version,r.errors, r.playback.map(p=>({panel:p.panel,raf:p.timeline.length,witnesses:p.phaseWitnesses.length})))
}
