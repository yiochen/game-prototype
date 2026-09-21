import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { createGame, pick, advanceDeal, finished, segments, choiceSuits } from '../engine.js';
const ROOT = '/prototypes/cloudtop-hotel/';
const card = (page, i) => page.locator(`#offers [data-offer-index="${i}"]`);
async function open(page, seed, reduced = true) {
  await page.emulateMedia({ reducedMotion: reduced ? 'reduce' : 'no-preference' });
  await page.goto(`${ROOT}?seed=${seed}`); await expect(page.locator('#world')).toHaveAttribute('data-ready', 'true');
}
async function buy(page, i, suit) {
  await card(page, i).click();
  if (await page.locator('#choice-dialog').isVisible()) await page.locator(suit ? `#room-choices [data-suit="${suit}"]` : '#room-choices button').first().click();
}
async function screenshot(page, name) { await mkdir('artifacts/cloudtop-hotel', { recursive: true }); await page.screenshot({ path: `artifacts/cloudtop-hotel/${name}.png` }); }
async function screenFits(page) {
  const layout = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, sw: document.documentElement.scrollWidth, sh: document.documentElement.scrollHeight, cards: [...document.querySelectorAll('.offer-card, footer button, .header-actions button, .ending:not([hidden]) button')].filter(e => e.getClientRects().length).map(e => ({ text: e.textContent, r: e.getBoundingClientRect().toJSON(), overflow: e.scrollHeight > e.clientHeight + 2 })) }));
  expect(layout.sw).toBeLessThanOrEqual(layout.width); expect(layout.sh).toBeLessThanOrEqual(layout.height);
  for (const { r, text, overflow } of layout.cards) { expect(r.bottom, text).toBeLessThanOrEqual(layout.height); expect(r.right, text).toBeLessThanOrEqual(layout.width); expect(r.top, text).toBeGreaterThanOrEqual(0); expect(r.left, text).toBeGreaterThanOrEqual(0); expect(overflow, text).toBe(false); }
}

test('catalog opens an independent Phaser hotel with loaded art', async ({ page }) => {
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto('/'); await page.getByRole('link', { name: /Cloudtop Hotel/ }).click();
  await expect(page.locator('#world')).toHaveAttribute('data-ready', 'true');
  await expect(page.locator('#world canvas')).toHaveAttribute('data-roof', 'false');
  await expect(page.locator('#offers button')).toHaveCount(3);
  expect(await page.locator('.offer-card img').evaluateAll(images => images.every(i => i.complete && i.naturalWidth))).toBe(true);
  await screenshot(page, 'opening-desktop'); expect(errors).toEqual([]);
});

test('full run matches engine, registers neighborhoods and adds roof only after completion', async ({ page }) => {
  const errors = []; page.on('pageerror', e => errors.push(e.message)); await open(page, 1); const s = createGame(1);
  while (!finished(s)) {
    await expect(page.locator('#world canvas')).toHaveAttribute('data-roof', 'false');
    const i = s.offer.findIndex(c => c.price <= s.cash), selected = s.offer[i].type === 'choice' ? choiceSuits(s)[0] : undefined;
    const previous = s.links.map(l => l.suit); await buy(page, i, selected); pick(s, i, selected); advanceDeal(s);
    expect(s.links.slice(0, previous.length).map(l => l.suit)).toEqual(previous);
    expect(await page.locator('#floor-record li').evaluateAll(items => items.map(l => l.dataset.type))).toEqual(s.links.map(l => l.suit));
    await expect(page.locator('#height')).toHaveText(String(s.links.length)); await expect(page.locator('#coins')).toHaveText(String(s.cash));
    await expect(page.locator('#world canvas')).toHaveAttribute('data-floor-count', String(s.links.length));
    for (const type of ['bunny', 'frog', 'cat']) await expect(page.locator(`.dock-chip.${type} .dock-count`)).toHaveText(String(segments(s, type).length));
  }
  await expect(page.locator('#world canvas')).toHaveAttribute('data-roof', 'true'); await expect(page.locator('#ending')).toBeVisible(); await expect(page.locator('#offers')).toBeHidden();
  await screenshot(page, 'completed-hotel');
  const overviewCount = await page.locator('#world canvas').evaluate(c => JSON.parse(c.dataset.visibleFloors).length);
  await page.locator('#overview').click();
  await expect.poll(() => page.locator('#world canvas').evaluate(c => JSON.parse(c.dataset.visibleFloors).length)).toBeLessThan(overviewCount);
  await expect(page.locator('#world canvas')).toHaveAttribute('data-roof', 'true');
  await screenshot(page, 'completed-closeup');
  for (const size of [{ width: 320, height: 480 }, { width: 844, height: 390 }]) { await page.setViewportSize(size); await screenFits(page); }
  await page.locator('#replay').click(); await expect(page.locator('#height')).toHaveText('0'); await expect(page.locator('#world canvas')).toHaveAttribute('data-roof', 'false'); expect(errors).toEqual([]);
});

test('Mosaic prints its order, appends it exactly, and closes the streak', async ({ page }) => {
  await open(page, 30); await buy(page, 1); await expect(page.locator('#strategy-status')).toContainText('Streak ready');
  const s = createGame(30); pick(s, 1); advanceDeal(s); const pattern = s.offer[0].sequence;
  await expect(card(page, 0)).toContainText('Mosaic'); await expect(card(page, 0)).toContainText('Ends your streak');
  await buy(page, 0); expect(await page.locator('#floor-record li').evaluateAll(items => items.map(l => l.dataset.type))).toEqual(pattern);
  await expect(page.locator('#height')).toHaveText('3'); await expect(page.locator('#strategy-status')).toBeHidden(); await screenshot(page, 'mosaic-hotel');
});

test('room choice can cancel, respects Type Lock, and stacks Neighborhood Streak', async ({ page }) => {
  await open(page, 0); await card(page, 2).click(); await expect(page.locator('#room-choices button')).toHaveCount(3);
  await page.keyboard.press('1'); await expect(page.locator('#coins')).toHaveText('100'); await page.keyboard.press('Escape'); await expect(card(page, 2)).toBeFocused();
  await buy(page, 2, 'frog'); await expect(page.locator('#floor-record li')).toHaveAttribute('data-type', 'frog');
  await open(page, 472); await buy(page, 0); await buy(page, 0); await expect(page.locator('#strategy-status')).toContainText('Cat lock · 3 shops');
  await card(page, 0).click(); await expect(page.locator('#room-choices button')).toHaveCount(1); await expect(page.locator('#room-choices button')).toContainText('+3 floors');
  await screenshot(page, 'choice-dialog'); await page.locator('#room-choices button').click(); await expect(page.locator('#strategy-status')).toContainText('2 shops');
  await buy(page, 2); await buy(page, 0); await expect(page.locator('#strategy-status')).not.toContainText('lock'); await expect(page.locator('#height')).toHaveText('13');
  await page.locator('#workshop-open').click(); await expect(page.locator('#installed')).toContainText('next +5'); await page.keyboard.press('Escape');
});

test('Copycat and Balloon Call append their outputs without changing earlier floors', async ({ page }) => {
  await open(page, 0); for (const i of [0,1,1,1,1,0,1,1,1,0,1]) await buy(page, i);
  const before = await page.locator('#floor-record li').evaluateAll(items => items.map(l => l.dataset.type));
  await expect(card(page, 1)).toContainText('Copycat'); await buy(page, 1);
  expect(await page.locator('#floor-record li').evaluateAll(items => items.map(l => l.dataset.type))).toEqual([...before,...Array(4).fill('cat')]);
  await open(page, 2); for (const i of [2,0,0,2,0,0,0,1,0]) await buy(page, i);
  await expect(card(page, 0)).toContainText('Balloon Call'); await expect(card(page, 0).locator('.card-effect')).toHaveText('+4'); await buy(page, 0);
  await expect(page.locator('#height')).toHaveText('29'); await screenshot(page, 'tall-hotel');
});

test('real delivery animates once, skips without rerolling, and replay cancels pending output', async ({ page }) => {
  await open(page, 15, false); await buy(page, 1); await expect(page.locator('#world')).toHaveAttribute('data-state', 'resolving'); await page.locator('#reveal-now').click();
  await buy(page, 1); await expect(page.locator('#status')).toHaveText('Unwrapping your surprise…'); await expect(page.locator('#coins')).toHaveText('87');
  await page.keyboard.press('2'); await expect(page.locator('#coins')).toHaveText('87'); await screenshot(page, 'parcel-arrival');
  await expect(page.locator('#world')).toHaveAttribute('data-state', 'picking', { timeout: 6000 }); await expect(page.locator('#height')).toHaveText('3');
  const output = await page.locator('#floor-record').textContent(); await page.locator('#replay').click(); await buy(page, 1); await page.locator('#reveal-now').click(); await buy(page, 1); await page.locator('#reveal-now').click();
  expect(await page.locator('#floor-record').textContent()).toBe(output);
  await page.locator('#replay').click(); await buy(page, 1); await page.locator('#replay').click();
  await expect(page.locator('#world')).toHaveAttribute('data-state', 'picking'); await expect(page.locator('#height')).toHaveText('0'); await expect(page.locator('#coins')).toHaveText('100');
  await page.waitForTimeout(900); await expect(page.locator('#height')).toHaveText('0');
});

test('controls and strategy effects fit phone, short phone, desktop and landscape', async ({ page }) => {
  await open(page, 472); await buy(page, 0); await buy(page, 0);
  for (const size of [{width:320,height:480},{width:390,height:844},{width:375,height:667},{width:1280,height:900},{width:844,height:390},{width:667,height:375}]) {
    await page.setViewportSize(size); await screenFits(page);
    await expect.poll(() => page.locator('#world canvas').evaluate(c => c.width)).toBe(await page.locator('#world').evaluate(e => Math.floor(e.clientWidth)));
    await screenshot(page, `layout-${size.width}x${size.height}`);
  }
  await page.locator('#rules-open').click(); const coins = await page.locator('#coins').textContent(); await page.keyboard.press('1'); await expect(page.locator('#coins')).toHaveText(coins); await expect(page.locator('#balance-table tr')).toHaveCount(14);
  await page.keyboard.press('Escape'); await expect(page.locator('#rules-open')).toBeFocused();
});
