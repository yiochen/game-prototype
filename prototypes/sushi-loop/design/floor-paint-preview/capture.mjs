import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
const base=process.env.TEST_URL||'http://127.0.0.1:4177';
const folder=new URL('../../review/20/floor-prototype/',import.meta.url);
await mkdir(folder,{recursive:true});
const browser=await chromium.launch(),errors=[],results=[];
for(const [width,height] of [[320,720],[390,844],[844,390],[1440,1000]]){
 const context=await browser.newContext({viewport:{width,height},hasTouch:true});
 const page=await context.newPage();
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);});
 await page.goto(base+'/prototypes/sushi-loop/design/floor-paint-preview/');
 const choose=s=>page.getByRole('combobox',{name:'Review state'}).selectOption(s);
 const shot=async n=>{await page.waitForTimeout(180);await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all([...document.images].map(i=>i.complete?Promise.resolve():new Promise(r=>i.onload=i.onerror=r))));await page.screenshot({path:new URL(`${n}-${width}x${height}.png`,folder).pathname});};
 const stored=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('sushi-loop-floor-ui-review-v1')));
 const cellPoint=async(x,y,fx=.5,fy=.5)=>{const b=await page.locator(`[data-cell="${x},${y}"]`).boundingBox();return {x:b.x+b.width*fx,y:b.y+b.height*fy};};
 await choose('palette');assert.equal(await page.locator('.paint-instruction').textContent(),'select a tile pattern');await shot('01-palette');
 // A wheel scroll reaches the last thumbnail without arming a brush or moving the world.
 const camera=(await stored()).camera;await page.getByRole('region',{name:'floor inventory'}).hover();await page.mouse.wheel(0,500);await page.waitForTimeout(100);
 assert.ok(await page.locator('.inventory').evaluate(el=>el.scrollLeft)>0);
 assert.deepEqual((await stored()).camera,camera);assert.equal(await page.locator('.pattern-choice[aria-pressed=true]').count(),0);
 await page.getByRole('button',{name:'Original Cream',exact:true}).focus();await shot('02-palette-scrolled');
 await choose('painting');assert.equal(await page.locator('.paint-instruction').textContent(),'paint the floor');await page.waitForTimeout(180);
 assert.equal(await page.locator('.furniture-sprite').first().evaluate(el=>getComputedStyle(el).opacity),'0.28');await shot('03-brush-selected');
 // Touching floor hides the instruction; release restores it. Fast sparse strokes fill crossed cells.
 let p=await cellPoint(3,4);await page.mouse.move(p.x,p.y);await page.mouse.down();assert.equal(await page.locator('.paint-instruction').evaluate(el=>getComputedStyle(el).visibility),'hidden');await shot('04-touch-down');
 let q=await cellPoint(5,4);await page.mouse.move(q.x,q.y);await page.mouse.up();assert.equal((await stored()).paint['4,4'],'jade');assert.equal((await stored()).paint['5,4'],'jade');
 assert.equal(await page.locator('.paint-instruction').evaluate(el=>getComputedStyle(el).visibility),'visible');
 // Furniture doesn't intercept brush strokes. Use a visible belt row at every size.
 if(height<560){await page.getByRole('button',{name:'Pan scene down',exact:true}).focus();await page.keyboard.press('Enter');}
 p=await cellPoint(3,6);await page.mouse.click(p.x,p.y);assert.equal((await stored()).paint['3,6'],'jade');await shot('05-painted-under-belt');
 // Scene controls pan with brush retained, without adding floor paint.
 const before=await stored();await page.getByRole('button',{name:'Pan scene right',exact:true}).focus();await page.keyboard.press('Enter');let after=await stored();assert.ok(after.camera.x<before.camera.x);assert.deepEqual(after.paint,before.paint);assert.equal(await page.getByRole('button',{name:'Jade Check',exact:true}).getAttribute('aria-pressed'),'true');
 // Pan sufficiently far to see the trash footprint; a stroke paints the open cell and skips the sofa.
 for(let i=0;i<3;i++){await page.getByRole('button',{name:'Pan scene right',exact:true}).focus();await page.keyboard.press('Enter');}
 if(height<560){await page.getByRole('button',{name:'Pan scene up',exact:true}).focus();await page.keyboard.press('Enter');}
 p=await cellPoint(6,4);q=await cellPoint(7,4);await page.mouse.move(p.x,p.y);await page.mouse.down();await page.mouse.move(q.x,q.y);await page.mouse.up();after=await stored();assert.equal(after.paint['6,4'],'jade');assert.equal(after.paint['7,4'],undefined);await shot('06-trash-blocked');
 if(height<560){await page.getByRole('button',{name:'Pan scene down',exact:true}).focus();await page.keyboard.press('Enter');}p=await cellPoint(8,7,.2,.2);await page.mouse.click(p.x,p.y);assert.equal((await stored()).paint['8,7'],'jade');const painted=(await stored()).paint;await page.getByRole('tab',{name:'Floor',exact:true}).click();assert.equal(await page.getByRole('button',{name:'Jade Check',exact:true}).isVisible(),false);assert.equal(await page.locator('.paint-instruction').textContent(),'paint the floor');await shot('07-palette-collapsed');await page.getByRole('tab',{name:'Floor',exact:true}).click();
 await page.getByRole('button',{name:'Exit floor brush',exact:true}).click();await page.waitForTimeout(180);assert.equal(await page.locator('.furniture-sprite').first().evaluate(el=>getComputedStyle(el).opacity),'1');assert.equal(await page.locator('.paint-instruction').textContent(),'select a tile pattern');await shot('08-brush-exit');
 await page.reload();assert.deepEqual((await stored()).paint,painted);
 // Shop stays open after a single debit, retains Owned, restores strip and camera on close.
 await choose('palette');await page.getByRole('region',{name:'floor inventory'}).hover();await page.mouse.wheel(0,120);await page.waitForTimeout(100);const scroll=await page.locator('.inventory').evaluate(el=>el.scrollLeft),shopCamera=(await stored()).camera;
 await page.getByRole('button',{name:'Shop',exact:true}).click();await shot('09-shop-offer');await page.getByRole('button',{name:'Buy Blue Wave for 600 coins',exact:true}).click();assert.equal((await stored()).coins,640);assert.equal((await stored()).owned[0],'blue-wave');assert.equal(await page.getByRole('dialog').count(),1);await shot('10-shop-owned');
 await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'hidden'});await page.waitForFunction(()=>document.activeElement?.classList.contains('shop-action'));assert.deepEqual((await stored()).camera,shopCamera);assert.equal(await page.locator('.inventory').evaluate(el=>el.scrollLeft),scroll);assert.equal(await page.getByRole('button',{name:'Shop',exact:true}).evaluate(el=>document.activeElement===el),true);
 await page.getByRole('button',{name:'Blue Wave',exact:true}).focus();await page.keyboard.press('Enter');assert.equal(await page.getByRole('button',{name:'Blue Wave',exact:true}).getAttribute('aria-pressed'),'true');await shot('11-new-pattern');
 await choose('poor');assert.equal(await page.getByRole('button',{name:'Buy Blue Wave for 600 coins',exact:true}).isDisabled(),true);await shot('12-shop-disabled');
 await choose('gallery');for(const s of ['normal','pressed','selected','disabled']){await page.getByRole('button',{name:s,exact:true}).click();await shot(`13-gallery-${s}`);}
 // Touch drag of thumbnails must browse only. Use the real mobile event sequence.
 await choose('painting');const stripBox=await page.locator('.inventory').boundingBox(),cdp=await context.newCDPSession(page),x=stripBox.x+stripBox.width*.8,y=stripBox.y+stripBox.height*.5;
 const touch=(type,px)=>cdp.send('Input.dispatchTouchEvent',{type,touchPoints:type==='touchEnd'?[]:[{x:px,y}]});
 let touchBefore;
 for(const state of ['palette','painting']){
  await choose(state);touchBefore=await stored();await touch('touchStart',x);
  assert.equal(await page.locator('.paint-instruction').evaluate(el=>getComputedStyle(el).visibility),'visible');
  await touch('touchMove',x-20);await touch('touchMove',x-130);
  assert.equal(await page.locator('.paint-instruction').evaluate(el=>getComputedStyle(el).visibility),'visible');
  assert.equal(await page.locator('.paint-instruction').textContent(),state==='palette'?'select a tile pattern':'paint the floor');
  await shot(`14-palette-scroll-instruction-${state}`);
  await touch('touchEnd',x-130);await page.waitForTimeout(100);
  assert.deepEqual((await stored()).paint,touchBefore.paint);assert.deepEqual((await stored()).camera,touchBefore.camera);
 }
 assert.ok(await page.locator('.inventory').evaluate(el=>el.scrollLeft)>0);assert.equal(await page.getByRole('button',{name:'Jade Check',exact:true}).getAttribute('aria-pressed'),'true');assert.deepEqual((await stored()).paint,touchBefore.paint);assert.deepEqual((await stored()).camera,touchBefore.camera);
 await page.getByRole('button',{name:'Original Cream',exact:true}).focus();await page.keyboard.press('Enter');assert.equal(await page.getByRole('button',{name:'Original Cream',exact:true}).getAttribute('aria-pressed'),'true');
 // Real touch painting uses the same gesture owner.
 await choose('painting');p=await cellPoint(3,4);q=await cellPoint(5,4);
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[p]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[q]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 assert.equal((await stored()).paint['4,4'],'jade');
 const holdBefore=await stored(),caret=await page.getByRole('button',{name:'Pan scene right',exact:true}).boundingBox();
 await page.mouse.move(caret.x+22,caret.y+26);await page.mouse.down();await page.waitForTimeout(180);await page.mouse.up();
 assert.ok((await stored()).camera.x<holdBefore.camera.x);assert.deepEqual((await stored()).paint,holdBefore.paint);
 assert.equal(await page.locator('.paint-instruction').evaluate(el=>getComputedStyle(el).visibility),'visible');
 const targets=await page.locator('.tab,.shop-action,.pattern-choice,.scene-caret,.brush-exit button').evaluateAll(a=>a.filter(e=>e.getClientRects().length).map(e=>({name:e.getAttribute('aria-label')||e.textContent,w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height})));
 assert.ok(targets.every(t=>t.w>=44&&t.h>=44));
 results.push({width,height,scene:await page.locator('.paint-scene').boundingBox(),targets,checks:'palette wheel/touch/focus, brush, sparse stroke, under furniture, camera, trash exclusion, collapse, exit, reload, Shop purchase/Owned/disabled/focus'});
 await context.close();
}
await browser.close();await writeFile(new URL('results.json',folder),JSON.stringify({base,errors,results},null,2)+'\n');assert.deepEqual(errors,[]);console.log('Floor UI review: four viewports passed; captures and results saved.');
