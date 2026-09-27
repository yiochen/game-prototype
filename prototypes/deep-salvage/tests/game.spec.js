import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

const URL = '/prototypes/deep-salvage/?test';
const cell = (page, index) => page.locator(`.cell[data-index="${index}"]`);
async function boot(page) {
  await page.goto(URL);
  await expect(page.locator('canvas')).toHaveAttribute('data-ready', 'true');
  await page.getByRole('button', { name: "Let's dive" }).click();
  await expect(page.locator('#modal')).not.toBeVisible();
}
async function aimPreview(page, target, pointer) {
  const b = await target.boundingBox(), ghost = await page.locator('#drag-ghost').boundingBox();
  return { x: b.x + b.width / 2 - (ghost.x + ghost.width / 2 - pointer.x), y: b.y + b.height / 2 - (ghost.y + ghost.height / 2 - pointer.y) };
}
async function drag(page, source, target, beforeRelease) {
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
    return { world: box('#world'), console: box('#console'), board: box('#board'), storage: box('#storage'), cell: box('.cell'), footer: box('.console-footer'), width: innerWidth, height: innerHeight, scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight };
  });
}

test('Pixel-shaped portrait and landscape layouts fit, render Phaser art and stay error-free', async ({ page }) => {
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await page.evaluate(() => window.__deepSalvage.advance(3));
  for (const [name, width, height] of [['pixel-10-pro', 412, 924], ['pixel-large-css', 448, 1000], ['pixel-browser-bars', 412, 820], ['small-phone', 360, 740], ['landscape', 924, 412]]) {
    await page.setViewportSize({ width, height });
    await expect.poll(async () => (await page.locator('canvas').boundingBox()).width).toBeGreaterThan(100);
    const b = await bounds(page);
    expect(b.scrollWidth).toBeLessThanOrEqual(width); expect(b.scrollHeight).toBeLessThanOrEqual(height);
    expect(b.board.y).toBeGreaterThanOrEqual(b.console.y);
    expect(b.board.bottom).toBeLessThanOrEqual(b.storage.y + 1);
    expect(b.footer.bottom).toBeLessThanOrEqual(height + 1);
    expect(b.board.right).toBeLessThanOrEqual(width);
    expect(b.cell.w).toBeGreaterThanOrEqual(44);
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
  await expect(page.locator('.stack[data-type="splitter"] .count')).toHaveText('2');
  await page.locator('#manual').click(); await expect(page.locator('.guide-row')).toHaveCount(14);
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().paused)).toBe(true);
  await page.getByRole('button', { name: 'Back to the dive' }).click();
  await page.reload(); await page.getByRole('button', { name: "Let's dive" }).click();
  const id3 = await page.evaluate(() => window.__deepSalvage.drop('splitter'));
  await page.locator(`.loot[data-id="${id3}"]`).click();
  await expect(page.locator('#modal')).not.toBeVisible();
});

test('drag storage and battlefield parts into lab, rotate once, reject occupied targets, and return to storage', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await drag(page, page.locator('.stack[data-type="mirror"]'), cell(page, 11));
  await expect(cell(page, 11)).toHaveAttribute('aria-label', /Mirror, 0 degrees/);
  await expect(page.locator('.stack[data-type="mirror"] .count')).toHaveText('1');
  await cell(page, 11).click();
  await expect(cell(page, 11)).toHaveAttribute('aria-label', /Mirror, 90 degrees/);
  await drag(page, cell(page, 11), cell(page, 22));
  await expect(cell(page, 11)).toHaveAttribute('aria-label', /Mirror, 90 degrees/);
  await drag(page, cell(page, 11), page.locator('#storage'));
  await expect(cell(page, 11)).toHaveClass(/empty/);
  await expect(page.locator('.stack[data-type="mirror"] .count')).toHaveText('2');
  const id = await page.evaluate(() => window.__deepSalvage.drop('lens'));
  await drag(page, page.locator(`.loot[data-id="${id}"]`), cell(page, 12));
  await expect(page.locator('#modal-title')).toHaveText('Lens.');
  await page.getByRole('button', { name: "Got it. Let's build" }).click();
  await expect(cell(page, 12)).toHaveAttribute('aria-label', /Lens/);
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().circuit.guns[0].piercing)).toBe(true);
  await shot(page, 'installed-lens');
});

test('touch tap rotates exactly once, touch salvage works, and cancelled drag never consumes a stack', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 412, height: 924 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
  const page = await context.newPage(); await boot(page);
  await cell(page, 22).tap();
  await expect(cell(page, 22)).toHaveAttribute('aria-label', /90 degrees/);
  await expect(page.locator('#gun-label')).toHaveText('0 guns online');
  const id = await page.evaluate(() => window.__deepSalvage.drop('mirror'));
  await page.locator(`.loot[data-id="${id}"]`).tap();
  await expect(page.locator('.stack[data-type="mirror"] .count')).toHaveText('3');
  const source = await page.locator('.stack[data-type="mirror"]').boundingBox();
  const cdp = await context.newCDPSession(page);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: source.x + 20, y: source.y + 20 }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: source.x + 20, y: source.y - 30 }] });
  await expect(page.locator('#drag-ghost')).toBeVisible();
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchCancel', touchPoints: [] });
  await expect(page.locator('#drag-ghost')).not.toBeVisible();
  await expect(page.locator('.stack[data-type="mirror"] .count')).toHaveText('3');
  const destination = await cell(page, 11).boundingBox();
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: source.x + 20, y: source.y + 20 }] });
  const initialPointer = { x: destination.x + 20, y: destination.y + 20 };
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [initialPointer] });
  const pointer = await aimPreview(page, cell(page, 11), initialPointer);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [pointer] });
  await expect(cell(page, 11)).toHaveClass(/target/);
  expect(pointer.y).toBeGreaterThan(destination.y + destination.height);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await expect(cell(page, 11)).toHaveAttribute('aria-label', /Mirror/);
  await expect(page.locator('.stack[data-type="mirror"] .count')).toHaveText('2');
  await context.close();
});

test('preview center determines highlighted and committed destinations, including grid edges and storage', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await drag(page, page.locator('.stack[data-type="mirror"]'), cell(page, 21), async pointer => {
    await expect(cell(page, 21)).toHaveClass(/target/);
    const box = await cell(page, 21).boundingBox();
    expect(pointer.y).toBeGreaterThan(box.y + box.height);
    await shot(page, 'preview-aligned-bottom-row');
  });
  await expect(cell(page, 21)).toHaveAttribute('aria-label', /Mirror/);
  // An occupied preview destination must be rejected even with the finger over
  // an empty neighboring cell. No source part is consumed.
  await drag(page, page.locator('.stack[data-type="mirror"]'), cell(page, 17), async () => {
    await expect(cell(page, 17)).toHaveClass(/invalid/);
  });
  await expect(page.locator('.stack[data-type="mirror"] .count')).toHaveText('1');
  await drag(page, cell(page, 21), page.locator('#storage'), async () => {
    await expect(page.locator('#storage')).toHaveClass(/drop-target/);
  });
  await expect(cell(page, 21)).toHaveClass(/empty/);
  await expect(page.locator('.stack[data-type="mirror"] .count')).toHaveText('2');
});

test('a gun beside the reactor stays powered and ignores rotation taps', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await drag(page, cell(page, 2), cell(page, 24));
  await cell(page, 22).click(); // Reactor now emits right through empty cell 23.
  for (let rotation = 0; rotation < 4; rotation++) {
    await expect(page.locator('#gun-label')).toHaveText('1 gun online');
    await expect(cell(page, 24)).toHaveClass(/active/);
    await cell(page, 24).click();
  }
  await expect(page.locator('#gun-label')).toHaveText('1 gun online');
  await page.locator('#manual').click();
  await expect(page.locator('.guide-row').filter({ has: page.getByRole('heading', { name: 'Gun', exact: true }) })).toContainText('all four sides');
});

test('a horizontal circuit amplifies, pierces and splits without orienting its parts', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await page.evaluate(() => {
    const grid = Array(25).fill(null);
    grid[10] = { type: 'reactor', rotation: 1 };
    grid[11] = { type: 'amplifier', rotation: 0 };
    grid[12] = { type: 'lens', rotation: 0 };
    grid[13] = { type: 'splitter', rotation: 0 };
    grid[8] = { type: 'gun', rotation: 0 };
    grid[18] = { type: 'gun', rotation: 0 };
    window.__deepSalvage.setGrid(grid);
  });
  for (const index of [11, 12, 13, 8, 18]) {
    await expect(cell(page, index)).toHaveAttribute('aria-label', /accepts beams from any side/);
    await cell(page, index).click();
    await expect(page.locator('#gun-label')).toHaveText('2 guns online');
  }
  const snapshot = await page.evaluate(() => window.__deepSalvage.snapshot());
  expect(snapshot.circuit.guns.map(g => ({ power: g.power, piercing: g.piercing }))).toEqual([{ power: 6, piercing: true }, { power: 6, piercing: true }]);
  expect([11, 12, 13, 8, 18].every(index => snapshot.grid[index].rotation === 0)).toBe(true);
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
  await drag(page, page.locator('.stack[data-type="gun"]'), cell(page, 3));
  await drag(page, page.locator('.stack[data-type="mirror"]'), cell(page, 11));
  await cell(page, 11).click();
  await drag(page, page.locator('.stack[data-type="mirror"]'), cell(page, 13));
  await page.locator('.stack[data-type="splitter"]').click();
  await cell(page, 12).click();
  await expect(page.locator('#gun-label')).toHaveText('2 guns online');
  const snapshot = await page.evaluate(() => window.__deepSalvage.snapshot());
  expect(snapshot.circuit.guns.map(g => g.power)).toEqual([6, 6]);
  expect(snapshot.grid[6]).toBeNull(); expect(snapshot.grid[8]).toBeNull();
  await shot(page, 'two-gun-circuit');
  await cell(page, 11).focus(); await page.keyboard.press('Enter');
  await expect(page.locator('#gun-label')).toHaveText('1 gun online');
  await page.keyboard.press('Delete');
  await expect(cell(page, 11)).toHaveClass(/empty/);
  await expect(page.locator('.stack[data-type="mirror"] .count')).toHaveText('1');
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
  await page.evaluate(() => { window.__deepSalvage.setGrid(Array(25).fill(null)); window.__deepSalvage.advance(180); });
  await expect(page.locator('#modal-title')).toHaveText('A brave little dive.');
  await page.getByRole('button', { name: 'Another dive' }).click();
  await expect(page.locator('#hull-label')).toHaveText('100');
  await expect(page.locator('#gun-label')).toHaveText('1 gun online');
});

test('an upgraded circuit reaches the beacon and end-state guide returns to the ending', async ({ page }) => {
  await boot(page);
  await page.evaluate(() => {
    const grid = window.__deepSalvage.snapshot().grid;
    grid[12] = { type: 'amplifier2', rotation: 0 }; grid[7] = { type: 'lens', rotation: 0 };
    window.__deepSalvage.setGrid(grid); window.__deepSalvage.advance(180);
  });
  await expect(page.locator('#modal-title')).toHaveText('Still in one piece.');
  await page.getByRole('button', { name: 'Study the parts' }).click();
  await page.getByRole('button', { name: 'Back to the dive' }).click();
  await expect(page.locator('#modal-title')).toHaveText('Still in one piece.');
});

test('drag duplicate parts to forge, highlight matches, pay once, pause timer, and install the upgraded output', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await drag(page, page.locator('.stack[data-type="amplifier"]'), page.locator('#forge-tab'));
  await expect(page.locator('.forge-slot[data-slot="0"]')).toHaveAttribute('data-type', 'amplifier');
  await expect(cell(page, 17)).toHaveClass(/forge-match/);
  await page.locator('#hold-tab').click();
  await expect(page.locator('.stack[data-type="amplifier"]')).toHaveClass(/forge-match/);
  await expect(page.locator('.stack[data-type="mirror"]')).not.toHaveClass(/forge-match/);
  await shot(page, 'forge-matching-parts');
  await drag(page, page.locator('.stack[data-type="amplifier"]'), page.locator('#forge-tab'));
  await expect(page.locator('#forge-result')).toHaveText('Overcharger');
  await page.evaluate(() => window.__deepSalvage.setCash(23));
  await expect(page.locator('#forge-start')).toBeDisabled();
  await page.evaluate(() => window.__deepSalvage.setCash(24));
  await page.locator('#forge-start').click();
  await expect(page.locator('#cash-label')).toHaveText('0');
  await expect(page.locator('.forge-slot').first()).toBeDisabled();
  await shot(page, 'forge-working');
  await page.locator('#pause').click();
  const before = await page.evaluate(() => window.__deepSalvage.snapshot().forge.job.remaining);
  await page.evaluate(() => window.__deepSalvage.advance(20));
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().forge.job.remaining)).toBe(before);
  await page.getByRole('button', { name: 'Keep going' }).click();
  await page.evaluate(() => window.__deepSalvage.advance(7));
  await expect(page.locator('#modal-title')).toHaveText('Overcharger.');
  await page.getByRole('button', { name: "Got it. Let's build" }).click();
  await page.locator('#hold-tab').click();
  await expect(page.locator('.stack[data-type="amplifier2"] .count')).toHaveText('1');
  await drag(page, page.locator('.stack[data-type="amplifier2"]'), cell(page, 12));
  await expect(cell(page, 2).locator('.part-readout')).toHaveText('28.8');
  await expect(cell(page, 12).locator('.tier-badge')).toHaveText('II');
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().forged)).toBe(1);
});

test('mixed recipe glows on battlefield, rejects incompatible parts, and its output makes stronger piercing beams', async ({ page }) => {
  await page.setViewportSize({ width: 412, height: 924 }); await boot(page);
  await page.evaluate(() => window.__deepSalvage.setCash(100));
  await drag(page, page.locator('.stack[data-type="amplifier"]'), page.locator('#forge-tab'));
  await page.locator('#hold-tab').click();
  await drag(page, page.locator('.stack[data-type="mirror"]'), page.locator('#forge-tab'), async () => {
    await expect(page.locator('#forge-tab')).toHaveClass(/invalid/);
  });
  await expect(page.locator('.stack[data-type="mirror"] .count')).toHaveText('2');
  const id = await page.evaluate(() => window.__deepSalvage.drop('lens'));
  await expect(page.locator(`.loot[data-id="${id}"]`)).toHaveClass(/forge-match/);
  await drag(page, page.locator(`.loot[data-id="${id}"]`), page.locator('#forge-tab'));
  await page.getByRole('button', { name: "Got it. Let's build" }).click();
  await expect(page.locator('#forge-result')).toHaveText('Piercing amplifier');
  await page.locator('#forge-start').click();
  await page.evaluate(() => window.__deepSalvage.advance(9));
  await expect(page.locator('#modal-title')).toHaveText('Piercing amplifier.');
  await page.getByRole('button', { name: "Got it. Let's build" }).click();
  await page.locator('#hold-tab').click();
  await drag(page, page.locator('.stack[data-type="prism"]'), cell(page, 12));
  await expect(cell(page, 2).locator('.part-readout')).toHaveText('21 ◆');
  await expect(page.locator('.beam[data-power="8"][data-piercing="false"]')).toHaveCount(1);
  await expect(page.locator('.beam[data-power="12"][data-piercing="false"]')).toHaveCount(1);
  const blue = page.locator('.beam[data-power="21"][data-piercing="true"]');
  await expect(blue).toHaveCount(2);
  expect(await blue.first().evaluate(el => parseFloat(el.style.strokeWidth))).toBeGreaterThan(await page.locator('.beam[data-power="8"]').evaluate(el => parseFloat(el.style.strokeWidth)));
  await shot(page, 'forged-piercing-beam');
});

test('forge ingredients can be returned safely and forge layout fits small phones and landscape', async ({ page }) => {
  await boot(page);
  await drag(page, cell(page, 17), page.locator('#forge-tab'));
  await page.locator('.forge-slot[data-slot="0"]').click();
  expect(await page.evaluate(() => window.__deepSalvage.snapshot().inventory.amplifier)).toBe(3);
  await expect(page.locator('.forge-slot[data-slot="0"]')).toHaveAttribute('data-type', '');
  for (const [width, height] of [[360, 740], [412, 820], [924, 412]]) {
    await page.setViewportSize({ width, height });
    for (const selector of ['#forge', '#forge-start', '.forge-slot']) {
      const b = await page.locator(selector).first().boundingBox();
      expect(b.y + b.height).toBeLessThanOrEqual(height); expect(b.x + b.width).toBeLessThanOrEqual(width);
      expect(b.height).toBeGreaterThanOrEqual(44);
    }
    await shot(page, `forge-${width}x${height}`);
  }
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
