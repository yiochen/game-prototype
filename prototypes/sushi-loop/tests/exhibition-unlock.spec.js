import {test,expect} from '@playwright/test';
const path='/prototypes/sushi-loop/design/expansion-preview/';
const key='sushi-loop-issue19-expansion-review-v2';
const saved=p=>p.evaluate(k=>JSON.parse(localStorage.getItem(k)),key);
const choose=(p,s)=>p.getByRole('combobox',{name:'Review state'}).selectOption(s);
const popup=p=>p.getByRole('dialog',{name:'Exhibition Unlocked',exact:true});

test.use({hasTouch:true});
test.beforeEach(async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.clock.install();await page.goto(path);await choose(page,'almost');
});

async function ready(page){
 await page.locator('[data-patch-id="dock-access"] button').focus();await page.keyboard.press('Enter');await page.getByRole('button',{name:'Clear for 180 coins',exact:true}).click();await page.clock.runFor(300);
 await page.getByRole('button',{name:'Inspect cover',exact:true}).focus();await page.keyboard.press('Enter');
}
async function reveal(page){await ready(page);await page.getByRole('button',{name:'Reveal',exact:true}).click();await page.clock.runFor(1300);await expect(popup(page)).toBeVisible();}

test('the unlock waits for explicit reveal and the full cover removal, preserving the fixed room',async({page})=>{
 await ready(page);const before=await saved(page),room=await page.locator('.exp-room').boundingBox();
 await expect(popup(page)).toHaveCount(0);await expect(page.getByRole('dialog')).not.toContainText(/Exhibition|submarine|Workshop/i);
 await page.getByRole('button',{name:'Reveal',exact:true}).click();
 await expect(page.locator('.opening-cover')).toHaveCount(1);await expect(popup(page)).toHaveCount(0);
 await page.clock.runFor(1050);await expect(page.locator('.opening-cover')).toHaveCount(1);await expect(popup(page)).toHaveCount(0);
 await page.keyboard.press('Tab');await page.keyboard.press('Escape');await page.mouse.click(190,95);
 expect((await saved(page)).camera).toEqual(before.camera);expect((await saved(page)).mode).toBe(before.mode);
 await page.clock.runFor(250);await expect(page.locator('.covered-landmark,.opening-cover,.reveal-opening-shield')).toHaveCount(0);await expect(popup(page)).toBeVisible();
 expect((await saved(page)).revealed).toBe(true);expect((await saved(page)).coins).toBe(before.coins);expect((await saved(page)).camera).toEqual(before.camera);expect(await page.locator('.exp-room').boundingBox()).toEqual(room);
});

test('the shared popup contains its image and 44 px controls on narrow phone, landscape and wide screens',async({page})=>{
 for(const [width,height] of [[320,720],[390,844],[720,1560],[1080,2340],[844,390],[1440,1000]]){
  await page.setViewportSize({width,height});await choose(page,'unlock');const dialog=popup(page);await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('heading')).toHaveText('Exhibition Unlocked');await expect(dialog.getByRole('button')).toHaveCount(2);
  const go=dialog.getByRole('button',{name:"Let's go",exact:true}),close=dialog.getByRole('button',{name:'Close',exact:true});
  await expect(go).toBeFocused();await page.keyboard.press('Tab');await expect(close).toBeFocused();await page.keyboard.press('Shift+Tab');await expect(go).toBeFocused();
  const scene=await page.locator('.expansion-scene').boundingBox(),card=await dialog.boundingBox();
  expect(card.x).toBeGreaterThanOrEqual(scene.x);expect(card.y).toBeGreaterThanOrEqual(scene.y);expect(card.x+card.width).toBeLessThanOrEqual(scene.x+scene.width+.5);expect(card.y+card.height).toBeLessThanOrEqual(scene.y+scene.height);
  for(const button of [close,go]){const box=await button.boundingBox();expect(box.width).toBeGreaterThanOrEqual(44);expect(box.height).toBeGreaterThanOrEqual(44);expect(box.x).toBeGreaterThanOrEqual(card.x);expect(box.x+box.width).toBeLessThanOrEqual(card.x+card.width);expect(box.y+box.height).toBeLessThanOrEqual(card.y+card.height);}
  const image=dialog.getByRole('img');await expect.poll(()=>image.evaluate(i=>i.complete&&i.naturalWidth===1536&&i.naturalHeight===1024)).toBe(true);const box=await image.boundingBox();expect(box.width/box.height).toBeCloseTo(1.5,2);
  const heading=await dialog.getByRole('heading').boundingBox(),x=await close.boundingBox();expect(heading.x+heading.width).toBeLessThanOrEqual(x.x);expect(await dialog.getByRole('heading').evaluate(e=>e.scrollWidth<=e.clientWidth)).toBe(true);
 }
});

test('X, Escape and Back close to the revealed room without changing camera, coins or edit mode',async({page})=>{
 for(const method of ['X','Escape','Back']){
  await choose(page,'almost');await page.getByRole('button',{name:'Edit',exact:true}).click();await reveal(page);const before=await saved(page),scene=await page.locator('.expansion-scene').boundingBox();
  await page.mouse.click(scene.x+5,scene.y+110);await expect(popup(page)).toBeVisible();expect(await saved(page)).toEqual(before);
  if(method==='X')await popup(page).getByRole('button',{name:'Close',exact:true}).click();else if(method==='Escape')await page.keyboard.press('Escape');else await page.goBack();
  await expect(popup(page)).toHaveCount(0);await expect(page.locator('.covered-landmark,.opening-cover')).toHaveCount(0);await expect(page.locator('.room-pan')).toBeFocused();expect(await saved(page)).toEqual(before);await expect(page.locator('.dock')).toBeVisible();
  await page.reload();await expect(popup(page)).toHaveCount(0);await expect(page.locator('.covered-landmark,.opening-cover')).toHaveCount(0);expect(await saved(page)).toEqual(before);
  await page.getByRole('button',{name:'Open Submarine',exact:true}).click();await expect(page.getByRole('heading',{name:'Submarine',exact:true})).toBeVisible();await expect(popup(page)).toHaveCount(0);await page.keyboard.press('Escape');
 }
});

test('reduced motion removes the cover immediately and still announces the unlock once',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await ready(page);await page.getByRole('button',{name:'Reveal',exact:true}).click();await expect(popup(page)).toBeVisible();await expect(page.locator('.covered-landmark,.opening-cover,.reveal-opening-shield')).toHaveCount(0);
 await popup(page).getByRole('button',{name:'Close',exact:true}).click();await page.reload();await expect(popup(page)).toHaveCount(0);expect((await saved(page)).revealed).toBe(true);
});

test('Back during the committed opening still leaves a dismissible unlock popup',async({page})=>{
 await ready(page);await page.getByRole('button',{name:'Reveal',exact:true}).click();await page.clock.runFor(300);await page.goBack();await page.clock.runFor(1000);await expect(popup(page)).toBeVisible();
 await popup(page).getByRole('button',{name:'Close',exact:true}).click();await expect(popup(page)).toHaveCount(0);expect(new URL(page.url()).pathname).toBe(path);expect((await saved(page)).revealed).toBe(true);await expect(page.locator('.covered-landmark,.opening-cover')).toHaveCount(0);
});

test("Let's go opens the existing expedition preparation without starting a journey",async({page})=>{
 await reveal(page);const before=await saved(page);await popup(page).getByRole('button',{name:"Let's go",exact:true}).click();await page.waitForURL(/#expedition-start$/);await expect(page.locator('.prototype-stage[data-story="expedition-start"]')).toBeVisible();await expect(page.getByRole('button',{name:'Start',exact:true})).toBeVisible();
 expect((await saved(page)).revealed).toBe(true);expect((await saved(page)).camera).toEqual(before.camera);expect((await saved(page)).coins).toBe(before.coins);
});
