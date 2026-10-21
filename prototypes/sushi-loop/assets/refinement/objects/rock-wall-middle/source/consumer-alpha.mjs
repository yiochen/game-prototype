import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';import path from 'node:path';
const base=path.resolve('prototypes/sushi-loop/assets/refinement/objects/rock-wall-middle'),out=path.join(base,'candidates/round-03/consumer');await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:960,height:1300},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.route('**/assets/production/sprites/rock-wall-middle/static-*.png*',async route=>{if(new URL(route.request().url()).searchParams.has('import'))return route.continue();const d=route.request().url().match(/static-([NESW])/)[1];await route.fulfill({path:path.join(base,`candidates/round-03/atlas-static-${d}.png`),contentType:'image/png'});});
await page.route('**/assets/production/sprites/rock-wall-edge/static-*.png*',async route=>{if(new URL(route.request().url()).searchParams.has('import'))return route.continue();const d=route.request().url().match(/static-([NESW])/)[1];await route.fulfill({path:path.join(base,`candidates/round-03/connected-published-${d}.png`),contentType:'image/png'});});
const cases=[];for(const direction of ['N','E','S','W'])for(const pitch of [128,32])for(const background of ['transparent'])cases.push({direction,pitch,phaseX:.25,phaseY:.5,background});
// Bounded coverage: all facings, two actual use pitches plus fractional fit pitch, four pan phases.
let n=0;const evidence=[];
for(const c of cases){
 const stem=`${c.direction}-${c.pitch}-${c.phaseX}-${c.phaseY}-${c.background}`;
 for(const mode of ['independent','connected']){
  const q=new URLSearchParams({...c,mode});await page.goto(`http://127.0.0.1:5194/prototypes/sushi-loop/assets/refinement/objects/rock-wall-middle/source/consumer-bench.html?${q}`,{waitUntil:'domcontentloaded'});
  await page.locator('.object-tile-scene image').first().waitFor({state:'attached'});await page.waitForFunction(()=>document.querySelectorAll('[data-sprite-source]').length>0);await page.evaluate(async()=>{await Promise.all([...document.querySelectorAll('image')].map(i=>new Promise(resolve=>{const t=new Image();t.onload=resolve;t.onerror=resolve;t.src=i.href.baseVal})));});
  const svg=page.locator('.object-tile-scene');await svg.screenshot({omitBackground:true,path:path.join(out,`${stem}-${mode}.png`)});
  evidence.push({case:stem,mode,...await page.evaluate(()=>window.benchEvidence)});
 }
 if(++n%12===0)console.log('consumer cases',n,'/',cases.length);
}
await fs.writeFile(path.join(out,'alpha-cases.json'),JSON.stringify({cases:cases.length,errors,evidence},null,2));await browser.close();
