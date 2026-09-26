import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { pendingRuns } from './milestone-fixtures.js';
import { replayRun, SCORE_VERSION } from '../score-rules.js';
import { claimMilestone } from '../engine.js';
const root='/prototypes/cloudtop-hotel/';
async function resume(page,run,reduced=true) {
  await page.emulateMedia({reducedMotion:reduced?'reduce':'no-preference'});
  await page.goto(root);
  await page.evaluate(({run,version})=>localStorage.setItem('cloudtop-guestbook-v1',JSON.stringify({runs:[],active:{...run,id:'milestone-test',version},sound:false})),{run,version:SCORE_VERSION});
  await page.reload();await expect(page.locator('#world')).toHaveAttribute('data-ready','true');
  await page.locator('#lobby-resume').click();
}
async function screenshot(page,name) {await mkdir('artifacts/cloudtop-hotel',{recursive:true});await page.screenshot({path:`artifacts/cloudtop-hotel/milestone-${name}.png`});}

test('all five milestones offer three centered paper cards with increasing tips and survive reload', async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(const [floor,run] of pendingRuns) {
    await resume(page,run);const state=replayRun(run.seed,run.moves,false);
    await expect(page.locator('#milestone-title')).toHaveText(`${floor} floors!`);
    await expect(page.locator('#milestone-choices button')).toHaveCount(3);
    await expect(page.locator('[data-gift="tips"]')).toContainText(`+${[5,10,20,35,60][[10,25,50,100,200].indexOf(floor)]} coins`);
    await screenshot(page,`floor-${floor}`);
    const rows=await page.locator('#floor-record').textContent(),streak=await page.locator('#strategy-status').textContent();
    await page.keyboard.press('1');await expect(page.locator('#coins')).toHaveText(String(state.cash));
    await page.locator('[data-gift="tips"]').click();claimMilestone(state,'tips');
    await expect(page.locator('#coins')).toHaveText(String(state.cash));
    expect(await page.locator('#floor-record').textContent()).toBe(rows);expect(await page.locator('#strategy-status').textContent()).toBe(streak);
    await page.reload();await page.locator('#lobby-resume').click();
    await expect(page.locator('#milestone-dialog')).toBeHidden();await expect(page.locator('#coins')).toHaveText(String(state.cash));
    const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('cloudtop-guestbook-v1')).active);
    expect(saved.moves.at(-1)).toEqual(['gift','tips']);expect(replayRun(saved.seed,saved.moves,false)).toEqual(state);
  }
  expect(errors).toEqual([]);
});
test('workshop and Lucky Bell gifts install without placing rooms or changing the streak',async({page})=>{
  for(const key of ['suit:frog','assembler','stabilizer']) {
    const run=pendingRuns.get(50);await resume(page,run);const state=replayRun(run.seed,run.moves,false),before=structuredClone(state);
    if(key!=='stabilizer')await page.locator('[data-gift="workshop"]').click();
    await page.locator(`[data-gift="${key}"]`).click();claimMilestone(state,key);
    await expect(page.locator(`[data-upgrade="${key}"]`)).toBeVisible();await expect(page.locator('#height')).toHaveText(String(before.links.length));
    await expect(page.locator('#coins')).toHaveText(String(state.cash));
    const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('cloudtop-guestbook-v1')).active);
    expect(replayRun(saved.seed,saved.moves,false)).toEqual(state);
  }
});
test('paper reward cards fit desktop, phone and landscape; dismiss and return preserve the gift',async({page})=>{
  await resume(page,pendingRuns.get(25));
  for(const [name,width,height] of [['desktop',1280,800],['phone',390,844],['small-phone',320,568],['landscape',844,390]]) {
    await page.setViewportSize({width,height});await page.mouse.move(0,0);await screenshot(page,name);
    const boxes=await page.locator('#milestone-choices button').evaluateAll(elements=>elements.map(el=>({r:el.getBoundingClientRect().toJSON(),sw:el.scrollWidth,cw:el.clientWidth,sh:el.scrollHeight,ch:el.clientHeight,bg:getComputedStyle(el).backgroundImage})));
    expect(boxes).toHaveLength(3);
    for(const {r,sw,cw,sh,ch,bg} of boxes){expect(r.left).toBeGreaterThanOrEqual(0);expect(r.right).toBeLessThanOrEqual(width);expect(r.top).toBeGreaterThanOrEqual(0);expect(r.bottom).toBeLessThanOrEqual(height);expect(sw).toBeLessThanOrEqual(cw);expect(sh).toBeLessThanOrEqual(ch);expect(bg).toContain('card-paper');}
    expect(Math.abs(boxes[0].r.top-boxes[2].r.top)).toBeLessThan(2);
    expect(Math.abs((boxes[0].r.left+boxes[2].r.right)/2-width/2)).toBeLessThan(12);
  }
  await page.keyboard.press('Escape');await expect(page.locator('#milestone-open')).toBeFocused();
  await page.locator('#milestone-open').click();await expect(page.locator('#milestone-title')).toHaveText('25 floors!');
  await page.locator('[data-gift="workshop"]').click();await page.locator('#milestone-back').click();await expect(page.locator('#milestone-choices button')).toHaveCount(3);
});
test('gift opens after animated delivery settles; reduced motion settles once and replay resets gifts',async({page})=>{
  const pending=pendingRuns.get(10),run={...pending,moves:pending.moves.slice(0,-1)},[index,suit]=pending.moves.at(-1);
  await resume(page,run,false);await page.locator(`[data-offer-index="${index}"]`).click();
  if(suit)await page.locator(`[data-suit="${suit}"]`).click();
  await expect(page.locator('#milestone-dialog')).toBeHidden();
  await page.emulateMedia({reducedMotion:'reduce'});
  await expect(page.locator('#milestone-dialog')).toBeVisible();
  await page.locator('[data-gift="tips"]').click();
  await page.locator('#menu-open').click();await page.locator('#replay').click();
  await expect(page.locator('#height')).toHaveText('0');await expect(page.locator('#coins')).toHaveText('100');await expect(page.locator('#milestone-dialog')).toBeHidden();
});
