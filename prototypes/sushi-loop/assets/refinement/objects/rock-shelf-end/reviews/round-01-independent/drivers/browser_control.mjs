import {chromium} from '@playwright/test';import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),out=path.join(root,'captures/consumer');let reports=[];
for(const [mode,options] of [['fullChrome',{headless:true,channel:'chromium'}],['shell',{headless:true}]]){
 const browser=await chromium.launch(options),report={mode,options,version:browser.version(),cases:[],errors:[]};
 for(const dpr of [1,2]){
  const context=await browser.newContext({viewport:{width:980,height:1000},deviceScaleFactor:dpr}),page=await context.newPage();page.on('pageerror',err=>report.errors.push(err.message));await page.goto('http://127.0.0.1:9146/reviews/round-01-independent/consumer.html');await page.waitForFunction(()=>window.ready);
  for(const [size,kind] of (dpr===1?[[128,'both'],[32,'pair'],[32,'closedRun']]:[[32,'pair'],[32,'closedRun']])){
   const cases=await page.evaluate(([size,kind])=>window.configure(size,kind),[size,kind]);let file=`${mode}-${size}-${kind}-dpr${dpr}.png`;await page.screenshot({path:path.join(out,file),fullPage:true});report.cases.push({file,size,kind,dpr,cases});
  }
  if(dpr===1)for(const kind of ['pair','closedRun'])for(const d of 'NESW'){const uri=await page.evaluate(([kind,d])=>window.raw(kind,d),[kind,d]);await fs.writeFile(path.join(out,`${mode}-raw-${kind}-${d}.png`),Buffer.from(uri.split(',')[1],'base64'))}
  await context.close();
 }
 await browser.close();reports.push(report);
}
await fs.writeFile(path.join(root,'measurements/browser-control.json'),JSON.stringify(reports,null,2));console.log('INDEPENDENT CONSUMER CONTROLS COMPLETE',reports.map(r=>({mode:r.mode,version:r.version,errors:r.errors,cases:r.cases.length})));
