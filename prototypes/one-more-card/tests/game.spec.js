import {test,expect} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
import {createGame,pick,advanceDeal,chain,segments,finished,BALANCE} from '../engine.js';
const card=(p,i)=>p.locator(`#offer [data-offer-index="${i}"]`);
async function replay(p){await p.keyboard.press('End');await p.locator('#replay').click();}
async function buy(p,i){await card(p,i).click();}

test('installed upgrades replace levels and do not add score themselves',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/prototypes/one-more-card/?seed=3');
 await expect(page.locator('#cash')).toHaveText('$100');await expect(card(page,0)).toContainText('0 → 1');
 await buy(page,0);await expect(page.locator('#cash')).toHaveText('$91');await expect(page.locator('#score')).toHaveText('0');
 await expect(page.locator('#installed')).toContainText('Assembler Lv1 · +1');await expect(card(page,0)).toContainText('1 → 2');
 await buy(page,0);await expect(page.locator('#installed .upgrade-chip')).toHaveCount(1);await expect(page.locator('#installed')).toContainText('Assembler Lv2 · +2');
 await expect(page.locator('#cash')).toHaveText('$79');await expect(page.locator('#score')).toHaveText('0');
 await expect(page.locator('[data-card-id="reactor:assembler:1"]')).toHaveCount(0);
});

test('Overgrow previews its automatic target and needs only one click',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/prototypes/one-more-card/?seed=3');await buy(page,2);
 await expect(page.locator('#cash')).toHaveText('$97');await expect(card(page,0)).toContainText('Overgrow');await expect(card(page,0)).toContainText('Moon 1 → 2');
 await buy(page,0);await expect(page.locator('#cash')).toHaveText('$92');await expect(page.locator('#score')).toHaveText('2');
 await expect(page.locator('#reveal')).toContainText('Longest segment: Moon 1 → 2');await expect(page.locator('#hand .sequence-link')).toHaveCount(2);
 await expect(page.locator('#target-panel')).toHaveCount(0);
});

test('Mystery has suspense, uses explicit Stabilizer odds, blocks duplicate purchases and skips deterministically',async({page})=>{
 await page.clock.install();await page.goto('/prototypes/one-more-card/?seed=15');await buy(page,1);await page.clock.runFor(280);
 await expect(page.locator('#installed')).toContainText('8 links: 19%');await expect(card(page,1)).toContainText('Odds 36/45/19%');
 await buy(page,1);await expect(page.locator('#cash')).toHaveText('$87');await expect(page.locator('#status')).toHaveText('Rolling your Mystery…');
 await expect(page.locator('#score')).toHaveText('0');await page.keyboard.press('2');await expect(page.locator('#cash')).toHaveText('$87');
 await page.clock.runFor(650);await expect(page.locator('#reveal')).toContainText('Rolled 3');await expect(page.locator('#score')).toHaveText('3');
 const cards=await page.locator('#hand').textContent();
 await replay(page);await buy(page,1);await page.locator('#finish-reaction').click();await buy(page,1);await page.locator('#finish-reaction').click();
 expect(await page.locator('#hand').textContent()).toBe(cards);await expect(page.locator('#cash')).toHaveText('$87');
});

test('Wealth refund is previewed, applies once, and removes active Rebate from offers',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/prototypes/one-more-card/?seed=2');await buy(page,0);
 await expect(page.locator('#installed')).toContainText('Rebate · $2 × 3 left');await expect(card(page,0)).toContainText('$91 left · $2 refund');
 await expect(page.locator('[data-card-id="wealth:rebate"]')).toHaveCount(0);await buy(page,0);
 await expect(page.locator('#cash')).toHaveText('$91');await expect(page.locator('#spent')).toHaveText('$11 spent · $2 refunded');
 await expect(page.locator('#installed')).toContainText('× 2 left');await expect(page.locator('#score')).toHaveText('3');
});

test('replay cancels pending Mystery reveals and resets automatic actions',async({page})=>{
 await page.clock.install();await page.goto('/prototypes/one-more-card/?seed=15');await buy(page,1);await page.clock.runFor(280);await buy(page,1);await replay(page);await page.clock.runFor(2000);
 await expect(page.locator('#cash')).toHaveText('$100');await expect(page.locator('#score')).toHaveText('0');await expect(page.locator('#hand .sequence-link')).toHaveCount(0);
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/prototypes/one-more-card/?seed=3');await buy(page,2);await buy(page,0);await replay(page);
 await expect(page.locator('#target-panel')).toHaveCount(0);await expect(page.locator('#cash')).toHaveText('$100');
});

test('full budget run, responsive layout, affordability and visible balance table',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:390,height:844});
 await page.goto('/prototypes/one-more-card/?seed=3');const s=createGame(3);
 await mkdir('artifacts/one-more-card',{recursive:true});await page.screenshot({path:'artifacts/one-more-card/engine-mobile.png',fullPage:true});
 let disabledCount=0;
 while(!finished(s)){
  const disabled=s.offer.findIndex(c=>c.price>s.cash);
  if(disabled>=0){disabledCount++;await expect(card(page,disabled)).toBeDisabled();await page.keyboard.press(String(disabled+1));await expect(page.locator('#cash')).toHaveText(`$${s.cash}`);}
  const i=s.offer.findIndex(c=>c.price<=s.cash);
  await buy(page,i);
  pick(s,i);advanceDeal(s);expect(await page.locator('#hand .sequence-link').evaluateAll(ls=>ls.map(l=>l.dataset.suit))).toEqual(s.links.map(l=>l.suit));await expect(page.locator('#score')).toHaveText(String(chain(s)));await expect(page.locator('#cash')).toHaveText(`$${s.cash}`);
 }
 expect(disabledCount).toBeGreaterThan(0);await expect(page.locator('#finished')).toHaveText(`${chain(s)} links · $${s.cash} left`);
 await expect(page.locator('#hand .link')).toHaveCount(chain(s));await expect(page.locator('#offer')).toBeHidden();
 for(const width of [320,390,1280]){await page.setViewportSize({width,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);}
 await page.screenshot({path:'artifacts/one-more-card/engine-desktop.png',fullPage:true});
 await page.locator('#rules-open').click();await expect(page.locator('#balance-body tr')).toHaveCount(11);await expect(page.locator('#weights')).toContainText(`base ${BALANCE.families.base}`);
 await page.getByRole('button',{name:'Close rules'}).click();await replay(page);await expect(page.locator('#cash')).toHaveText('$100');expect(errors).toEqual([]);
});

async function expectScreenFit(page) {
 const measurements=await page.evaluate(()=>{
  const controls=[...document.querySelectorAll('#offer:not([hidden]) .offer-card, footer button, #target-panel:not([hidden]) button:not([hidden])')].filter(e=>e.getClientRects().length);
  return {width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight,
   footerTop:document.querySelector('footer').getBoundingClientRect().top,shopBottom:document.querySelector('.shop-panel').getBoundingClientRect().bottom,
   controls:controls.map(e=>{const r=e.getBoundingClientRect();return {text:e.textContent,top:r.top,bottom:r.bottom,left:r.left,right:r.right,overflow:e.scrollHeight>e.clientHeight+2};})};
 });
 expect(measurements.shopBottom).toBeLessThanOrEqual(measurements.footerTop);
 expect(await page.locator('#hand').evaluate(e=>e.hidden || (e.scrollHeight<=e.clientHeight+1 && e.scrollWidth<=e.clientWidth+1))).toBe(true);
 expect(measurements.scrollWidth).toBeLessThanOrEqual(measurements.width);
 expect(measurements.scrollHeight).toBeLessThanOrEqual(measurements.height);
 for(const r of measurements.controls){expect(r.top,r.text).toBeGreaterThanOrEqual(0);expect(r.bottom,r.text).toBeLessThanOrEqual(measurements.height);expect(r.left,r.text).toBeGreaterThanOrEqual(0);expect(r.right,r.text).toBeLessThanOrEqual(measurements.width);expect(r.overflow,r.text).toBe(false);}
}

test('one-screen layout keeps controls visible on phones, desktop and landscape',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/prototypes/one-more-card/?seed=0');
 for(const size of [{width:320,height:480},{width:375,height:500},{width:320,height:568},{width:390,height:844},{width:1280,height:800},{width:844,height:390},{width:667,height:375}]){
  await page.setViewportSize(size);await expectScreenFit(page);
  await page.mouse.wheel(0,800);expect(await page.evaluate(()=>scrollY)).toBe(0);
 }
 await page.setViewportSize({width:320,height:568});
 for(const i of [0,1,1,1,1,0,1,1,0,0,1]){await buy(page,i);await expectScreenFit(page);}
 await expect(page.locator('#collection-pager')).toBeHidden();await expect(page.locator('#hand .sequence-link[hidden]')).toHaveCount(0);await expect(page.locator('#hand .chain-card')).toHaveCount(0);await expectScreenFit(page);
 await page.locator('#show-engine').click();await expect(page.locator('#installed')).toBeVisible();await expect(page.locator('#hand')).toBeHidden();
 await expectScreenFit(page);await page.locator('#show-chain').click();
 await buy(page,1);await expectScreenFit(page);await expect(page.locator('#target-panel')).toHaveCount(0);
 await page.screenshot({path:'artifacts/one-more-card/one-screen-small-phone.png'});
 const cash=await page.locator('#cash').textContent();await page.locator('#rules-open').click();await page.keyboard.press('1');await expect(page.locator('#cash')).toHaveText(cash);
 await page.keyboard.press('Escape');await expect(page.locator('#rules-dialog')).not.toBeVisible();await expect(page.locator('#rules-open')).toBeFocused();
 await page.setViewportSize({width:844,height:390});await expectScreenFit(page);await page.screenshot({path:'artifacts/one-more-card/one-screen-landscape.png'});
});

test('level-three Stabilizer odds remain explicit and fit a short phone screen',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:320,height:480});await page.goto('/prototypes/one-more-card/?seed=396');
 for(const i of [1,2,0])await buy(page,i);
 await expect(page.locator('#installed')).toContainText('Stabilizer Lv3 · 8 links: 34.39%');
 await expect(card(page,0)).toContainText('Odds 12.96/52.65/34.39%');await expectScreenFit(page);
 await page.screenshot({path:'artifacts/one-more-card/stabilizer-odds-phone.png'});
});
