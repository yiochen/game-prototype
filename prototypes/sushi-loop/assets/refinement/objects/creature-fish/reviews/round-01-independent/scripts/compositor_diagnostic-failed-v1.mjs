import{chromium}from'@playwright/test';import{createServer}from'node:http';import{readFile,writeFile,mkdir}from'node:fs/promises';import{resolve,dirname,extname}from'node:path';import{fileURLToPath}from'node:url';
const P=resolve(dirname(fileURLToPath(import.meta.url)),'..'),O=resolve(P,'../../candidates/round-01'),out=resolve(P,'compositor-diagnostic');await mkdir(out,{recursive:true});const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png'};
const server=createServer(async(req,res)=>{try{const u=new URL(req.url,'http://local'),p=resolve(O,'.'+decodeURIComponent(u.pathname));if(!p.startsWith(O+'/'))throw Error('scope');res.writeHead(200,{'Content-Type':mime[extname(p)]||'application/octet-stream'});res.end(await readFile(p));}catch(e){res.writeHead(404);res.end(String(e));}});await new Promise(r=>server.listen(0,'127.0.0.1',r));const url=`http://127.0.0.1:${server.address().port}/consumer-fixture/fixture.html`;const records=[];
for(const[mode,launch]of[['full-chromium',{headless:true,channel:'chromium'}],['headless-shell',{headless:true}]]){
 const b=await chromium.launch(launch),ctx=await b.newContext({viewport:{width:393,height:852},deviceScaleFactor:1});
 for(const clip of ['normal','caught']){
  const page=await ctx.newPage();await page.goto(url);await page.waitForFunction(()=>window.fixtureReady);await page.evaluate(clip=>window.play({clipId:clip,mode:'phone',bg:'light'}),clip);const shots=[];
  for(let i=0;i<14;i++){const path=resolve(out,`${mode}-${clip}-${String(i).padStart(2,'0')}.png`);const before=await page.evaluate(()=>({time:performance.now(),frames:[...document.querySelectorAll('.card')].map(c=>Number(c.dataset.frame))}));await page.screenshot({path});shots.push({path,phaseBeforeScreenshot:before});await page.waitForTimeout(65);}
  const trace=await page.evaluate(()=>window.stop());records.push({mode,launch,version:b.version(),clip,viewport:{width:393,height:852},DPR:1,bg:'light',shots,trace,scope:'Existing exact frozen consumer fixture, bounded normal/caught phone PNG samples to diagnose original compositor recording chroma artifacts. No helper/art/state/layout mutations or new viewport/background Cartesian.'});await page.close();
 }
 await ctx.close();await b.close();
}
await writeFile(resolve(P,'compositor-diagnostic.json'),JSON.stringify(records,null,2));server.close();console.log('COMPOSITOR_DIAGNOSTIC_COMPLETE',records.length);
