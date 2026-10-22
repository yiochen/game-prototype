import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const base=path.dirname(fileURLToPath(import.meta.url)),obj=path.dirname(base),out=path.join(obj,'candidates/round-01/consumer');
const origin=process.env.REEF_CONSUMER_ORIGIN||'http://127.0.0.1:5181';
const url=origin+'/prototypes/sushi-loop/assets/refinement/objects/reef-corner/source/consumer.html';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const phases=[{root:0,pan:0},{root:.25,pan:.75},{root:.5,pan:0},{root:.75,pan:.25}];
const backgrounds=['#f2f0e8','#777b82','#17202b'];
const modes=[['full-chromium',{headless:true,channel:'chromium'}],['headless-shell',{headless:true}]];
const require=createRequire(import.meta.url);
const ledger={node:process.version,playwright:require('@playwright/test/package.json').version,url,viewport:{width:1280,height:1000},deviceScaleFactor:1,helpers:{},modes:[]};
for(const name of ['world-sprite-raster.js','sprite-layout.js'])ledger.helpers[name]=sha(await fs.readFile(path.join(base,'resources',name)));
for(const [name,launch] of modes){
  const dir=path.join(out,name);await fs.mkdir(dir,{recursive:true});
  const browser=await chromium.launch(launch),page=await browser.newPage({viewport:ledger.viewport,deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(url);await page.waitForFunction(()=>window.ready);
  const mode={name,launch,version:browser.version(),captures:[],pageErrors:errors};
  const raws=new Map();
  for(const direction of ['N','E','S','W'])for(const size of [128,32])for(let phase=0;phase<phases.length;phase++)for(let bg=0;bg<backgrounds.length;bg++){
    const settings={direction,size,phase,background:backgrounds[bg],...phases[phase]};const rec=await page.evaluate(s=>window.capture(s),settings);
    const bytes=Buffer.from(rec.raw.split(',')[1],'base64');delete rec.raw;const hash=sha(bytes);let rawPath=raws.get(hash);
    if(!rawPath){rawPath=`raw-${direction}-phase${phase}.png`;await fs.writeFile(path.join(dir,rawPath),bytes);raws.set(hash,rawPath);}
    const screenshot=`${direction}-cell${size}-phase${phase}-bg${bg}.png`;const shot=await page.locator('#stage').screenshot({path:path.join(dir,screenshot),animations:'disabled'});
    mode.captures.push({...settings,...rec,raw:{path:`consumer/${name}/${rawPath}`,sha256:hash},screenshot:{path:`consumer/${name}/${screenshot}`,sha256:sha(shot)}});
  }
  ledger.modes.push(mode);await browser.close();
}
await fs.writeFile(path.join(out,'capture-ledger.json'),JSON.stringify(ledger,null,2)+'\n');
console.log(JSON.stringify({modes:ledger.modes.map(m=>({name:m.name,version:m.version,captures:m.captures.length,errors:m.pageErrors}))}));
