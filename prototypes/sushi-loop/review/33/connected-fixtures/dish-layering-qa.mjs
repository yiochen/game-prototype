import {createRequire} from 'node:module';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {join} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../../../../../',import.meta.url));
const require=createRequire(join(root,'package.json')),{chromium,expect}=require('@playwright/test');
const {placementAtTime,groundRoot}=await import(pathToFileURL(join(root,'prototypes/sushi-loop/wireframe/sprite-layout.js')));
const library=JSON.parse(await readFile(join(root,'prototypes/sushi-loop/assets/production/library.json'),'utf8'));
const objects=library.objects,byid=new Map(objects.map(o=>[o.id,o]));
const output='/private/tmp/sushi-object-review/connected-fixtures/visible-dish';
await mkdir(output,{recursive:true});
const browser=await chromium.launch(),began=Date.now(),report={samples:[],errors:[],httpErrors:[]};
const pairs=[];
try{
 const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
 page.on('pageerror',e=>report.errors.push(e.message));page.on('response',r=>{if(r.status()>=400)report.httpErrors.push([r.status(),r.url()]);});
 for(const object of objects.filter(o=>o.kind==='belt')){
  await page.goto(`http://127.0.0.1:4189/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-${object.id}`);
  const stage=page.locator('#prototype-stage');await expect(stage).toHaveAttribute('data-story',`object-${object.id}`);
  await stage.getByLabel('Roots & attachments',{exact:true}).uncheck();
  const scenes=object.interactions,scene=scenes.find(s=>s.placements.some(p=>p.motion));
  const placement=scene.placements.find(p=>p.motion),figure=stage.locator('.object-interaction').nth(scenes.indexOf(scene));
  expect(placement.renderPass).toBe('foreground');
  const decoded=await figure.locator('image').evaluateAll(async elements=>Promise.all([...new Set(elements.map(e=>e.getAttribute('href')))].map(src=>new Promise(resolve=>{const image=new Image();image.onload=()=>resolve([image.naturalWidth,image.naturalHeight]);image.onerror=()=>resolve([0,0]);image.src=src;}))));
  expect(decoded.every(([w,h])=>w&&h)).toBe(true);
  const total=Math.round(placement.motion.duration*12);
  for(const frame of [0,Math.round(total/4),Math.round(total/2),Math.round(total*3/4),total-1]){
   await stage.getByRole('slider',{name:'Animation frame'}).fill(String(frame));
   const svg=figure.locator('.object-tile-scene'),dish=svg.locator(`:scope > g[data-object="${placement.object}"]`);
   expect(await svg.locator(':scope > g[data-object]').last().getAttribute('data-object')).toBe(placement.object);
   const expected=groundRoot(placementAtTime(placement,frame/12),byid.get(placement.object));
   const actual=await dish.locator(':scope > svg').evaluate(e=>['x','y'].map(k=>Number(e.getAttribute(k))));
   expect(actual.every((v,i)=>Math.abs(v+byid.get(placement.object).root[i]-expected[i])<.001)).toBe(true);
   const visible=join(output,`${object.id}-${frame}-visible.png`),hidden=join(output,`${object.id}-${frame}-hidden.png`);
   await svg.screenshot({path:visible});
   await dish.evaluate(e=>e.style.visibility='hidden');await svg.screenshot({path:hidden});await dish.evaluate(e=>e.style.visibility='');
   pairs.push({id:object.id,frame,visible,hidden});report.samples.push({id:object.id,frame,root:expected});
  }
  console.log(`PASS ${object.id}: registered plate paints above all decks at five route positions`);
 }
 report.pixels=JSON.parse(execFileSync('/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',['-c',String.raw`import json,sys
from PIL import Image,ImageChops
out=[]
for pair in json.load(sys.stdin):
 a=Image.open(pair['visible']).convert('RGBA');b=Image.open(pair['hidden']).convert('RGBA')
 diff=ImageChops.difference(a,b).convert('RGB');mask=diff.point(lambda p:255 if p else 0).convert('L')
 out.append({'id':pair['id'],'frame':pair['frame'],'changedPixels':sum(1 for p in mask.getdata() if p),'bounds':diff.getbbox()})
print(json.dumps(out))`],{input:JSON.stringify(pairs),encoding:'utf8'}));
 expect(report.pixels).toHaveLength(100);
 for(const sample of report.pixels)expect(sample.changedPixels,`${sample.id} frame${sample.frame}: visible plate pixels`).toBeGreaterThan(15);
 expect(report.errors).toEqual([]);expect(report.httpErrors).toEqual([]);report.passed=true;
} catch(error){report.failure=error.stack;throw error;}finally{report.durationSeconds=(Date.now()-began)/1000;await writeFile(join(output,'report.json'),JSON.stringify(report,null,2));await browser.close();console.log(`REPORT ${join(output,'report.json')}; ${report.durationSeconds}s`);}
