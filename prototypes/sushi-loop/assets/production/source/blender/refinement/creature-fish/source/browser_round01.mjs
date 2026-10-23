import{build}from'esbuild';import{chromium}from'@playwright/test';import{createServer}from'node:http';import{readFile,writeFile,mkdir,copyFile,stat}from'node:fs/promises';import{resolve,dirname,extname}from'node:path';import{fileURLToPath}from'node:url';import{createHash}from'node:crypto';
const P=dirname(fileURLToPath(import.meta.url)),O=resolve(P,'../candidates/round-01'),F=resolve(O,'consumer-fixture');await mkdir(F,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex');
for(const n of['world-sprite-raster.js','sprite-layout.js'])await copyFile(resolve(P,'round-01-resources/consumer',n),resolve(F,n));await copyFile(resolve(P,'fixture_round01.js'),resolve(F,'fixture.js'));
await writeFile(resolve(F,'fixture.html'),'<!doctype html><meta charset="utf-8"><title>Fish native body consumer evidence</title><style>body{margin:0;font:12px system-ui;background:#bfc4c8}h1{font-size:13px;margin:6px;height:16px}#stage{display:grid;gap:0;width:max-content}.card{position:relative;overflow:hidden}.label{position:absolute;top:3px;left:5px;color:#fff;background:#1119;padding:1px 4px;z-index:2}svg{display:block;overflow:hidden}canvas{display:block;width:100%;height:100%}</style><h1 id="heading">Loading current consumer</h1><div id="stage"></div><script type="module" src="fixture.bundle.js"></script>');
const bundle=await build({entryPoints:[resolve(F,'fixture.js')],bundle:true,format:'esm',outfile:resolve(F,'fixture.bundle.js'),metafile:true,absWorkingDir:resolve(P,'../../../../../../../..')});await writeFile(resolve(O,'consumer-bundle-metafile.json'),JSON.stringify(bundle.metafile,null,2));
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png'};
const server=createServer(async(req,res)=>{try{const u=new URL(req.url,'http://local'),p=resolve(O,'.'+decodeURIComponent(u.pathname));if(!p.startsWith(O+'/'))throw Error('scope');const b=await readFile(p);res.writeHead(200,{'Content-Type':mime[extname(p)]||'application/octet-stream'});res.end(b);}catch(e){res.writeHead(404);res.end(String(e));}});await new Promise(r=>server.listen(0,'127.0.0.1',r));const url=`http://127.0.0.1:${server.address().port}/consumer-fixture/fixture.html`;
const C=JSON.parse(await readFile(resolve(O,'consumer-catalog.json'),'utf8')),G=JSON.parse(await readFile(resolve(O,'geometry-ledger.json'),'utf8'));const modes=[],errors=[];
function extremes(ci){return Object.fromEntries(['N','E','S','W'].map(d=>[d,ci==='normal'?0:G.views.filter(r=>r.clip===ci&&r.direction===d).reduce((a,b)=>a.maxArmatureRelativeVertexDisplacementFromFrame1>b.maxArmatureRelativeVertexDisplacementFromFrame1?a:b).index]));}
for(const[mode,launch]of[['full-chromium',{headless:true,channel:'chromium'}],['headless-shell',{headless:true}]]){
 const browser=await chromium.launch(launch),folder=resolve(O,'consumer',mode);await mkdir(folder,{recursive:true});const run={mode,launch,browserVersion:browser.version(),executable:mode==='full-chromium'?'Playwright chromium channel chromium (full headless Chromium)':'Playwright default bundled chromium headless shell',defaultExecutablePath:chromium.executablePath(),DPR:1,checks:[],playback:[],errors:[]};
 const context=await browser.newContext({viewport:{width:2300,height:1150},deviceScaleFactor:1}),page=await context.newPage();page.on('pageerror',e=>run.errors.push(e.message));await page.goto(url);await page.waitForFunction(()=>window.fixtureReady);
 for(const[i,c]of C.clips.entries()){
  const bg=['light','gray','dark'][i%3],record=await page.evaluate(a=>window.show(a),{clipId:c.id,mode:'sheet',bg,zoom:.4});const p=resolve(folder,`allframes-${c.id}-${bg}.png`);await page.locator('#stage').screenshot({path:p});run.checks.push({path:p,sha256:sha(await readFile(p)),allFrames:[...Array(12).keys()],directions:['N','E','S','W'],record});
 }
 for(const ci of ['normal','hook','caught','escape'])for(const bg of ['light','gray','dark']){
  const record=await page.evaluate(a=>window.show(a),{clipId:ci,mode:'logical',bg,zoom:1,framesByFacing:extremes(ci),sockets:bg==='gray'});const p=resolve(folder,`logical-${ci}-${bg}.png`);await page.locator('#stage').screenshot({path:p});run.checks.push({path:p,sha256:sha(await readFile(p)),record,socketOverlay:bg==='gray'});
 }
 await page.setViewportSize({width:393,height:852});
 for(const ci of ['normal','hook','caught','escape'])for(const bg of ['light','gray','dark']){
  const record=await page.evaluate(a=>window.show(a),{clipId:ci,mode:'phone',bg,zoom:.4,framesByFacing:extremes(ci),sockets:bg==='gray'});const p=resolve(folder,`phone-contact-${ci}-${bg}.png`);await page.screenshot({path:p});run.checks.push({path:p,sha256:sha(await readFile(p)),record,viewport:{width:393,height:852},DPR:1,socketOverlay:bg==='gray'});
 }
 await context.close();
 // Each state/viewport gets its own short full compositor recording, avoiding ambiguous slices.
 for(const view of ['phone','logical'])for(const[i,c]of C.clips.entries()){
  const bg=['light','gray','dark'][i%3],viewport=view==='phone'?{width:393,height:852}:{width:1840,height:640};
  const ct=await browser.newContext({viewport,deviceScaleFactor:1,recordVideo:{dir:resolve(folder,'videos'),size:viewport}}),pg=await ct.newPage();pg.on('pageerror',e=>run.errors.push(e.message));await pg.goto(url);await pg.waitForFunction(()=>window.fixtureReady);const started=await pg.evaluate(a=>window.play(a),{clipId:c.id,mode:view,bg});await pg.waitForTimeout(2300);const stopped=await pg.evaluate(()=>window.stop());const p=resolve(folder,`${view}-terminal-${c.id}-${bg}.png`);await pg.screenshot({path:p});const video=pg.video();await ct.close();const vp=await video.path();const stable=resolve(folder,'videos',`${view}-${c.id}-${bg}.webm`);await copyFile(vp,stable);
  const indices=[...new Set(stopped.trace.flatMap(t=>t.frames))].sort((a,b)=>a-b),changes=stopped.trace.filter((t,j,a)=>!j||JSON.stringify(t.frames)!==JSON.stringify(a[j-1].frames));
  const last=stopped.trace.at(-1),cadence=stopped.trace.slice(1).map((t,j)=>t.elapsed-stopped.trace[j].elapsed);
  const check={clip:c.id,viewport:view,viewportPixels:viewport,DPR:1,bg,started,seconds:2.3,trace:stopped.trace,phaseChanges:changes,visitedIndices:indices,terminal:last?.frames,expectedTerminal:c.loop?'cycle':'frame11-hold',rafIntervalRange:[Math.min(...cadence),Math.max(...cadence)],screenshot:{path:p,sha256:sha(await readFile(p))},video:{path:stable,originalPath:vp,sha256:sha(await readFile(stable)),encoding:'Actual Playwright compositor webm; preserved original, no frame-substitution or APNG.'}};
  if(indices.length!==12)throw Error(`Missing runtime phase ${mode} ${view} ${c.id}: ${indices}`);
  if(!c.loop&&!last.frames.every(f=>f===11))throw Error('One shot not held');run.playback.push(check);console.log('FISH_BROWSER',mode,view,c.id,'RAF',stopped.trace.length,'phases',indices.length);
 }
 await browser.close();modes.push(run);await writeFile(resolve(O,'browser-evidence.json'),JSON.stringify({scope:'Exact current catalog raster/layout consumer fixture, no full gameplay/Godot/device claim.',helperSHA256:await Promise.all(['world-sprite-raster.js','sprite-layout.js'].map(async n=>({path:resolve(F,n),sha256:sha(await readFile(resolve(F,n)))}))),modes},null,2));
}
server.close();console.log('FISH_BROWSER_COMPLETE');
