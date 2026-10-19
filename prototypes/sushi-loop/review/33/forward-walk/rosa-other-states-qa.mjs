import {createRequire} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../../../../../',import.meta.url));
const require=createRequire(join(root,'package.json')),{chromium,expect}=require('@playwright/test');
const output='/private/tmp/sushi-object-review/walk-gait/rosa-other-states',report={clips:[],errors:[]};
const browser=await chromium.launch(),began=Date.now();
try{
 const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});page.on('pageerror',e=>report.errors.push(e.message));
 await page.goto('http://127.0.0.1:4189/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-customer-rosa');
 const stage=page.locator('#prototype-stage');await expect(stage).toHaveAttribute('data-story','object-customer-rosa');await stage.getByLabel('Roots & attachments',{exact:true}).uncheck();
 for(const clip of ['stand','seated-wait','eat']){
  await stage.getByLabel('Scene state',{exact:true}).selectOption(clip);
  for(const frame of [0,3,6,9]){
   await stage.getByRole('slider',{name:'Animation frame'}).fill(String(frame));
   for(const direction of ['N','E','S','W'])await expect(stage.locator('.object-tile-scene').first().locator(`:scope > g[data-object="customer-rosa"][data-direction="${direction}"]`)).toHaveAttribute('data-frame',String(frame));
  }
  await stage.getByRole('slider',{name:'Animation frame'}).fill('6');
  const images=await stage.locator('.object-review-section').first().locator('image').evaluateAll(async nodes=>Promise.all([...new Set(nodes.map(e=>e.getAttribute('href')))].map(src=>new Promise(resolve=>{const i=new Image();i.onload=()=>resolve([i.naturalWidth,i.naturalHeight]);i.onerror=()=>resolve([0,0]);i.src=src;}))));
  expect(images.every(([w,h])=>w&&h)).toBe(true);
  if(clip==='seated-wait')await stage.locator('.object-interaction').first().screenshot({path:join(output,'rosa-seated-wait-actual-stool-context.png')});
  if(clip==='eat'){
   // Verification only: substitute the current S eat frame into the already
   // registered stool placement. Production UI and manifest remain unchanged.
   await page.evaluate(()=>{
    const source=document.querySelector('.object-tile-scene > g[data-object="customer-rosa"][data-direction="S"] > svg');
    const figure=document.querySelector('.object-interaction'),target=figure.querySelector('g[data-object="customer-rosa"] > svg'),replacement=source.cloneNode(true);
    for(const key of ['x','y'])replacement.setAttribute(key,target.getAttribute(key));target.replaceWith(replacement);
    figure.querySelector('figcaption').textContent='Verification-only eat pose on the registered stool placement';
   });
   await stage.locator('.object-interaction').first().screenshot({path:join(output,'rosa-eat-transient-stool-diagnostic.png')});
  }
  report.clips.push({id:clip,facings:4,sampledFrames:[0,3,6,9],decodedImages:images.length});
 }
 expect(report.errors).toEqual([]);report.passed=true;
}catch(error){report.failure=error.stack;throw error;}finally{report.durationSeconds=(Date.now()-began)/1000;await writeFile(join(output,'browser-report.json'),JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify(report));}
