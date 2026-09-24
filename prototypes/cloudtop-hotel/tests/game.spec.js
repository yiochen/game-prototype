import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { createGame, pick, advanceDeal, finished, segments, choiceSuits } from '../engine.js';
const ROOT = '/prototypes/cloudtop-hotel/';
const card = (page, i) => page.locator(`#offers [data-offer-index="${i}"]`);
const help = (page, i) => page.locator(`#offers [data-offer-help="${i}"]`);
async function open(page, seed, reduced = true) {
  await page.emulateMedia({ reducedMotion: reduced ? 'reduce' : 'no-preference' });
  await page.goto(`${ROOT}?seed=${seed}`); await expect(page.locator('#world')).toHaveAttribute('data-ready', 'true');
}
async function buy(page, i, suit) {
  await card(page, i).click();
  if (await page.locator('#choice-dialog').isVisible()) await page.locator(suit ? `#room-choices [data-suit="${suit}"]` : '#room-choices button').first().click();
}
async function control(page, id) {
  if (!await page.locator('#menu-dialog').isVisible()) await page.locator('#menu-open').click();
  await page.locator('#' + id).click();
}
async function screenshot(page, name) { await mkdir('artifacts/cloudtop-hotel', { recursive: true }); await page.screenshot({ path: `artifacts/cloudtop-hotel/${name}.png` }); }
async function paperLoads(page, selector, variable) {
  const surfaces = await page.locator(selector).evaluateAll(async (items, variable) => {
    const source = getComputedStyle(document.documentElement).getPropertyValue(variable).trim();
    const url = source.match(/url\(["']?(.*?)["']?\)/)?.[1];
    if (!url) return { loaded: false, applied: [] };
    const image = new Image(); image.src = url; await image.decode();
    return { loaded: image.naturalWidth > 0, applied: items.map(item =>
      [null, '::before', '::after'].some(pseudo => getComputedStyle(item, pseudo).backgroundImage.includes(url))) };
  }, variable);
  expect(surfaces.loaded).toBe(true); expect(surfaces.applied.length).toBeGreaterThan(0);
  expect(surfaces.applied.every(Boolean)).toBe(true);
}
async function screenFits(page) {
  const layout = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, sw: document.documentElement.scrollWidth, sh: document.documentElement.scrollHeight, cards: [...document.querySelectorAll('.offer-card, .card-help, #menu-open, dialog[open] button')].filter(e => e.getClientRects().length).map(e => ({ text: e.textContent, r: e.getBoundingClientRect().toJSON(), overflow: e.scrollHeight > e.clientHeight + 2 })) }));
  expect(layout.sw).toBeLessThanOrEqual(layout.width); expect(layout.sh).toBeLessThanOrEqual(layout.height);
  for (const { r, text, overflow } of layout.cards) { expect(r.bottom, text).toBeLessThanOrEqual(layout.height); expect(r.right, text).toBeLessThanOrEqual(layout.width); expect(r.top, text).toBeGreaterThanOrEqual(0); expect(r.left, text).toBeGreaterThanOrEqual(0); expect(overflow, text).toBe(false); }
}

test('catalog opens an independent Phaser hotel with loaded art', async ({ page }) => {
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto('/'); await page.getByRole('link', { name: /Cloudtop Hotel/ }).click();
  await expect(page.locator('#world')).toHaveAttribute('data-ready', 'true');
  await expect(page.locator('#world canvas')).toHaveAttribute('data-roof', 'false');
  await expect(page.locator('#offers .offer-card')).toHaveCount(3);
  await expect(page.locator('#offers .card-help')).toHaveCount(3);
  await expect.poll(() => page.locator('.offer-card img').evaluateAll(images => images.every(i => i.complete && i.naturalWidth))).toBe(true);
  await expect(page.locator('.offer-card .card-art').first()).toBeVisible();
  await paperLoads(page, '#offers .offer-card', '--card-paper');
  await expect(page.locator('#world canvas')).toHaveAttribute('data-sprite-frames', /actors:/);
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
  await control(page, 'overview');
  await expect.poll(() => page.locator('#world canvas').evaluate(c => JSON.parse(c.dataset.visibleFloors).length)).toBeLessThan(overviewCount);
  await expect(page.locator('#world canvas')).toHaveAttribute('data-roof', 'true');
  await screenshot(page, 'completed-closeup');
  for (const size of [{ width: 320, height: 480 }, { width: 844, height: 390 }]) { await page.setViewportSize(size); await screenFits(page); }
  await control(page, 'replay'); await expect(page.locator('#height')).toHaveText('0'); await expect(page.locator('#world canvas')).toHaveAttribute('data-roof', 'false'); expect(errors).toEqual([]);
});

test('Mosaic prints its order, appends it exactly, and closes the streak', async ({ page }) => {
  await open(page, 30); await buy(page, 1); await expect(page.locator('#strategy-status')).toContainText('Streak ready');
  const s = createGame(30); pick(s, 1); advanceDeal(s); const pattern = s.offer[0].sequence;
  await expect(card(page, 0)).toContainText('Mosaic');
  await help(page, 0).click(); await expect(page.locator('#effect-dialog')).toContainText(/Ends (your streak|Neighborhood Streak)/);
  await page.locator('#effect-close').click();
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
  await control(page, 'workshop-open'); await expect(page.locator('#installed')).toContainText('next +5'); await page.keyboard.press('Escape');
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
  await open(page, 15, false); await buy(page, 1); await expect(page.locator('#world')).toHaveAttribute('data-state', 'launching'); await control(page, 'reveal-now');
  await buy(page, 1); await expect(page.locator('#status')).toHaveText('Unwrapping your surprise…'); await expect(page.locator('#coins')).toHaveText('87');
  await page.keyboard.press('2'); await expect(page.locator('#coins')).toHaveText('87'); await screenshot(page, 'parcel-arrival');
  await expect(page.locator('#world')).toHaveAttribute('data-state', 'picking', { timeout: 6000 }); await expect(page.locator('#height')).toHaveText('3');
  const output = await page.locator('#floor-record').textContent(); await control(page, 'replay'); await buy(page, 1); await control(page, 'reveal-now'); await buy(page, 1); await control(page, 'reveal-now');
  expect(await page.locator('#floor-record').textContent()).toBe(output);
  await control(page, 'replay'); await buy(page, 1); await control(page, 'replay');
  await expect(page.locator('#world')).toHaveAttribute('data-state', 'picking'); await expect(page.locator('#height')).toHaveText('0'); await expect(page.locator('#coins')).toHaveText('100');
  await page.waitForTimeout(1800); await expect(page.locator('#height')).toHaveText('0'); await expect(page.locator('#coins')).toHaveText('100');
});

test('controls and strategy effects fit phone, short phone, desktop and landscape', async ({ page }) => {
  await open(page, 472); await buy(page, 0); await buy(page, 0);
  for (const size of [{width:320,height:480},{width:390,height:844},{width:375,height:667},{width:1280,height:900},{width:844,height:390},{width:667,height:375}]) {
    await page.setViewportSize(size); await screenFits(page);
    await expect.poll(() => page.locator('#world canvas').evaluate(c => c.width)).toBe(await page.locator('#world').evaluate(e => Math.floor(e.clientWidth)));
    await screenshot(page, `layout-${size.width}x${size.height}`);
  }
  await control(page, 'rules-open'); const coins = await page.locator('#coins').textContent(); await page.keyboard.press('1'); await expect(page.locator('#coins')).toHaveText(coins); await expect(page.locator('#balance-table tr')).toHaveCount(14);
  await page.keyboard.press('Escape'); await expect(page.locator('#rules-open')).toBeFocused();
});

test('Copycat plays its generated poses and unfolding frames; reduced motion freezes idle sheets', async ({ page }) => {
  await open(page, 0); for (const i of [0,1,1,1,1,0,1,1,1,0,1]) await buy(page, i);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await expect(page.locator('#world canvas')).toHaveAttribute('data-motion', 'true');
  await page.evaluate(() => {
    const canvas = document.querySelector('#world canvas');
    window.observedHotelFrames = new Set(); window.observedHotelStages = new Set();
    window.hotelObserver = new MutationObserver(() => {
      if (canvas.dataset.action !== 'overgrow') return;
      canvas.dataset.spriteFrames.split(',').forEach(frame => window.observedHotelFrames.add(frame));
      window.observedHotelStages.add(canvas.dataset.choreography);
    });
    window.hotelObserver.observe(canvas, { attributes: true });
  });
  await buy(page, 1);
  await expect(page.locator('#world canvas')).toHaveAttribute('data-choreography', 'stamp'); await screenshot(page, 'copycat-stamp');
  await expect(page.locator('#world canvas')).toHaveAttribute('data-choreography', 'unfold'); await screenshot(page, 'copycat-unfold');
  await expect(page.locator('#world')).toHaveAttribute('data-state', 'picking', { timeout: 7000 });
  const observed = await page.evaluate(() => { window.hotelObserver.disconnect(); return { frames: [...window.observedHotelFrames], stages: [...window.observedHotelStages] }; });
  for (const frame of ['actors:0','actors:1','actors:2','actors:3','rooms-cat:1','rooms-cat:2']) expect(observed.frames).toContain(frame);
  for (const stage of ['spot','stamp','send','unfold','celebrate']) expect(observed.stages).toContain(stage);
  const idle = await page.locator('#world canvas').getAttribute('data-sprite-frames');
  await expect.poll(() => page.locator('#world canvas').getAttribute('data-sprite-frames')).not.toBe(idle);
  await page.emulateMedia({ reducedMotion: 'reduce' }); await expect(page.locator('#world canvas')).toHaveAttribute('data-motion', 'false');
  const still = await page.locator('#world canvas').getAttribute('data-sprite-frames'); await page.waitForTimeout(700);
  expect(await page.locator('#world canvas').getAttribute('data-sprite-frames')).toBe(still);
});

test('full-screen scenery and tilted cards keep all utility controls in an accessible menu', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 }); await open(page, 0);
  const scenery = await page.locator('.sky-backdrop').evaluate(e => ({ rect: e.getBoundingClientRect().toJSON(), image: getComputedStyle(e).backgroundImage }));
  expect(scenery.rect).toMatchObject({ x: 0, y: 0, width: 390, height: 844 }); expect(scenery.image).toContain('sky-');
  expect(await page.locator('#offers').evaluate(e => getComputedStyle(e).transform)).toContain('matrix3d');
  await expect(page.locator('.masthead, .shop-heading, .world-note, footer')).toHaveCount(0);
  const utilities = ['sound-toggle','motion-toggle','replay','new-game','overview','workshop-open','rules-open'];
  for (const id of utilities) await expect(page.locator('#' + id)).toBeHidden();
  await page.locator('#menu-open').click(); await expect(page.locator('#menu-dialog')).toBeVisible();
  await page.keyboard.press('1'); await expect(page.locator('#coins')).toHaveText('100');
  await page.locator('#sound-toggle').click(); await expect(page.locator('#sound-toggle')).toHaveAttribute('aria-pressed', 'true');
  await page.locator('#motion-toggle').click(); await expect(page.locator('#world canvas')).toHaveAttribute('data-motion', 'true');
  await page.locator('#motion-toggle').click(); await expect(page.locator('#world canvas')).toHaveAttribute('data-motion', 'false');
  await page.locator('#workshop-open').click(); await expect(page.locator('#workshop-dialog')).toBeVisible(); await expect(page.locator('#menu-dialog')).toBeHidden();
  await page.keyboard.press('Escape'); await expect(page.locator('#menu-dialog')).toBeVisible(); await expect(page.locator('#workshop-open')).toBeFocused();
  for (const size of [{width:320,height:480},{width:667,height:375}]) { await page.setViewportSize(size); await screenFits(page); }
  await screenshot(page, 'menu-landscape');
  await page.keyboard.press('Escape'); await expect(page.locator('#menu-dialog')).toBeHidden(); await expect(page.locator('#menu-open')).toBeFocused();
  await buy(page, 2, 'frog'); await expect(page.locator('#height')).toHaveText('1');
  const seed = new URL(page.url()).searchParams.get('seed'); await control(page, 'new-game');
  await expect(page.locator('#menu-dialog')).toBeHidden(); await expect(page.locator('#height')).toHaveText('0'); await expect(page.locator('#coins')).toHaveText('100');
  expect(new URL(page.url()).searchParams.get('seed')).not.toBe(seed);
});

test('card help explains a power without buying it, keeps shortcuts blocked, and returns focus', async ({ page }) => {
  await page.setViewportSize({ width: 784, height: 1233 }); await open(page, 'gcdolqp');
  await expect(card(page, 0)).toContainText('Frog Room Pattern');
  await expect(card(page, 2)).toContainText('Frog Pack');
  await expect(page.locator('#offers .card-detail, #offers .card-footer')).toHaveCount(0);
  await expect(page.locator('#offers')).not.toContainText('coins left');
  await expect(page.locator('.coins')).not.toContainText(/coins/i);
  for (let i = 0; i < 3; i++) {
    const price = card(page, i).locator('.price');
    await expect(price).toContainText('6'); await expect(price.locator('img')).toBeVisible();
    const cost = await price.boundingBox(), info = await help(page, i).boundingBox();
    expect(cost.x + cost.width).toBeLessThan(info.x);
  }
  const ids = await page.locator('#offers .offer-card').evaluateAll(cards => cards.map(c => c.dataset.cardId));
  await help(page, 0).click(); await expect(page.locator('#effect-dialog')).toBeVisible();
  await expect(page.locator('#effect-dialog')).toContainText(/Future Frog.*\+1/);
  await page.keyboard.press('1'); await page.keyboard.press('3');
  await expect(page.locator('#coins')).toHaveText('100'); await expect(page.locator('#height')).toHaveText('0');
  await expect(page.locator('.card-flight')).toHaveCount(0);
  await screenshot(page, 'card-effect-help');
  await page.keyboard.press('Escape'); await expect(help(page, 0)).toBeFocused();
  expect(await page.locator('#offers .offer-card').evaluateAll(cards => cards.map(c => c.dataset.cardId))).toEqual(ids);
  await page.setViewportSize({ width: 390, height: 844 }); await screenFits(page);
  await help(page, 2).click(); await expect(page.locator('#effect-dialog')).toContainText('3 fixed floors');
  await expect(page.locator('#coins')).toHaveText('100'); await expect(page.locator('.card-flight')).toHaveCount(0);
  await page.locator('#effect-close').click(); await expect(help(page, 2)).toBeFocused();
  await buy(page, 2); await expect(page.locator('#coins')).toHaveText('94'); await expect(page.locator('#height')).toHaveText('3');
  await expect(page.locator('#floor-record li')).toHaveCount(3);
});

test('the full-screen hotel keeps the cardboard tray at its native ratio across screen shapes', async ({ page }) => {
  await open(page, 0); for (const i of [0,1,1,1,2]) await buy(page, i);
  const trayArtRatio = await page.evaluate(async () => {
    const source = getComputedStyle(document.documentElement).getPropertyValue('--tray-art').trim();
    const image = new Image(); image.src = source.match(/url\(["']?(.*?)["']?\)/)[1]; await image.decode();
    return image.naturalWidth / image.naturalHeight;
  });
  expect(trayArtRatio).toBe(3);
  for (const size of [{width:784,height:1233},{width:390,height:844},{width:320,height:480},{width:1280,height:900},{width:1440,height:600},{width:844,height:390},{width:667,height:375}]) {
    await page.setViewportSize(size); await screenFits(page);
    await expect.poll(() => page.locator('#world canvas').evaluate(c => {
      const rect = c.getBoundingClientRect(); return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
    })).toEqual({ x: 0, y: 0, width: size.width, height: size.height });
    const tray = await page.locator('#tray').boundingBox();
    expect(tray.width / tray.height).toBeCloseTo(trayArtRatio, 2);
    if (size.height > size.width) expect(tray.width).toBeGreaterThan(size.width * .9);
    // Matching the wrapper alone is insufficient: unequal background scaling
    // can still stretch the artwork inside a correctly proportioned tray.
    const paintedRatios = await page.locator('#tray').evaluate((element, nativeRatio) => {
      const bounds = element.getBoundingClientRect();
      return ['::before', '::after'].map(pseudo => {
        const values = getComputedStyle(element, pseudo).backgroundSize.split(' ');
        if (['contain', 'cover'].includes(values[0]) || values.includes('auto')) return nativeRatio;
        const length = (value, container) => value.endsWith('%') ? parseFloat(value) * container / 100 : parseFloat(value);
        return length(values[0], bounds.width) / length(values[1], bounds.height);
      });
    }, trayArtRatio);
    for (const ratio of paintedRatios) expect(ratio).toBeCloseTo(trayArtRatio, 2);
    for (let i = 0; i < 3; i++) {
      await help(page, i).click(); await expect(page.locator('#effect-dialog')).toBeVisible();
      await page.locator('#effect-close').click();
    }
    await expect(page.locator('#coins')).toHaveText('78');
    await screenshot(page, `continuous-scene-${size.width}x${size.height}`);
  }
  await paperLoads(page, '.coins, .height, .dock-chip', '--hud-tab');
  await expect(page.locator('.height')).toHaveAttribute('aria-label', /floors/i);
  await expect(page.locator('.height')).not.toContainText(/floors/i);
  await expect(page.locator('#height-art .sprite-art')).toBeVisible();
  await expect(page.locator('#coin-art .sprite-art')).toBeVisible();
  await expect(page.locator('#dock .dock-multiply')).toHaveText(['×', '×', '×']);
  for (const type of ['bunny', 'frog', 'cat']) await expect(page.locator(`.dock-chip.${type}`)).toHaveAttribute('aria-label', new RegExp(`${type}: \\d+ neighborhood balloons`, 'i'));
  await expect(page.locator('#height')).toHaveText('6'); await expect(page.locator('#coins')).toHaveText('78');
});

test('a selected card flies to the center and bursts before money or room effects apply', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 }); await open(page, 'gcdolqp', false);
  await page.evaluate(() => {
    window.cardFlightStages = [];
    window.cardFlightObserver = new MutationObserver(() => {
      const flight = document.querySelector('.card-flight');
      if (!flight || window.cardFlightStages.at(-1)?.phase === flight.dataset.phase) return;
      const rect = flight.querySelector('.card-flight-card').getBoundingClientRect();
      window.cardFlightStages.push({ phase: flight.dataset.phase, coins: document.querySelector('#coins').textContent,
        floors: document.querySelector('#height').textContent, center: { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 } });
    });
    window.cardFlightObserver.observe(document.body, { attributes: true, childList: true, subtree: true });
  });
  await buy(page, 2);
  await expect(page.locator('#world')).toHaveAttribute('data-state', 'launching');
  await expect(page.locator('#coins')).toHaveText('100'); await expect(page.locator('#height')).toHaveText('0');
  await page.keyboard.press('1'); await page.keyboard.press('3');
  await expect(page.locator('#world')).toHaveAttribute('data-state', 'resolving');
  await expect(page.locator('#coins')).toHaveText('94');
  await expect(page.locator('#world')).toHaveAttribute('data-state', 'picking', { timeout: 6000 });
  await expect(page.locator('#height')).toHaveText('3');
  const stages = await page.evaluate(() => { window.cardFlightObserver.disconnect(); return window.cardFlightStages; });
  expect(stages.map(stage => stage.phase)).toEqual(['flight','inflate','burst']);
  for (const stage of stages.slice(0, 2)) { expect(stage.coins).toBe('100'); expect(stage.floors).toBe('0'); }
  expect(stages[1].center.x).toBeCloseTo(195, 0); expect(stages[1].center.y).toBeCloseTo(422, 0);
  expect(stages[2].coins).toBe('94'); await expect(page.locator('.card-flight')).toHaveCount(0);

  // Turning on reduced motion during a launch finishes that exact purchase once.
  await control(page, 'replay'); await buy(page, 2);
  await expect(page.locator('#world')).toHaveAttribute('data-state', 'launching');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await expect(page.locator('#world')).toHaveAttribute('data-state', 'picking');
  await expect(page.locator('#height')).toHaveText('3'); await expect(page.locator('#coins')).toHaveText('94');
  await expect(page.locator('.card-flight')).toHaveCount(0);
  await page.waitForTimeout(1200);
  await expect(page.locator('#height')).toHaveText('3'); await expect(page.locator('#coins')).toHaveText('94');
});

test('clouds drift and islands float independently, pause for reduced motion, and resume in place', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 }); await open(page, 0);
  for (const i of [0,1,1,1,2]) await buy(page, i);
  await control(page, 'overview');
  const sky = page.locator('.sky-backdrop');
  await expect(sky).toHaveAttribute('data-motion', 'false');
  await expect(page.locator('.sky-island')).toHaveCount(5); await expect(page.locator('.sky-cloud')).toHaveCount(9);
  const positions = () => page.locator('.sky-sprite').evaluateAll(items => items.map(e => getComputedStyle(e).transform));
  const frozen = await positions(); await page.waitForTimeout(250); expect(await positions()).toEqual(frozen);
  await control(page, 'motion-toggle'); await page.locator('#resume').click();
  await expect(sky).toHaveAttribute('data-motion', 'true');
  for (const kind of ['cloud', 'island']) {
    const sprite = page.locator(`.sky-${kind} .sky-sprite`).first(); const before = await sprite.evaluate(e => getComputedStyle(e).transform);
    await expect.poll(() => sprite.evaluate(e => getComputedStyle(e).transform)).not.toBe(before);
  }
  // Check the actual pixels can load and that cutouts have real alpha, not a painted backdrop.
  expect(await page.locator('.sky-sprite').first().evaluate(async e => {
    const image = new Image(); image.src = getComputedStyle(e).backgroundImage.slice(5,-2); await image.decode();
    const canvas = document.createElement('canvas'); canvas.width = image.width; canvas.height = image.height;
    const context = canvas.getContext('2d'); context.drawImage(image,0,0);
    return context.getImageData(0,0,1,1).data[3];
  })).toBe(0);
  await screenshot(page, 'moving-scenery-phone');
  await control(page, 'motion-toggle'); await page.locator('#resume').click();
  await expect(sky).toHaveAttribute('data-motion', 'false');
  await expect.poll(() => sky.evaluate(e => e.getAnimations({ subtree: true }).every(a => a.playState === 'paused'))).toBe(true);
  const paused = await positions(); await page.waitForTimeout(300); expect(await positions()).toEqual(paused);
  await control(page, 'motion-toggle');
  // Resuming keeps each animation's phase instead of resetting the scene.
  const elapsed = await sky.evaluate(e => e.getAnimations({ subtree: true }).map(a => a.currentTime));
  expect(elapsed.every(t => t > 1000)).toBe(true);
  await page.locator('#resume').click(); await expect.poll(positions).not.toEqual(paused);
  await page.emulateMedia({ reducedMotion: 'no-preference' }); await page.emulateMedia({ reducedMotion: 'reduce' });
  await expect(sky).toHaveAttribute('data-motion', 'false');
  const systemPaused = await positions(); await page.waitForTimeout(250); expect(await positions()).toEqual(systemPaused);
  for (const size of [{width:320,height:480},{width:1280,height:900},{width:844,height:390}]) {
    await page.setViewportSize(size); await screenFits(page); await screenshot(page, `moving-scenery-${size.width}x${size.height}`);
  }
  await expect(page.locator('#height')).toHaveText('6'); await expect(page.locator('#coins')).toHaveText('78');
});
