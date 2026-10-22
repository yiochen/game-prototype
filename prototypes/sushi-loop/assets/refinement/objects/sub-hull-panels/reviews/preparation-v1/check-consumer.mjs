import { chromium } from './resources/tools/node_modules/playwright/index.mjs';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import crypto from 'node:crypto';
const out=path.dirname(new URL(import.meta.url).pathname),mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png'};
const server=http.createServer((req,res)=>{
 const route=decodeURIComponent(req.url.split('?')[0]),p=path.resolve(out,'.'+route);
 if(!p.startsWith(out)||!fs.existsSync(p)||!fs.statSync(p).isFile()){res.writeHead(404);res.end('Not found');return;}
 res.writeHead(200,{'Content-Type':mime[path.extname(p)]||'application/octet-stream'});res.end(fs.readFileSync(p));
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const url=`http://127.0.0.1:${server.address().port}/consumer-demo.html`,browser=await chromium.launch({headless:true}),record={scope:'Bounded original-source separate-sprite replay, no canonical component or main approval',browserVersion:browser.version(),executable:chromium.executablePath(),views:[],consoleErrors:[]};
try{
 for(const [name,viewport] of [['phone',{width:390,height:844}],['landscape',{width:844,height:390}]]){
  const context=await browser.newContext({viewport,deviceScaleFactor:1});const page=await context.newPage();page.on('pageerror',e=>record.consoleErrors.push(e.message));
  await page.goto(url);await page.waitForFunction(()=>document.querySelectorAll('svg[data-ready="true"]').length===4);
  const unique=Array.from({length:4},()=>new Set());
  for(let frame=0;frame<12;frame++){
   await page.evaluate(f=>window.setReviewFrame(f),frame);await page.waitForFunction(f=>[...document.querySelectorAll('section strong')].every(e=>e.textContent.endsWith(`frame ${f+1}/12`))&&document.querySelectorAll('svg[data-ready="true"]').length===4,frame);
   const hashes=await page.locator('canvas').evaluateAll(canvases=>canvases.map(c=>c.toDataURL()));hashes.forEach((h,i)=>unique[i].add(h));
   if([0,6].includes(frame))await page.screenshot({path:path.join(out,`consumer-${name}-frame-${frame+1}.png`),fullPage:true});
  }
  record.views.push({name,viewport,uniquePaintedFramesByFacing:unique.map(s=>s.size),readyScenes:await page.locator('svg[data-ready="true"]').count(),rasterErrors:await page.locator('svg[data-error]').evaluateAll(es=>es.map(e=>e.getAttribute('data-error'))),pageOverflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)});await context.close();
 }
}finally{await browser.close();server.close();}
record.executableSHA256=crypto.createHash('sha256').update(fs.readFileSync(record.executable)).digest('hex');fs.writeFileSync(path.join(out,'consumer-check.json'),JSON.stringify(record,null,2));
if(record.consoleErrors.length||record.views.some(v=>v.readyScenes!==4||v.pageOverflow||v.rasterErrors.some(Boolean)||v.uniquePaintedFramesByFacing.some(n=>n<6)))throw Error('Consumer evidence failed');
console.log(JSON.stringify(record,null,2));
