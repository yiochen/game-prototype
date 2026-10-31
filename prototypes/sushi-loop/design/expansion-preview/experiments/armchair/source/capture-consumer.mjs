import {chromium} from 'playwright';
import {writeFile,readFile} from 'node:fs/promises';
const round=process.argv[2];if(!round)throw Error('round required');
const folder=new URL('../candidates/'+round+'/',import.meta.url);const errors=[];
const browser=await chromium.launch();const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
await page.goto(new URL('consumer.html',folder).href);await page.evaluate(()=>window.evidenceReady);await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:new URL('phone-consumer.png',folder).pathname});
const measurements=await page.locator('.sprite').evaluateAll(els=>els.map(el=>({src:el.getAttribute('src'),left:el.style.left,top:el.style.top,width:el.getBoundingClientRect().width,complete:el.complete,naturalWidth:el.naturalWidth,naturalHeight:el.naturalHeight,className:el.className})));
await browser.close();await writeFile(new URL('consumer-check.json',folder),JSON.stringify({viewport:[390,844],deviceScaleFactor:1,errors,measurements,allLoaded:measurements.every(m=>m.complete&&m.naturalWidth>0)},null,2)+'\n');if(errors.length)throw Error(errors.join('\n'));
