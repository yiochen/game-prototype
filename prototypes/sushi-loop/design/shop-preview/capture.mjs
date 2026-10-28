import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';
const base=process.env.TEST_URL||'http://127.0.0.1:4177';
const url=base+'/prototypes/sushi-loop/design/shop-preview/?state=shop';
const folder=new URL('../../review/18/maple-popup/',import.meta.url);
await mkdir(folder,{recursive:true});
const browser=await chromium.launch(),errors=[];
for(const [w,h] of [[320,720],[390,844],[844,390],[1440,1000]]){
 const page=await browser.newPage({viewport:{width:w,height:h}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.evaluate(()=>document.fonts.ready);
 const shot=async n=>{await page.waitForTimeout(200);await page.evaluate(()=>Promise.all([...document.images].map(i=>i.complete?Promise.resolve():new Promise(r=>{i.onload=i.onerror=r;}))));await page.screenshot({path:new URL(`${n}-${w}x${h}.png`,folder).pathname});};
 await shot('shop');await page.getByRole('button',{name:'Buy Wood stool for 80 coins',exact:true}).click();await page.waitForTimeout(180);await page.screenshot({path:new URL(`purchase-flight-${w}x${h}.png`,folder).pathname});await page.locator('.purchase-flight').waitFor({state:'detached'});await shot('purchase-arrived');
 await page.getByRole('button',{name:'Close Shop',exact:true}).click();await page.getByRole('button',{name:'Wood stool, 1 available',exact:true}).click();
 // Portrait targets remain square; use a reachable top cell in short landscape.
 const cell=h<500?0:36;await page.getByRole('button',{name:`Place Wood stool in cell ${cell}`,exact:true}).click();await page.getByRole('button',{name:'Select placed Wood stool',exact:true}).click();await shot('placed-selected');
 await page.getByRole('combobox',{name:'Review state'}).selectOption('poor');await shot('disabled');
 await page.getByRole('combobox',{name:'Review state'}).selectOption('sold');await page.locator('.supply-scroll').evaluate(el=>el.scrollTop=el.scrollHeight);await shot('sold-out');
 await page.getByRole('combobox',{name:'Review state'}).selectOption('gallery');await page.getByRole('button',{name:'pressed',exact:true}).click();await shot('gallery-pressed');
 await page.getByRole('combobox',{name:'Review state'}).selectOption('live');await shot('live-no-shop');await page.getByRole('combobox',{name:'Review state'}).selectOption('restaurant');await shot('edit-tray-entry');
 await page.close();
}
await browser.close();await writeFile(new URL('capture-errors.json',folder),JSON.stringify({base,errors},null,2)+'\n');if(errors.length)process.exitCode=1;
