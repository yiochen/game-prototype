import { createRequire } from 'node:module';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
const root=fileURLToPath(new URL('../../../../../',import.meta.url));
const require=createRequire(join(root,'package.json'));
const {chromium,expect}=require('@playwright/test');
const {placementAtTime,groundRoot}=await import(pathToFileURL(join(root,'prototypes/sushi-loop/wireframe/sprite-layout.js')));
const library=JSON.parse(await readFile(join(root,'prototypes/sushi-loop/assets/production/library.json'),'utf8'));
const objects=library.objects,byid=new Map(objects.map(o=>[o.id,o]));
const targets=objects.filter(o=>o.interactions.some(s=>s.connectionReview));
expect(targets).toHaveLength(50);
const output='/private/tmp/sushi-object-review/connected-fixtures/rendered';
await mkdir(output,{recursive:true});
const base='http://127.0.0.1:4189/prototypes/sushi-loop/?ntl-drawer-state=hidden';
const report={started:new Date().toISOString(),results:[],responsive:[],screenshots:[],errors:[],failedImages:[],httpErrors:[]};
const began=Date.now();
const browser=await chromium.launch();
let context,page;
async function createPage(viewport={width:390,height:844},mobile=false){
 if(context)await context.close();
 context=await browser.newContext({viewport,isMobile:mobile,hasTouch:mobile,reducedMotion:'reduce'});
 page=await context.newPage();
 page.on('pageerror',e=>report.errors.push(e.message));
 page.on('response',response=>{if(response.status()>=400)report.httpErrors.push([response.status(),response.url()]);});
}
async function nested(){return page.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>/auto|scroll/.test(getComputedStyle(e).overflowY)&&e.scrollHeight>e.clientHeight+2&&e.getClientRects().length&&!e.matches('textarea, select')).map(e=>e.id||e.className));}
async function decode(locator){
 const images=await locator.locator('image').evaluateAll(async elements=>Promise.all([...new Set(elements.map(e=>e.getAttribute('href')))].map(src=>new Promise(resolve=>{const image=new Image();image.onload=()=>resolve({src,width:image.naturalWidth,height:image.naturalHeight});image.onerror=()=>resolve({src,width:0,height:0});image.src=src;}))));
 report.failedImages.push(...images.filter(i=>!i.width||!i.height));
 expect(images.every(i=>i.width&&i.height)).toBe(true);
 return images.length;
}
async function open(id){await page.goto(`${base}#object-${id}`);const stage=page.locator('#prototype-stage');await expect(stage).toHaveAttribute('data-story',`object-${id}`);await expect(stage.locator('.object-export-pending')).toHaveCount(0);return stage;}
async function screenshot(locator,name){await locator.screenshot({path:join(output,name)});report.screenshots.push(name);}
const near=(a,b)=>Math.abs(a-b)<.001;
try{
 for(const [index,object]of targets.entries()){
  if(index%10===0)await createPage();
  const stage=await open(object.id),figures=stage.locator('.object-interaction');
  await expect(figures).toHaveCount(object.interactions.length);
  let joins=0,decoded=0;
  for(const [sceneIndex,scene]of object.interactions.entries()){
   const figure=figures.nth(sceneIndex),svg=figure.locator('.object-tile-scene');
   await expect(figure.locator('figcaption')).toHaveText(scene.name);
   const tiles=svg.locator(':scope > g[data-object]');
   await expect(tiles).toHaveCount(scene.placements.length);
   const actual=await tiles.evaluateAll(nodes=>nodes.map(e=>({id:e.dataset.object,direction:e.dataset.direction,frame:e.dataset.frame,source:e.querySelector(':scope > svg[data-sprite-source]')?.dataset.spriteSource,ports:[...e.querySelectorAll(':scope > .object-attachment.is-port')].map(p=>({name:p.dataset.attachment,point:['cx','cy'].map(k=>Number(p.querySelector('circle').getAttribute(k)))})),root:['cx','cy'].map(k=>Number(e.querySelector(':scope > .object-root circle').getAttribute(k)))})));
   expect(actual.map(p=>p.id).sort()).toEqual(scene.placements.map(p=>p.object).sort());
   expect(actual.every(p=>p.source?.startsWith('sprites/'))).toBe(true);
   if(scene.connectionReview?.kind==='directed-belt'||scene.connectionReview?.kind==='profile-join'){
    const expectedRoot=groundRoot({x:2,y:2,direction:'S'},object);
    const reviewed=actual.find(p=>p.id===object.id&&p.root.every((v,i)=>near(v,expectedRoot[i])));
    expect(reviewed,object.id).toBeTruthy();
    for(const port of reviewed.ports){
     expect(actual.some(other=>other!==reviewed&&other.ports.some(p=>p.point.every((v,i)=>near(v,port.point[i]))&&(object.kind!=='belt'||p.name!==port.name))),`${object.id}/${port.name} rendered port coincidence`).toBe(true);joins++;
    }
   }
   decoded+=await decode(figure);
  }
  if(object.kind==='belt'){
   for(const frame of [7,23,24]){
    await stage.getByRole('slider',{name:'Animation frame'}).fill(String(frame));
    const route=figures.locator('g[data-object^="belt-"]');
    expect((await route.evaluateAll(nodes=>nodes.map(e=>Number(e.dataset.frame)))).every(f=>f===frame%24)).toBe(true);
    const moving=object.interactions.find(s=>s.placements.some(p=>p.motion));
    const placement=moving.placements.find(p=>p.motion),timed=placementAtTime(placement,frame/12);
    const expected=groundRoot(timed,byid.get(placement.object));
    const rootCircle=figures.nth(object.interactions.indexOf(moving)).locator(`g[data-object="${placement.object}"] > .object-root circle`);
    const actual=await rootCircle.evaluate(e=>['cx','cy'].map(k=>Number(e.getAttribute(k))));
    expect(actual.every((v,i)=>near(v,expected[i]))).toBe(true);
   }
  }
  expect(await nested(),object.id).toEqual([]);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth),object.id).toBeLessThanOrEqual(391);
  report.results.push({id:object.id,kind:object.interactions[0].connectionReview.kind,scenes:object.interactions.length,renderedJoinedPorts:joins,decodedImages:decoded});
  console.log(`PASS ${index+1}/50 ${object.id}: ${joins} rendered joins`);
 }
 await createPage({width:1440,height:1000});
 for(const id of ['belt-corner-n-e','belt-corner-e-n','wall-inner-corner','wall-outer-corner','reef-corner']){
  const stage=await open(id),figures=stage.locator('.object-interaction');
  if(id.startsWith('belt-'))await stage.getByRole('slider',{name:'Animation frame'}).fill('48');
  await decode(figures);
  await stage.getByLabel('Roots & attachments',{exact:true}).uncheck();
  await screenshot(figures.first(),`${id}-desktop-clean.png`);
  if(id.startsWith('belt-'))await screenshot(figures.nth(1),`${id}-desktop-staged-dish.png`);
  await stage.getByLabel('Roots & attachments',{exact:true}).check();
  await screenshot(figures.first(),`${id}-desktop-ports.png`);
 }
 for(const [viewport,mobile]of [[{width:320,height:740},true],[{width:844,height:390},false]]){
  await createPage(viewport,mobile);
  for(const id of ['belt-corner-n-e','wall-inner-corner','dock-entry']){
   const stage=await open(id),figure=stage.locator('.object-interaction').first();
   await stage.getByLabel('Roots & attachments',{exact:true}).uncheck();
   await decode(figure);
   await figure.scrollIntoViewIfNeeded();
   expect(await nested()).toEqual([]);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(viewport.width+1);
   const before=await page.evaluate(()=>scrollY);
   await figure.hover();await page.mouse.wheel(0,180);
   await expect.poll(()=>page.evaluate(()=>scrollY)).toBeGreaterThan(before+30);
   await screenshot(figure,`${id}-${viewport.width}-clean.png`);
   report.responsive.push({id,width:viewport.width,nestedVerticalScrollers:await nested(),wheelFrom:before,wheelTo:await page.evaluate(()=>scrollY)});
  }
  if(mobile){
   const stage=await open('belt-corner-n-e'),target=stage.locator('.object-interaction').first();
   await target.scrollIntoViewIfNeeded();
   await page.evaluate(()=>{const max=document.scrollingElement.scrollHeight-innerHeight;if(max-scrollY<180)scrollTo(0,Math.max(0,max-180));});
   const b=await target.boundingBox(),x=Math.min(280,Math.max(40,b.x+b.width/2)),y=Math.min(640,Math.max(300,b.y+Math.min(b.height-12,180)));
   const from=await page.evaluate(()=>scrollY),client=await context.newCDPSession(page);
   await client.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
   for(let s=1;s<=6;s++){await client.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y-s*26}]});await new Promise(r=>setTimeout(r,30));}
   await client.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
   await expect.poll(()=>page.evaluate(()=>scrollY)).toBeGreaterThan(from+30);
   report.touch={from,to:await page.evaluate(()=>scrollY),nestedVerticalScrollers:await nested()};
  }
 }
 expect(report.failedImages).toEqual([]);expect(report.errors).toEqual([]);expect(report.httpErrors).toEqual([]);
 report.passed=true;
} catch(error){report.failure=error.stack;throw error;} finally{
 report.durationSeconds=(Date.now()-began)/1000;await writeFile(join(output,'report.json'),JSON.stringify(report,null,2));await browser.close();
 console.log(`REPORT ${join(output,'report.json')}; ${report.durationSeconds}s`);
}
