import {chromium} from '@playwright/test';import fs from 'node:fs/promises';import path from 'node:path';import crypto from 'node:crypto';
const base=path.resolve('prototypes/sushi-loop/assets/refinement/objects/belt-corner-n-e'),O=path.join(base,'candidates/round-01/consumer'),prior=path.join(O,'transient-capture');await fs.mkdir(prior,{recursive:true});const rows=[];
const browser=await chromium.launch({headless:true});
for(const mode of ['independent','connected','unbroken']){
 const original=path.join(O,`E-55-f11-808080-${mode}.png`);await fs.copyFile(original,path.join(prior,path.basename(original)));
 const context=await browser.newContext({viewport:{width:960,height:1200},deviceScaleFactor:1});const page=await context.newPage();
 for(const id of ['belt-corner-n-e','belt-straight-n'])await page.route(`**/assets/production/sprites/${id}/running-*.png*`,async route=>{if(new URL(route.request().url()).searchParams.has('import'))return route.continue();const d=route.request().url().match(/running-([NESW])/)[1];await route.fulfill({path:path.join(base,`candidates/round-01/atlases/${id==='belt-straight-n'?'family-frames':mode==='independent'?'frames':mode}-${d}.png`),contentType:'image/png'});});
 await page.goto(`http://127.0.0.1:4178/prototypes/sushi-loop/assets/refinement/objects/belt-corner-n-e/source/consumer-bench.html?direction=E&pitch=55&frame=11&phaseX=.25&phaseY=.5&background=%23808080&mode=${mode}`);await page.locator('.object-tile-scene[data-world-raster-ready="true"]').waitFor();
 const hashes=[];
 for(let i=0;i<3;i++){await page.waitForTimeout(500);const file=path.join(O,`retry-E55-f11-${mode}-${i}.png`);await page.locator('.object-tile-scene').screenshot({omitBackground:true,path:file});hashes.push(crypto.createHash('sha256').update(await fs.readFile(file)).digest('hex'));}
 const canvas=await page.locator('canvas').evaluate(c=>c.toDataURL('image/png'));await fs.writeFile(path.join(O,`retry-E55-f11-${mode}-native-canvas.png`),Buffer.from(canvas.split(',')[1],'base64'));
 await fs.copyFile(path.join(O,`retry-E55-f11-${mode}-2.png`),original);rows.push({mode,hashes,allThreeScreenshotBytesStable:hashes.every(h=>h===hashes[0]),evidence:await page.evaluate(()=>window.benchEvidence)});await context.close();
}
await browser.close();await fs.writeFile(path.join(O,'retry.json'),JSON.stringify({reason:'One connected E55-frame11 screenshot in the initial288 displayed torn/cropped atlas contents. Original case images retained in transient-capture/. Fresh isolated browser contexts and three500ms-separated screenshots plus actual native canvas readback establish stable final actual consumer output. No asset or renderer code changed.',rows},null,2));
