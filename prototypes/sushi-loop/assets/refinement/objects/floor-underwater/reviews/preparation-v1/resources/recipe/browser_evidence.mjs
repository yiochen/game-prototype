import {createRequire} from 'node:module';
import fs from 'node:fs';import path from 'node:path';import http from 'node:http';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
const require=createRequire(import.meta.url);
const P=path.dirname(fileURLToPath(import.meta.url));const R=path.join(P,'resources');const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const frozenPackage=path.join(R,'node-loaded/playwright/index.js');const {chromium}=require(fs.existsSync(frozenPackage)?frozenPackage:'playwright');
const source=fs.readFileSync(path.join(R,'world-sprite-raster.js'),'utf8');
const extracted=source.slice(source.indexOf('export function worldRasterPlan'),source.indexOf('export function useWorldSpriteRaster'));
fs.writeFileSync(path.join(R,'world-raster-functions.js'),'// Verbatim pure consumer functions from world-sprite-raster.js SHA256 '+sha(Buffer.from(source))+'\n'+extracted);
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png'};
const server=http.createServer((req,res)=>{const name=path.resolve(P,'.'+decodeURIComponent(req.url.split('?')[0]));if(!name.startsWith(P+path.sep)){res.writeHead(403).end();return;}try{res.setHeader('Content-Type',mime[path.extname(name)]||'text/plain');res.end(fs.readFileSync(name));}catch(e){res.writeHead(404).end();}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1000,height:1000},deviceScaleFactor:1});
await page.goto('http://127.0.0.1:'+server.address().port+'/consumer.html');await page.waitForFunction(()=>window.ready);
const out=path.join(P,'consumer');fs.mkdirSync(out,{recursive:true});const cases=[];
const offsets=[[0,0],[.125,.375],[.25,.5],[.5,.25],[.875,.625]];const backgrounds=['#f5f5f0','#808080','#14181e'];
for(const direction of 'NESW')for(let phase=0;phase<12;phase++)for(let k=0;k<offsets.length;k++) {
 const c={direction,phase,offset:offsets[k],pan:[offsets[k][1],offsets[k][0]],background:backgrounds[phase%3],width:320};
 const audit=await page.evaluate(c=>window.renderCase(c),c);cases.push(audit);
 if(k===phase%5)await page.locator('svg').screenshot({path:path.join(out,`phone-${direction}-${String(phase).padStart(2,'0')}.png`)});
}
for(const direction of 'NESW')for(const [label,width] of [['native',870.4],['logical',435.2]])for(let bg=0;bg<3;bg++){
 const c={direction,phase:3,offset:[.25,.5],pan:[.5,.25],background:backgrounds[bg],width};
 cases.push(await page.evaluate(c=>window.renderCase(c),c));
 await page.locator('svg').screenshot({path:path.join(out,`${label}-${direction}-${bg}.png`)});
}
for(const direction of 'NESW')for(let bg=0;bg<3;bg++){
 const c={direction,phase:bg*3,offset:[.25,.5],pan:[.5,.25],background:backgrounds[bg],width:360,context:true};
 cases.push(await page.evaluate(c=>window.renderCase(c),c));await page.locator('svg').screenshot({path:path.join(out,`context-${direction}-${bg}.png`)});
}
const runtime={node:process.version,nodeExecutable:process.execPath,browserVersion:browser.version(),browserExecutable:chromium.executablePath(),browserSHA256:sha(fs.readFileSync(chromium.executablePath())),playwrightVersion:'1.63.0',loadedPackageClosure:[]};
await browser.close();server.close();
for(const [filename,module] of Object.entries(require.cache)) {
 if(!filename.includes('/node_modules/')&&!filename.includes('/resources/node-loaded/'))continue;
 const rel=filename.includes('/resources/node-loaded/')?path.relative(path.join(R,'node-loaded'),filename):filename.split('/node_modules/').slice(1).join('/node_modules/');const dest=path.join(R,'node-loaded',rel);fs.mkdirSync(path.dirname(dest),{recursive:true});if(path.resolve(filename)!==path.resolve(dest))fs.copyFileSync(filename,dest);runtime.loadedPackageClosure.push({path:path.relative(P,dest),sha256:sha(fs.readFileSync(dest))});
}
fs.writeFileSync(path.join(P,'consumer-audit.json'),JSON.stringify({method:'Frozen actual registration helpers and verbatim worldRasterPlan/paintWorldRaster. Nearest common nativecanvas composition after resizing, then ordinary SVG foreignObject final filtering. No fitting, warps, alpha repair, per-tile overlaps, nudges or per-facing recolor.',cases},null,2)+'\n');
fs.writeFileSync(path.join(P,'browser-runtime.json'),JSON.stringify(runtime,null,2)+'\n');
console.log(JSON.stringify({cases:cases.length,coverageFailures:cases.filter(c=>c.interiorAlpha.nonOpaque),browser:runtime.browserVersion,loadedPackageFiles:runtime.loadedPackageClosure.length}));
