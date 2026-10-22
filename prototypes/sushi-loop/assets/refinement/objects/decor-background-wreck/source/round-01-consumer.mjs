// Exact frozen current helper fixture; substitutes only candidate own atlases.
import {chromium} from '@playwright/test';
import {readFileSync,writeFileSync,existsSync,mkdirSync} from 'node:fs';
import {createServer} from 'node:http';
import {fileURLToPath} from 'node:url';
import {dirname,resolve,extname} from 'node:path';
import {createHash} from 'node:crypto';
const P=dirname(fileURLToPath(import.meta.url)),B=resolve(P,'..'),R=resolve(P,'round-01-resources/consumer'),O=resolve(B,'candidates/round-01');
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const server=createServer((req,res)=>{
 if(req.url==='/favicon.ico'){res.statusCode=204;res.end();return;}
 const rel=decodeURIComponent(req.url.split('?')[0]).replace(/^\/resources\/consumer\//,''),path=resolve(R,rel);
 if(!path.startsWith(R)||!existsSync(path)){res.statusCode=404;res.end();return;}
 res.setHeader('Content-Type',({'.js':'application/javascript','.html':'text/html','.json':'application/json','.png':'image/png'})[extname(path)]||'text/plain');res.end(readFileSync(path));
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const url='http://127.0.0.1:'+server.address().port+'/resources/consumer/study.html';
const cases=[];for(const cell of [128,32,47.3])for(const background of ['#eef2ed','#808080','#102433'])cases.push({kind:'facings',cell,background,phase:cell===47.3?[.37,.61]:[0,0],pan:cell===47.3?[.23,.47]:[0,0],seconds:0});
cases.push({kind:'repeat',cell:32,phase:[.37,.61],pan:[.23,.47],background:'#102433',seconds:0});
for(const seconds of [0,.5,1,2])cases.push({kind:'context',cell:32,phase:[.37,.61],pan:[.23,.47],background:'#102433',seconds});
cases.push({kind:'context',cell:128,phase:[0,0],pan:[0,0],background:'#102433',seconds:0});
const runs=[];
for(const [mode,launch] of [['full-chromium',{headless:true,channel:'chromium'}],['headless-shell',{headless:true}]]){
 const browser=await chromium.launch(launch),context=await browser.newContext({viewport:{width:1400,height:1000},deviceScaleFactor:1}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push({type:'pageerror',message:String(e)}));page.on('requestfailed',r=>errors.push({type:'requestfailed',url:r.url(),failure:r.failure()}));page.on('console',m=>{if(m.type()==='error')errors.push({type:'console',message:m.text()});});
 await page.goto(url);await page.waitForFunction(()=>typeof window.drawSourceStudy==='function');
 const dest=resolve(O,'consumer',mode);mkdirSync(dest,{recursive:true});const results=[];
 for(let i=0;i<cases.length;i++){
  const result=await page.evaluate(c=>window.drawSourceStudy(c),cases[i]);const path=resolve(dest,String(i).padStart(2,'0')+'-'+cases[i].kind+'.png');await page.locator('svg').first().screenshot({path});
  results.push({...result,caseIndex:i,viewport:{width:1400,height:1000},screenshot:path.slice(B.length+1),screenshotSHA256:sha(path),captureMethod:'actual SVG locator screenshot at prescribed CSS scale'});
 }
 const viewportContexts=[];
 for(const [width,height,cell] of [[320,720,32],[1280,720,128]]){
  await page.setViewportSize({width,height});const config={kind:'context',cell,phase:[.37,.61],pan:[.23,.47],background:'#102433',seconds:0};const result=await page.evaluate(c=>window.drawSourceStudy(c),config);
  const path=resolve(dest,`viewport-${width}x${height}.png`);await page.screenshot({path,fullPage:false});
  viewportContexts.push({...result,viewport:{width,height},screenshot:path.slice(B.length+1),screenshotSHA256:sha(path),captureMethod:'true final viewport page screenshot, DPR1; no crop or image fitting'});
 }
 runs.push({mode,launch,browserVersion:browser.version(),userAgent:await page.evaluate(()=>navigator.userAgent),viewport:{width:1400,height:1000},dpr:1,errors,cases:results,viewportContexts});await browser.close();
}
writeFileSync(resolve(O,'consumer-ledger.json'),JSON.stringify({asset:'decor-background-wreck',round:'round-01',node:{executable:process.execPath,version:process.version},method:'Exact frozen SpriteScene helper fixture native nearest AFTER resize then ordinary wholecanvas CSS filtering. No crop, warp, perview recolor, alpha/RGB repair. Floor/actors frozen original companion atlas bytes. This is a bounded fixture, not full React UI/Godot/device evidence.',helperSHA256:{spriteLayout:sha(resolve(R,'sprite-layout.js')),worldSpriteRaster:sha(resolve(R,'world-sprite-raster.js')),actualLoadedBundle:sha(resolve(R,'study-bundle.js')),entrySource:sha(resolve(R,'consumer-entry.js')),fixture:sha(resolve(R,'fixture.json'))},runs},null,2)+'\n');
await new Promise(r=>server.close(r));console.log(JSON.stringify({casesPerMode:cases.length,runs:runs.map(r=>({mode:r.mode,version:r.browserVersion,errors:r.errors,finalViewportCount:r.viewportContexts.length,smoothing:r.cases.every(c=>c.smoothingAfterResize===false)}))}));
