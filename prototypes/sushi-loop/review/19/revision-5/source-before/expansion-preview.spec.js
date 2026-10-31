import {test,expect} from '@playwright/test';
const path='/prototypes/sushi-loop/design/expansion-preview/';
const key='sushi-loop-issue19-expansion-review-v2';
test.use({hasTouch:true});
const saved=p=>p.evaluate(k=>JSON.parse(localStorage.getItem(k)),key);
const state=(p,s)=>p.getByRole('combobox',{name:'Review state'}).selectOption(s);
async function paintedPoint(page,id){const image=page.locator(`[data-patch-id="${id}"] img`);await expect.poll(()=>image.evaluate(i=>i.complete&&i.naturalWidth>0),{timeout:15000}).toBe(true);return image.evaluate(img=>{const c=document.createElement('canvas');c.width=img.naturalWidth;c.height=img.naturalHeight;const ctx=c.getContext('2d');ctx.drawImage(img,0,0);const a=ctx.getImageData(0,0,c.width,c.height),b=img.getBoundingClientRect(),scene=img.closest('main').getBoundingClientRect();const points=[];for(let y=0;y<c.height;y+=4)for(let x=0;x<c.width;x+=4){const sx=b.x+x/c.width*b.width,sy=b.y+y/c.height*b.height;if(a.data[(y*c.width+x)*4+3]>240&&sx>scene.x+10&&sx<scene.x+scene.width-10&&sy>scene.y+90&&sy<scene.y+scene.height-20)points.push({x:sx,y:sy,score:Math.hypot(x-c.width/2,y-c.height*.56)});}points.sort((a,b)=>a.score-b.score);if(!points.length)throw new Error('No visible painted point');return points[0];});}
test.beforeEach(async({page})=>{await page.setViewportSize({width:390,height:844});await page.clock.install();await page.goto(path);await page.getByRole('button',{name:'Reset',exact:true}).click();});
test('inspect matches preview, centers, shields outside taps and Cancel preserves camera',async({page})=>{
 const opener=page.locator('[data-patch-id="dock-access"] .patch-hit');await opener.focus();await opener.press('Enter');const before=await saved(page);
 await expect(page.getByRole('dialog')).toBeVisible();await expect(page.getByRole('img',{name:'Wrecked car',exact:true})).toBeVisible();await expect(page.locator('.garbage-patch.selected')).toHaveCount(1);
 await page.mouse.click(20,150);await expect(page.getByRole('dialog')).toBeVisible();await expect(page.getByRole('dialog').getByRole('button')).toHaveCount(2);
 await page.getByRole('button',{name:'Cancel',exact:true}).click();await expect(opener).toBeFocused();expect((await saved(page)).camera).toEqual(before.camera);expect((await saved(page)).cleared).toEqual([]);expect((await saved(page)).coins).toBe(before.coins);
});
test('browser Back and Escape close without clearing or moving the camera',async({page})=>{
 const opener=page.locator('[data-patch-id="dock-access"] .patch-hit');await opener.focus();await opener.press('Enter');const before=await saved(page);await page.goBack();await expect(page.getByRole('dialog')).toHaveCount(0);await expect(opener).toBeFocused();expect((await saved(page)).camera).toEqual(before.camera);
 await opener.focus();await opener.press('Enter');await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);expect((await saved(page)).cleared).toEqual([]);
});
test('confirm commits once before visual removal and opens both shared dock targets',async({page})=>{
 await state(page,'clear');await page.getByRole('button',{name:'Clear for 180 coins',exact:true}).dblclick();await expect(page.getByRole('dialog')).toHaveCount(0);
 const m=await saved(page);expect(m.coins).toBe(460);expect(m.cleared).toEqual(['dock-access']);await page.clock.runFor(300);
 await expect(page.locator('[data-patch-id="dock-access"] .patch-hit')).toHaveCount(0);await expect(page.getByRole('button',{name:'Open Submarine',exact:true})).toBeEnabled();await expect(page.getByRole('button',{name:'Open Workshop',exact:true})).toBeEnabled();
 await page.reload();expect((await saved(page)).cleared).toEqual(['dock-access']);expect((await saved(page)).coins).toBe(460);await page.getByRole('button',{name:'Open Workshop',exact:true}).click();await expect(page.getByRole('heading',{name:'Workshop',exact:true})).toBeVisible();await page.keyboard.press('Escape');
});
test('unaffordable keeps the cost readable, disables only Clear, and traps modal focus',async({page})=>{
 await state(page,'poor');const clear=page.getByRole('button',{name:'Clear for 180 coins',exact:true});await expect(clear).toBeDisabled();await expect(clear).toHaveText('Clear ★180');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});await expect(cancel).toBeFocused();await page.keyboard.press('Tab');await expect(cancel).toBeFocused();await page.keyboard.press('Shift+Tab');await expect(cancel).toBeFocused();expect((await saved(page)).coins).toBe(60);
});
test('Edit clear pauses earnings and newly opened floor accepts placement across reload',async({page})=>{
 await state(page,'edit');const m=await saved(page);await page.clock.runFor(30000);expect((await saved(page)).coins).toBe(m.coins);
 await page.locator('[data-patch-id="sofa-west"] .patch-hit').focus();await page.keyboard.press('Enter');await page.getByRole('button',{name:'Clear for 120 coins',exact:true}).click();await page.clock.runFor(300);expect((await saved(page)).mode).toBe('edit');await expect(page.locator('.dock')).toBeVisible();
 await page.getByRole('button',{name:'Place wood stool',exact:true}).click();await page.getByRole('button',{name:'Place stool at 7, 4',exact:true}).click();expect((await saved(page)).objects).toEqual([{x:7,y:4,art:'stool-wood'}]);await page.reload();expect((await saved(page)).objects).toHaveLength(1);
});
test('drag pans at constant tile pitch and a moved touch cannot inspect',async({page})=>{
 const tile=await page.locator('.exp-cell').first().boundingBox(),before=await saved(page);await page.mouse.move(248,505);await page.mouse.down();await page.mouse.move(145,450,{steps:8});await page.mouse.up();await page.clock.runFor(1);
 const after=await saved(page);expect(after.camera.x).toBeLessThan(before.camera.x);expect((await page.locator('.exp-cell').first().boundingBox()).width).toBeCloseTo(tile.width);await expect(page.getByRole('dialog')).toHaveCount(0);
});
test('gallery shares the popup and all whole-object previews, with pressed/disabled states',async({page})=>{
 await state(page,'gallery');for(const id of ['garbage-sofa-S','garbage-car-E','garbage-shelving-N','garbage-armchair-W','garbage-cabinet-S']){await page.getByRole('combobox',{name:'Whole object'}).selectOption(id);await expect(page.locator('.object-preview')).toHaveCount(2);}
 await page.getByRole('button',{name:'pressed',exact:true}).click();await expect(page.locator('.wr-prepare.sample-pressed')).toHaveCount(1);await page.getByRole('button',{name:'disabled',exact:true}).click();await expect(page.getByRole('dialog').getByRole('button',{name:/Clear for/})).toBeDisabled();
});
test('touch drag pans without opening a patch; a stationary tap inspects it',async({page})=>{
 const cdp=await page.context().newCDPSession(page);const before=await saved(page);
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:248,y:490}]});
 for(let i=1;i<=6;i++)await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:248-i*12,y:490}]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await page.clock.runFor(1);await expect(page.getByRole('dialog')).toHaveCount(0);expect((await saved(page)).camera.x).toBeLessThan(before.camera.x);
 const point=await paintedPoint(page,'dock-access');await page.touchscreen.tap(point.x,point.y);await expect(page.getByRole('dialog')).toBeVisible();await cdp.detach();
});
test('phone, landscape and wider portrait contain every popup control and all assets',async({page})=>{
 for(const [width,height] of [[320,720],[390,844],[844,390],[1440,1000]]){await page.setViewportSize({width,height});await state(page,'poor');await page.evaluate(()=>document.fonts.ready);
 const scene=await page.locator('.expansion-scene').boundingBox(),dialog=await page.getByRole('dialog').boundingBox();expect(dialog.x).toBeGreaterThanOrEqual(scene.x);expect(dialog.y+dialog.height).toBeLessThanOrEqual(scene.y+scene.height);
 for(const button of await page.getByRole('dialog').getByRole('button').all()){const b=await button.boundingBox();expect(b.height).toBeGreaterThanOrEqual(44);expect(b.width).toBeGreaterThanOrEqual(44);expect(b.x+b.width).toBeLessThanOrEqual(dialog.x+dialog.width);}
 const cell=await page.locator('.exp-cell').first().boundingBox();expect(cell.width).toBeCloseTo(cell.height);await expect.poll(()=>page.evaluate(()=>[...document.images].filter(i=>i.hasAttribute('src')&&(!i.complete||!i.naturalWidth)).map(i=>i.src)),{timeout:15000}).toEqual([]);
 await state(page,'edit');await expect.poll(()=>page.locator('.item-preview img').evaluateAll(nodes=>nodes.every(n=>!!n.getAttribute('src')&&n.complete&&n.naturalWidth>0))).toBe(true);
 }
});

test('trash variety exposes five real models and all native facings without a repeated stamp',async({page})=>{
 await state(page,'variety');await expect(page.getByRole('heading',{name:'Whole-object trash',exact:true})).toBeVisible();await expect(page.locator('.facing-row button')).toHaveCount(20);
 await page.locator('.variety-scroll').evaluate(el=>el.scrollTop=el.scrollHeight);await page.getByRole('button',{name:'Preview Broken cabinet, facing S',exact:true}).click();await expect(page.getByRole('img',{name:'Broken cabinet',exact:true}).first()).toBeVisible();await expect(page.getByRole('button',{name:'Clear for 90 coins',exact:true})).toBeEnabled();
});
test('edge comparison retains the same scene and shows the ImageGen target on phone and wide layouts',async({page})=>{
 await state(page,'edge');expect(await page.locator('.perimeter-decor').count()).toBeGreaterThan(60);const before=await saved(page);await page.getByRole('button',{name:'Target',exact:true}).click();await expect(page.getByRole('img',{name:/ImageGen target: layered/})).toBeVisible();expect((await saved(page)).camera).toEqual(before.camera);await page.getByRole('button',{name:'Objects',exact:true}).click();await expect(page.locator('.expansion-scene')).toBeVisible();
 await page.setViewportSize({width:1440,height:1000});await expect(page.locator('.edge-target')).toBeVisible();await expect(page.locator('.expansion-scene')).toBeVisible();const a=await page.locator('.expansion-scene').boundingBox(),b=await page.locator('.edge-target').boundingBox();expect(a.x+a.width).toBeLessThan(b.x);
});
test('undecorated room fills the view and stays filled when panned to its bounds',async({page})=>{
 await state(page,'bare');
 await expect(page.locator('.perimeter-decor,.perimeter-lantern,.perimeter-ground')).toHaveCount(0);
 for(const [width,height] of [[320,720],[390,844],[844,390],[1440,1000]]){
  await page.setViewportSize({width,height});await page.getByRole('button',{name:'Reset',exact:true}).click();
  const viewport=await page.locator('.expansion-scene').boundingBox();
  const covers=()=>page.locator('.exp-room').evaluate(el=>{const room=el.getBoundingClientRect(),view=el.closest('main').getBoundingClientRect();return room.left<=view.left+.5&&room.top<=view.top+.5&&room.right>=view.right-.5&&room.bottom>=view.bottom-.5;});
  await expect.poll(covers).toBe(true);const before=await page.locator('.exp-cell').first().boundingBox();expect(before.width).toBeCloseTo(before.height);
  await page.mouse.move(viewport.x+viewport.width/2,viewport.y+viewport.height/2);await page.mouse.wheel(100000,100000);await expect.poll(covers).toBe(true);
  await page.mouse.wheel(-100000,-100000);await expect.poll(async()=>(await saved(page)).camera).toEqual({x:0,y:0});await expect.poll(covers).toBe(true);
  expect((await page.locator('.exp-cell').first().boundingBox()).width).toBeCloseTo(before.width);
 }
 await state(page,'edge');expect(await page.locator('.perimeter-decor').count()).toBeGreaterThan(60);
});
