import fs from 'node:fs';import path from 'node:path';import http from 'node:http';import crypto from 'node:crypto';import {createRequire} from 'node:module';import {fileURLToPath} from 'node:url';
const P=path.dirname(fileURLToPath(import.meta.url));const require=createRequire(import.meta.url),{chromium}=require(path.join(P,'resources/node-loaded/playwright/index.js'));const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const variants=process.argv.slice(2);if(!variants.length)throw Error('Explicit variant required');
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png'};const server=http.createServer((req,res)=>{const file=path.resolve(P,'.'+decodeURIComponent(req.url.split('?')[0]));if(!file.startsWith(P+path.sep))return res.writeHead(403).end();try{res.setHeader('Content-Type',mime[path.extname(file)]||'text/plain');res.end(fs.readFileSync(file));}catch(e){res.writeHead(404).end();}});await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1000,height:1000},deviceScaleFactor:1});await page.goto(`http://127.0.0.1:${server.address().port}/consumer.html`);await page.waitForFunction(()=>window.ready);
const offsets=[[0,0],[.125,.375],[.25,.5],[.5,.25],[.875,.625]],backgrounds=['#f5f5f0','#808080','#14181e'];
for(const variant of variants){
 const out=path.join(P,variant,'consumer');fs.mkdirSync(out,{recursive:true});const cases=[];
 for(const direction of 'NESW')for(const phase of [0,3])for(const kind of ['native','independent'])for(let size=0;size<2;size++)for(let k=0;k<offsets.length;k++)for(let bg=0;bg<3;bg++){
  const c={variant,direction,phase,kind,width:size?320:435.2,offset:offsets[k],pan:[offsets[k][1],offsets[k][0]],background:backgrounds[bg]};cases.push(await page.evaluate(c=>window.renderCase(c),c));
  if(k===2){const filename=`${size?'phone':'logical'}-${kind}-${direction}-${phase}-bg${bg}.png`;await page.locator('svg').screenshot({path:path.join(out,filename)});}
 }
 fs.writeFileSync(path.join(P,variant,'consumer-report.json'),JSON.stringify({method:'Exact frozen source registration and actual common-nativecanvas nearest functions, ordinary final SVG filtering; no fitting/repair/overlap. Source study only.',cases},null,2)+'\n');console.log(JSON.stringify({variant,cases:cases.length,interiorFailures:cases.filter(c=>c.interior.nonOpaque).length,minInteriorAlpha:Math.min(...cases.map(c=>c.interior.minAlpha))}));
}
fs.writeFileSync(path.join(P,'consumer-runtime.json'),JSON.stringify({node:process.version,nodeExecutable:process.execPath,browserVersion:browser.version(),browserExecutable:chromium.executablePath(),browserSHA256:sha(fs.readFileSync(chromium.executablePath())),frozenPlaywright:'resources/node-loaded/playwright/index.js'},null,2)+'\n');await browser.close();server.close();
