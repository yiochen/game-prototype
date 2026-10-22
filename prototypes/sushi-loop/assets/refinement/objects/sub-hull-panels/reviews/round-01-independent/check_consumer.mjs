import {chromium} from './resources/tools/node_modules/playwright/index.mjs';
import fs from 'node:fs';import path from 'node:path';import http from 'node:http';import crypto from 'node:crypto';
const out=path.dirname(new URL(import.meta.url).pathname),ex=path.resolve(out,'../..'),mime={'.html':'text/html','.js':'text/javascript','.png':'image/png','.apng':'image/png','.json':'application/json'};
const loopHTML=`<html><style>body{margin:0;background:#A8ADAE}img{display:block}.row{display:flex} .row img{width:192px;height:352px}.all{width:768px;height:352px}</style><div class="row">${['N','E','S','W'].map(d=>`<img src="/candidates/round-01/previews/active-${d}.apng">`).join('')}</div><img class="all" src="/candidates/round-01/previews/active-all4.apng"></html>`;
const server=http.createServer((req,res)=>{
 const route=decodeURIComponent(req.url.split('?')[0]);if(route==='/review-loop.html'){res.writeHead(200,{'Content-Type':'text/html'});res.end(loopHTML);return;}
 const aliases={'/source/consumer-demo.html':out+'/resources/consumer/consumer-demo.html','/source/consumer-demo.js':out+'/resources/consumer/consumer-demo.js'};const p=aliases[route]||path.resolve(ex,'.'+route);
 if(!(p.startsWith(ex+'/'))||!fs.existsSync(p)||!fs.statSync(p).isFile()){res.writeHead(404);res.end('Missing');return;}
 res.writeHead(200,{'Content-Type':mime[path.extname(p)]||'application/octet-stream'});res.end(fs.readFileSync(p));
});await new Promise(r=>server.listen(0,'127.0.0.1',r));const base=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({headless:true}),record={browser:browser.version(),errors:[],views:[],loopStream:[],scope:'Independent execution of exact copied sealed consumer bundle/descriptors; true native assembled main image plus separate upgrade/eel. Final main approval excluded.'};
try{
 for(const [name,viewport] of [['phone',{width:390,height:844}],['landscape',{width:844,height:390}]]){
  const context=await browser.newContext({viewport,deviceScaleFactor:1}),page=await context.newPage();page.on('pageerror',e=>record.errors.push(e.message));await page.goto(base+'/source/consumer-demo.html');await page.waitForFunction(()=>document.querySelectorAll('svg[data-ready="true"]').length===4);
  for(const bg of ['light','gray','dark']){
   const unique=[new Set(),new Set(),new Set(),new Set()],states=[];
   for(const [clip,frame] of [['idle',0],...Array.from({length:12},(_,i)=>['active',i])]){
    const state={bg,clip,frame};await page.evaluate(s=>window.setReviewState(s),state);await page.waitForFunction(s=>{const m=document.querySelector('main');return m.dataset.bg===s.bg&&m.dataset.clip===s.clip&&+m.dataset.frame===s.frame&&document.querySelectorAll('svg[data-ready="true"]').length===4},state);
    const raw=await page.locator('canvas').evaluateAll(cs=>cs.map(c=>({data:c.toDataURL(),smoothing:c.getContext('2d').imageSmoothingEnabled,size:[c.width,c.height]})));if(clip==='active')raw.forEach((r,i)=>unique[i].add(r.data));if(raw.some(r=>r.smoothing))throw Error('Native common-canvas nearest sampling not restored');
    if(clip==='idle'||frame===3){const filename=`replay-${name}-${bg}-${clip}-${frame+1}.png`;await page.screenshot({path:path.join(out,filename),fullPage:true});states.push({clip,frame,path:filename});}
   }
   record.views.push({name,bg,viewport,states,uniqueCanvasFrames:unique.map(s=>s.size),allNativeCanvasNearest:true,overflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),rasterErrors:await page.locator('svg').evaluateAll(es=>es.map(e=>e.dataset.error))});
  }await context.close();
 }
 const context=await browser.newContext({viewport:{width:768,height:704},deviceScaleFactor:1}),page=await context.newPage();await page.goto(base+'/review-loop.html');await page.waitForFunction(()=>[...document.images].every(i=>i.complete));
 for(let i=0;i<24;i++){await page.waitForTimeout(70);const filename=`loop-playback-${String(i).padStart(2,'0')}.png`;await page.screenshot({path:path.join(out,filename)});record.loopStream.push({path:filename,at:await page.evaluate(()=>performance.now()),sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(out,filename))).digest('hex')});}await context.close();
}finally{await browser.close();server.close();}
record.uniqueLoopScreenshots=new Set(record.loopStream.map(r=>r.sha256)).size;fs.writeFileSync(path.join(out,'consumer-independent-check.json'),JSON.stringify(record,null,2));fs.writeFileSync(path.join(out,'loop-playback.html'),loopHTML);
if(record.errors.length||record.views.some(v=>v.overflow||v.rasterErrors.some(Boolean)||v.uniqueCanvasFrames.some(n=>n<6))||record.uniqueLoopScreenshots<6)throw Error('Independent consumer/loop evidence failed');console.log('CONSUMER_REPLAY_PASS',record.views.length,record.uniqueLoopScreenshots);
