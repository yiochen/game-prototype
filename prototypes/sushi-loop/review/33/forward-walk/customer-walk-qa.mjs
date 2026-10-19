import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {join} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../../../../../',import.meta.url));
const require=createRequire(join(root,'package.json')),{chromium,expect}=require('@playwright/test');
const {spriteFrame}=await import(pathToFileURL(join(root,'prototypes/sushi-loop/wireframe/sprite-layout.js')));
const library=JSON.parse(await readFile(join(root,'prototypes/sushi-loop/assets/production/library.json'),'utf8'));
const requested=process.env.REVIEW_CUSTOMER_IDS?.split(',').filter(Boolean);
const objects=library.objects.filter(o=>o.id.startsWith('customer-')&&(!requested||requested.includes(o.id)));
const output=process.env.REVIEW_OUTPUT||'/private/tmp/sushi-object-review/walk-gait/final';await mkdir(output,{recursive:true});
expect(objects).toHaveLength(requested?.length||4);
const baseline=JSON.parse(execFileSync('git',['show','8104b82:prototypes/sushi-loop/assets/production/library.json'],{cwd:root,encoding:'utf8',maxBuffer:16*1024*1024}));
const baselineById=new Map(baseline.objects.map(o=>[o.id,o]));
const oldWalk=JSON.parse(await readFile(new URL('./before-frontend-inspection.json',import.meta.url),'utf8'));
for(const object of library.objects.filter(o=>!o.id.startsWith('customer-'))){
 const prior=baselineById.get(object.id);
 expect({captureFingerprint:object.captureFingerprint,clips:object.clips,interactions:object.interactions},`${object.id}: preserve connected-belt revision`).toEqual({captureFingerprint:prior.captureFingerprint,clips:prior.clips,interactions:prior.interactions});
}
for(const object of objects){
 const prior=baselineById.get(object.id);
 for(const key of ['frameSize','root','sourceScale','footprint','projection'])expect(object[key],`${object.id}: preserve ${key}`).toEqual(prior[key]);
 expect(object.clips.map(c=>[c.id,c.frames,c.fps,c.loop]),`${object.id}: preserve native cadence`).toEqual(prior.clips.map(c=>[c.id,c.frames,c.fps,c.loop]));
 const walk=object.clips.find(c=>c.id==='walk'),old=oldWalk.objects.find(o=>o.id===object.id);
 for(const direction of ['N','E','S','W'])expect(createHash('sha256').update(await readFile(join(root,'prototypes/sushi-loop/assets/production',walk.directions[direction].image))).digest('hex'),`${object.id}/${direction}: newly captured gait`).not.toBe(old.atlasHashes[direction]);
}
const base=process.env.REVIEW_URL||'http://127.0.0.1:4189/prototypes/sushi-loop/?ntl-drawer-state=hidden';
const browser=await chromium.launch(),began=Date.now(),report={unchangedNonCustomerRecords:113,customers:[],errors:[],httpErrors:[]};
try{
 const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
 page.on('pageerror',e=>report.errors.push(e.message));page.on('response',r=>{if(r.status()>=400)report.httpErrors.push([r.status(),r.url()]);});
 for(const object of objects){
  await page.goto(`${base}#object-${object.id}`);
  const stage=page.locator('#prototype-stage');await expect(stage).toHaveAttribute('data-story',`object-${object.id}`);
  await stage.getByLabel('Roots & attachments',{exact:true}).uncheck();
  const summary={id:object.id,clips:[],decodedImages:0};
  for(const clip of object.clips.filter(c=>['walk','panic'].includes(c.id))){
   expect(clip.frames).toBeGreaterThanOrEqual(6);expect(clip.fps).toBe(12);
   expect(clip.frameOrder).toEqual(Array.from({length:clip.frames},(_,i)=>i));
   await stage.getByLabel('Scene state',{exact:true}).selectOption(clip.id);
   const scene=stage.locator('.object-tile-scene').first();
   await expect(stage.locator('.object-animation[open]')).toHaveCount(1);
   await expect(stage.locator('.object-animation:not([open]) svg')).toHaveCount(0);
   for(let frame=0;frame<clip.frames;frame++){
    await stage.getByRole('slider',{name:'Animation frame'}).fill(String(frame));
    for(const direction of ['N','E','S','W']){
     const pose=scene.locator(`:scope > g[data-object="${object.id}"][data-direction="${direction}"]`);
     await expect(pose).toHaveAttribute('data-frame',String(frame));
     const actual=await pose.locator(':scope > svg[data-sprite-source]').evaluate(e=>({source:e.dataset.spriteSource,rect:e.getAttribute('viewBox').split(' ').map(Number),size:['width','height'].map(k=>Number(e.getAttribute(k)))}));
     const expected=spriteFrame(object,clip,direction,frame/12);
     expect(actual).toEqual({source:expected.image,rect:expected.rect,size:expected.frameSize});
    }
   }
   const decoded=await scene.locator('image').evaluateAll(async nodes=>Promise.all([...new Set(nodes.map(e=>e.getAttribute('href')))].map(src=>new Promise(resolve=>{const i=new Image();i.onload=()=>resolve([i.naturalWidth,i.naturalHeight]);i.onerror=()=>resolve([0,0]);i.src=src;}))));
   expect(decoded.every(([w,h])=>w&&h)).toBe(true);summary.decodedImages+=decoded.length;
   for(const direction of ['N','E','S','W']){
    const href=await scene.locator(`:scope > g[data-object="${object.id}"][data-direction="${direction}"] image`).getAttribute('href');
    const fetched=await (await page.request.get(new URL(href,base).href)).body();
    const exported=await readFile(join(root,'prototypes/sushi-loop/assets/production',clip.directions[direction].image));
    expect(createHash('sha256').update(fetched).digest('hex'),`${object.id}/${clip.id}/${direction}: current published atlas bytes`).toBe(createHash('sha256').update(exported).digest('hex'));
   }
   await stage.getByRole('slider',{name:'Animation frame'}).fill(String(Math.floor(clip.frames/4)));
   await stage.locator('.object-review-section').first().screenshot({path:join(output,`${object.id}-${clip.id}-phone-four-directions.png`)});
   summary.clips.push({id:clip.id,frames:clip.frames,directions:4,checkedFrameRectangles:clip.frames*4});
  }
  const walk=object.clips.find(c=>c.id==='walk');await stage.getByLabel('Scene state',{exact:true}).selectOption('walk');
  await stage.getByRole('slider',{name:'Animation frame'}).fill('0');
  await page.evaluate(()=>{const node=document.querySelector('.object-tile-scene > g[data-object]');window.__walkFrames=[Number(node.dataset.frame)];window.__walkObserver=new MutationObserver(()=>{const value=Number(node.dataset.frame);if(value!==window.__walkFrames.at(-1))window.__walkFrames.push(value);});window.__walkObserver.observe(node,{attributes:true,attributeFilter:['data-frame']});});
  await stage.getByRole('button',{name:'Play animations',exact:true}).click();
  await page.waitForTimeout(Math.ceil(walk.frames/12*1000)+150);
  await stage.getByRole('button',{name:'Pause animations',exact:true}).click();
  const frames=await page.evaluate(()=>{window.__walkObserver.disconnect();return window.__walkFrames;});
  expect(frames.length).toBeGreaterThan(walk.frames/2);
  for(let i=1;i<frames.length;i++){const step=(frames[i]-frames[i-1]+walk.frames)%walk.frames;expect(step).toBeGreaterThan(0);expect(step).toBeLessThan(walk.frames/2);}
  summary.playbackFrames=frames;
  summary.nestedVerticalScrollers=await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>/auto|scroll/.test(getComputedStyle(e).overflowY)&&e.scrollHeight>e.clientHeight+2&&e.getClientRects().length&&!e.matches('textarea, select')).map(e=>e.id||e.className));
  expect(summary.nestedVerticalScrollers).toEqual([]);expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(391);
  report.customers.push(summary);console.log(`PASS ${object.id}: walk/panic atlas order,4facings and live forward frame clock`);
 }
 expect(report.errors).toEqual([]);expect(report.httpErrors).toEqual([]);report.passed=true;
}catch(error){report.failure=error.stack;throw error;}finally{report.durationSeconds=(Date.now()-began)/1000;await writeFile(join(output,'report.json'),JSON.stringify(report,null,2));await browser.close();console.log(`REPORT ${join(output,'report.json')}; ${report.durationSeconds}s`);}
