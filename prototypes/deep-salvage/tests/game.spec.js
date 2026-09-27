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
async function drag(page, source, target) {
  const a = await source.boundingBox(), b = await target.boundingBox();
  await page.mouse.move(a.x + a.width / 2, a.y + a.height / 2);
  await page.mouse.down();
  await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 12 });
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
  await page.locator('#manual').click(); await expect(page.locator('.guide-row')).toHaveCount(6);
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
  await cell(page, 17).tap();
  await expect(cell(page, 17)).toHaveAttribute('aria-label', /90 degrees/);
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
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: destination.x + 20, y: destination.y + 20 }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await expect(cell(page, 11)).toHaveAttribute('aria-label', /Mirror/);
  await expect(page.locator('.stack[data-type="mirror"] .count')).toHaveText('2');
  await context.close();
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
  await cell(page, 12).focus(); await page.keyboard.press('Enter');
  await expect(page.locator('#gun-label')).toHaveText('0 guns online');
  await page.keyboard.press('Delete');
  await expect(cell(page, 12)).toHaveClass(/empty/);
  await expect(page.locator('.stack[data-type="splitter"] .count')).toHaveText('1');
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
    grid[12] = { type: 'amplifier', rotation: 0 }; grid[7] = { type: 'lens', rotation: 0 };
    window.__deepSalvage.setGrid(grid); window.__deepSalvage.advance(180);
  });
  await expect(page.locator('#modal-title')).toHaveText('Still in one piece.');
  await page.getByRole('button', { name: 'Study the parts' }).click();
  await page.getByRole('button', { name: 'Back to the dive' }).click();
  await expect(page.locator('#modal-title')).toHaveText('Still in one piece.');
});
