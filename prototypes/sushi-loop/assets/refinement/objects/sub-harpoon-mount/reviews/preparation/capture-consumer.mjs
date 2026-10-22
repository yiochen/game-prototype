import { chromium } from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs/promises';
const p=path.dirname(new URL(import.meta.url).pathname);const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1300,height:1000},deviceScaleFactor:1});const results=[];const errors=[];page.on('pageerror',e=>errors.push(String(e)));
for(const pitch of [128,47.3,32])for(const d of ['N','E','S','W'])for(const f of [1,6,12]){
 await page.goto(`http://127.0.0.1:4186/consumer.html?d=${d}&f=${f}&pitch=${pitch}`);
 await page.waitForFunction(()=>document.body.dataset.ready==='true');await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
 const data=await page.evaluate(()=>window.consumerEvidence);data.screenshot=`consumer-${d}-${f}-${pitch}.png`;await page.screenshot({path:path.join(p,data.screenshot),fullPage:true});results.push(data);
}
await fs.writeFile(path.join(p,'consumer-evidence.json'),JSON.stringify({method:'Exact immutable actual layout/raster functions; ordinary Chromium canvas and SVG foreignObject, whole frames, no per-view fitting. This bench is source-context preparation, not actual React-page approval.',browser:browser.version(),errors,cases:results},null,2)+'\n');await browser.close();
