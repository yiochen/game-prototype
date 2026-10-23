import fs from 'node:fs/promises';import http from 'node:http';import path from 'node:path';import {createHash} from 'node:crypto';import {createRequire} from 'node:module';import {fileURLToPath} from 'node:url';
const req=createRequire(import.meta.url),{chromium}=req('@playwright/test');
const P=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),out=path.join(P,'candidates/round-02/consumer');await fs.mkdir(out,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex'),hashfile=async p=>sha(await fs.readFile(p));
const cases=JSON.parse(await fs.readFile(path.join(P,'inputs/root-preparation-reconciliation-v1.json'),'utf8')).consumerCases;
const server=http.createServer(async(request,response)=>{try{let p=request.url.split('?')[0];if(p==='/')p='/source/consumer-round02.html';if(p==='/react-stub.js'){response.setHeader('content-type','text/javascript');response.end('export const useLayoutEffect=()=>{throw new Error("unused React hook")};export const useRef=useLayoutEffect;export const useState=useLayoutEffect;');return;}const file=path.resolve(P,'.'+decodeURIComponent(p));if(!file.startsWith(P+'/'))throw Error('path');const bytes=await fs.readFile(file);response.setHeader('content-type',file.endsWith('.js')?'text/javascript':file.endsWith('.json')?'application/json':file.endsWith('.png')?'image/png':'text/html');response.end(bytes);}catch(e){response.statusCode=404;response.end(String(e));}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const port=server.address().port,runs=[];
for(const config of [{id:'full-chromium',options:{headless:true,channel:'chromium'}},{id:'headless-shell',options:{headless:true}}]){
 const browser=await chromium.launch(config.options),browserVersion=await browser.version();
 for(const c of cases){const viewport={width:c.viewport[0],height:c.viewport[1]},context=await browser.newContext({viewport,deviceScaleFactor:c.DPR}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(`http://127.0.0.1:${port}/?case=${encodeURIComponent(JSON.stringify(c))}`);await page.waitForFunction(()=>window.roundStudy?.ready===true);const data=await page.evaluate(()=>window.roundStudy),stem=`${config.id}-${c.id}`;await page.screenshot({path:path.join(out,stem+'.png'),fullPage:true});
  const unique=new Map();for(const r of data.records){const bytes=Buffer.from(r.data.split(',')[1],'base64'),hash=sha(bytes);if(!unique.has(hash)){const name=`${stem}-${r.kind}-${r.direction}.png`;await fs.writeFile(path.join(out,name),bytes);unique.set(hash,name);}r.nativeCanvasFile=unique.get(hash);r.nativeCanvasSHA256=hash;delete r.data;}
  runs.push({id:config.id,launchOptions:config.options,browserVersion,viewport,DPR:c.DPR,case:c,screenshot:`candidates/round-02/consumer/${stem}.png`,errors,records:data.records,scope:data.scope});await context.close();
 }
 await browser.close();
}
await new Promise(resolve=>server.close(resolve));
// Freeze actual loaded JavaScript files only, never the browser or application trees.
const loaded=[];for(const p of Object.keys(req.cache)){if(p.includes('/node_modules/')&&!p.endsWith('.node')){const b=await fs.readFile(p),rel=p.split('/node_modules/').slice(1).join('/node_modules/'),dest=path.join(P,'source/round-01-resources/node-loaded',rel);if(await hashfile(dest)!==sha(b))throw Error('Frozen runtime changed: '+dest);loaded.push({path:path.relative(P,dest),sha256:sha(b),originalPath:p});}}
const executablePaths=[process.execPath,chromium.executablePath()];
// Full Chromium actually selected by channel; record both Playwright registry binaries.
const registry=req(path.join(path.dirname(req.resolve('playwright-core/package.json')),'lib/coreBundle.js'));
const executableRecords=[];for(const e of registry.registry.registry.executables()){if(['chromium','chromium-headless-shell'].includes(e.name)){const p=e.executablePath();if(p&&!executablePaths.includes(p))executablePaths.push(p)}}
for(const p of executablePaths){const s=await fs.stat(p);executableRecords.push({path:p,bytes:s.size,sha256:await hashfile(p),policy:'external runtime executable hashed, not copied'});}
const helpers=await Promise.all(['source/consumer-round02.html','source/capture-consumer-round02.mjs','source/round-01-resources/sprite-layout.js','source/round-01-resources/world-sprite-raster.js','inputs/catalog-object.json',...['N','E','S','W'].map(d=>`candidates/round-02/atlases/static-${d}.png`)].map(async p=>({path:p,sha256:await hashfile(path.join(P,p))})));
await fs.writeFile(path.join(out,'record.json'),JSON.stringify({runs,helperHashes:helpers,actualLoadedNodeDependencyClosure:loaded,executables:executableRecords,playwrightVersion:req('@playwright/test/package.json').version},null,2)+'\n');console.log(JSON.stringify({runs:runs.length,loadedFiles:loaded.length,errors:runs.flatMap(r=>r.errors)}));
