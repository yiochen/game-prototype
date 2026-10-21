import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
const B=path.resolve('prototypes/sushi-loop/assets/refinement/objects/column-broken');
const O=path.join(B,'reviews/consumer-round-03');await fs.mkdir(O,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const urls={},expected={};for(const d of 'NESW'){const bytes=await fs.readFile(path.join(B,`candidates/round-03/atlases/static-${d}.png`));expected[d]=sha(bytes);urls[d]=`http://127.0.0.1:4178/prototypes/sushi-loop/assets/refinement/objects/column-broken/candidates/round-03/atlases/static-${d}.png?sha256=${expected[d]}`;}
const browser=await chromium.launch({headless:true});const page=await browser.newPage({deviceScaleFactor:1});const errors=[],responses=[],pending=[],cases=[];
page.on('pageerror',error=>errors.push(error.message));
page.on('response',r=>{if(r.url().includes('/column-broken/candidates/round-03/atlases/'))pending.push((async()=>{responses.push({url:r.url(),status:r.status(),sha256:sha(await r.body())});})());});
await page.route('**/assets/production/sprites/column-broken/static-*.png*',async route=>{const u=new URL(route.request().url());if(u.searchParams.has('import')||u.searchParams.has('url'))return route.continue();const d=u.pathname.match(/static-([NESW])/)[1];await route.fulfill({status:302,headers:{location:urls[d]},body:''});});
for(const [name,width,height] of [['desktop',1440,1000],['phone',390,844],['landscape',844,390]]){
 await page.setViewportSize({width,height});await page.emulateMedia({reducedMotion:'reduce'});await page.goto('http://127.0.0.1:4178/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-column-broken',{waitUntil:'domcontentloaded'});
 await page.locator('#prototype-stage[data-story="object-column-broken"]').waitFor();await page.waitForFunction(()=>[...document.querySelectorAll('.object-tile-scene')].length>=3&&[...document.querySelectorAll('.object-tile-scene')].every(s=>s.dataset.worldRasterReady==='true'));
 const check=page.getByLabel('Roots & attachments');if(await check.isChecked())await check.uncheck();
 const scenes=page.locator('.object-tile-scene');const state=await scenes.evaluateAll(ns=>ns.map(s=>({label:s.getAttribute('aria-label'),ready:s.dataset.worldRasterReady,error:s.dataset.worldRasterError,viewBox:s.getAttribute('viewBox'),canvas:[s.querySelector('canvas').width,s.querySelector('canvas').height],sources:[...s.querySelectorAll('[data-sprite-source]')].map(x=>x.dataset.spriteSource)})));
 const files=[];for(let i=0;i<3;i++){await scenes.nth(i).scrollIntoViewIfNeeded();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));const f=`${name}-${['four-facings','repeated','interaction'][i]}.png`;await scenes.nth(i).screenshot({path:path.join(O,f)});files.push(f);}
 await scenes.first().scrollIntoViewIfNeeded();await page.screenshot({path:path.join(O,`${name}-viewport.png`)});
 cases.push({name,viewport:[width,height],url:page.url(),state,files,viewportScreenshot:`${name}-viewport.png`,documentOverflow:await page.evaluate(()=>({scrollWidth:document.documentElement.scrollWidth,viewport:window.innerWidth}))});
}
await Promise.all(pending);await browser.close();const result={source:'independent judge live actual SpriteScene inspection',expected,urls,responses,errors,cases};await fs.writeFile(path.join(O,'evidence.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({errors,responseHashesCorrect:responses.every(r=>r.sha256===new URL(r.url).searchParams.get('sha256')),cases:cases.map(c=>({name:c.name,scenes:c.state.length,overflow:c.documentOverflow}))},null,2));
