import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';
const base=process.env.TEST_URL||'http://127.0.0.1:4181';
const folder=new URL('../../review/19/exhibition-unlocked/',import.meta.url);
const prefix=process.env.CAPTURE_PREFIX||'local';
await mkdir(folder,{recursive:true});
const browser=await chromium.launch(),errors=[],measurements=[];
for(const [width,height] of [[320,720],[390,844],[720,1560],[1080,2340],[844,390],[1440,1000]]){
 const page=await browser.newPage({viewport:{width,height},hasTouch:true});await page.clock.install();
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);});
 await page.goto(base+'/prototypes/sushi-loop/design/expansion-preview/?state=unlock');
 const choose=s=>page.getByRole('combobox',{name:'Review state'}).selectOption(s);
 const shot=async n=>{await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all([...document.images].map(i=>i.decode().catch(()=>{}))));await page.screenshot({path:new URL(`${prefix}-${n}-${width}x${height}.png`,folder).pathname});};
 const dialog=page.getByRole('dialog',{name:'Exhibition Unlocked',exact:true});await dialog.waitFor();await shot('unlocked');
 measurements.push({width,height,scene:await page.locator('.expansion-scene').boundingBox(),card:await dialog.boundingBox(),art:await dialog.locator('.exhibition-art').boundingBox(),buttons:await dialog.getByRole('button').evaluateAll(a=>a.map(e=>({name:e.getAttribute('aria-label')||e.textContent,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))),heading:await dialog.getByRole('heading').evaluate(e=>({font:getComputedStyle(e).fontSize,clipped:e.scrollWidth>e.clientWidth}))});
 const go=dialog.getByRole('button',{name:"Let's go",exact:true});await go.hover();await page.mouse.down();await shot('go-pressed');await page.mouse.move(0,0);await page.mouse.up();
 const close=dialog.getByRole('button',{name:'Close',exact:true});await close.hover();await page.mouse.down();await shot('x-pressed');await page.mouse.move(0,0);await page.mouse.up();await close.click();await page.clock.runFor(40);await shot('dismissed');
 await choose('almost');await page.locator('[data-patch-id="dock-access"] button').focus();await page.keyboard.press('Enter');await page.getByRole('button',{name:'Clear for 180 coins',exact:true}).click();await page.clock.runFor(300);
 await page.getByRole('button',{name:'Inspect cover',exact:true}).focus();await page.keyboard.press('Enter');await shot('anonymous-question');await page.getByRole('button',{name:'Reveal',exact:true}).click();await page.clock.runFor(500);await shot('opening');await page.clock.runFor(800);await shot('after-reveal');await close.click();await page.reload();await page.clock.runFor(40);await shot('reload-no-popup');
 await page.close();
}
await browser.close();await writeFile(new URL(`${prefix}-capture-results.json`,folder),JSON.stringify({base,errors,measurements},null,2)+'\n');if(errors.length)throw new Error(errors.join('\n'));
