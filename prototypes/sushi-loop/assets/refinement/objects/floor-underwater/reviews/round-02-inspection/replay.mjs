import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const P=path.dirname(fileURLToPath(import.meta.url)),O=path.resolve(P,'../..');
const require=createRequire(import.meta.url),{chromium}=require(path.join(P,'resources/node-loaded/playwright/index.js'));
const hash=b=>createHash('sha256').update(b).digest('hex');
const sources={current:readFileSync(path.join(P,'resources/world-raster-functions.js')),old:readFileSync(path.join(P,'resources/world-raster-functions-old.js'))};
const requests=new Map();let mode='current';
const server=http.createServer((req,res)=>{
 const name=decodeURIComponent(req.url.split('?')[0]);
 let file=name==='/source/consumer-resources/world-raster-functions.js'?path.join(P,`resources/world-raster-functions${mode==='old'?'-old':''}.js`):path.resolve(O,'.'+name);
 if(!file.startsWith(O+path.sep)){res.writeHead(403).end();return;}
 try{const b=readFileSync(file);requests.set(file,{path:path.relative(O,file),sha256:hash(b),bytes:b.length,relativeTo:'object',pathBase:O});res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png'})[path.extname(file)]||'text/plain');res.end(b);}catch{res.writeHead(404).end();}
});
const write=(file,data)=>writeFileSync(file,JSON.stringify(data,null,2)+'\n');
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const summaries=[];
try{
 for(const backend of ['full-chrome','headless-shell']){
  const output=path.join(P,backend);mkdirSync(output,{recursive:true});
  const launch={headless:true,...(backend==='full-chrome'?{executablePath:chromium.executablePath()}:{} )};
  const browser=await chromium.launch(launch);const errors=[];
  try{
   mode='current';const page=await browser.newPage({viewport:{width:1200,height:1200},deviceScaleFactor:1});
   page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);});
   await page.goto(`http://127.0.0.1:${server.address().port}/source/consumer.html`);await page.waitForFunction(()=>window.ready);
   const cases=[],offsets=[[0,0],[.125,.375],[.25,.5],[.5,.25],[.875,.625]],backgrounds=['#f5f5f0','#808080','#14181e'];
   for(const kind of ['native','independent']) for(const direction of 'NESW'){
    for(let phase=0;phase<12;phase++)for(const offset of offsets)for(const background of backgrounds){
     const input={kind,direction,phase,offset,pan:[offset[1],offset[0]],background,width:320};
     cases.push(await page.evaluate(input=>window.renderCase(input),input));
    }
    console.log(JSON.stringify({backend,completedKind:kind,direction,cases:cases.length}));
   }
   for(const kind of ['native','independent'])for(const direction of 'NESW')for(let bg=0;bg<3;bg++)cases.push(await page.evaluate(input=>window.renderCase(input),{kind,direction,phase:bg*3,offset:[.25,.5],pan:[.5,.25],background:backgrounds[bg],width:435.2}));
   for(const direction of 'NESW')for(let bg=0;bg<3;bg++){
    cases.push(await page.evaluate(input=>window.renderCase(input),{kind:'independent',direction,phase:bg*3,offset:[.25,.5],pan:[.5,.25],background:backgrounds[bg],width:360,context:true}));
    if(bg===0)await page.locator('svg').screenshot({path:path.join(output,`context-${direction}-0.png`)});
   }
   const playback=[];
   for(const direction of 'NESW')for(const kind of ['native','independent'])playback.push(await page.evaluate(({direction,kind})=>window.playLoop(direction,kind,2.05),{direction,kind}));
   const regressions=[];
   const controlInputs=[{label:'first',kind:'independent',direction:'N',phase:0,offset:[.125,.375],pan:[.375,.125],background:backgrounds[0],width:320},{label:'worst',kind:'independent',direction:'N',phase:5,offset:[.25,.5],pan:[.5,.25],background:backgrounds[0],width:320}];
   for(const input of controlInputs){const result=await page.evaluate(input=>window.renderCase(input),input);await page.locator('svg').screenshot({path:path.join(output,`current-${input.label}.png`)});regressions.push({renderer:'current',label:input.label,result});}
   // Actual old production helper is a positive failure control, never a readiness backend.
   await page.close();mode='old';const oldPage=await browser.newPage({viewport:{width:1200,height:1200},deviceScaleFactor:1});
   oldPage.on('pageerror',e=>errors.push(e.message));await oldPage.goto(`http://127.0.0.1:${server.address().port}/source/consumer.html`);await oldPage.waitForFunction(()=>window.ready);
   for(const input of controlInputs){const result=await oldPage.evaluate(input=>window.renderCase(input),input);await oldPage.locator('svg').screenshot({path:path.join(output,`old-${input.label}.png`)});regressions.push({renderer:'old',label:input.label,result});}
   const report={backend,browserVersion:browser.version(),executable:backend==='full-chrome'?chromium.executablePath():'Playwright default headless-shell',currentProductionRendererSHA256:hash(readFileSync(path.join(P,'resources/world-sprite-raster.js'))),productionFunctionsSHA256:hash(sources.current),oldProductionRendererSHA256:hash(readFileSync(path.join(P,'resources/world-sprite-raster-old.js'))),oldFunctionsSHA256:hash(sources.old),fixtureManifestSHA256:hash(readFileSync(path.join(O,'source/handoff-manifest-round01.json'))),cases,playback,regressions,errors};
   write(path.join(output,'report.json'),report);
   const summary={backend,cases:cases.length,minAlpha:Math.min(...cases.map(c=>c.interiorAlpha.minAlpha)),alphaFailures:cases.filter(c=>c.interiorAlpha.nonOpaque).length,smoothingFailures:cases.filter(c=>c.smoothingAfterResize!==false).length,playbackRuns:playback.length,playbackPhases:playback.map(p=>[...new Set(p.transitions.map(t=>t.phase))]),control:regressions.map(r=>({renderer:r.renderer,label:r.label,alpha:r.result.interiorAlpha})),errors};
   summaries.push(summary);console.log(JSON.stringify(summary));
   assert.equal(cases.length,1476);assert.equal(summary.alphaFailures,0);assert.equal(summary.smoothingFailures,0);assert.deepEqual(errors,[]);assert.ok(playback.every(p=>new Set(p.transitions.map(t=>t.phase)).size===12 && p.transitions.filter(t=>t.phase===0).length>=2));
   if(backend==='full-chrome')assert.equal(regressions.find(r=>r.renderer==='old'&&r.label==='worst').result.interiorAlpha.minAlpha,128);
  }finally{await browser.close();}
 }
 write(path.join(P,'replay-summary.json'),{reports:summaries});
}finally{write(path.join(P,'served-resources.json'),{relativeTo:'object',pathBase:O,resources:[...requests.values()]});await new Promise(r=>server.close(r));}
