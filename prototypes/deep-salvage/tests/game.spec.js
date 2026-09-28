import { test, expect } from '@playwright/test';
import { PARTS } from '../parts.js';
import { mkdir } from 'node:fs/promises';

// Netlify's documented query flag keeps its review drawer off the mobile controls.
const URL = '/prototypes/deep-salvage/?test&ntl-drawer-state=hidden';
const forge = (page, index) => page.locator(`.forge-slot[data-slot="${index}"]`);
async function dropIntoForge(page, type, index) {
  const id = await page.evaluate(type => window.__deepSalvage.drop(type), type);
  await drag(page, page.locator(`.loot[data-id="${id}"]`), forge(page, index));
  await page.getByRole('button', { name: "Got it. Let's build" }).click();
}
const cell = (page, index) => page.locator(`.cell[data-index="${index}"]`);
async function boot(page) {
  await page.goto(URL);
  await expect(page.locator('canvas')).toHaveAttribute('data-ready', 'true');
  await page.getByRole('button', { name: "Let's dive" }).click();
  await expect(page.locator('#modal')).not.toBeVisible();
}
async function storedPart(page, type) {
  const locator = page.locator(`.stack[data-type="${type}"]`);
  await expect(locator).toBeVisible();
  return locator;
}
async function aimPreview(page, target, pointer) {
  const b = await target.boundingBox(), ghost = await page.locator('#drag-ghost').boundingBox();
  return { x: b.x + b.width / 2 - (ghost.x + ghost.width / 2 - pointer.x), y: b.y + b.height / 2 - (ghost.y + ghost.height / 2 - pointer.y) };
}
async function drag(page, source, target, beforeRelease) {
  if (await source.evaluate(el => el.classList.contains('stack'))) await source.scrollIntoViewIfNeeded();
  const a = await source.boundingBox(), b = await target.boundingBox();
  await page.mouse.move(a.x + a.width / 2, a.y + a.height / 2);
  await page.mouse.down();
  const initialPointer = { x: a.x + a.width / 2 + 10, y: a.y + a.height / 2 - 10 };
  await page.mouse.move(initialPointer.x, initialPointer.y);
  const pointer = await aimPreview(page, target, initialPointer);
  await page.mouse.move(pointer.x, pointer.y, { steps: 12 });
  const ghost = await page.locator('#drag-ghost').boundingBox();
  expect(ghost.x + ghost.width / 2).toBeCloseTo(b.x + b.width / 2, 0);
  expect(ghost.y + ghost.height / 2).toBeCloseTo(b.y + b.height / 2, 0);
  if (beforeRelease) await beforeRelease(pointer);
  await page.mouse.up();
}
async function shot(page, name) {
  await mkdir('artifacts/deep-salvage', { recursive: true });
  await page.screenshot({ path: `artifacts/deep-salvage/${name}.png` });
}
async function bounds(page) {
  return page.evaluate(() => {
    const box = selector => { const r = document.querySelector(selector).getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height, bottom: r.bottom, right: r.right }; };
    return { world: box('#world'), console: box('#console'), board: box('#board'), storage: box('#storage'), forge: box('#forge'), cell: box('.cell'), width: innerWidth, height: innerHeight, scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight };
  });
}

test('Pixel-shaped portrait and landscape layouts fit, render Phaser art and stay error-free', async ({ page }) => {
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await page.evaluate(() => window.__deepSalvage.advance(3));
  await expect(page.locator('.cell')).toHaveCount(30);
  await expect(page.locator('.forge-slot')).toHaveCount(5);
  await expect(page.locator('#storage button')).toHaveCount(14);
  await expect(page.locator('#console h1, #console h2, #console p, #console .part-readout, #forge-start')).toHaveCount(0);
  for (const [name, width, height] of [['pixel-10-pro', 412, 924], ['pixel-large-css', 448, 1000], ['pixel-browser-bars', 412, 820], ['small-phone', 360, 740], ['landscape', 924, 412]]) {
    await page.setViewportSize({ width, height });
    await expect.poll(async () => (await page.locator('canvas').boundingBox()).width).toBeGreaterThan(100);
    const b = await bounds(page);
    expect(b.scrollWidth).toBeLessThanOrEqual(width); expect(b.scrollHeight).toBeLessThanOrEqual(height);
    expect(b.board.y).toBeGreaterThanOrEqual(b.console.y);
    expect(b.board.bottom).toBeLessThanOrEqual(b.storage.y + 1);
    expect(b.storage.bottom).toBeLessThanOrEqual(height + 1);
    expect(b.storage.right).toBeCloseTo(b.forge.right, 0);
    expect(b.storage.x).toBeLessThanOrEqual(b.board.x);
    expect(b.board.right).toBeLessThanOrEqual(b.forge.x);
    expect(b.forge.right).toBeLessThanOrEqual(width);
    expect(b.forge.y).toBeLessThanOrEqual(b.board.y + 1);
    expect(b.forge.bottom).toBeLessThanOrEqual(height);
    const slots = await page.locator('.forge-slot').evaluateAll(els => els.map(el => { const r = el.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, bottom: r.bottom }; }));
    for (let i = 0; i < slots.length; i++) {
      expect(slots[i].width).toBeGreaterThanOrEqual(44);
      expect(slots[i].width).toBeCloseTo(b.cell.w, 0);
      expect(slots[i].x).toBe(slots[0].x);
      if (i) expect(slots[i].y).toBeGreaterThanOrEqual(slots[i - 1].bottom);
    }
    expect(b.cell.w).toBeGreaterThanOrEqual(44);
    const storageCells = await page.locator('#storage button').evaluateAll(els => els.map(el => { const r = el.getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height}; }));
    expect(new Set(storageCells.map(r => Math.round(r.y))).size).toBe(2);
    for (const slot of storageCells) {
      expect(slot.w).toBeGreaterThanOrEqual(44); expect(slot.h).toBeGreaterThanOrEqual(44);
      expect(slot.w).toBeCloseTo(b.cell.w,0);
    }

    await shot(page, name);
  }
  expect(errors).toEqual([]);
});

test('tap salvage stacks, first acquisition pauses once, guide pauses and discovery survives reload', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  const id = await page.evaluate(() => window.__deepSalvage.drop('splitter'));
  await page.locator(`.loot[data-id="${id}"]`).click();
  await expect(page.locator('#modal-title')).toHaveText('Splitter.');
  const before = await page.evaluate(() => window.__deepSalvage.snapshot().elapsed);
  await page.evaluate(() => window.__deepSalvage.advance(2));
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().elapsed)).toBe(before);
  await shot(page, 'first-discovery');
  await page.getByRole('button', { name: "Got it. Let's build" }).click();
  const id2 = await page.evaluate(() => window.__deepSalvage.drop('splitter'));
  await page.locator(`.loot[data-id="${id2}"]`).click();
  await expect(page.locator('#modal')).not.toBeVisible();
  await expect((await storedPart(page, 'splitter')).locator('.count')).toHaveText('2');
  await page.locator('#manual').click(); await expect(page.locator('.guide-row')).toHaveCount(20);
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().paused)).toBe(true);
  await page.getByRole('button', { name: 'Back to the dive' }).click();
  await page.reload(); await page.getByRole('button', { name: "Let's dive" }).click();
  const id3 = await page.evaluate(() => window.__deepSalvage.drop('splitter'));
  await page.locator(`.loot[data-id="${id3}"]`).click();
  await expect(page.locator('#modal')).not.toBeVisible();
});

test('drag storage and battlefield parts into lab, rotate once, reject occupied targets, and return to storage', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await drag(page, (await storedPart(page, 'mirror')), cell(page, 13));
  await expect(cell(page, 13)).toHaveAttribute('aria-label', /Mirror, 0 degrees/);
  await expect((await storedPart(page, 'mirror')).locator('.count')).toHaveText('1');
  await cell(page, 13).click();
  await expect(cell(page, 13)).toHaveAttribute('aria-label', /Mirror, 90 degrees/);
  await drag(page, cell(page, 13), cell(page, 26));
  await expect(cell(page, 13)).toHaveAttribute('aria-label', /Mirror, 90 degrees/);
  await drag(page, cell(page, 13), page.locator('#storage'));
  await expect(cell(page, 13)).toHaveClass(/empty/);
  await expect((await storedPart(page, 'mirror')).locator('.count')).toHaveText('2');
  const id = await page.evaluate(() => window.__deepSalvage.drop('lens'));
  await drag(page, page.locator(`.loot[data-id="${id}"]`), cell(page, 14));
  await expect(page.locator('#modal-title')).toHaveText('Lens.');
  await page.getByRole('button', { name: "Got it. Let's build" }).click();
  await expect(cell(page, 14)).toHaveAttribute('aria-label', /Lens/);
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().circuit.guns[0].piercing)).toBe(true);
  await shot(page, 'installed-lens');
});

test('touch tap rotates exactly once, touch salvage works, and cancelled drag never consumes a stack', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 412, height: 924 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
  const page = await context.newPage(); await boot(page);
  await cell(page, 26).tap();
  await expect(cell(page, 26)).toHaveAttribute('aria-label', /90 degrees/);
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().circuit.guns.length)).toBe(0);
  const id = await page.evaluate(() => window.__deepSalvage.drop('mirror'));
  await page.locator(`.loot[data-id="${id}"]`).tap();
  await expect((await storedPart(page, 'mirror')).locator('.count')).toHaveText('3');
  const source = await (await storedPart(page, 'mirror')).boundingBox();
  const cdp = await context.newCDPSession(page);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: source.x + 20, y: source.y + 20 }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: source.x + 20, y: source.y - 30 }] });
  await expect(page.locator('#drag-ghost')).toBeVisible();
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchCancel', touchPoints: [] });
  await expect(page.locator('#drag-ghost')).not.toBeVisible();
  await expect((await storedPart(page, 'mirror')).locator('.count')).toHaveText('3');
  const destination = await cell(page, 13).boundingBox();
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: source.x + 20, y: source.y + 20 }] });
  const initialPointer = { x: destination.x + 20, y: destination.y + 20 };
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [initialPointer] });
  const pointer = await aimPreview(page, cell(page, 13), initialPointer);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [pointer] });
  await expect(cell(page, 13)).toHaveClass(/target/);
  expect(pointer.y).toBeGreaterThan(destination.y + destination.height);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await expect(cell(page, 13)).toHaveAttribute('aria-label', /Mirror/);
  await expect((await storedPart(page, 'mirror')).locator('.count')).toHaveText('2');
  // Touch can move directly from the visible hold to the forge, without tabs.
  const mirror = await (await storedPart(page, 'mirror')).boundingBox();
  const start = { x: mirror.x + mirror.width / 2, y: mirror.y + mirror.height / 2 };
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [start] });
  const moved = { x: start.x + 12, y: start.y - 12 };
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [moved] });
  const forgePointer = await aimPreview(page, page.locator('.forge-slot[data-slot="0"]'), moved);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [forgePointer] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await expect(page.locator('.forge-slot[data-slot="0"]')).toHaveAttribute('data-type', 'mirror');
  await expect(page.locator('#storage')).toBeVisible();
  await context.close();
});

test('preview center determines highlighted and committed destinations, including grid edges and storage', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await drag(page, (await storedPart(page, 'mirror')), cell(page, 25), async pointer => {
    await expect(cell(page, 25)).toHaveClass(/target/);
    const box = await cell(page, 25).boundingBox();
    expect(pointer.y).toBeGreaterThan(box.y + box.height);
    await shot(page, 'preview-aligned-bottom-row');
  });
  await expect(cell(page, 25)).toHaveAttribute('aria-label', /Mirror/);
  // An occupied preview destination must be rejected even with the finger over
  // an empty neighboring cell. No source part is consumed.
  await drag(page, (await storedPart(page, 'mirror')), cell(page, 20), async () => {
    await expect(cell(page, 20)).toHaveClass(/invalid/);
  });
  await expect((await storedPart(page, 'mirror')).locator('.count')).toHaveText('1');
  await drag(page, cell(page, 25), page.locator('#storage'), async () => {
    await expect(page.locator('#storage')).toHaveClass(/drop-target/);
  });
  await expect(cell(page, 25)).toHaveClass(/empty/);
  await expect((await storedPart(page, 'mirror')).locator('.count')).toHaveText('2');
});

test('a gun beside the reactor stays powered and ignores rotation taps', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await drag(page, cell(page, 2), cell(page, 28));
  await cell(page, 26).click(); // Reactor now emits right through empty cell 23.
  for (let rotation = 0; rotation < 4; rotation++) {
    expect(await page.evaluate(() => window.__deepSalvage.snapshot().circuit.guns.length)).toBe(1);
    await expect(cell(page, 28)).toHaveClass(/active/);
    await cell(page, 28).click();
  }
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().circuit.guns.length)).toBe(1);
  await page.locator('#manual').click();
  await expect(page.locator('.guide-row').filter({ has: page.getByRole('heading', { name: 'Laser gun', exact: true }) })).toContainText('all four sides');
});

test('a horizontal circuit amplifies, pierces and splits without orienting its parts', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await page.evaluate(() => {
    const grid = Array(30).fill(null);
    grid[12] = { type: 'reactor', rotation: 1 };
    grid[13] = { type: 'amplifier', rotation: 0 };
    grid[14] = { type: 'lens', rotation: 0 };
    grid[15] = { type: 'splitter', rotation: 0 };
    grid[9] = { type: 'gun', rotation: 0 };
    grid[21] = { type: 'gun', rotation: 0 };
    window.__deepSalvage.setGrid(grid);
  });
  for (const index of [13, 14, 15, 9, 21]) {
    await expect(cell(page, index)).toHaveAttribute('aria-label', /accepts beams from any side/);
    await cell(page, index).click();
    expect(await page.evaluate(() => window.__deepSalvage.snapshot().circuit.guns.length)).toBe(2);
  }
  const snapshot = await page.evaluate(() => window.__deepSalvage.snapshot());
  expect(snapshot.circuit.guns.map(g => ({ power: g.power, piercing: g.piercing }))).toEqual([{ power: 6, piercing: true }, { power: 6, piercing: true }]);
  expect([13, 14, 15, 9, 21].every(index => snapshot.grid[index].rotation === 0)).toBe(true);
  await shot(page, 'omnidirectional-circuit');
});

test('player builds two guns using real controls, with empty cells between mirrors and guns', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await page.evaluate(() => window.__deepSalvage.advance(6));
  // Falling loot intentionally never becomes position-stable. Click its current
  // hit target like a player, rather than waiting for Playwright's stability gate.
  const fallingPart = page.getByRole('button', { name: 'Salvage Splitter', exact: true });
  await expect(fallingPart).toBeVisible();
  const lootBox = await fallingPart.boundingBox();
  await page.mouse.click(lootBox.x + lootBox.width / 2, lootBox.y + lootBox.height / 2);
  await page.getByRole('button', { name: "Got it. Let's build" }).click();
  await drag(page, cell(page, 2), cell(page, 1));
  await drag(page, (await storedPart(page, 'gun')), cell(page, 3));
  await drag(page, (await storedPart(page, 'mirror')), cell(page, 13));
  await cell(page, 13).click();
  await drag(page, (await storedPart(page, 'mirror')), cell(page, 15));
  await (await storedPart(page, 'splitter')).click();
  await cell(page, 14).click();
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().circuit.guns.length)).toBe(2);
  const snapshot = await page.evaluate(() => window.__deepSalvage.snapshot());
  expect(snapshot.circuit.guns.map(g => g.power)).toEqual([6, 6]);
  expect(snapshot.grid[7]).toBeNull(); expect(snapshot.grid[9]).toBeNull();
  await shot(page, 'two-gun-circuit');
  await cell(page, 13).focus(); await page.keyboard.press('Enter');
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().circuit.guns.length)).toBe(1);
  await page.keyboard.press('Delete');
  await expect(cell(page, 13)).toHaveClass(/empty/);
  await expect((await storedPart(page, 'mirror')).locator('.count')).toHaveText('1');
});

test('loot expiry flashes then disappears, pause freezes clocks, and defeat restarts cleanly', async ({ page }) => {
  await boot(page);
  const id = await page.evaluate(() => window.__deepSalvage.drop('mirror'));
  await page.evaluate(() => window.__deepSalvage.advance(9.5));
  await expect(page.locator(`.loot[data-id="${id}"]`)).toHaveClass(/expiring/);
  await page.locator('#pause').click();
  const before = await page.evaluate(() => window.__deepSalvage.snapshot().elapsed);
  await page.evaluate(() => window.__deepSalvage.advance(20));
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().elapsed)).toBe(before);
  await page.getByRole('button', { name: 'Keep going' }).click();
  await page.evaluate(() => window.__deepSalvage.advance(3));
  await expect(page.locator(`.loot[data-id="${id}"]`)).toHaveCount(0);
  await page.evaluate(() => { window.__deepSalvage.setGrid(Array(30).fill(null)); window.__deepSalvage.advance(180); });
  await expect(page.locator('#modal-title')).toHaveText('A brave little dive.');
  await page.getByRole('button', { name: 'Another dive' }).click();
  await expect(page.locator('#hull-label')).toHaveText('100');
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().circuit.guns.length)).toBe(1);
});

test('an upgraded circuit reaches the beacon and end-state guide returns to the ending', async ({ page }) => {
  await boot(page);
  await page.evaluate(() => {
    const grid = window.__deepSalvage.snapshot().grid;
    grid[14] = { type: 'amplifier2', rotation: 0 }; grid[8] = { type: 'lens', rotation: 0 };
    window.__deepSalvage.setGrid(grid); window.__deepSalvage.advance(180);
  });
  await expect(page.locator('#modal-title')).toHaveText('Still in one piece.');
  await page.getByRole('button', { name: 'Study the parts' }).click();
  await page.getByRole('button', { name: 'Back to the dive' }).click();
  await expect(page.locator('#modal-title')).toHaveText('Still in one piece.');
});

test('automatic forge waits for cash, locks only ingredients, pauses, and preserves unrelated parts', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  // Keep recipe timing and cash checks independent of combat rewards.
  await page.evaluate(() => { window.__deepSalvage.setEnemies([]); window.__deepSalvage.setSpawnDelay(1000); window.__deepSalvage.setCash(0); });
  await drag(page, await storedPart(page, 'medic'), forge(page, 4));
  await drag(page, await storedPart(page, 'amplifier'), forge(page, 0));
  await expect(cell(page, 20)).toHaveClass(/forge-match/);
  await expect(await storedPart(page, 'amplifier')).toHaveClass(/forge-match/);
  await drag(page, await storedPart(page, 'amplifier'), forge(page, 2));
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().forge.job)).toBeNull();
  await expect(forge(page, 0)).toHaveClass(/waiting-cash/);
  await drag(page, await storedPart(page, 'pulse'), forge(page, 1));
  await page.evaluate(() => { window.__deepSalvage.setCash(24); window.__deepSalvage.advance(.01); });
  await expect(page.locator('#cash-label')).toHaveText('0');
  await expect(forge(page, 0)).toBeDisabled(); await expect(forge(page, 2)).toBeDisabled();
  await expect(forge(page, 4)).toBeEnabled();
  await shot(page, 'automatic-forge-working');
  await page.locator('#pause').click();
  const before = await page.evaluate(() => window.__deepSalvage.snapshot().forge.job.remaining);
  await page.evaluate(() => window.__deepSalvage.advance(20));
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().forge.job.remaining)).toBe(before);
  await page.getByRole('button', { name: 'Keep going' }).click();
  await drag(page, forge(page, 4), forge(page, 3));
  await expect(forge(page, 3)).toHaveAttribute('data-type', 'medic');
  await page.evaluate(() => window.__deepSalvage.advance(7));
  await expect(page.locator('#modal-title')).toHaveText('Overcharger.');
  await page.getByRole('button', { name: "Got it. Let's build" }).click();
  await expect(forge(page, 0)).toHaveAttribute('data-type', '');
  await expect(forge(page, 3)).toHaveAttribute('data-type', 'medic');
  await expect(forge(page, 1)).toHaveAttribute('data-type', 'pulse');
  await drag(page, await storedPart(page, 'amplifier2'), cell(page, 14));
  await expect(cell(page, 14).locator('.tier-badge')).toHaveText('II');
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().forged)).toBe(1);
});

test('mixed recipe accepts unrelated parts and makes stronger piercing beams automatically', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await page.evaluate(() => window.__deepSalvage.setCash(100));
  await drag(page, await storedPart(page, 'amplifier'), forge(page, 0));
  await drag(page, await storedPart(page, 'medic'), forge(page, 1));
  const id = await page.evaluate(() => window.__deepSalvage.drop('lens'));
  await expect(page.locator(`.loot[data-id="${id}"]`)).toHaveClass(/forge-match/);
  await drag(page, page.locator(`.loot[data-id="${id}"]`), forge(page, 2));
  await page.getByRole('button', { name: "Got it. Let's build" }).click();
  await expect(forge(page, 0)).toBeDisabled();
  await page.evaluate(() => window.__deepSalvage.advance(9));
  await expect(page.locator('#modal-title')).toHaveText('Piercing amplifier.');
  await page.getByRole('button', { name: "Got it. Let's build" }).click();
  await expect(forge(page, 1)).toHaveAttribute('data-type', 'medic');
  await drag(page, await storedPart(page, 'prism'), cell(page, 14));
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().circuit.guns[0].piercing)).toBe(true);
  const blue = page.locator('.beam[data-power="21"][data-piercing="true"]');
  await expect(blue).toHaveCount(2);
  expect(await blue.first().evaluate(el => parseFloat(el.style.strokeWidth))).toBeGreaterThan(await page.locator('.beam[data-power="8"]').first().evaluate(el => parseFloat(el.style.strokeWidth)));
  await shot(page, 'forged-piercing-beam');
});

test('unmatched forge ingredients can be returned by tap or dragged into the lab', async ({ page }) => {
  await boot(page);
  await drag(page, cell(page, 20), forge(page, 0));
  await forge(page, 0).click();
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().inventory.amplifier)).toBe(3);
  await expect(forge(page, 0)).toHaveAttribute('data-type', '');
  await drag(page, await storedPart(page, 'mirror'), forge(page, 4));
  await drag(page, forge(page, 4), cell(page, 29));
  await expect(cell(page, 29)).toHaveAttribute('aria-label', /Mirror/);
  await expect(page.locator('[role=tab], #forge-start')).toHaveCount(0);
});

test('combat produces shield and hull feedback for submarine and enemies', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await page.evaluate(() => {
    window.__deepSalvage.setEnemies([
      { id: 900, type: 'warden', hp: 180, maxHp: 180, shield: 40, maxShield: 40, armor: 3, damage: 14, speed: 0, x: .3, y: .4, attackIn: 0, attackInterval: 1.8 },
      { id: 901, type: 'crab', hp: 125, maxHp: 125, shield: 0, armor: 4, damage: 14, speed: 0, x: .32, y: .65, attackIn: 0, attackInterval: 1.8 },
    ]);
    window.__deepSalvage.advance(.01);
  });
  const s = await page.evaluate(() => window.__deepSalvage.snapshot());
  expect(s.hull).toBe(96); expect(s.shield).toBe(0);
  expect(s.submarine.shieldFlash).toBeGreaterThan(0); expect(s.submarine.hitFlash).toBeGreaterThan(0);
  expect(s.enemies[0].shieldFlash).toBeGreaterThan(0);
  await shot(page, 'combat-shield-impact');
  await expect(page.locator('canvas')).toHaveAttribute('data-ready', 'true');
});

test('manual lists all recipes and three upgraded ingredients forge without a premature recipe', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await page.locator('#manual').click();
  await expect(page.locator('.recipe-row')).toHaveCount(13);
  await expect(page.locator('.recipe-row').filter({ hasText: '→ Prism overcharger' })).toContainText('1 × Piercing amplifier + 1 × Overcharger + 1 × Rail lens');
  await shot(page, 'recipe-manual');
  await page.getByRole('button', { name: 'Back to the dive' }).click();
  await page.evaluate(() => { window.__deepSalvage.setEnemies([]); window.__deepSalvage.setSpawnDelay(1000); window.__deepSalvage.setCash(100); });
  for (const [index, type] of ['prism', 'amplifier2', 'lens2'].entries()) {
    await dropIntoForge(page, type, index);
    if (index < 2) expect(await page.evaluate(() => window.__deepSalvage.snapshot().forge.job)).toBeNull();
  }
  await expect(forge(page, 2)).toBeDisabled();
  await expect(page.locator('#cash-label')).toHaveText('58');
  await shot(page, 'three-part-forge');
  await page.evaluate(() => window.__deepSalvage.advance(10));
  await expect(page.locator('#modal-title')).toHaveText('Prism overcharger.');
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().inventory.prism2)).toBe(1);
});

test('four-part recipe waits for every distinct upgraded ingredient', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await page.evaluate(() => { window.__deepSalvage.setEnemies([]); window.__deepSalvage.setSpawnDelay(1000); window.__deepSalvage.setCash(100); });
  for (const [index, type] of ['splitter2', 'mirror2', 'reactor2', 'gun2'].entries()) {
    await dropIntoForge(page, type, index);
    if (index < 3) {
      expect(await page.evaluate(() => window.__deepSalvage.snapshot().forge.job)).toBeNull();
      await expect(page.locator('#cash-label')).toHaveText('100');
    }
  }
  await expect(page.locator('#cash-label')).toHaveText('40');
  await shot(page, 'four-part-forge');
  await page.evaluate(() => window.__deepSalvage.advance(11));
  await expect(page.locator('#modal-title')).toHaveText('Duplicator.');
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().inventory.splitter3)).toBe(1);
});

test('continuous laser and draggable pulse gun show independent damage, charging, pause and release', async ({ page }) => {
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await drag(page, cell(page, 2), cell(page, 0));
  await drag(page, (await storedPart(page, 'pulse')), cell(page, 2));
  await expect(cell(page, 2).locator('.part-pulse')).toBeVisible();
  await page.evaluate(() => {
    const grid = window.__deepSalvage.snapshot().grid;
    grid[24] = { type: 'reactor', rotation: 0 }; grid[2].charge = 0;
    window.__deepSalvage.setGrid(grid);
    window.__deepSalvage.setEnemies([{ id: 950, type: 'warden', hp: 1000, maxHp: 1000, shield: 0, armor: 0, speed: 0, x: .7, y: .4, attackIn: 100 }]);
    window.__deepSalvage.advance(1);
  });
  const charging = await page.evaluate(() => window.__deepSalvage.snapshot());
  expect(charging.laserBeams).toHaveLength(1);
  expect(charging.grid[2].charge).toBeGreaterThanOrEqual(12);
  expect(charging.enemies.find(e => e.id === 950).hp).toBeLessThan(1000);
  expect(charging.shots.filter(s => s.pulse)).toHaveLength(0);
  await expect(cell(page, 0)).toHaveClass(/active/);
  expect(await cell(page, 2).locator('.charge-meter i').evaluate(el => parseFloat(el.style.width))).toBeGreaterThan(30);
  await shot(page, 'laser-and-pulse-charging');
  await page.locator('#manual').click();
  const pausedCharge = await page.evaluate(() => window.__deepSalvage.snapshot().grid[2].charge);
  await page.evaluate(() => window.__deepSalvage.advance(5));
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().grid[2].charge)).toBe(pausedCharge);
  await expect(page.locator('.guide-row').filter({ has: page.getByRole('heading', { name: 'Pulse gun', exact: true }) })).toContainText('54-damage pulse');
  await expect(page.locator('.recipe-row').filter({ hasText: '→ Pulse gun' })).toContainText('1 × Laser gun + 1 × Reactor');
  await page.getByRole('button', { name: 'Back to the dive' }).click();
  await page.evaluate(() => {
    const grid = window.__deepSalvage.snapshot().grid; grid[2].charge = 35.9;
    window.__deepSalvage.setGrid(grid); window.__deepSalvage.advance(.01);
  });
  const fired = await page.evaluate(() => window.__deepSalvage.snapshot());
  expect(fired.shots.some(s => s.pulse)).toBe(true);
  expect(fired.grid[2].charge).toBeLessThan(3);
  expect(fired.enemies.find(e => e.id === 950).hp).toBeLessThan(charging.enemies.find(e => e.id === 950).hp - 54);
  await shot(page, 'pulse-release');
  expect(errors).toEqual([]);
});

test('Shield and Medic drag from hold, charge from a reactor, restore vitals and pause with the guide', async ({ page }) => {
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await drag(page, (await storedPart(page, 'reactor')), cell(page, 24));
  await drag(page, (await storedPart(page, 'shield')), cell(page, 0));
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().circuit.supports.length)).toBe(1);
  await page.evaluate(() => { window.__deepSalvage.setVitals(80, 0); window.__deepSalvage.advance(4.1); });
  const shield = await page.evaluate(() => window.__deepSalvage.snapshot());
  expect(shield.shield).toBe(12); expect(shield.hull).toBe(80);
  await shot(page, 'shield-terminal');
  await drag(page, cell(page, 0), page.locator('#storage'));
  await drag(page, (await storedPart(page, 'medic')), cell(page, 0));
  await page.evaluate(() => { window.__deepSalvage.setVitals(60, 24); window.__deepSalvage.advance(2); });
  await page.locator('#manual').click();
  const charge = await page.evaluate(() => window.__deepSalvage.snapshot().grid[0].charge);
  await page.evaluate(() => window.__deepSalvage.advance(10));
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().grid[0].charge)).toBe(charge);
  await expect(page.locator('.guide-row')).toHaveCount(20);
  await expect(page.locator('.recipe-row')).toHaveCount(13);
  await expect(page.locator('.enemy-row')).toHaveCount(10);
  await expect(page.locator('.recipe-row').filter({hasText:'→ Aegis shield'})).toContainText('20 shield');
  await page.getByRole('button', {name:'Back to the dive'}).click();
  await page.evaluate(() => window.__deepSalvage.advance(4.1));
  const healed = await page.evaluate(() => window.__deepSalvage.snapshot());
  expect(healed.hull).toBe(72); expect(healed.grid[0].charge).toBeLessThan(16);
  await shot(page, 'medic-terminal');
  expect(errors).toEqual([]);
});

test('route selection changes encounters and scenery, survives restart, and offers readable enemy guide', async ({ page }) => {
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.setViewportSize({ width: 412, height: 924 }); await page.goto(URL);
  await expect(page.locator('.route-card')).toHaveCount(3);
  await shot(page, 'route-selection');
  for (const [id, location, depth] of [['kelp','EMERALD SHALLOWS','460 m ↓'], ['foundry','COLD PIPELINES','1260 m ↓']]) {
    await page.locator(`[data-map="${id}"]`).click();
    await expect(page.locator(`[data-map="${id}"]`)).toHaveAttribute('aria-pressed','true');
    await page.getByRole('button', {name:"Let's dive"}).click();
    await expect(page.locator('#location-label')).toHaveText(location);
    await expect(page.locator('.depth')).toHaveText(depth);
    await expect(page.locator('canvas')).toHaveAttribute('data-map',id);
    await page.evaluate(() => window.__deepSalvage.advance(3));
    await shot(page, `map-${id}-portrait`);
    await page.setViewportSize({width:924,height:412}); await shot(page, `map-${id}-landscape`);
    const b = await bounds(page); expect(b.scrollWidth).toBe(924); expect(b.scrollHeight).toBe(412);
    await page.setViewportSize({width:412,height:924});
    await page.locator('#pause').click(); await page.getByRole('button', {name:'Start a new dive',exact:true}).click();
    expect(await page.evaluate(() => window.__deepSalvage.snapshot().mapId)).toBe(id);
    await page.locator('#pause').click(); await page.getByRole('button', {name:'Choose another route'}).click();
  }
  await page.locator('[data-map=city]').click();
  await page.getByRole('button', {name:'Back to current dive'}).click();
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().mapId)).toBe('foundry');
  await page.locator('#manual').click();
  await page.getByRole('heading', {name:'Enemy field guide'}).scrollIntoViewIfNeeded();
  await expect(page.locator('.enemy-row').filter({hasText:'Harpoon sniper'})).toContainText('every 3 seconds');
  await expect(page.locator('.enemy-row').filter({hasText:'Volt leech'})).toContainText('twice as much shield');
  await shot(page, 'enemy-field-guide');
  expect(errors).toEqual([]);
});


test('fourteen fixed storage slots stay visible, do not scroll, and free slots without shifting neighbors', async ({ browser }) => {
  const context = await browser.newContext({viewport:{width:360,height:740},isMobile:true,hasTouch:true});
  const page = await context.newPage(); await boot(page);
  await expect(page.locator('#stacks .stack')).toHaveCount(14);
  await expect(page.locator('#hold-prev, #hold-next')).toHaveCount(0);
  await expect(page.locator('.empty-slot')).toHaveCount(7);
  const reactor = page.locator('.stack[data-type="reactor"]');
  const reactorSlot = await reactor.getAttribute('data-slot');
  const mirror = page.locator('.stack[data-type="mirror"]');
  const original = await mirror.boundingBox();
  const cdp = await context.newCDPSession(page);
  await cdp.send('Input.dispatchTouchEvent', {type:'touchStart',touchPoints:[{x:original.x+22,y:original.y+22}]});
  await cdp.send('Input.dispatchTouchEvent', {type:'touchMove',touchPoints:[{x:original.x+100,y:original.y+22}]});
  await expect(page.locator('#drag-ghost')).toBeVisible();
  expect(await page.locator('#storage').evaluate(el=>el.scrollLeft)).toBe(0);
  await cdp.send('Input.dispatchTouchEvent', {type:'touchCancel',touchPoints:[]});
  await expect(mirror.locator('.count')).toHaveText('2');
  await reactor.tap(); await cell(page,24).tap();
  await expect(cell(page,24)).toHaveAttribute('aria-label',/Reactor/);
  await expect(page.locator(`.stack[data-slot="${reactorSlot}"]`)).toHaveClass(/empty-slot/);
  expect(await mirror.boundingBox()).toEqual(original);
  await expect(page.locator('#stacks .stack')).toHaveCount(14);
  await shot(page,'fixed-parts-small-phone');
  await context.close();
});

test('full storage rejects new types safely and completed upgrades remain usable in the forge', async ({ page }) => {
  await page.setViewportSize({width:412,height:924}); await boot(page);
  const inventory = Object.fromEntries(Object.keys(PARTS).filter(type => !['amplifier2','prism'].includes(type)).slice(0,14).map(type => [type, type === 'amplifier' ? 3 : 1]));
  await page.evaluate(inventory => {
    window.__deepSalvage.setEnemies([]); window.__deepSalvage.setSpawnDelay(1000);
    window.__deepSalvage.setInventory(inventory);
  }, inventory);
  await expect(page.locator('#stacks .stack:not(.empty-slot)')).toHaveCount(14);
  const id = await page.evaluate(() => window.__deepSalvage.drop('prism'));
  await page.locator(`.loot[data-id="${id}"]`).click();
  await expect(page.locator('#toast')).toHaveText('Storage full');
  await expect(page.locator(`.loot[data-id="${id}"]`)).toBeVisible();
  await expect(page.locator('#modal')).not.toBeVisible();
  for (const index of [0,1]) await drag(page, await storedPart(page,'amplifier'), forge(page,index));
  await page.evaluate(() => window.__deepSalvage.advance(7));
  await expect(page.locator('#modal-title')).toHaveText('Overcharger.');
  await page.getByRole('button',{name:"Got it. Let's build"}).click();
  await expect(forge(page,0)).toHaveAttribute('data-type','amplifier2');
  await expect(forge(page,0)).toBeEnabled();
  await expect(page.locator('#stacks .stack:not(.empty-slot)')).toHaveCount(14);
  await forge(page,0).click();
  await expect(forge(page,0)).toHaveAttribute('data-type','amplifier2');
  await shot(page,'full-hold-forge-output');
  await drag(page,forge(page,0),cell(page,14));
  await expect(cell(page,14)).toHaveAttribute('aria-label',/Overcharger/);
});
