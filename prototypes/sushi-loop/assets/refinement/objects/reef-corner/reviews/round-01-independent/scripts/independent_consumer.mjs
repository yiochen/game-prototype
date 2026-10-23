import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),out=path.join(root,'evidence/consumer');await fs.mkdir(out,{recursive:true});
const require=createRequire(import.meta.url),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const url='http://127.0.0.1:5181/prototypes/sushi-loop/assets/refinement/objects/reef-corner/reviews/round-01-independent/resources/consumer/host.html';
const ledger={candidatePacketSHA256:'969ab83edd7a8d615fe7284bb7c979a293a5bfde0a6d0b50abe62ac16068f599',url,node:process.version,nodeExecutable:process.execPath,playwright:require('@playwright/test/package.json').version,viewport:{width:1280,height:1000},deviceScaleFactor:1,helpers:{},modes:[]};
for(const n of ['world-sprite-raster.js','sprite-layout.js'])ledger.helpers[n]=sha(await fs.readFile(path.join(root,'resources/consumer',n)));
for(const [name,launch] of [['full-chromium',{headless:true,channel:'chromium'}],['headless-shell',{headless:true}]]){
 const browser=await chromium.launch(launch),page=await browser.newPage({viewport:ledger.viewport,deviceScaleFactor:1});const errors=[];page.on('pageerror',x=>errors.push(x.message));await page.goto(url);await page.waitForFunction(()=>window.ready);
 const mode={name,launch,version:browser.version(),executablePath:chromium.executablePath(),pageErrors:errors,cases:[]};const rawHashes=new Map();
 for(const direction of ['N','E','S','W'])for(const size of [128,32])for(const [phase,{root,pan}] of [[1,{root:.25,pan:.75}],[3,{root:.75,pan:.25}]])for(const control of ['individual','native'])for(const [bg,background] of ['#f2f0e8','#777b82','#17202b'].entries()){
  const settings={direction,size,phase,root,pan,control,bg,background};const rec=await page.evaluate(s=>window.capture(s),settings);const bytes=Buffer.from(rec.raw.split(',')[1],'base64');delete rec.raw;const rawHash=sha(bytes);let rawFile=rawHashes.get(rawHash);
  if(!rawFile){rawFile=`${name}-${direction}-p${phase}-${control}-raw.png`;await fs.writeFile(path.join(out,rawFile),bytes);rawHashes.set(rawHash,rawFile);}
  const filename=`${name}-${direction}-cell${size}-p${phase}-${control}-bg${bg}.png`;const shot=await page.locator('#stage').screenshot({path:path.join(out,filename),animations:'disabled'});mode.cases.push({...rec,raw:{path:`evidence/consumer/${rawFile}`,sha256:rawHash},screenshot:{path:`evidence/consumer/${filename}`,sha256:sha(shot)}});
 }
 ledger.modes.push(mode);await browser.close();
}
await fs.writeFile(path.join(root,'evidence/independent-consumer-ledger.json'),JSON.stringify(ledger,null,2)+'\n');console.log(JSON.stringify(ledger.modes.map(x=>({name:x.name,version:x.version,cases:x.cases.length,errors:x.pageErrors})),null,2));
