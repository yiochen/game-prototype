import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import crypto from 'node:crypto';
const require=createRequire(import.meta.url),base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),root=path.resolve(base,'../..');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const mime={'.html':'text/html','.js':'application/javascript','.json':'application/json','.png':'image/png'};
const server=http.createServer(async(req,res)=>{try{const p=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://local').pathname));if(!(p===root||p.startsWith(root+path.sep)))throw Error('outside root');const data=await fs.readFile(p);res.writeHead(200,{'Content-Type':mime[path.extname(p)]||'application/octet-stream'});res.end(data)}catch(e){res.writeHead(404);res.end('not found')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const url='http://127.0.0.1:'+server.address().port+'/reviews/round-01-independent/resources/browser/harness.html';
const ids=['background-light','background-gray','background-dark','phase-css','phase-root','phase-pan','control-port-W','control-port-E','control-extended'],results=[];
try{
 for(const [mode,options] of [['fullChrome',{channel:'chromium'}],['shell',{}]]){
  const browser=await chromium.launch({headless:true,...options}),context=await browser.newContext({viewport:{width:1840,height:1200},deviceScaleFactor:1}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(String(e)));await page.goto(url);await page.waitForFunction(()=>window.ready===true,{timeout:45000});
  const evidence=await page.evaluate(()=>window.evidence),shots=[];
  for(const id of ids){const p=path.join(base,'captures',mode+'-'+id+'.png');await page.locator('#'+id).screenshot({path:p});const own=await fs.readFile(p),original=await fs.readFile(path.join(root,'candidates/round-01','consumer-'+mode+'-'+id+'.png'));shots.push({id,path:path.relative(base,p),sha256:sha(own),candidateSHA256:sha(original),exactPngBytes:own.equals(original)})}
  if(mode==='fullChrome')for(const rec of await page.evaluate(()=>window.nativeCanvasPNGs))await fs.writeFile(path.join(base,'captures',`consumer-${rec.kind}-${rec.d}.png`),Buffer.from(rec.png.split(',')[1],'base64'));
  results.push({mode,options,version:browser.version(),url,errors,evidence,screenshots:shots});await browser.close();console.log(mode+' complete; errors='+errors.length+'; exact screenshots='+shots.filter(s=>s.exactPngBytes).length+'/'+shots.length);
 }
 const modules=[];
 for(const [filename,m]of Object.entries(require.cache)){
  if(!filename.includes('/node_modules/playwright'))continue;
  const p=path.resolve(filename),rel=p.slice(p.indexOf('/node_modules/')+14),dest=path.join(base,'resources/node-loaded',rel),bytes=await fs.readFile(p);
  await fs.mkdir(path.dirname(dest),{recursive:true});await fs.writeFile(dest,bytes);modules.push({source:p,path:path.relative(base,dest),sha256:sha(bytes)});
 }
 for(const pkg of ['playwright','playwright-core']){
  const p=require.resolve(pkg+'/package.json'),dest=path.join(base,'resources/node-loaded',pkg,'package.json'),bytes=await fs.readFile(p);await fs.mkdir(path.dirname(dest),{recursive:true});await fs.writeFile(dest,bytes);modules.push({source:p,path:path.relative(base,dest),sha256:sha(bytes)});
 }
 await fs.writeFile(path.join(base,'browser-independent.json'),JSON.stringify({node:process.version,launches:results,actualLoadedModules:modules,method:'Independent replay of copied browser-only review harness with actual current frozen consumer modules unchanged; candidate/approved-middle exact atlases read only. All evidence output remains inside own reviews.'},null,2)+'\n');
}finally{await new Promise(r=>server.close(r))}
