import {test,expect} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
import {createGame,pick,advanceDeal,segments} from '../engine.js';
const root='/prototypes/cloudtop-hotel/';
async function open(page,seed=147){
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.goto(`${root}?seed=${seed}`);
 await expect(page.locator('#world')).toHaveAttribute('data-ready','true');
 await page.locator('#lobby-play').click();
}
async function buy(page,index,suit){
 await page.locator(`#offers [data-offer-index="${index}"]`).click();
 if(suit) await page.locator(`#room-choices [data-suit="${suit}"]`).click();
 await expect(page.locator('#world')).toHaveAttribute('data-state','picking');
}
async function control(page,id){await page.locator('#menu-open').click();await page.locator(`#${id}`).click();}
async function fits(page){
 const result=await page.evaluate(()=>({width:innerWidth,height:innerHeight,sw:document.documentElement.scrollWidth,sh:document.documentElement.scrollHeight,boxes:[...document.querySelectorAll('.offer-card,.card-help,.strategy-chip,#camera-toggle')].filter(e=>e.getClientRects().length).map(e=>e.getBoundingClientRect().toJSON())}));
 expect(result.sw).toBeLessThanOrEqual(result.width);expect(result.sh).toBeLessThanOrEqual(result.height);
 for(const box of result.boxes){expect(box.left).toBeGreaterThanOrEqual(0);expect(box.right).toBeLessThanOrEqual(result.width);expect(box.top).toBeGreaterThanOrEqual(0);expect(box.bottom).toBeLessThanOrEqual(result.height);}
}
test('Guest Parade previews, cancellation, bonus guests, reload and ending match committed purchases',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await open(page);
 const s=createGame(147),sky=page.locator('.sky-backdrop'),canvas=page.locator('#world canvas');
 await expect(page.locator('[data-type="parade"] .parade-guest')).toHaveCount(3);
 await page.locator('[data-offer-help="0"]').click();await expect(page.locator('#effect-dialog')).toContainText('random type different from the purchase');await page.keyboard.press('Escape');
 for(const [i,suit] of [[0],[1]]){await buy(page,i,suit);pick(s,i,suit);advanceDeal(s);}
 await expect(sky).toHaveAttribute('data-frenzy','true');await expect(canvas).toHaveAttribute('data-frenzy','true');
 await expect(page.locator('#strategy-status')).toContainText('next +2 · change from Cat');
 await page.locator('[data-offer-index="1"]').click();
 await expect(page.locator('#room-choices [data-suit="cat"]')).toContainText('Ends your streak');
 await expect(page.locator('#room-choices [data-suit="bunny"]')).toContainText('Parade +2 random rooms');
 await page.keyboard.press('Escape');await expect(page.locator('#coins')).toHaveText(String(s.cash));
 await buy(page,1,'bunny');pick(s,1,'bunny');advanceDeal(s);
 expect(await page.locator('#floor-record li').evaluateAll(es=>es.map(e=>e.dataset.type))).toEqual(s.links.map(l=>l.suit));
 for(const suit of ['bunny','frog','cat'])await expect(page.locator(`.dock-chip.${suit} .dock-count`)).toHaveText(String(segments(s,suit).length));
 await expect(page.locator('#purchase-feedback')).toContainText(`Parade +2 ${s.history.at(-1).paradeSuit === 'cat' ? 'Cat' : 'Frog'} rooms`);
 await page.reload();await expect(page.locator('#world')).toHaveAttribute('data-ready','true');await expect(sky).toHaveAttribute('data-frenzy','false');
 await page.locator('#lobby-resume').click();await expect(sky).toHaveAttribute('data-frenzy','true');
 expect(await page.locator('#floor-record li').evaluateAll(es=>es.map(e=>e.dataset.type))).toEqual(s.links.map(l=>l.suit));
 await expect(page.locator('[data-offer-index="1"] .streak-hint')).toHaveText('Ends streak');await buy(page,1);
 await expect(sky).toHaveAttribute('data-frenzy','false');await expect(canvas).toHaveAttribute('data-celebrating-guests','0');
 expect(errors).toEqual([]);
});
test('frenzy travels behind cheering guests, fits screens, freezes for reduced motion and clears on replay',async({page})=>{
 await open(page);for(const [i,suit] of [[0],[1],[1,'bunny']])await buy(page,i,suit);
 await page.locator('#camera-toggle').click();
 const sky=page.locator('.sky-backdrop'),canvas=page.locator('#world canvas'),ribbon=page.locator('.frenzy-rainbow').first();
 await expect(canvas).toHaveAttribute('data-celebrating-guests','15');
 const roomFrames=(await canvas.getAttribute('data-sprite-frames')).split(',').filter(f=>f.startsWith('rooms-'));
 expect(roomFrames.length).toBe(15);expect(roomFrames.every(f=>f.endsWith(':6'))).toBe(true);
 const transform=()=>ribbon.evaluate(e=>getComputedStyle(e).transform);
 const frozen=await transform();await page.waitForTimeout(150);expect(await transform()).toBe(frozen);
 await page.emulateMedia({reducedMotion:'no-preference'});await expect.poll(transform).not.toBe(frozen);
 await mkdir('artifacts/cloudtop-hotel',{recursive:true});
 for(const viewport of [{width:784,height:1233},{width:390,height:844},{width:320,height:480},{width:844,height:390}]){
  await page.setViewportSize(viewport);await fits(page);await page.screenshot({path:`artifacts/cloudtop-hotel/frenzy-${viewport.width}x${viewport.height}.png`});
 }
 await page.emulateMedia({reducedMotion:'reduce'});
 await expect.poll(()=>sky.evaluate(e=>e.getAnimations({subtree:true}).every(a=>a.playState==='paused'))).toBe(true);
 const paused=await transform();await page.waitForTimeout(150);expect(await transform()).toBe(paused);
 await control(page,'lobby-open');await expect(sky).toHaveAttribute('data-frenzy','false');
 await page.locator('#lobby-resume').click();await expect(sky).toHaveAttribute('data-frenzy','true');
 await control(page,'replay');await expect(sky).toHaveAttribute('data-frenzy','false');await expect(canvas).toHaveAttribute('data-celebrating-guests','0');
});
test('Neighborhood Streak also activates frenzy and Mosaic removes it',async({page})=>{
 await open(page,30);await buy(page,1);await expect(page.locator('.sky-backdrop')).toHaveAttribute('data-frenzy','true');
 await buy(page,0);await expect(page.locator('.sky-backdrop')).toHaveAttribute('data-frenzy','false');
});
test('animated parade activation and reveal commit one deterministic bonus batch',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await open(page);
 await page.emulateMedia({reducedMotion:'no-preference'});
 await buy(page,0);await expect(page.locator('.sky-backdrop')).toHaveAttribute('data-frenzy','true');
 const s=createGame(147);pick(s,0);advanceDeal(s);pick(s,1);advanceDeal(s);
 await page.locator('[data-offer-index="1"]').click();
 await expect(page.locator('#world')).toHaveAttribute('data-state','resolving');
 await control(page,'reveal-now');
 await expect(page.locator('#world')).toHaveAttribute('data-state','picking');
 expect(await page.locator('#floor-record li').evaluateAll(es=>es.map(e=>e.dataset.type))).toEqual(s.links.map(l=>l.suit));
 await expect(page.locator('#coins')).toHaveText(String(s.cash));
 await page.emulateMedia({reducedMotion:'reduce'});await page.waitForTimeout(250);
 await expect(page.locator('#height')).toHaveText(String(s.links.length));
 expect(errors).toEqual([]);
});
