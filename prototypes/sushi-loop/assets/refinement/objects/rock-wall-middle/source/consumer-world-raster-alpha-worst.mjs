import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';import path from 'node:path';import crypto from 'node:crypto';
const base=path.resolve('prototypes/sushi-loop/assets/refinement/objects/rock-wall-middle'),out=path.join(base,'candidates/round-04/consumer-world-raster');await fs.mkdir(out,{recursive:true});
const dependencyNames=['object-review.jsx','sprite-layout.js','world-sprite-raster.js'];
const dependencies=Object.fromEntries(await Promise.all(dependencyNames.map(async n=>[n,crypto.createHash('sha256').update(await fs.readFile(path.resolve('prototypes/sushi-loop/wireframe',n))).digest('hex')])));
const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:960,height:1300},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
for(const [id,pattern]of [['rock-wall-middle','atlas-static'],['rock-wall-edge','connected-published']])await page.route(`**/assets/production/sprites/${id}/static-*.png*`,async route=>{if(new URL(route.request().url()).searchParams.has('import'))return route.continue();const d=route.request().url().match(/static-([NESW])/)[1];await route.fulfill({path:path.join(base,`candidates/round-03/${pattern}-${d}.png`),contentType:'image/png'});});
const cases=[{direction:'E',pitch:128,phaseX:.25,phaseY:.5,background:'transparent'}];
let n=0;const evidence=[];
for(const c of cases){
 const suffix=c.background==='#808080'?'':`-${c.background.startsWith('#')?c.background.slice(1):c.background}`;
 const stem=`${c.direction}-${c.pitch}-${c.phaseX}-${c.phaseY}${suffix}`;
 for(const mode of ['independent','connected']){
  const q=new URLSearchParams({...c,mode});await page.goto(`http://127.0.0.1:4178/prototypes/sushi-loop/assets/refinement/objects/rock-wall-middle/source/consumer-world-raster-bench.html?${q}`,{waitUntil:'domcontentloaded'});
  await page.locator('.object-tile-scene[data-world-raster-ready="true"]').waitFor({state:'visible'});
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const state=await page.evaluate(async()=>{const s=document.querySelector('.object-tile-scene'),c=s.querySelector('canvas'),f=s.querySelector('foreignObject');const bytes=c.getContext('2d').getImageData(0,0,c.width,c.height).data;const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');return {ready:s.dataset.worldRasterReady,error:s.dataset.worldRasterError||null,canvasSize:[c.width,c.height],canvasRGBAsha256:hash,worldRasterBounds:[f.getAttribute('x'),f.getAttribute('y'),f.getAttribute('width'),f.getAttribute('height')].map(Number)}});
  if(state.ready!=='true'||state.error)throw new Error(JSON.stringify(state));
  await page.locator('.object-tile-scene').screenshot({omitBackground:true,path:path.join(out,`${stem}-${mode}.png`)});
  evidence.push({case:stem,mode,...await page.evaluate(()=>window.benchEvidence),worldRaster:state});
 }
 if(++n%12===0)console.log('world-raster consumer cases',n,'/',cases.length);
}
const finalDependencies=Object.fromEntries(await Promise.all(dependencyNames.map(async n=>[n,crypto.createHash('sha256').update(await fs.readFile(path.resolve('prototypes/sushi-loop/wireframe',n))).digest('hex')])));
await fs.writeFile(path.join(out,'alpha-worst-case.json'),JSON.stringify({cases:cases.length,errors,dependencies,finalDependencies,dependenciesUnchanged:JSON.stringify(dependencies)===JSON.stringify(finalDependencies),evidence},null,2));await browser.close();
