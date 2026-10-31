import {chromium} from 'playwright';
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
const exp=path.resolve('prototypes/sushi-loop/design/expansion-preview/experiments/cabinet'),out=path.join(exp,'candidates/round-01'),base='http://127.0.0.1:4176';
const hash=s=>createHash('sha256').update(s).digest('hex');
const registration=JSON.parse(await readFile('prototypes/sushi-loop/design/expansion-preview/world-registration.json','utf8'));
const bbox=JSON.parse(await readFile(path.join(out,'alpha-bounds.json'),'utf8'));
for(const f of ['N','E','S','W'])registration[`garbage-cabinet-${f}`]={frame_size:[448,672],root:[224,448],crop_xywh:[0,0,896,1344],visible_bounds:bbox[f],footprint:['E','W'].includes(f)?[1,2]:[2,1],facing:f};
const browser=await chromium.launch();const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});const errors=[],responses=[];
page.on('pageerror',e=>errors.push(e.message));
await page.route('**/world-registration.json*',r=>r.fulfill({contentType:'text/javascript',body:`export default ${JSON.stringify(registration)};`}));
await page.route('**/expansion-preview/app.jsx*',async r=>{
 const response=await r.fetch();let body=await response.text();
 body=body.replace('const art = (n) => images[`./assets/${n}.png`];','const art = (n) => n.startsWith("garbage-cabinet-") ? "/candidate-cabinet/"+n.slice(-1)+".png" : images[`./assets/${n}.png`];');
 body=body.replace(/y: p\.h - 0\.35/g,'y: p.h / 2');
 await writeFile(path.join(out,'consumer-app-executed.js'),body.replace(/\/\/# sourceMappingURL=.*/g,''));responses.push({resource:'in-memory app module',sha256:hash(body)});await r.fulfill({response,body});
});
// Defer unfinished armchair family in this cabinet-only evidence context. Actual packing algorithm remains intact.
await page.route('**/expansion-preview/balance.js*',async r=>{
 const response=await r.fetch();let body=await response.text();body=body.replace(/\{ id: "garbage-armchair"[^\n]*\n/,'').replace(/add\(make\("armchair-west"[^\n]*\n/,'');
 await writeFile(path.join(out,'consumer-balance-executed.js'),body.replace(/\/\/# sourceMappingURL=.*/g,''));responses.push({resource:'in-memory balance without deferred armchair',sha256:hash(body)});await r.fulfill({response,body});
});
await page.route('**/candidate-cabinet/*.png',async r=>{const f=r.request().url().split('/').at(-1);await r.fulfill({contentType:'image/png',body:await readFile(path.join(out,f))});});
await page.addInitScript(()=>{localStorage.clear();localStorage.setItem('sushi-loop-issue19-expansion-review-v2',JSON.stringify({version:2,mode:'live',coins:640,cleared:[],objects:[],camera:{x:-7,y:0},elapsed:0,category:'layout'}));});
await page.goto(base+'/prototypes/sushi-loop/design/expansion-preview/?state=restaurant');
await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all([...document.images].map(i=>i.complete?Promise.resolve():new Promise(r=>i.onload=i.onerror=r))));
await page.screenshot({path:path.join(out,'phone-consumer.png')});
const measurements=await page.locator('.garbage-patch').evaluateAll(a=>a.map(el=>({name:el.querySelector('button')?.getAttribute('aria-label'),patch:el.getBoundingClientRect().toJSON(),image:el.querySelector('img')?.getBoundingClientRect().toJSON(),src:el.querySelector('img')?.src})).filter(o=>o.src?.includes('candidate-cabinet')));
await writeFile(path.join(out,'consumer-report.json'),JSON.stringify({method:'Actual running expansion page through isolated Playwright response substitution; candidate cabinet images and measured registration; geometric footprint-center placement; current deterministic dense packing with unfinished armchair family omitted in-memory. No runtime/production files mutated.',base,viewport:[390,844],cellPitch:390/7,sourceRoot:[224,448],sourceFrame:[448,672],nativeFrame:[896,1344],errors,responses,measurements,limits:'Static cabinet visual/readability check. Full state interaction and deferred armchair integration belong to coordinator.'},null,2)+'\n');
await browser.close();if(errors.length)throw new Error(errors.join('\n'));console.log(JSON.stringify({errors,cabinets:measurements.length}));
