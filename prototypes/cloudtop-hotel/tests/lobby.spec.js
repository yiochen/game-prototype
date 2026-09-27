import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { createGame, pick, advanceDeal, choiceSuits } from '../engine.js';
import { SCORE_VERSION } from '../score-rules.js';
const ROOT='/prototypes/cloudtop-hotel/', API='**/api/cloudtop-hotel/leaderboard';
const entries=Array.from({length:12},(_,i)=>({id:String(i),name:['Cloud Keeper','Mochi & Co','Paper Pilot'][i%3],floors:122-i*5,neighborhoods:20-i,coins:i%3,seed:'stay'+i,createdAt:'2026-01-01'}));
async function open(page,reduced=true) {
  await page.emulateMedia({reducedMotion:reduced?'reduce':'no-preference'});
  await page.route(API,route=>route.fulfill({json:{entries,version:SCORE_VERSION}}));
  await page.goto(ROOT+'?seed=lobby-test'); await expect(page.locator('#world')).toHaveAttribute('data-ready','true');
}
async function shot(page,name) { await mkdir('artifacts/cloudtop-hotel',{recursive:true}); await page.screenshot({path:`artifacts/cloudtop-hotel/${name}.png`}); }

test('lobby shields gameplay, opens rules, saves purchases and resumes after reload',async({page})=>{
  const errors=[]; page.on('pageerror',e=>errors.push(e.message)); await open(page);
  await expect(page.locator('#home-title')).toBeFocused(); await page.keyboard.press('1'); await expect(page.locator('#coins')).toHaveText('100');
  await page.locator('#lobby-rules').click(); await expect(page.locator('#rules-dialog')).toBeVisible(); await page.keyboard.press('Escape'); await expect(page.locator('#lobby-rules')).toBeFocused();
  await page.locator('#lobby-play').click(); await page.locator('#offers .offer-card').first().click();
  if(await page.locator('#choice-dialog').isVisible()) await page.locator('#room-choices button').first().click();
  const floors=await page.locator('#height').textContent(), coins=await page.locator('#coins').textContent();
  await page.reload(); await page.locator('#lobby-resume').click();
  await expect(page.locator('#coins')).toHaveText(coins); await expect(page.locator('#height')).toHaveText(floors);
  await page.locator('#menu-open').click(); await page.locator('#lobby-open').click(); await expect(page.locator('#home-title')).toBeFocused();
  await page.locator('#lobby-board').click(); await expect(page.locator('.leaderboard-row')).toHaveCount(12); await page.keyboard.press('Escape'); await expect(page.locator('#home-page')).toBeVisible();
  expect(errors).toEqual([]);
});
test('each entrance is animated, then motion can be disabled without hiding controls',async({page})=>{
  await open(page,false);
  await page.locator('#lobby-board').click(); await page.locator('#board-back').click();
  const choreography=await page.locator('#home-page').evaluate(el=>[...el.querySelectorAll('[data-enter]')].filter(e=>!e.hidden&&e.getClientRects().length).map(e=>({animation:e.getAnimations().length,delay:e.dataset.delay})));
  expect(choreography.filter(e=>e.animation).length).toBeGreaterThan(10);
  await page.locator('#lobby-motion').click();
  expect(await page.locator('#frontdesk').evaluate(el=>el.getAnimations({subtree:true}).length)).toBe(0);
  await page.locator('#lobby-board').click(); await expect(page.locator('.leaderboard-row')).toHaveCount(12);
  expect(await page.locator('#frontdesk').evaluate(el=>el.getAnimations({subtree:true}).length)).toBe(0);
  await page.reload(); await expect(page.locator('#lobby-motion')).toHaveAttribute('aria-pressed','true');
});
test('shared leaderboard handles failure, retry, empty personal history and tab races',async({page})=>{
  await open(page); await page.unroute(API); await page.route(API,route=>route.fulfill({status:503,json:{error:'Offline'}}));
  await page.locator('#lobby-board').click(); await expect(page.locator('#empty-title')).toContainText('away');
  await page.locator('#board-personal').click(); await expect(page.locator('#empty-title')).toHaveText('Your story starts here.');
  await page.unroute(API); await page.route(API,async route=>{await new Promise(resolve=>setTimeout(resolve,200)); await route.fulfill({json:{entries}}).catch(()=>{});});
  await page.locator('#board-everyone').click(); await page.locator('#board-personal').click(); await page.waitForTimeout(250); await expect(page.locator('#empty-title')).toHaveText('Your story starts here.');
  await page.locator('#board-everyone').click(); await expect(page.locator('.leaderboard-row')).toHaveCount(12);
});
test('completed hotel is saved and submitted with replay evidence, with retry and no duplicate submission',async({page})=>{
  await open(page); await page.locator('#lobby-play').click(); const state=createGame('lobby-test');
  const moves=[];
  while(state.phase==='picking') {
    const i=state.offer.findIndex(c=>c.price<=state.cash), suit=state.offer[i].type==='choice'?choiceSuits(state)[0]:null;
    await page.locator(`#offers [data-offer-index="${i}"]`).click();
    if(suit) await page.locator(`#room-choices [data-suit="${suit}"]`).click();
    moves.push([i,suit]); pick(state,i,suit); advanceDeal(state);
  }
  await page.locator('#roof-card').click(); await page.locator('#ending-board').click();
  await expect(page.locator('#score-summary')).toContainText(`${state.links.length} floors`);
  let submissions=0; await page.unroute(API); await page.route(API,async route=>{
    if(route.request().method()==='GET') return route.fulfill({json:{entries}});
    submissions++; expect(route.request().postDataJSON()).toEqual({version:SCORE_VERSION,name:'Cloud Keeper',seed:'lobby-test',moves});
    if(submissions===1) return route.fulfill({status:503,json:{error:'Please try again.'}});
    return route.fulfill({json:{entry:{id:'shared-id',name:'Cloud Keeper'},rank:1,entries}});
  });
  await page.locator('#innkeeper-name').fill('Cloud Keeper'); await page.locator('#score-submit').click(); await expect(page.locator('#score-message')).toHaveText('Please try again.');
  await page.locator('#score-submit').click(); await expect(page.locator('#score-message')).toContainText('#1'); await expect(page.locator('#score-submit')).toBeDisabled();
  await page.locator('#board-personal').click(); await expect(page.locator('.leaderboard-row')).toHaveCount(1); await expect(page.locator('.rank-score')).toContainText(String(state.links.length));
  await page.locator('#board-back').click(); await expect(page.locator('#lobby-resume')).toBeHidden();
  await page.reload(); await page.locator('#lobby-board').click(); await page.locator('#board-personal').click(); await expect(page.locator('.leaderboard-row')).toHaveCount(1); await expect(page.locator('#lobby-resume')).toBeHidden(); expect(submissions).toBe(2);
});
test('lobby and guestbook fit desktop, phone, small phone and landscape with reachable controls',async({page})=>{
  await open(page);
  for(const [name,width,height] of [['desktop',1440,900],['mobile',390,844],['small',320,568],['landscape',844,390]]) {
    await page.setViewportSize({width,height}); await shot(page,`lobby-${name}`);
    await expect(page.locator('#lobby-play')).toBeInViewport(); await page.locator('#lobby-board').click(); await expect(page.locator('.leaderboard-row')).toHaveCount(12);
    await shot(page,`guestbook-${name}`);
    const dims=await page.locator('#frontdesk').evaluate(el=>({scroll:el.scrollWidth,width:el.clientWidth,buttons:[...el.querySelectorAll('button,input')].filter(e=>e.getClientRects().length).map(e=>({left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right}))}));
    expect(dims.scroll).toBeLessThanOrEqual(dims.width); for(const b of dims.buttons){expect(b.left).toBeGreaterThanOrEqual(0);expect(b.right).toBeLessThanOrEqual(width);}
    await page.locator('#board-back').click();
  }
});
