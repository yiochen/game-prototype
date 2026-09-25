import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
const ROOT = '/prototypes/cloudtop-hotel/';
async function open(page, reduced = true) {
  await page.emulateMedia({reducedMotion:reduced?'reduce':'no-preference'});
  await page.route('**/api/cloudtop-hotel/leaderboard',route=>route.fulfill({json:{entries:[{id:'one',name:'Paper Pilot',floors:72,neighborhoods:12,coins:0}]}}));
  await page.goto(ROOT+'?seed=paper-test'); await expect(page.locator('#world')).toHaveAttribute('data-ready','true');
}
async function surfaces(page, selector) {
  const styles = await page.locator(selector).evaluateAll(items=>items.map(el=>{
    const skin=getComputedStyle(el,'::before');
    return {source:skin.borderImageSource,slice:skin.borderImageSlice,corners:skin.borderImageWidth,background:getComputedStyle(el).backgroundImage};
  }));
  expect(styles.length).toBeGreaterThan(0);
  for(const style of styles) { expect(style.source).toContain('origami-paper'); expect(style.slice).toBe('25% fill'); expect(style.background).toBe('none'); }
  return styles;
}
test('one nine-slice material covers title, leaderboard, gameplay and every popup',async({page})=>{
  await open(page); await surfaces(page,'.hanging-sign,#lobby-play,#lobby-board');
  await page.locator('#lobby-board').click(); await expect(page.locator('.leaderboard-row')).toHaveCount(1); await surfaces(page,'.guestbook-paper,.leaderboard-row,.board-tabs button');
  await page.locator('#board-back').click(); await page.locator('#lobby-play').click(); await surfaces(page,'.stat,.dock-chip,#offers .offer-card,#camera-toggle');
  await page.locator('#menu-open').click(); await surfaces(page,'#menu-dialog,#menu-dialog button');
  await page.locator('#rules-open').click(); await surfaces(page,'#rules-dialog'); await page.keyboard.press('Escape');
  await page.locator('#workshop-open').click(); await surfaces(page,'#workshop-dialog'); await page.keyboard.press('Escape'); await page.keyboard.press('Escape');
  await page.locator('#offers .card-help').first().click(); await surfaces(page,'#effect-dialog'); await page.keyboard.press('Escape');
  await page.locator('#height-info').click(); await surfaces(page,'#hud-dialog'); await page.keyboard.press('Escape');
  // Choice uses the same material even before a seed happens to offer it.
  await surfaces(page,'#choice-dialog');
});
test('paper corners stay fixed within a breakpoint and content fits a small phone',async({page})=>{
  await page.setViewportSize({width:1280,height:850}); await open(page);
  const first=(await surfaces(page,'.hanging-sign'))[0];
  await page.setViewportSize({width:1600,height:950}); const second=(await surfaces(page,'.hanging-sign'))[0]; expect(second.corners).toBe(first.corners);
  for(const [width,height] of [[390,844],[320,480],[844,390]]) {
    await page.setViewportSize({width,height}); await expect(page.locator('#lobby-play')).toBeInViewport();
    await page.locator('#lobby-board').click(); await expect(page.locator('.leaderboard-row')).toBeVisible();
    const fit=await page.locator('#frontdesk').evaluate(el=>({width:el.clientWidth,scroll:el.scrollWidth})); expect(fit.scroll).toBeLessThanOrEqual(fit.width);
    await page.locator('#board-back').click();
  }
});
test('real hinged leaves unfold and clean up on close, navigation, and reduced motion',async({page})=>{
  await open(page,false); await page.locator('#lobby-rules').click();
  const dialog=page.locator('#rules-dialog'); await expect(dialog).toHaveAttribute('data-folding','y');
  const hinges=await dialog.locator(':scope > .paper-fold-rig .paper-fold-leaf').evaluateAll(leaves=>leaves.map(el=>({origin:getComputedStyle(el).transformOrigin,frames:el.getAnimations()[0]?.effect.getKeyframes().map(f=>f.transform)})));
  expect(hinges).toHaveLength(2); expect(hinges[0].origin).not.toBe(hinges[1].origin); expect(hinges[0].frames[0]).toContain('rotateX');
  await page.keyboard.press('Escape'); await expect(dialog.locator('.paper-fold-rig')).toHaveCount(0);
  await page.locator('#lobby-board').click(); await expect(page.locator('.guestbook-paper')).toHaveAttribute('data-folding','x');
  await page.locator('#board-back').click(); await expect(page.locator('#guestbook-page .paper-fold-rig')).toHaveCount(0);
  await page.locator('#lobby-motion').click(); await expect(page.locator('.paper-fold-rig')).toHaveCount(0);
  await page.locator('#lobby-rules').click(); await expect(dialog).toBeVisible(); await expect(dialog.locator('.paper-fold-rig')).toHaveCount(0); await page.keyboard.press('Escape');
  await page.locator('#lobby-play').click(); await page.locator('#offers .offer-card').first().click();
  if(await page.locator('#choice-dialog').isVisible()) await page.locator('#room-choices button').first().click();
  await expect(page.locator('#coins')).not.toHaveText('100');
});
test('unfold screenshot shows actual creased paper leaves before the text arrives',async({page})=>{
  await page.setViewportSize({width:1100,height:800}); await open(page,false); await page.locator('#lobby-rules').click();
  await page.locator('#rules-dialog').evaluate(el=>{
    for(const animation of el.getAnimations({subtree:true})) { animation.pause(); animation.currentTime=120; }
  });
  await mkdir('artifacts/origami',{recursive:true}); await page.screenshot({path:'artifacts/origami/unfold-midpoint.png'});
  await page.keyboard.press('Escape'); await expect(page.locator('#rules-dialog .paper-fold-rig')).toHaveCount(0);
});
