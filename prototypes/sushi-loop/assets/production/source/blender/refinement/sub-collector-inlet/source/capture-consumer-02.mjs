import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';import{fileURLToPath}from'node:url';import{chromium}from'@playwright/test';
const source=path.dirname(fileURLToPath(import.meta.url)),out=path.resolve(source,'../candidates/round-02'),baseDir=out;const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png','.webp':'image/webp'};
const server=http.createServer(async(req,res)=>{try{const p=path.resolve(baseDir,'.'+decodeURIComponent(req.url.split('?')[0]));if(!p.startsWith(baseDir+path.sep))throw Error('outside');res.setHeader('Content-Type',mime[path.extname(p)]||'text/plain');res.end(await fs.readFile(p));}catch{res.statusCode=404;res.end('missing');}});await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});let errors=[];page.on('pageerror',e=>errors.push(String(e)));await page.goto(`http://127.0.0.1:${server.address().port}/consumer/index.html`);await page.waitForFunction(()=>window.ready);await fs.mkdir(path.join(out,'consumer/captures'),{recursive:true});let records=[];
async function capture(opt,key){const m=await page.evaluate(async opt=>await window.show(opt),opt);const p=`consumer/captures/${key}.png`;await page.screenshot({path:path.join(out,p),fullPage:false});records.push({...m,viewport:page.viewportSize(),capture:p});}
for(const direction of'NESW'){
 for(let frame=0;frame<12;frame++)await capture({direction,frame,width:390,cell:47.3,bg:'light',pan:[.37,.63],idle:false},`phone-${direction}-${String(frame+1).padStart(2,'0')}`);
 for(let frame=0;frame<12;frame++)await capture({direction,frame,width:390,cell:32,bg:'light',pan:[.37,.63],idle:false},`phone32-${direction}-${String(frame+1).padStart(2,'0')}`);
 await capture({direction,frame:0,cell:47.3,idle:true},`phone-idle-${direction}`);
 await capture({direction,frame:0,cell:32,idle:true},`phone32-idle-${direction}`);
 for(const bg of['light','gray','dark'])for(const cell of[32,47.3])await capture({direction,frame:3,idle:false,cell,bg,pan:[.125,.875]},`phone-${direction}-${bg}-${cell}`);
}
await page.setViewportSize({width:1120,height:720});
for(const direction of'NESW')for(const frame of[0,2,3,6,9,11])await capture({direction,frame,width:1120,cell:128,bg:'gray',pan:[.37,.63],idle:false},`landscape-${direction}-${String(frame+1).padStart(2,'0')}`);
for(const direction of'NESW')await capture({direction,frame:0,idle:true},`landscape-idle-${direction}`);
for(const direction of'NESW')for(const bg of['light','dark'])await capture({direction,frame:3,idle:false,bg,pan:[.125,.875]},`landscape-${direction}-${bg}-128`);
await page.setViewportSize({width:390,height:844});const playback=[];
for(const direction of'NESW')for(const cell of[32,47.3]){
 const samples=await page.evaluate(async({direction,cell})=>{await window.show({direction,width:390,cell,bg:'light',pan:[.37,.63],idle:false});window.togglePlayback();const t=performance.now(),seen=[];while(performance.now()-t<1150){await new Promise(r=>setTimeout(r,20));seen.push({elapsedMs:performance.now()-t,frame:window.lastEvidence.frame});}window.togglePlayback();return seen;},{direction,cell});
 playback.push({direction,cell,width:390,samples,uniqueObservedFrames:[...new Set(samples.map(s=>s.frame))].sort((a,b)=>a-b)});
}
await fs.writeFile(path.join(out,'consumer/receipt.json'),JSON.stringify({browser:browser.version(),helpers:['15-sprite-layout.js','16-world-sprite-raster.js'],semantics:'Exact snapshotted real spriteFrame/clipFor/groundRoot/orderPlacements/sceneBounds and worldRasterPlan/paintWorldRaster execute. Native canvas nearest after resize, then ordinary complete-canvas browser downsample. One actual native assembled Sub; independent equipment/eel beside it. Static upgraded-dock-ready main and provisional other gear labelled. No standalone overlay simulates integration.',captures:records,playback,errors},null,2)+'\n');await browser.close();await new Promise(r=>server.close(r));console.log(JSON.stringify({captures:records.length,errors,nearestAfterResize:records.every(r=>r.nearestAfterResize)}));if(errors.length||records.some(r=>!r.nearestAfterResize))process.exitCode=1;
