import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';
const base=process.env.TEST_URL||'http://127.0.0.1:4177';
const folder=new URL('../../review/19/revision-8/',import.meta.url);
await mkdir(folder,{recursive:true});
const browser=await chromium.launch(),errors=[],measurements=[];
for(const [width,height] of [[320,720],[390,844],[844,390],[1440,1000]]){
 const page=await browser.newPage({viewport:{width,height},hasTouch:true});await page.clock.install();
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);});
 await page.goto(base+'/prototypes/sushi-loop/design/expansion-preview/');
 const choose=s=>page.getByRole('combobox',{name:'Review state'}).selectOption(s);
 const shot=async n=>{await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all([...document.images].map(i=>i.complete?Promise.resolve():new Promise(r=>i.onload=i.onerror=r))));await page.screenshot({path:new URL(`${n}-${width}x${height}.png`,folder).pathname});};
 for(const s of ['covered','partial','edit']){await choose(s);await page.getByRole('button',{name:'Uncover submarine',exact:true}).focus();await page.keyboard.press('Enter');await shot(`submarine-blocked-${s}`);}
 await choose('bare');await shot('edge-to-edge');await choose('restaurant');await shot('restaurant');await choose('clear');await shot('clearance-selected');
 const clear=page.getByRole('button',{name:'Clear for 180 coins',exact:true});await clear.hover();await page.mouse.down();await shot('clearance-pressed');await page.mouse.up();await page.clock.runFor(300);await shot('car-cleared-still-covered');
 await choose('almost');await shot('one-surrounding-trash-left');await page.locator('[data-patch-id="dock-access"] .patch-hit').focus();await page.keyboard.press('Enter');await clear.click();await page.clock.runFor(300);await shot('cleared-dock');
 await choose('poor');await shot('clearance-disabled');measurements.push({width,height,scene:await page.locator('.expansion-scene').boundingBox(),card:await page.getByRole('dialog').boundingBox(),actions:await page.getByRole('dialog').getByRole('button').evaluateAll(a=>a.map(b=>({name:b.getAttribute('aria-label')||b.textContent,width:b.clientWidth,height:b.clientHeight,disabled:b.disabled})))});
 await choose('edit');await shot('edit');await page.locator('[data-patch-id="sofa-west"] .patch-hit').focus();await page.keyboard.press('Enter');await shot('edit-sofa-confirm');await page.getByRole('button',{name:'Clear for 120 coins',exact:true}).click();await page.clock.runFor(300);
 if(height<560){await page.locator('.room-pan').focus();await page.keyboard.press('ArrowDown');await page.keyboard.press('ArrowDown');}
 await page.getByRole('button',{name:'Place wood stool',exact:true}).click();await page.getByRole('button',{name:'Place stool at 7, 4',exact:true}).click();await shot('edit-cleared-placement');
 await choose('gallery');for(const [art,label] of [['garbage-armchair-S','armchair']]){await page.getByRole('combobox',{name:'Whole object'}).selectOption(art);for(const state of ['normal','pressed','disabled','selected']){await page.getByRole('button',{name:state,exact:true}).click();await shot(`gallery-${label}-${state}`);}}
 await choose('variety');await shot('variety-top');await page.locator('.variety-scroll').evaluate(el=>el.scrollTop=el.scrollHeight);await shot('variety-bottom');await choose('edge');await shot('edge-native');if(width<=1050){await page.getByRole('button',{name:'Target',exact:true}).click();await shot('edge-target');}
 await page.close();
}
await browser.close();await writeFile(new URL('capture-results.json',folder),JSON.stringify({base,errors,measurements},null,2)+'\n');if(errors.length)throw new Error(errors.join('\n'));
