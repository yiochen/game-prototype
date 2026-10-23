import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';import path from 'node:path';import crypto from 'node:crypto';
const base=path.resolve('prototypes/sushi-loop/assets/refinement/objects/decor-foreground-rock'),out=path.join(base,'candidates/round-01/consumer');await fs.mkdir(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const dependencyNames=['object-review.jsx','sprite-layout.js','world-sprite-raster.js','object-review-data.js'];
const dependencies=Object.fromEntries(await Promise.all(dependencyNames.map(async n=>[n,sha(await fs.readFile(path.resolve('prototypes/sushi-loop/wireframe',n)))])));
const candidateUrls={};for(const d of 'NESW'){const b=await fs.readFile(path.join(base,`candidates/round-01/atlases/static-${d}.png`));candidateUrls[d]=`http://127.0.0.1:4178/prototypes/sushi-loop/assets/refinement/objects/decor-foreground-rock/candidates/round-01/atlases/static-${d}.png?sha256=${sha(b)}`;}
const browser=await chromium.launch({headless:true});const page=await browser.newPage({deviceScaleFactor:1});const errors=[],redirects=[],responses=[];page.on('pageerror',e=>errors.push(e.message));
page.on('response',async res=>{if(res.url().includes('/decor-foreground-rock/candidates/round-01/atlases/')){const b=await res.body();responses.push({url:res.url(),status:res.status(),sha256:sha(b),expectedSHA256:new URL(res.url()).searchParams.get('sha256')});}});
await page.route('**/assets/production/sprites/decor-foreground-rock/static-*.png*',async route=>{
 const u=new URL(route.request().url());if(u.searchParams.has('import')||u.searchParams.has('url'))return route.continue();const d=u.pathname.match(/static-([NESW])/)[1];redirects.push({from:u.href,to:candidateUrls[d],direction:d});await route.fulfill({status:302,headers:{location:candidateUrls[d]},body:''});
});
const cases=[];for(const [name,width,height] of [['desktop',1440,1000],['phone',390,844],['landscape',844,390]]){
 await page.setViewportSize({width,height});await page.emulateMedia({reducedMotion:'reduce'});
 await page.goto('http://127.0.0.1:4178/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-decor-foreground-rock',{waitUntil:'domcontentloaded'});
 await page.locator('#prototype-stage[data-story="object-decor-foreground-rock"]').waitFor();
 const scenes=page.locator('.object-tile-scene');await scenes.first().waitFor();
 await page.waitForFunction(()=>[...document.querySelectorAll('.object-tile-scene')].length>=3&&[...document.querySelectorAll('.object-tile-scene')].every(s=>s.dataset.worldRasterReady==='true'));
 const rootCheck=page.getByLabel('Roots & attachments');if(await rootCheck.isChecked())await rootCheck.uncheck();
 await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
 const state=await scenes.evaluateAll(nodes=>nodes.map(s=>({label:s.getAttribute('aria-label'),ready:s.dataset.worldRasterReady,error:s.dataset.worldRasterError||null,viewBox:s.getAttribute('viewBox'),size:[s.getBoundingClientRect().width,s.getBoundingClientRect().height],canvas:[s.querySelector('canvas')?.width,s.querySelector('canvas')?.height],sources:[...s.querySelectorAll('[data-sprite-source]')].map(n=>n.dataset.spriteSource),placements:[...s.querySelectorAll(':scope > g[data-placement]')].map(n=>n.dataset.placement)})));
 const selected=name==='landscape'?[0]:[0,1,2];const images=[];
 for(const i of selected){await scenes.nth(i).scrollIntoViewIfNeeded();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(r)));const file=`${name}-${['four-facings','repeated','interaction'][i]}.png`;await scenes.nth(i).screenshot({path:path.join(out,file)});images.push(`candidates/round-01/consumer/${file}`);}
 if(name==='phone'){await scenes.first().scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'phone-standalone-context.png')});images.push('candidates/round-01/consumer/phone-standalone-context.png');}
 const paintedCanvases=await scenes.locator('canvas').evaluateAll(ns=>ns.map(n=>n.toDataURL('image/png'))); const paintSignatures=paintedCanvases.map(p=>sha(Buffer.from(p.split(',')[1],'base64'))); cases.push({name,viewport:[width,height],url:page.url(),paintSignatures,worldRasterReady:state.every(s=>s.ready==='true'&&!s.error),scenes:state,images});
}
// Representative larger scenery composition uses the actual full underwater renderer.
// Browser-only fixture replaces two outer reef slots and adds one bank-side stone;
// all app files remain byte-for-byte unchanged and actors retain native registrations.
const underwaterSource=await fs.readFile(path.resolve('prototypes/sushi-loop/wireframe/underwater-showcase-data.js'),'utf8');
const fixtureSource=underwaterSource.replace("...gardens,", "...gardens,\n    item('candidate-near-sub', 'decor-foreground-rock', 1.25, 11.3, 'S'),\n    item('candidate-near-eel', 'decor-foreground-rock', 4.7, 5.9, 'W'),\n    item('candidate-bank-north', 'decor-foreground-rock', 1.0, 2.4, 'E'),");
let fixtureModuleRequests=0;await page.route('**/wireframe/underwater-showcase-data.js*',async route=>{fixtureModuleRequests++;return route.fulfill({status:200,contentType:'application/javascript',body:fixtureSource});});
for(const [name,width,height] of [['phone',390,844],['landscape',844,390],['desktop',1440,1000]]){
 await page.setViewportSize({width,height});await page.goto('http://127.0.0.1:4178/prototypes/sushi-loop/?ntl-drawer-state=hidden&candidate-fixture=foreground-round01#scene-underwater',{waitUntil:'domcontentloaded'});
 await page.locator('#prototype-stage[data-story="scene-underwater"]').waitFor();
 const scene=page.locator('.world-showcase-figure .object-tile-scene');await scene.waitFor();
 await page.waitForFunction(()=>document.querySelector('.world-showcase-figure .object-tile-scene')?.dataset.worldRasterReady==='true');
 await scene.scrollIntoViewIfNeeded();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
 const state=await scene.evaluate(s=>({ready:s.dataset.worldRasterReady,error:s.dataset.worldRasterError||null,viewBox:s.getAttribute('viewBox'),size:[s.getBoundingClientRect().width,s.getBoundingClientRect().height],canvas:[s.querySelector('canvas')?.width,s.querySelector('canvas')?.height],sources:[...s.querySelectorAll('[data-sprite-source]')].map(n=>n.dataset.spriteSource),placements:[...s.querySelectorAll(':scope > g[data-placement]')].map(n=>n.dataset.placement)}));
 const file=`${name}-underwater-scenery.png`;await scene.screenshot({path:path.join(out,file)});
 cases.push({name:`${name}-underwater-representative-fixture`,viewport:[width,height],url:page.url(),worldRasterReady:state.ready==='true'&&!state.error,scenes:[state],images:[`candidates/round-01/consumer/${file}`],fixture:{originalSHA256:sha(Buffer.from(underwaterSource)),fixtureSHA256:sha(Buffer.from(fixtureSource)),sourceUnchanged:sha(await fs.readFile(path.resolve('prototypes/sushi-loop/wireframe/underwater-showcase-data.js')))===sha(Buffer.from(underwaterSource)),addedNativePlacements:[['decor-foreground-rock',1.25,11.3,'S'],['decor-foreground-rock',4.7,5.9,'W'],['decor-foreground-rock',1,2.4,'E']]}});
}
const evidence={fixtureModuleRequests,renderer:'actual catalog #object-decor-foreground-rock SpriteScene with shared world-sprite-raster.js',candidateBinding:'production image requests redirect to exact same-origin candidate URL with sha256 query; no production files modified',candidateUrls,dependencies,errors,redirects,responses,cases};
await fs.writeFile(path.join(out,'evidence.json'),JSON.stringify(evidence,null,2)+'\n');await browser.close();console.log(JSON.stringify({cases:cases.map(c=>({name:c.name,ready:c.worldRasterReady,images:c.images})),errors,redirects:redirects.length,responses:responses.length,allResponseHashesMatch:responses.every(r=>r.sha256===r.expectedSHA256)},null,2));
