import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../candidates/round-01');
const url=process.argv[2]||'http://127.0.0.1:8873/source/consumer-round-01.html';
for(const [name,options]of [['fullChrome',{channel:'chromium'}],['shell',{}]]){
 const browser=await chromium.launch({headless:true,...options});
 const context=await browser.newContext({viewport:{width:1840,height:1200},deviceScaleFactor:1});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));await page.goto(url);await page.waitForFunction(()=>window.ready===true,{timeout:45000});
 const evidence=await page.evaluate(()=>window.evidence);await fs.writeFile(path.join(base,`consumer-${name}-results.json`),JSON.stringify({browser:browser.version(),launch:options,url,errors,...evidence},null,2)+'\n');
 for(const id of (process.argv[3]?[process.argv[3]]:['background-light','background-gray','background-dark','phase-css','phase-root','phase-pan','control-port-W','control-port-E','control-extended']))await page.locator('#'+id).screenshot({path:path.join(base,`consumer-${name}-${id}.png`)});
 if(name==='fullChrome'){
  for(const r of await page.evaluate(()=>window.nativeCanvasPNGs))await fs.writeFile(path.join(base,`consumer-nativecanvas-${r.kind}-${r.d}.png`),Buffer.from(r.png.split(',')[1],'base64'));
 }
 await browser.close();console.log(name+' captured; errors='+errors.length);
}
