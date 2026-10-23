import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';import path from 'node:path';
const here=path.dirname(new URL(import.meta.url).pathname);const out=path.join(here,'consumer');await fs.mkdir(out,{recursive:true});
const base='http://127.0.0.1:4197/resources/consumer/index.html';const report={browserModes:[]};
for(const [id,launch] of [['chromium',{headless:true,channel:'chromium'}],['shell',{headless:true}]]){
 const browser=await chromium.launch(launch);const record={id,launch,version:browser.version(),screenshots:[],playback:[]};
 const context=await browser.newContext({viewport:{width:800,height:1240},deviceScaleFactor:1});const page=await context.newPage();
 for(const scale of [1,.5])for(const [bg,color] of [['light','#f3eee4'],['gray','#777777'],['dark','#132033']]){
  await page.setViewportSize({width:scale===1?800:390,height:scale===1?1240:844});await page.goto(`${base}?scale=${scale}&bg=${encodeURIComponent(color)}`);await page.waitForFunction(()=>window.ready);
  const file=`${id}-${scale===1?'logical':'phone'}-${bg}.png`;await page.screenshot({path:path.join(out,file),fullPage:true});record.screenshots.push({file,viewport:page.viewportSize(),dpr:1,evidence:await page.evaluate(()=>window.evidence)});
 }
 await page.goto(`${base}?scale=.5&mode=all&bg=%23777777`);await page.waitForFunction(()=>window.ready);const all=`${id}-all48.png`;await page.screenshot({path:path.join(out,all),fullPage:true});record.screenshots.push({file:all,viewport:page.viewportSize(),dpr:1,evidence:await page.evaluate(()=>window.evidence)});await context.close();
 const motion=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,recordVideo:{dir:out,size:{width:390,height:844}}});const play=await motion.newPage();await play.goto(`${base}?scale=.5&mode=play&bg=%23777777`);await play.waitForFunction(()=>window.ready);await play.evaluate(()=>window.startPlayback());
 for(const t of [.02,.27,.52,.77,1.03,1.5]){
  await play.waitForFunction(t=>window.evidence.elapsed>=t,t);const file=`${id}-play-${String(t).replace('.','_')}.png`;await play.screenshot({path:path.join(out,file)});record.playback.push({file,requestedSeconds:t,evidence:await play.evaluate(()=>window.evidence)});
 }
 await play.waitForFunction(()=>window.evidence.complete);record.playbackFinal=await play.evaluate(()=>window.evidence);const video=play.video();await motion.close();await video.saveAs(path.join(out,`${id}-playback.webm`));record.video=`${id}-playback.webm`;await video.delete();
 await browser.close();report.browserModes.push(record);await fs.writeFile(path.join(here,'consumer-report.json'),JSON.stringify(report,null,2)+'\n');
}
