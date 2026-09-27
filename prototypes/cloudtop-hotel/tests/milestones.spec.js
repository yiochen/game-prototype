import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { milestoneRuns } from './milestone-fixtures.js';
import { replayRun, SCORE_VERSION } from '../score-rules.js';
const root='/prototypes/cloudtop-hotel/';
async function resume(page,run,reduced=true) {
  await page.emulateMedia({reducedMotion:reduced?'reduce':'no-preference'});
  await page.goto(root);
  await page.evaluate(({run,version})=>localStorage.setItem('cloudtop-guestbook-v1',JSON.stringify({runs:[],active:{...run,id:'milestone-test',version},sound:false})),{run,version:SCORE_VERSION});
  await page.reload();await expect(page.locator('#world')).toHaveAttribute('data-ready','true');await page.locator('#lobby-resume').click();
}
async function buy(page,[index,suit]) {
  await page.locator(`[data-offer-index="${index}"]`).click();
  if(suit)await page.locator(`[data-suit="${suit}"]`).click();
}
async function shot(page,name) {await mkdir('artifacts/cloudtop-hotel',{recursive:true});await page.screenshot({path:`artifacts/cloudtop-hotel/automatic-gift-${name}.png`});}

test('all five gifts arrive without selection, preserve replay, and never open a reward dialog',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(const [floor,fixture] of milestoneRuns) {
    await resume(page,fixture.before);await buy(page,fixture.move);
    const state=replayRun(fixture.after.seed,fixture.after.moves,false),gift=state.gifts.find(g=>g.floor===floor);
    await expect(page.locator('#world')).toHaveAttribute('data-state','picking');
    await expect(page.locator('dialog[open]')).toHaveCount(0);
    await expect(page.locator('#milestone-celebration')).toContainText(`${floor} floors!`);
    await expect(page.locator('.milestone-gift')).toHaveAttribute('data-reward',gift.key);
    await expect(page.locator('#coins')).toHaveText(String(state.cash));
    await expect(page.locator('#height')).toHaveText(String(state.links.length));
    await expect(page.locator('#milestone-celebration button')).toHaveCount(0);
    const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('cloudtop-guestbook-v1')).active);
    expect(saved.moves).toEqual(fixture.after.moves);expect(replayRun(saved.seed,saved.moves,false)).toEqual(state);
    await page.reload();await page.locator('#lobby-resume').click();
    await expect(page.locator('#coins')).toHaveText(String(state.cash));await expect(page.locator('#milestone-celebration')).toBeHidden();
  }
  expect(errors).toEqual([]);
});
test('paper celebration fits desktop, phone and landscape and does not block the next card',async({page})=>{
  const fixture=milestoneRuns.get(25);
  for(const [name,width,height] of [['desktop',1280,800],['phone',390,844],['small-phone',320,568],['landscape',844,390]]) {
    await page.setViewportSize({width,height});await resume(page,fixture.before);await buy(page,fixture.move);await shot(page,name);
    const panel=page.locator('#milestone-celebration');await expect(panel).toBeVisible();
    const box=await panel.boundingBox();expect(box.x).toBeGreaterThanOrEqual(0);expect(box.y).toBeGreaterThanOrEqual(0);expect(box.x+box.width).toBeLessThanOrEqual(width);expect(box.y+box.height).toBeLessThanOrEqual(height);
    await expect(panel).toHaveCSS('pointer-events','none');
    const state=replayRun(fixture.after.seed,fixture.after.moves,false),index=state.offer.findIndex(c=>c.price<=state.cash);
    await buy(page,[index,state.offer[index].type==='choice'?'bunny':null]);
    await expect(page.locator('#coins')).not.toHaveText(String(state.cash));
  }
});
test('animation and reduced motion award once, auto-dismiss, and replay clears the gift',async({page})=>{
  const fixture=milestoneRuns.get(10);await resume(page,fixture.before,false);await buy(page,fixture.move);
  await expect(page.locator('#milestone-celebration')).toBeHidden();await page.emulateMedia({reducedMotion:'reduce'});
  await expect(page.locator('#milestone-celebration')).toBeVisible();
  await expect(page.locator('#milestone-celebration')).toBeHidden({timeout:6000});
  await expect(page.locator('#coins')).toHaveText(String(replayRun(fixture.after.seed,fixture.after.moves,false).cash));
  await page.locator('#menu-open').click();await page.locator('#replay').click();
  await expect(page.locator('#height')).toHaveText('0');await expect(page.locator('#coins')).toHaveText('100');await expect(page.locator('#milestone-celebration')).toBeHidden();
});
