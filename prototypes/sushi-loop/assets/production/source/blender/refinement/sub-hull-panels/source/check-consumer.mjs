import {chromium} from './resources/tools/node_modules/playwright/index.mjs';
import fs from 'node:fs';import http from 'node:http';import path from 'node:path';import crypto from 'node:crypto';
const source=path.dirname(new URL(import.meta.url).pathname),out=path.join(source,'../candidates/round-01/consumer'),experiment=path.resolve(source,'..');fs.mkdirSync(out,{recursive:true});
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png'};
const server=http.createServer((req,res)=>{const p=path.resolve(experiment,'.'+decodeURIComponent(req.url.split('?')[0]));if(!p.startsWith(experiment+'/')||!fs.existsSync(p)||!fs.statSync(p).isFile()){res.writeHead(404);res.end('Missing');return}res.writeHead(200,{'Content-Type':mime[path.extname(p)]||'application/octet-stream'});res.end(fs.readFileSync(p))});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const url=`http://127.0.0.1:${server.address().port}/source/consumer-demo.html`;
const browser=await chromium.launch({headless:true}),record={scope:'Native assembled frozen preliminary upgraded Sub + independent candidate armor sprite + source eel. All4 views; all12 active phases and idle;3 backgrounds;2 viewport sizes. Main final576 and other equipment approvals pending.',browser:browser.version(),executable:chromium.executablePath(),views:[],errors:[]};
try{
 for(const [name,viewport] of [['phone',{width:390,height:844}],['landscape',{width:844,height:390}]] ){
  const context=await browser.newContext({viewport,deviceScaleFactor:1});const page=await context.newPage();page.on('pageerror',e=>record.errors.push(e.message));
  await page.goto(url);await page.waitForFunction(()=>document.querySelectorAll('svg[data-ready="true"]').length===4);
  for(const bg of ['light','gray','dark']){
   const hashes=Array.from({length:4},()=>new Set()),states=[];
   for(const [clip,frame] of [['idle',0],...Array.from({length:12},(_,i)=>['active',i])]){
    await page.evaluate(s=>window.setReviewState(s),{clip,frame,bg});
    await page.waitForFunction(s=>{const m=document.querySelector('main');return m?.dataset.clip===s.clip&&+m.dataset.frame===s.frame&&m.dataset.bg===s.bg&&document.querySelectorAll('svg[data-ready="true"]').length===4},{clip,frame,bg});
    const data=await page.locator('canvas').evaluateAll(cs=>cs.map(c=>c.toDataURL()));if(clip==='active')data.forEach((h,i)=>hashes[i].add(h));
    const filename=`${name}-${bg}-${clip}-${frame+1}.png`;await page.screenshot({path:path.join(out,filename),fullPage:true});
    states.push({clip,frameIndex:frame,path:`candidates/round-01/consumer/${filename}`,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(out,filename))).digest('hex')});
   }
   record.views.push({name,viewport,background:bg,states,uniqueActiveFramesByFacing:hashes.map(s=>s.size),horizontalOverflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),rasterErrors:await page.locator('svg').evaluateAll(es=>es.map(e=>e.dataset.error)),sceneSampling:await page.locator('svg').evaluateAll(es=>es.map(e=>({direction:e.dataset.direction,nativeScale:+e.dataset.nativeScale,logicalToViewportZoom:e.getBoundingClientRect().width/e.viewBox.baseVal.width,wholeCanvasCSSFilter:'ordinary browser default; image-rendering:auto'})))});
  }
  await context.close();
 }
}finally{await browser.close();server.close()}
record.executableSHA256=crypto.createHash('sha256').update(fs.readFileSync(record.executable)).digest('hex');
fs.writeFileSync(path.join(out,'check.json'),JSON.stringify(record,null,2));
if(record.errors.length||record.views.some(v=>v.horizontalOverflow||v.rasterErrors.some(Boolean)||v.uniqueActiveFramesByFacing.some(n=>n<6)))throw Error('Consumer evidence failed');
console.log(JSON.stringify({views:record.views.length,screenshots:record.views.flatMap(v=>v.states).length,uniqueFrames:record.views.map(v=>v.uniqueActiveFramesByFacing),errors:record.errors}));
