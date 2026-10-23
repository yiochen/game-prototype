import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const P=path.dirname(fileURLToPath(import.meta.url));const url='http://127.0.0.1:5163/prototypes/sushi-loop/assets/refinement/objects/creature-eel/reviews/preparation-v1/consumer.html';
const records=[];
for(const [id,launch]of [['chromium',{headless:true,channel:'chromium'}],['shell',{headless:true}]]){
 const browser=await chromium.launch(launch);const context=await browser.newContext({viewport:{width:1800,height:960},deviceScaleFactor:1,recordVideo:{dir:path.join(P,'browser',id,'video'),size:{width:1000,height:800}}});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));await page.goto(url);await page.waitForFunction(()=>window.studyReady===true);
 const r={id,launch,version:browser.version(),DPR:1,viewport:{width:1800,height:960},modes:[],errors};
 for(const mode of ['all','logical','attachments']){const plan=await page.evaluate(m=>window.showStudy(m),mode);await page.screenshot({path:path.join(P,'browser',id,mode+'.png'),fullPage:true});r.modes.push({mode,plan});}
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>window.showStudy('phone'));await page.screenshot({path:path.join(P,'browser',id,'phone.png'),fullPage:true});r.phoneViewport={width:390,height:844};
 await page.setViewportSize({width:1000,height:800});await page.evaluate(()=>window.showStudy('playback'));r.timeline=await page.evaluate(()=>window.startPlayback());for(const seconds of [0,.5,11/12,1,2]){r.modes.push({mode:'playback',seconds,frames:await page.evaluate(t=>window.setSeconds(t),seconds)});await page.screenshot({path:path.join(P,'browser',id,`playback-${String(seconds).replace('.','_')}.png`),fullPage:true})}
 await context.close();await browser.close();records.push(r);
}
await fs.writeFile(path.join(P,'browser-records.json'),JSON.stringify(records,null,2)+'\n');console.log(JSON.stringify(records.map(({id,version,errors,timeline})=>({id,version,errors,timelineSamples:timeline.length})),null,2));
