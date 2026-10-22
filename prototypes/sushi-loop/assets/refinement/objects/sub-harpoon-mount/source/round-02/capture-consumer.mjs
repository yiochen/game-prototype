import {chromium} from '@playwright/test';
import path from 'node:path';import fs from 'node:fs/promises';
const p=path.dirname(new URL(import.meta.url).pathname),out=path.join(p,'../../candidates/round-02/consumer');await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true}),errors=[],cases=[];
for(const viewport of [{width:390,height:844},{width:1120,height:720}]){
 const page=await browser.newPage({viewport,deviceScaleFactor:1});page.on('pageerror',e=>errors.push(String(e)));
 for(const bg of ['light','gray','dark'])for(const d of ['N','E','S','W'])for(const f of (viewport.width===390?Array.from({length:13},(_,i)=>i):[0,1,6,12])){
  const fraction=f%2===0?.37:.63;await page.goto(`http://127.0.0.1:4192/source/round-02/consumer.html?d=${d}&f=${f}&bg=${bg}&fraction=${fraction}`);await page.waitForFunction(()=>document.body.dataset.ready==='true');await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  const data=await page.evaluate(()=>window.consumerEvidence);data.path=`candidates/round-02/consumer/${viewport.width}-${bg}-${d}-${f.toString().padStart(2,'0')}.png`;await page.screenshot({path:path.join(p,'../..',data.path)});cases.push(data);
 }
 await page.close();
}
await fs.writeFile(path.join(out,'evidence.json'),JSON.stringify({method:'Actual Chromium native-canvas consumer on390x844 phone and1120x720 landscape. Phone all52 required phases across3 backgrounds and all3 pitches; landscape all4 views neutral/frame1/6/12 across3 backgrounds. Fractional roots/pan alternate .37/.63. Main sprite is native assembled neutral upgraded capture, no separate launcher overlay.',browser:browser.version(),errors,cases},null,2)+'\n');await browser.close();
console.log('CONSUMER_COMPLETE',cases.length,errors.length);
