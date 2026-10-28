import {test,expect} from '@playwright/test';
const path='/prototypes/sushi-loop/design/shop-preview/?state=shop';
const key='sushi-loop-issue18-shop-review-v2';
const saved=p=>p.evaluate(k=>JSON.parse(localStorage.getItem(k)),key);
test.beforeEach(async({page})=>{await page.setViewportSize({width:390,height:844});await page.goto(path);await page.getByRole('button',{name:'Reset',exact:true}).click();});
test('buy, place, return and reload preserve real quantities',async({page})=>{
 await page.getByRole('button',{name:'Buy Wood stool for 80 coins',exact:true}).click();
 expect((await saved(page)).coins).toBe(1160);expect((await saved(page)).inventory.stool).toBe(1);
 await page.getByRole('button',{name:'Close Shop',exact:true}).click();
 await page.getByRole('button',{name:'Wood stool, 1 available',exact:true}).click();await page.getByRole('button',{name:'Place Wood stool in cell 36',exact:true}).click();
 expect((await saved(page)).inventory.stool).toBe(0);expect((await saved(page)).objects).toHaveLength(1);
 await page.reload();await page.getByRole('button',{name:'Close Shop',exact:true}).click();
 await page.getByRole('button',{name:'Select placed Wood stool',exact:true}).click();await page.getByRole('button',{name:'Return',exact:true}).click();
 expect((await saved(page)).inventory.stool).toBe(1);expect((await saved(page)).coins).toBe(1160);
});
test('limited stock sells out in place and cannot be bought after reload',async({page})=>{
 const buy=page.getByRole('button',{name:'Buy Wood barrel for 160 coins',exact:true});await buy.click();
 await expect(page.getByRole('button',{name:'Buy Wood barrel for 160 coins, sold out',exact:true})).toBeDisabled();
 expect((await saved(page)).coins).toBe(1080);await page.reload();expect((await saved(page)).inventory.barrel).toBe(1);
 await expect(page.getByRole('article',{name:'Wood barrel',exact:true})).toContainText('Sold out');
});
test('poor offers retain cost and accessible Buy labels',async({page})=>{
 await page.getByRole('combobox',{name:'Review state'}).selectOption('poor');const buttons=page.locator('.cost-action');expect(await buttons.count()).toBe(5);
 for(const b of await buttons.all()){await expect(b).toBeDisabled();await expect(b).toHaveAccessibleName(/^Buy /);await expect(b).toHaveText(/\d/);}
});
test('return preserves camera, mode, category, strip scroll and opener focus',async({page})=>{
 await page.getByRole('button',{name:'Close Shop',exact:true}).click();
 await page.mouse.move(170,300);await page.mouse.down();await page.mouse.move(195,310,{steps:5});await page.mouse.up();
 await page.locator('.inventory').evaluate(el=>el.scrollLeft=80);const before=await saved(page);const scroll=await page.locator('.inventory').evaluate(el=>el.scrollLeft);
 const opener=page.locator('.shop-action');await opener.click();await page.getByRole('button',{name:'Close Shop',exact:true}).click();await expect(opener).toBeFocused();
 const after=await saved(page);expect(before.camera.x).toBe(25);expect(after.camera).toEqual(before.camera);expect(after.mode).toBe(before.mode);expect(after.category).toBe(before.category);expect(await page.locator('.inventory').evaluate(el=>el.scrollLeft)).toBe(scroll);
});
test('Shop is Edit-only, hides the tray, and retains the pause',async({page})=>{
 await page.clock.install();await page.reload();let before=await saved(page);await page.clock.runFor(13000);expect((await saved(page)).coins).toBe(before.coins);expect((await saved(page)).charge).toBe(before.charge);
 await expect(page.locator('.dock')).toBeHidden();await expect(page.locator('.hud-shop')).toHaveCount(0);
 await page.getByRole('button',{name:'Close Shop',exact:true}).click();await expect(page.locator('.dock')).toBeVisible();await page.getByRole('button',{name:'Live',exact:true}).click();
 await expect(page.getByRole('button',{name:'Shop',exact:true})).toHaveCount(0);await expect(page.getByRole('dialog')).toHaveCount(0);before=await saved(page);await page.clock.runFor(13000);expect((await saved(page)).coins).toBe(before.coins+18);
 await page.getByRole('button',{name:'Edit',exact:true}).click();await page.locator('.shop-action').click();await expect(page.getByRole('dialog')).toBeVisible();await expect(page.locator('.dock')).toBeHidden();
});
test('keyboard focus stays on paper, Escape and browser Back restore opener',async({page})=>{
 await page.keyboard.press('Tab');expect(await page.evaluate(()=>!!document.activeElement.closest('.shop-overlay'))).toBe(true);
 await page.keyboard.press('Escape');await expect(page.locator('.shop-action')).toBeFocused();await page.locator('.shop-action').click();await page.goBack();await expect(page.locator('.shop-action')).toBeFocused();await page.locator('.shop-action').click();await page.getByRole('button',{name:'Back to inventory',exact:true}).focus();await page.keyboard.press('Enter');await expect(page.locator('.dock')).toBeVisible();await expect(page.locator('.shop-action')).toBeFocused();
});
test('gallery uses identical rows and exposes pressed, disabled and sold-out states',async({page})=>{
 await page.getByRole('combobox',{name:'Review state'}).selectOption('gallery');await page.getByRole('button',{name:'pressed',exact:true}).click();await expect(page.locator('.sample-pressed')).toHaveCount(1);
 await page.getByRole('button',{name:'disabled',exact:true}).click();await expect(page.locator('.cost-action:disabled')).toHaveCount(5);await page.getByRole('button',{name:'Sold out',exact:true}).click();await expect(page.locator('.supply-row.sold-out')).toHaveCount(2);
});
test('touch browsing owns horizontal motion and an upward pickup places one bought good',async({browser})=>{
 const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto((process.env.TEST_URL||'http://127.0.0.1:4175')+path);await page.getByRole('button',{name:'Buy Wood stool for 80 coins',exact:true}).tap();await page.getByRole('button',{name:'Back to inventory',exact:true}).tap();await expect(page.locator('.dock')).toBeVisible();
 const client=await context.newCDPSession(page),center=r=>({x:r.x+r.width/2,y:r.y+r.height/2});
 async function touch(from,to,cancel=false){await client.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[from]});for(let i=1;i<=12;i++)await client.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:from.x+(to.x-from.x)*i/12,y:from.y+(to.y-from.y)*i/12}]});await client.send('Input.dispatchTouchEvent',{type:cancel?'touchCancel':'touchEnd',touchPoints:[]});}
 let from=center(await page.getByRole('button',{name:'Wood stool, 1 available',exact:true}).boundingBox());await touch(from,{x:from.x-75,y:from.y});expect(await page.locator('.inventory').evaluate(el=>el.scrollLeft)).toBeGreaterThan(10);expect((await saved(page)).objects).toHaveLength(0);
 await page.locator('.inventory').evaluate(el=>el.scrollLeft=0);from=center(await page.getByRole('button',{name:'Wood stool, 1 available',exact:true}).boundingBox());const to=center(await page.locator('.floor-cell').nth(36).boundingBox());await touch(from,to,true);expect((await saved(page)).inventory.stool).toBe(1);
 await touch(from,to);expect((await saved(page)).objects).toHaveLength(1);expect((await saved(page)).inventory.stool).toBe(0);expect(errors).toEqual([]);await context.close();
});
for(const [width,height] of [[320,720],[390,844],[844,390],[1440,1000]])test(`layout and touch bounds ${width}×${height}`,async({page})=>{
 await page.setViewportSize({width,height});await page.evaluate(()=>document.fonts.ready);const bounds=await page.locator('.scene').boundingBox();expect(bounds.width).toBeLessThanOrEqual(width);expect(bounds.height).toBeLessThanOrEqual(height);
 expect(await page.locator('.supply-scroll').evaluate(el=>el.scrollWidth<=el.clientWidth)).toBe(true);
 for(const b of await page.locator('.cost-action,.shared-close,.shopping-bag').all()){const r=await b.boundingBox();expect(r.width).toBeGreaterThanOrEqual(44);expect(r.height).toBeGreaterThanOrEqual(44);}
 await page.locator('.supply-scroll').evaluate(el=>el.scrollTop=el.scrollHeight);await expect(page.getByRole('article',{name:'Wood barrel',exact:true})).toBeInViewport();
 const scroll=await page.locator('.supply-scroll').boundingBox(),bag=await page.locator('.shopping-bag').boundingBox();expect(scroll.y+scroll.height).toBeLessThanOrEqual(bag.y);
});

test('purchases fly to the bag without status copy; closing during travel preserves payment',async({page})=>{
 await page.getByRole('button',{name:'Buy Wood stool for 80 coins',exact:true}).click();await expect(page.locator('.purchase-flight')).toHaveCount(1);await expect(page.getByRole('button',{name:'Back to inventory',exact:true})).toBeVisible();
 await expect(page.locator('.purchase-receipt')).toHaveCount(0);await expect(page.locator('.shop-overlay')).not.toContainText('Added to inventory');
 await page.getByRole('button',{name:'Back to inventory',exact:true}).click();await expect(page.locator('.dock')).toBeVisible();expect((await saved(page)).coins).toBe(1160);expect((await saved(page)).inventory.stool).toBe(1);
 await page.locator('.shop-action').click();await expect(page.locator('.purchase-flight')).toHaveCount(0);expect((await saved(page)).inventory.stool).toBe(1);
 await page.getByRole('button',{name:'Buy Belt tile for 40 coins',exact:true}).click();await expect(page.locator('.purchase-flight')).toHaveCount(0,{timeout:2000});expect((await saved(page)).inventory.belt).toBe(1);
});
test('reduced motion skips item travel and still commits a purchase',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await page.getByRole('button',{name:'Buy Wood stool for 80 coins',exact:true}).click();await expect(page.locator('.purchase-flight')).toHaveCount(0);expect((await saved(page)).inventory.stool).toBe(1);expect((await saved(page)).coins).toBe(1160);
});
test('successive purchases have independent flights and cannot be paid again by animation',async({page})=>{
 const buy=page.getByRole('button',{name:'Buy Belt tile for 40 coins',exact:true});await buy.click();await page.waitForTimeout(80);await buy.click();
 expect((await saved(page)).inventory.belt).toBe(2);expect((await saved(page)).coins).toBe(1160);await expect(page.locator('.purchase-flight')).toHaveCount(2);await expect(page.locator('.purchase-flight')).toHaveCount(0,{timeout:2000});expect((await saved(page)).inventory.belt).toBe(2);expect((await saved(page)).coins).toBe(1160);
});
